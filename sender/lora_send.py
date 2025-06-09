from LoRaRF import SX126x
import time
import uuid
import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')

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
            lora.send(line.strip().encode('utf-8'))
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

def main():
    print(f"🚀 Starting LoRa Node - Device ID: {device_id}")
    lora.begin()
    lora.setTxPower(config.getint('lora', 'tx_power'))
    lora.setFrequency(config.getfloat('lora', 'frequency'))
    lora.setSpreadingFactor(config.getint('lora', 'spreading_factor'))
    lora.setBandwidth(config.getint('lora', 'bandwidth'))
    lora.setCodingRate(config.getint('lora', 'coding_rate'))
    lora.setPreambleLength(config.getint('lora', 'preamble_length'))

    temp = config.getfloat('send', 'mock_temp')
    hum = config.getfloat('send', 'mock_hum')
    ph = config.getfloat('send', 'mock_ph')
    interval = config.getint('send', 'interval')

    counter = 0
    while True:
        payload = f"id:{device_id},temp:{temp},hum:{hum},ph:{ph},count:{counter}"

        try:
            lora.send(payload.encode('utf-8'))
            print(f"📤 Sent: {payload}")
            retry_unsent_data()
        except Exception as e:
            print(f"❌ Send failed: {e}")
            backup_payload(payload)

        counter += 1
        time.sleep(interval)

if __name__ == "__main__":
    main()
