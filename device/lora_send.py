import sx126x
import time
import uuid
import configparser
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import secrets
import json
import random

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

# สร้าง LoRa node object ตามแบบใน main.py
node = sx126x.sx126x(
    serial_num="/dev/ttyS0",
    freq=config.getint('lora', 'frequency', fallback=868),
    addr=config.getint('lora', 'address', fallback=0),
    power=config.getint('lora', 'tx_power', fallback=22),
    rssi=config.getboolean('lora', 'rssi', fallback=True),
    air_speed=config.getint('lora', 'air_speed', fallback=2400),
    relay=config.getboolean('lora', 'relay', fallback=False)
)

BACKUP_FILE = "unsent_data.log"

def backup_payload(payload):
    with open(BACKUP_FILE, "a") as f:
        f.write(payload + "\n")

def send_lora_message(message):
    """ส่งข้อความผ่าน LoRa ตามรูปแบบของ main.py"""
    try:
        # กำหนดค่าเริ่มต้นสำหรับการส่งแบบ broadcast
        dest_addr = config.getint('lora', 'dest_address', fallback=65535)  # broadcast address
        dest_freq = config.getint('lora', 'dest_frequency', fallback=868)
        
        # คำนวณ offset frequency
        offset_freq = dest_freq - (850 if dest_freq > 850 else 410)
        
        # สร้าง data packet ตามรูปแบบใน main.py
        # receiving node high/low + freq + own high/low + own freq + payload
        data = (bytes([dest_addr >> 8]) + 
                bytes([dest_addr & 0xff]) + 
                bytes([offset_freq]) + 
                bytes([node.addr >> 8]) + 
                bytes([node.addr & 0xff]) + 
                bytes([node.offset_freq]) + 
                message.encode('utf-8'))
        
        node.send(message.encode('utf-8'))
        return True
    except Exception as e:
        print(f"❌ LoRa send error: {e}")
        return False

def retry_unsent_data():
    if not os.path.exists(BACKUP_FILE):
        return

    with open(BACKUP_FILE, "r") as f:
        lines = f.readlines()

    success_lines = []
    for line in lines:
        try:
            encrypted = line.strip()
            if send_lora_message(encrypted):
                print(f"📤 Retried: {encrypted[:50]}...")
                success_lines.append(line)
                time.sleep(0.5)
            else:
                break
        except Exception as e:
            print(f"⚠️ Retry failed: {e}")
            break

    if len(success_lines) == len(lines):
        os.remove(BACKUP_FILE)
        print("🧹 All retries sent successfully. Backup log removed.")
    else:
        with open(BACKUP_FILE, "w") as f:
            for line in lines:
                if line not in success_lines:
                    f.write(line)

def encrypt_payload(plain_text: str) -> str:
    start_time = time.perf_counter()

    backend = default_backend()
    iv = secrets.token_bytes(16)  # สุ่ม IV 16 bytes
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()

    # PKCS#7 padding แบบง่าย
    raw = plain_text.encode('utf-8')
    pad_len = 16 - (len(raw) % 16)
    padded_data = raw + bytes([pad_len] * pad_len)

    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    encoded = base64.b64encode(iv + encrypted).decode('utf-8')

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"⏱️ Encryption time: {elapsed:.6f} seconds")

    return encoded

def generate_sensor_data():
    """สร้างข้อมูลเซ็นเซอร์แบบ mock หรือจากค่าจริง"""
    # ใช้ค่าจาก config หรือสุ่มค่าใหม่
    use_random = config.getboolean('send', 'use_random', fallback=False)
    
    if use_random:
        temp = round(random.uniform(20.0, 40.0), 2)
        hum = round(random.uniform(30.0, 90.0), 2)
        pressure = round(random.uniform(980.0, 1020.0), 2)
        battery = round(random.uniform(10.0, 100.0), 2)
    else:
        temp = config.getfloat('send', 'mock_temp', fallback=25.5)
        hum = config.getfloat('send', 'mock_hum', fallback=60.0)
        pressure = config.getfloat('send', 'mock_pressure', fallback=1013.25)
        battery = config.getfloat('send', 'mock_battery', fallback=85.0)
    
    return temp, hum, pressure, battery

def main():
    print(f"🚀 Starting LoRa Node - Device ID: {device_id}")
    print(f"📡 LoRa Config: Freq={node.freq}MHz, Addr={node.addr}, Power={node.power}dBm")
    
    # รอให้ LoRa module พร้อม
    time.sleep(1)

    interval = config.getint('send', 'interval', fallback=10)
    enable_encryption = config.getboolean('send', 'enable_encryption', fallback=True)
    mock_rssi = config.getint('send', 'mock_rssi', fallback=-85)

    while True:
        try:
            # สร้างข้อมูลเซ็นเซอร์
            temp, hum, pressure, battery = generate_sensor_data()
            
            # สร้าง JSON payload
            data = {
                "device_id": device_id,
                "timestamp": time.time(),
                "temperature": temp,
                "humidity": hum,
                "pressure": pressure,
                "battery": battery,
                "rssi": mock_rssi,
                "encrypted": enable_encryption,
                "mock": True
            }
            
            payload = json.dumps(data, separators=(',', ':'))  # compact JSON
            print(f"📊 Data: {payload}")
            
            # เข้ารหัสถ้าเปิดใช้งาน
            if enable_encryption:
                final_payload = encrypt_payload(payload)
                print(f"🔐 Encrypted length: {len(final_payload)} bytes")
            else:
                final_payload = payload

            if send_lora_message(final_payload):
                print(f"📤 Sent successfully!")
                retry_unsent_data()
            else:
                print(f"❌ Send failed")
                backup_payload(final_payload)

            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping LoRa sender...")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(5)  # รอก่อนลองใหม่

if __name__ == "__main__":
    main()