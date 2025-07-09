# device/main.py

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
from core.encryption import EncryptionManager

KEYFILE = 'keyfile.bin'

config = configparser.ConfigParser()
config.read('config.ini')

debug = config.getboolean('debug', 'enabled', fallback=False)

def load_key():
    if not os.path.exists(KEYFILE):
        raise FileNotFoundError(f"Key file '{KEYFILE}' not found.")
    with open(KEYFILE, 'rb') as f:
        key = f.read()
        if len(key) != 32:
            raise ValueError("Key length must be exactly 32 bytes (256 bits).")
        return key

EN_KEY = base64.b64encode(load_key()).decode('utf-8')
em = EncryptionManager(method="AES", key=EN_KEY)

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
    try:
        dest_addr = config.getint('lora', 'dest_address', fallback=65535)
        dest_freq = config.getint('lora', 'dest_frequency', fallback=868)
        offset_freq = dest_freq - (850 if dest_freq > 850 else 410)
        if debug:
            print(f"🔧 Debug - Dest: {dest_addr}, Freq: {dest_freq}, Offset: {offset_freq}")
            print(f"🔧 Debug - Source: {node.addr}, Source Offset: {node.offset_freq}")
        
        # สร้าง header
        header = bytes([
            dest_addr >> 8,
            dest_addr & 0xff, 
            offset_freq,
            node.addr >> 8,
            node.addr & 0xff,
            node.offset_freq
        ])
        
        payload_bytes = message.encode('utf-8')
        full_packet = header + payload_bytes
        
        if debug:
        # Debug output
            print(f"🔧 Header hex: {header.hex()}")
            print(f"🔧 Payload: {message}")
            print(f"🔧 Payload hex: {payload_bytes.hex()}")
            print(f"🔧 Full packet hex: {full_packet.hex()}")
            print(f"🔧 Full packet length: {len(full_packet)} bytes")
        
        # ส่งข้อมูล
        node.send(full_packet)
        
        return True
    except Exception as e:
        print(f"❌ LoRa send error: {e}")
        import traceback
        traceback.print_exc()
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
                if debug:
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


def generate_mock_sensor_data():
    data = {
        "timestamp": time.time(),
        "sensor_readings": {
            "ph": round(random.uniform(6.5, 8.5), 2),
            "ec": random.randint(600, 1200),          # µS/cm
            "tds": random.randint(300, 600),          # ppm
            "salinity": round(random.uniform(0.1, 0.6), 2),  # ppt
            "do": round(random.uniform(5.0, 9.0), 2),        # mg/L
            "saturation": round(random.uniform(70.0, 100.0), 1)  # %
        },
        "location": {
            "device_id": device_id,
            "site": None,
            "battery": None,
            "rssi": None,
            "coordinates": {
                "lat": None,
                "lon": None
            }
        }
    }
    return data

def main():
    print(f"🚀 Starting LoRa Node - Device ID: {device_id}")
    print(f"📡 LoRa Config: Freq={node.freq}MHz, Addr={node.addr}, Power={node.power}dBm")
    
    # รอให้ LoRa module พร้อม
    time.sleep(1)

    interval = config.getint('send', 'interval', fallback=10)
    enable_encryption = config.getboolean('encryption', 'enable_encryption', fallback=True)
    mock_rssi = config.getint('send', 'mock_rssi', fallback=-85)

    while True:
        try:
            # สร้างข้อมูลเซ็นเซอร์
            data = generate_mock_sensor_data()
                        
            payload = json.dumps(data, separators=(',', ':'))  # compact JSON
            if debug:
                print(f"📊 Data: {payload}")
            
            # เข้ารหัสถ้าเปิดใช้งาน
            if enable_encryption:
                final_payload = "[EN]"+em.encrypt(payload)
                print(f"🔐 Encrypted length: {len(final_payload)} bytes")
                
            else:
                final_payload = payload
                
            if send_lora_message(final_payload):
                print("📤 Sent successfully!")
                retry_unsent_data()
            else:
                print("❌ Send failed")
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