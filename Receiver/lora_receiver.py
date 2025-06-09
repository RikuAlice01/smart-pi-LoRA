from LoRaRF import SX126x
import time
import configparser
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

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

def decrypt_payload(encoded_text: str) -> str:
    backend = default_backend()
    raw = base64.b64decode(encoded_text)
    iv = raw[:16]
    encrypted_data = raw[16:]

    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    padded_plain = decryptor.update(encrypted_data) + decryptor.finalize()

    pad_len = padded_plain[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Invalid padding length.")
    plain = padded_plain[:-pad_len]

    return plain.decode('utf-8')

def main():
    print("🚀 Starting LoRa Receiver")
    lora = SX126x()
    lora.begin()
    lora.setFrequency(config.getfloat('lora', 'frequency'))
    lora.setSpreadingFactor(config.getint('lora', 'spreading_factor'))
    lora.setBandwidth(config.getint('lora', 'bandwidth'))
    lora.setCodeRate(config.getint('lora', 'coding_rate'))
    lora.setPreambleLength(config.getint('lora', 'preamble_length'))

    while True:
        try:
            data = lora.receive(timeout=10)
            if data:
                encrypted_str = data.decode('utf-8')
                print(f"📥 Received encrypted: {encrypted_str}")

                plaintext = decrypt_payload(encrypted_str)
                print(f"🔓 Decrypted payload: {plaintext}")

            else:
                print("⏳ Waiting for data...")

        except Exception as e:
            print(f"⚠️ Error during receive or decrypt: {e}")

        time.sleep(0.5)

if __name__ == "__main__":
    main()
