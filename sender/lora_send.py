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

def retry_unsent_data():
    if not os.path.exists(BACKUP_FILE):
        return

    with open(BACKUP_FILE, "r") as f:
        lines = f.readlines()

    success_lines = []
    for line in lines:
        try:
            encrypted = line.strip().encode('utf-8')
            lora.send(encrypted)
            print(f"📤 Retried: {line.strip()}")
            success_lines.append(line)
            time.sleep(0.5)
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

def main():
    print(f"🚀 Starting LoRa Node - Device ID: {device_id}")
    lora.begin()
    lora.setTxPower(config.getint('lora', 'tx_power'))
    lora.setFrequency(config.getfloat('lora', 'frequency'))
    lora.setSpreadingFactor(config.getint('lora', 'spreading_factor'))
    lora.setBandwidth(config.getint('lora', 'bandwidth'))
    lora.setCodeRate(config.getint('lora', 'coding_rate'))
    lora.setPreambleLength(config.getint('lora', 'preamble_length'))

    temp = config.getfloat('send', 'mock_temp')
    hum = config.getfloat('send', 'mock_hum')
    ph = config.getfloat('send', 'mock_ph')
    interval = config.getint('send', 'interval')

    counter = 0
    while True:
        # เพิ่ม timestamp เป็น ISO 8601 UTC string
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        payload = f"id:{device_id},temp:{temp},hum:{hum},ph:{ph},count:{counter},timestamp:{timestamp}"
        encrypted_payload = encrypt_payload(payload)

        try:
            lora.write(encrypted_payload.encode('utf-8'))
            print(f"📤 Sent (encrypted): {encrypted_payload}")
            retry_unsent_data()
        except Exception as e:
            print(f"❌ Send failed: {e}")
            backup_payload(encrypted_payload)

        counter += 1
        time.sleep(interval)

if __name__ == "__main__":
    main()
