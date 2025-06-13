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
    try:
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
    except Exception as e:
        raise Exception(f"Decryption failed: {e}")

def check_spi_devices():
    """Check if SPI devices are available"""
    spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1', '/dev/spidev1.0', '/dev/spidev1.1']
    available_devices = []
    
    for device in spi_devices:
        if os.path.exists(device):
            available_devices.append(device)
    
    return available_devices

def test_lora_communication(lora):
    """Test if LoRa module is responding"""
    try:
        status = lora.getModemStatus()
        print(f"✅ LoRa module status: {status}")
        return True
    except Exception as e:
        print(f"❌ LoRa communication test failed: {e}")
        return False

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
                    
                    # Test communication
                    if test_lora_communication(lora):
                        print(f"✅ Successfully connected with bus={bus}, cs={cs}")
                        success = True
                        break
                    else:
                        print(f"❌ Communication test failed for bus={bus}, cs={cs}")
                        
                except Exception as e:
                    print(f"❌ Failed with bus={bus}, cs={cs}: {e}")
        
        if not success:
            print("❌ All SPI configurations failed.")
            print("🔧 Hardware troubleshooting:")
            print("   1. Check LoRa module connections")
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
        
        # Set LoRa packet mode
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
        
        print("✅ LoRa module configured successfully")
        
        # ✅ เพิ่มการตรวจสอบ RSSI และ SNR
        print("📡 Listening for messages...")
        receive_count = 0
        last_activity = time.time()
        
        while True:
            try:
                # ✅ ปรับปรุงการรับข้อมูล
                if lora.available():
                    receive_count += 1
                    current_time = time.time()
                    
                    # อ่านข้อมูลทั้งหมด
                    data = lora.read()
                    
                    # ตรวจสอบ RSSI และ SNR
                    rssi = lora.getRSSI()
                    snr = lora.getSNR()
                    
                    print(f"\n📡 === Message #{receive_count} ===")
                    print(f"📏 Received {len(data)} bytes")
                    print(f"📊 RSSI: {rssi} dBm, SNR: {snr} dB")
                    
                    try:
                        # ลองแปลงเป็น string
                        if isinstance(data, (bytes, bytearray)):
                            encrypted_str = data.decode('utf-8')
                        else:
                            encrypted_str = ''.join(chr(b) for b in data)
                            
                        print(f"📥 Encrypted data: {encrypted_str[:100]}...")
                        
                        # ถอดรหัส
                        plaintext = decrypt_payload(encrypted_str)
                        print(f"🔓 Decrypted: {plaintext}")
                        
                        last_activity = current_time
                        
                    except UnicodeDecodeError:
                        print(f"📥 Raw data (non-UTF8): {data[:50].hex()}...")
                    except Exception as decrypt_error:
                        print(f"🔓 Decryption failed: {decrypt_error}")
                        if 'encrypted_str' in locals():
                            print(f"📥 Failed data: {encrypted_str[:100]}...")
                        else:
                            print(f"📥 Raw data: {data[:50].hex()}...")
                    
                    print("=" * 40)
                    
                else:
                    # แสดงสถานะการรอ
                    current_time = time.time()
                    elapsed = current_time - last_activity
                    
                    if int(elapsed) % 30 == 0:  # แสดงทุก 30 วินาที
                        print(f"⏳ Waiting... (no data for {elapsed:.0f}s, received: {receive_count})")
                    
                    time.sleep(0.1)  # ลดการใช้ CPU
                    
            except KeyboardInterrupt:
                print("\n🛑 Stopping receiver...")
                break
            except Exception as e:
                print(f"⚠️ Error during receive: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"❌ Failed to initialize LoRa module: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()