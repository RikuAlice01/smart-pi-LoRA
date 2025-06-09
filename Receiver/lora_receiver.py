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

def check_spi_devices():
    """Check if SPI devices are available"""
    spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1', '/dev/spidev1.0', '/dev/spidev1.1']
    available_devices = []
    
    for device in spi_devices:
        if os.path.exists(device):
            available_devices.append(device)
    
    return available_devices

def main():
    print("🚀 Starting LoRa Receiver")
    
    # Check SPI devices first
    print("🔍 Checking SPI devices...")
    spi_devices = check_spi_devices()
    
    if not spi_devices:
        print("❌ No SPI devices found!")
        print("🔧 To fix this:")
        print("   1. Run: sudo raspi-config")
        print("   2. Go to Interface Options > SPI > Enable")
        print("   3. Reboot your Pi")
        print("   4. Or run: echo 'dtparam=spi=on' | sudo tee -a /boot/config.txt && sudo reboot")
        return
    else:
        print(f"✅ Found SPI devices: {spi_devices}")
    
    # Initialize LoRa module
    lora = SX126x()
    
    try:
        # Try different SPI configurations
        print("🔧 Attempting to initialize LoRa module...")
        
        configs_to_try = [
            (0, 0, "/dev/spidev0.0"),
            (0, 1, "/dev/spidev0.1"), 
            (1, 0, "/dev/spidev1.0"),
            (1, 1, "/dev/spidev1.1")
        ]
        
        success = False
        for bus, cs, device in configs_to_try:
            if os.path.exists(device):
                try:
                    print(f"🔧 Trying bus={bus}, cs={cs} ({device})...")
                    lora.begin(bus=bus, cs=cs)
                    print(f"✅ Successfully connected with bus={bus}, cs={cs}")
                    success = True
                    break
                except Exception as e:
                    print(f"❌ Failed with bus={bus}, cs={cs}: {e}")
        
        if not success:
            print("❌ All SPI configurations failed.")
            print("🔧 Hardware troubleshooting:")
            print("   1. Check LoRa module connections:")
            print("      VCC  → 3.3V (Pin 1)")
            print("      GND  → GND  (Pin 6)")
            print("      SCK  → GPIO 11 (Pin 23)")  
            print("      MISO → GPIO 9  (Pin 21)")
            print("      MOSI → GPIO 10 (Pin 19)")
            print("      CS   → GPIO 8  (Pin 24)")
            print("   2. Verify 3.3V power supply (NOT 5V)")
            print("   3. Check for loose connections")
            return
        
        # Configure LoRa parameters
        print("🔧 Configuring LoRa parameters...")
        lora.setFrequency(config.getfloat('lora', 'frequency'))
        lora.setSpreadingFactor(config.getint('lora', 'spreading_factor'))
        lora.setBandwidth(config.getint('lora', 'bandwidth'))
        lora.setCodeRate(config.getint('lora', 'coding_rate'))
        lora.setPreambleLength(config.getint('lora', 'preamble_length'))
        
        # Set to receive mode - Use simpler approach
        try:
            # Try the old method first
            lora.setLoRaPacket(True)
            print("✅ Using basic LoRa packet mode")
        except TypeError:
            # If that fails, try with all parameters
            lora.setLoRaPacket(
                implicitHeader=False,
                preambleLength=config.getint('lora', 'preamble_length'),
                payloadLength=255,
                crcOn=True
            )
            print("✅ Using advanced LoRa packet mode")
        
        lora.setBlockingReceive(False)
        print("✅ LoRa module configured successfully")
        
        print("📡 Listening for messages...")
        
        while True:
            try:
                rx_len = lora.available()
                if rx_len:
                    print(f"📏 Received {rx_len} bytes")
                    data = bytearray()
                    for i in range(rx_len):
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
                        print(f"📥 Raw encrypted data: {encrypted_str if 'encrypted_str' in locals() else data.hex()}")
                else:
                    print("⏳ Waiting for data...", end='\r')
                    
            except Exception as e:
                print(f"⚠️ Error during receive: {e}")
                
            time.sleep(1)
            
    except Exception as e:
        print(f"❌ Failed to initialize LoRa module: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()