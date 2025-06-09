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
    
    # Initialize LoRa module
    lora = SX126x()
    
    try:
        # Try different SPI configurations
        print("🔧 Attempting to initialize LoRa module...")
        
        # Try bus=0, cs=0 first
        try:
            lora.begin(bus=0, cs=0)
            print("✅ Successfully connected with bus=0, cs=0")
        except:
            print("❌ Failed with bus=0, cs=0, trying bus=0, cs=1...")
            try:
                lora.begin(bus=0, cs=1)
                print("✅ Successfully connected with bus=0, cs=1")
            except:
                print("❌ Failed with bus=0, cs=1, trying bus=1, cs=0...")
                try:
                    lora.begin(bus=1, cs=0)
                    print("✅ Successfully connected with bus=1, cs=0")
                except:
                    print("❌ All SPI configurations failed. Check hardware connections.")
                    return
        
        # Configure LoRa parameters
        print("🔧 Configuring LoRa parameters...")
        lora.setFrequency(config.getfloat('lora', 'frequency'))
        lora.setSpreadingFactor(config.getint('lora', 'spreading_factor'))
        lora.setBandwidth(config.getint('lora', 'bandwidth'))
        lora.setCodeRate(config.getint('lora', 'coding_rate'))
        lora.setPreambleLength(config.getint('lora', 'preamble_length'))
        
        # Set to receive mode
        lora.setLoRaPacket(True)
        lora.setBlockingReceive(False)
        print("✅ LoRa module configured successfully")
        
        print("📡 Listening for messages...")
        
        while True:
            try:
                rx_len = lora.available()
                if rx_len:
                    data = bytearray()
                    for i in range(rx_len):  # Fixed: was "for * in range(rx*len)"
                        data.append(lora.read())
                    
                    try:
                        encrypted_str = data.decode('utf-8')
                        print(f"📥 Received encrypted: {encrypted_str}")
                        plaintext = decrypt_payload(encrypted_str)
                        print(f"🔓 Decrypted payload: {plaintext}")
                    except UnicodeDecodeError:
                        print(f"📥 Received raw data (non-UTF8): {data.hex()}")
                    except Exception as decrypt_error:
                        print(f"🔓 Decryption failed: {decrypt_error}")
                        print(f"📥 Raw encrypted data: {encrypted_str if 'encrypted_str' in locals() else 'N/A'}")
                else:
                    print("⏳ Waiting for data...")
                    
            except Exception as e:
                print(f"⚠️ Error during receive: {e}")
                
            time.sleep(0.5)
            
    except Exception as e:
        print(f"❌ Failed to initialize LoRa module: {e}")
        print("🔧 Troubleshooting tips:")
        print("   1. Check SPI connections (MOSI, MISO, SCK, CS)")
        print("   2. Verify power supply (3.3V)")
        print("   3. Check if SPI is enabled: sudo raspi-config")
        print("   4. Try different CS pins")
        print("   5. Verify module is properly seated")

if __name__ == "__main__":  # Fixed: was "if **name** == "__main__""
    main()