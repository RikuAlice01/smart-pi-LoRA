from LoRaRF import SX126x
import time

def test_lora_connection():
    """ทดสอบการเชื่อมต่อ LoRa แบบง่าย"""
    
    print("🔧 Testing LoRa Connection...")
    
    lora = SX126x()
    
    try:
        # ลองเชื่อมต่อ
        lora.begin()
        print("✅ LoRa.begin() successful")
        
        # ทดสอบการอ่านสถานะ
        try:
            status = lora.getModemStatus()
            print(f"✅ Modem Status: {status}")
        except:
            print("⚠️ Cannot read modem status")
        
        # กำหนดค่าพื้นฐาน
        lora.setFrequency(865.0)
        lora.setSpreadingFactor(7)
        lora.setBandwidth(125000)
        print("✅ Basic configuration set")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_simple_send():
    """ทดสอบส่งข้อความง่ายๆ"""
    
    if not test_lora_connection():
        return
    
    lora = SX126x()
    lora.begin()
    lora.setFrequency(865.0)
    lora.setSpreadingFactor(7)
    lora.setBandwidth(125000)
    
    message = "TEST123"
    print(f"📤 Sending: {message}")
    
    try:
        lora.write(message.encode(), len(message))
        print("✅ Send successful")
    except Exception as e:
        print(f"❌ Send failed: {e}")

def test_simple_receive():
    """ทดสอบรับข้อความง่ายๆ"""
    
    if not test_lora_connection():
        return
    
    lora = SX126x()
    lora.begin()
    lora.setFrequency(865.0)
    lora.setSpreadingFactor(7)
    lora.setBandwidth(125000)
    
    print("📡 Listening for simple messages...")
    
    for i in range(30):  # ฟัง 30 วินาที
        try:
            if lora.available():
                data = lora.read()
                print(f"📥 Received: {data}")
                
                try:
                    message = data.decode('utf-8')
                    print(f"🔤 Decoded: {message}")
                except:
                    print(f"📊 Raw: {data.hex()}")
                    
            else:
                print(f"⏳ Waiting... ({i+1}/30)")
                
        except Exception as e:
            print(f"⚠️ Error: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python lora_test.py test    - Test connection")
        print("  python lora_test.py send    - Test sending")  
        print("  python lora_test.py receive - Test receiving")
    elif sys.argv[1] == "test":
        test_lora_connection()
    elif sys.argv[1] == "send":
        test_simple_send()
    elif sys.argv[1] == "receive":
        test_simple_receive()
    else:
        print("Invalid command")