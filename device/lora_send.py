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

def load_key():
    if not os.path.exists(KEYFILE):
        raise FileNotFoundError(f"Key file '{KEYFILE}' not found.")
    with open(KEYFILE, 'rb') as f:
        key = f.read()
        if len(key) != 32:
            raise ValueError("Key length must be exactly 32 bytes (256 bits).")
        return key

EN_KEY = base64.b64encode(load_key()).decode('utf-8')

print(f"🔑 Loaded encryption key: {EN_KEY}")
em = EncryptionManager(method="AES", key=EN_KEY)

# original_data = '{"device_id":"node_E87F29","timestamp":1751868377.785197,"temperature":35.7,"humidity":79.37,"pressure":1010.13,"battery":21.42,"rssi":-85}'
# print(f"📝 ข้อมูลต้นฉบับ: {original_data}")

# # เข้ารหัส
# encrypted = em.encrypt(original_data)
# print(f"🔐 ข้อมูลที่เข้ารหัส: {encrypted}")
        
# # ตรวจสอบว่าข้อมูลถูกเข้ารหัสหรือไม่
# is_encrypted = em.is_encrypted(encrypted)
# print(f"✅ ข้อมูลถูกเข้ารหัส: {is_encrypted}")
        
# # ถอดรหัส
# decrypted = em.decrypt(encrypted)
# print(f"🔓 ข้อมูลที่ถอดรหัส: {decrypted}")

config = configparser.ConfigParser()
config.read('config.ini')

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
        # กำหนดค่าเริ่มต้นสำหรับการส่งแบบ broadcast
        dest_addr = config.getint('lora', 'dest_address', fallback=65535)  # broadcast address
        dest_freq = config.getint('lora', 'dest_frequency', fallback=868)
        
        # คำนวณ offset frequency
        offset_freq = dest_freq - (850 if dest_freq > 850 else 410)
        
        # สร้าง data packet ตามรูปแบบใน main.py
        # receiving node high/low + freq + own high/low + own freq + payload
        header = bytearray([
            dest_addr >> 8,           # destination address high byte
            dest_addr & 0xff,         # destination address low byte  
            offset_freq,              # destination frequency offset
            node.addr >> 8,           # source address high byte
            node.addr & 0xff,         # source address low byte
            node.offset_freq          # source frequency offset
        ])

        payload_bytes = message.encode('utf-8')
        full_packet = header + payload_bytes
        
        node.send(full_packet)
        print(f"📤 Sent {len(full_packet)} bytes: header={header.hex()} payload_len={len(payload_bytes)}")
        
        return True
    except Exception as e:
        print(f"❌ LoRa send error: {e}")
        return False

# # Alternative method - ถ้าต้องการใช้ node.send()
# def send_lora_message_alternative(message):
#     try:
#         dest_addr = config.getint('lora', 'dest_address', fallback=65535)
#         dest_freq = config.getint('lora', 'dest_frequency', fallback=868)
#         offset_freq = dest_freq - (850 if dest_freq > 850 else 410)
        
#         # สร้าง header เป็น bytes
#         header = bytes([
#             dest_addr >> 8,
#             dest_addr & 0xff, 
#             offset_freq,
#             node.addr >> 8,
#             node.addr & 0xff,
#             node.offset_freq
#         ])
        
#         # รวม header + message เป็น bytes
#         full_data = header + message.encode('utf-8')
        
#         # ส่งผ่าน node.send() โดยไม่ต้อง decode
#         node.send(full_data)
        
#         return True
#     except Exception as e:
#         print(f"❌ LoRa send error: {e}")
#         return False

def send_lora_message_debug(message):
    try:
        dest_addr = config.getint('lora', 'dest_address', fallback=65535)
        dest_freq = config.getint('lora', 'dest_frequency', fallback=868)
        offset_freq = dest_freq - (850 if dest_freq > 850 else 410)
        
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
                "rssi": mock_rssi
            }
            
            payload = json.dumps(data, separators=(',', ':'))  # compact JSON
            print(f"📊 Data: {payload}")
            
            # เข้ารหัสถ้าเปิดใช้งาน
            if enable_encryption:
                final_payload = em.encrypt(payload)
                print(f"🔐 Encrypted length: {len(final_payload)} bytes")
                
            else:
                final_payload = payload

            print(f"📦 Final payload: {final_payload}")
            
            final_payload = em.decrypt(final_payload)
            print(f"🔓 Decrypted payload: {final_payload}")
            
            
            # if send_lora_message(final_payload):
            #     print("📤 Sent successfully!")
            #     retry_unsent_data()
            # else:
            #     print("❌ Send failed")
            #     backup_payload(final_payload)

            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping LoRa sender...")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(5)  # รอก่อนลองใหม่

if __name__ == "__main__":
    main()