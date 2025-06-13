from LoRaRF import SX126x
import time
import uuid
import configparser
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import secrets
import datetime

config = configparser.ConfigParser()
config.read('config.ini')

KEYFILE = 'keyfile.bin'

def load_key():
    if not os.path.exists(KEYFILE):
        raise FileNotFoundError(f"Key file '{KEYFILE}' not found.")
    with open(KEYFILE, 'rb') as f:
        key = f.read()
        if len(key) != 32:
            raise ValueError("Key length must be exactly 32 bytes (256 bits).")
        return key

AES_KEY = load_key()

def get_device_id():
    mac = hex(uuid.getnode())[2:].upper().zfill(12)
    prefix = config.get('device', 'id_prefix', fallback='node_')
    return f"{prefix}{mac[-6:]}"

device_id = get_device_id()
lora = SX126x()
BACKUP_FILE = "unsent_data.log"

def backup_payload(payload):
    with open(BACKUP_FILE, "a") as f:
        f.write(payload + "\n")

def encrypt_payload(plain_text: str) -> str:
    start_time = time.perf_counter()

    backend = default_backend()
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()

    # PKCS#7 padding
    raw = plain_text.encode('utf-8')
    pad_len = 16 - (len(raw) % 16)
    padded_data = raw + bytes([pad_len] * pad_len)

    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    encoded = base64.b64encode(iv + encrypted).decode('utf-8')

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"⏱️ Encryption time: {elapsed:.6f} seconds")

    return encoded

def check_spi_connection():
    """Check if LoRa module responds"""
    try:
        # Try to read a register to verify communication
        version = lora.getModemStatus()
        print(f"✅ LoRa module responding, status: {version}")
        return True
    except Exception as e:
        print(f"❌ LoRa module not responding: {e}")
        return False

def main():
    print(f"🚀 Starting LoRa Node - Device ID: {device_id}")
    
    # Initialize with error handling
    try:
        lora.begin()
        print("✅ LoRa module initialized")
        
        # Check connection
        if not check_spi_connection():
            print("❌ Cannot communicate with LoRa module")
            return
            
    except Exception as e:
        print(f"❌ Failed to initialize LoRa: {e}")
        return
    
    # Configure LoRa parameters
    try:
        lora.setTxPower(config.getint('lora', 'tx_power'))
        lora.setFrequency(config.getfloat('lora', 'frequency'))
        lora.setSpreadingFactor(config.getint('lora', 'spreading_factor'))
        lora.setBandwidth(config.getint('lora', 'bandwidth'))
        lora.setCodeRate(config.getint('lora', 'coding_rate'))
        lora.setPreambleLength(config.getint('lora', 'preamble_length'))
        
        # ✅ เพิ่มการกำหนด LoRa packet mode ให้ตรงกับ receiver
        try:
            lora.setLoRaPacket(False, config.getint('lora', 'preamble_length'), 255)
            print("✅ Using basic LoRa packet mode")
        except TypeError:
            lora.setLoRaPacket(
                implicitHeader=False,
                preambleLength=config.getint('lora', 'preamble_length'),
                payloadLength=255,
                crcOn=True
            )
            print("✅ Using advanced LoRa packet mode")
            
        print("✅ LoRa parameters configured")
        
    except Exception as e:
        print(f"❌ Failed to configure LoRa: {e}")
        return

    temp = config.getfloat('send', 'mock_temp')
    hum = config.getfloat('send', 'mock_hum')
    ph = config.getfloat('send', 'mock_ph')
    interval = config.getint('send', 'interval')

    counter = 0
    consecutive_failures = 0
    
    while True:
        try:
            timestamp = datetime.datetime.utcnow().isoformat() + "Z"
            payload = f"id:{device_id},temp:{temp},hum:{hum},ph:{ph},count:{counter},timestamp:{timestamp}"
            
            print(f"📝 Original payload: {payload}")
            encrypted_payload = encrypt_payload(payload)
            print(f"🔐 Encrypted payload: {encrypted_payload}")
            
            # ✅ ปรับปรุงวิธีการส่งข้อมูล
            payload_bytes = encrypted_payload.encode('utf-8')
            print(f"📏 Payload length: {len(payload_bytes)} bytes")
            
            # ตรวจสอบขนาดข้อมูล
            if len(payload_bytes) > 255:
                print(f"⚠️ Payload too large: {len(payload_bytes)} bytes (max 255)")
                # ลดขนาดข้อมูลหรือแบ่งส่ง
                continue
            
            # ส่งข้อมูล
            lora.write(payload_bytes, len(payload_bytes))
            print(f"📤 Sent successfully: {len(payload_bytes)} bytes")
            
            consecutive_failures = 0
            
        except Exception as e:
            consecutive_failures += 1
            print(f"❌ Send failed (attempt {consecutive_failures}): {e}")
            backup_payload(encrypted_payload)
            
            # หยุดชั่วคราวถ้าเกิดข้อผิดพลาดติดต่อกัน
            if consecutive_failures >= 3:
                print("⚠️ Too many consecutive failures, waiting longer...")
                time.sleep(30)
                consecutive_failures = 0

        counter += 1
        time.sleep(interval)

if __name__ == "__main__":
    main()