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
        except Exception as e:
            print(f"⚠️ Cannot read modem status: {e}")
        
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
        # แปลงข้อความเป็น list ของ integers (bytes)
        message_bytes = list(message.encode('utf-8'))
        print(f"📊 Encoded bytes: {message_bytes}")
        
        # ส่งข้อมูล
        lora.write(message_bytes, len(message_bytes))
        print("✅ Send successful")
        
        # รอให้การส่งเสร็จสิ้น
        time.sleep(0.1)
        
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
            # ตรวจสอบว่ามีข้อมูลรับหรือไม่
            received_length = lora.available()
            
            if received_length > 0:
                print(f"📨 Data available: {received_length} bytes")
                
                # อ่านข้อมูล
                data = lora.read()
                print(f"📥 Raw received: {data} (type: {type(data)})")
                
                # ตรวจสอบประเภทของข้อมูลที่รับมา
                if isinstance(data, (list, tuple)):
                    # ถ้าเป็น list หรือ tuple ของ integers
                    try:
                        # แปลงเป็น bytes แล้วเป็น string
                        byte_data = bytes(data)
                        message = byte_data.decode('utf-8')
                        print(f"🔤 Decoded message: {message}")
                    except Exception as decode_error:
                        print(f"⚠️ Decode error: {decode_error}")
                        print(f"📊 Raw bytes: {[hex(b) for b in data]}")
                        
                elif isinstance(data, int):
                    # ถ้าเป็น integer เดี่ยว
                    try:
                        if data != 0:  # ไม่ใช่ค่าว่าง
                            message = chr(data)
                            print(f"🔤 Single char: {message}")
                        else:
                            print("📭 Empty data (0)")
                    except:
                        print(f"📊 Raw int: {data}")
                        
                elif isinstance(data, bytes):
                    # ถ้าเป็น bytes
                    try:
                        message = data.decode('utf-8')
                        print(f"🔤 Decoded message: {message}")
                    except:
                        print(f"📊 Raw bytes: {data.hex()}")
                        
                else:
                    print(f"❓ Unknown data type: {type(data)}")
                    
            else:
                print(f"⏳ Waiting... ({i+1}/30)")
                
        except Exception as e:
            print(f"⚠️ Receive error: {e}")
            
        time.sleep(1)

def test_ping_pong():
    """ทดสอบส่งและรับแบบ ping-pong"""
    
    if not test_lora_connection():
        return
    
    lora = SX126x()
    lora.begin()
    lora.setFrequency(865.0)
    lora.setSpreadingFactor(7)
    lora.setBandwidth(125000)
    
    print("🏓 Starting ping-pong test...")
    print("This will send a message every 5 seconds and listen in between")
    
    counter = 0
    
    for i in range(12):  # รัน 1 นาที (12 x 5 วินาที)
        # ส่งข้อความ
        counter += 1
        message = f"PING-{counter:03d}"
        
        try:
            message_bytes = list(message.encode('utf-8'))
            lora.write(message_bytes, len(message_bytes))
            print(f"📤 Sent: {message}")
        except Exception as e:
            print(f"❌ Send error: {e}")
        
        # ฟังข้อความตอบกลับ 5 วินาที
        print("📡 Listening for response...")
        
        for j in range(5):
            try:
                if lora.available() > 0:
                    data = lora.read()
                    
                    if isinstance(data, (list, tuple)):
                        try:
                            message_received = bytes(data).decode('utf-8')
                            print(f"📥 Received: {message_received}")
                        except:
                            print(f"📊 Raw response: {data}")
                    elif isinstance(data, int) and data != 0:
                        print(f"📥 Received single byte: {data} ({chr(data) if 32 <= data <= 126 else 'non-printable'})")
                    
            except Exception as e:
                print(f"⚠️ Listen error: {e}")
                
            time.sleep(1)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python lora_test.py test     - Test connection")
        print("  python lora_test.py send     - Test sending")  
        print("  python lora_test.py receive  - Test receiving")
        print("  python lora_test.py pingpong - Test ping-pong communication")
    elif sys.argv[1] == "test":
        test_lora_connection()
    elif sys.argv[1] == "send":
        test_simple_send()
    elif sys.argv[1] == "receive":
        test_simple_receive()
    elif sys.argv[1] == "pingpong":
        test_ping_pong()
    else:
        print("Invalid command")