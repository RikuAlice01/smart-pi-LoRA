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
        
        # ทดสอบการอ่านสถานะ (ข้ามไปถ้าไม่มี method นี้)
        try:
            # ลองใช้ method อื่นที่อาจมี
            if hasattr(lora, 'getStatus'):
                status = lora.getStatus()
                print(f"✅ Status: {status}")
            elif hasattr(lora, 'status'):
                status = lora.status()
                print(f"✅ Status: {status}")
            else:
                print("⚠️ No status method available")
        except Exception as e:
            print(f"⚠️ Cannot read status: {e}")
        
        # กำหนดค่าพื้นฐาน
        lora.setFrequency(865.0)
        lora.setSpreadingFactor(7)
        lora.setBandwidth(125000)
        print("✅ Basic configuration set")
        
        return lora  # คืนค่า lora object เพื่อใช้ต่อ
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def test_simple_send():
    """ทดสอบส่งข้อความง่ายๆ"""
    
    lora = test_lora_connection()
    if lora is None:
        return
    
    message = "TEST123"
    print(f"📤 Sending: {message}")
    
    try:
        # แปลงข้อความเป็น list ของ integers (bytes)
        message_bytes = list(message.encode('utf-8'))
        print(f"📊 Encoded bytes: {message_bytes}")
        
        # ส่งข้อมูล
        result = lora.write(message_bytes, len(message_bytes))
        print(f"✅ Send successful, result: {result}")
        
        # รอให้การส่งเสร็จสิ้น
        time.sleep(0.1)
        
    except Exception as e:
        print(f"❌ Send failed: {e}")
        # ลองวิธีอื่น
        try:
            print("🔄 Trying alternative send method...")
            # ลองส่งเป็น string
            result2 = lora.write(message)
            print(f"✅ Alternative send successful: {result2}")
        except Exception as e2:
            print(f"❌ Alternative send also failed: {e2}")
            
            # ลองส่งทีละ byte
            try:
                print("🔄 Trying byte-by-byte send...")
                for i, byte_val in enumerate(message_bytes):
                    lora.write([byte_val], 1)
                    time.sleep(0.01)
                print("✅ Byte-by-byte send completed")
            except Exception as e3:
                print(f"❌ Byte-by-byte send failed: {e3}")

def test_simple_receive():
    """ทดสอบรับข้อความง่ายๆ"""
    
    lora = test_lora_connection()
    if lora is None:
        return
    
    print("📡 Listening for simple messages...")
    print("📋 Method info:")
    
    # ตรวจสอบ methods ที่มี
    methods = [method for method in dir(lora) if not method.startswith('_')]
    receive_methods = [m for m in methods if 'read' in m.lower() or 'recv' in m.lower() or 'available' in m.lower()]
    print(f"📋 Available receive methods: {receive_methods}")
    
    for i in range(30):  # ฟัง 30 วินาที
        try:
            # วิธีที่ 1: ใช้ available() และ read()
            try:
                available_bytes = lora.available()
                
                if available_bytes and available_bytes > 0:
                    print(f"📨 Data available: {available_bytes} bytes")
                    
                    # ลองอ่านข้อมูลด้วยวิธีต่างๆ
                    data = None
                    
                    # วิธีที่ 1: read() ธรรมดา
                    try:
                        data = lora.read()
                        print(f"📥 read(): {data} (type: {type(data)})")
                    except Exception as e:
                        print(f"⚠️ read() error: {e}")
                    
                    # วิธีที่ 2: ลอง read(length)
                    try:
                        if available_bytes > 1:
                            data2 = lora.read(available_bytes)
                            print(f"📥 read(length): {data2} (type: {type(data2)})")
                            data = data2
                    except Exception as e:
                        print(f"⚠️ read(length) error: {e}")
                    
                    # วิธีที่ 3: ลองใช้ readBytes ถ้ามี
                    try:
                        if hasattr(lora, 'readBytes'):
                            data3 = lora.readBytes(available_bytes)
                            print(f"📥 readBytes(): {data3} (type: {type(data3)})")
                            data = data3
                    except Exception as e:
                        print(f"⚠️ readBytes() error: {e}")
                    
                    # ประมวลผลข้อมูลที่อ่านได้
                    if data is not None:
                        decode_received_data(data)
                        
                else:
                    print(f"⏳ Waiting... ({i+1}/30) - No data available")
                    
            except Exception as e:
                print(f"⚠️ Main receive error: {e}")
            
            # วิธีที่ 4: ลองใช้ receive mode ถ้ามี
            try:
                if hasattr(lora, 'receive') and i == 0:  # ทำครั้งเดียว
                    lora.receive()
                    print("📡 Set to receive mode")
            except Exception as e:
                print(f"⚠️ Receive mode error: {e}")
                
        except Exception as e:
            print(f"⚠️ Loop error: {e}")
            
        time.sleep(1)

def decode_received_data(data):
    """แยกฟังก์ชันสำหรับถอดรหัสข้อมูลที่รับมา"""
    
    try:
        if isinstance(data, (list, tuple)):
            if len(data) > 0:
                # แปลงเป็น bytes แล้วเป็น string
                try:
                    byte_data = bytes(data)
                    message = byte_data.decode('utf-8')
                    print(f"🔤 Decoded message: '{message}'")
                except Exception as decode_error:
                    print(f"⚠️ UTF-8 decode error: {decode_error}")
                    # ลองแสดงเป็น hex
                    hex_data = [f"0x{b:02x}" for b in data if isinstance(b, int)]
                    print(f"📊 Hex data: {hex_data}")
            else:
                print("📭 Empty list/tuple")
                
        elif isinstance(data, int):
            if data != 0:
                try:
                    if 32 <= data <= 126:  # printable ASCII
                        char = chr(data)
                        print(f"🔤 Single char: '{char}' (ASCII {data})")
                    else:
                        print(f"📊 Single byte: {data} (0x{data:02x})")
                except:
                    print(f"📊 Raw int: {data}")
            else:
                print("📭 Empty data (0)")
                
        elif isinstance(data, bytes):
            if len(data) > 0:
                try:
                    message = data.decode('utf-8')
                    print(f"🔤 Decoded message: '{message}'")
                except:
                    print(f"📊 Raw bytes (hex): {data.hex()}")
            else:
                print("📭 Empty bytes")
                
        elif isinstance(data, str):
            print(f"🔤 String message: '{data}'")
            
        else:
            print(f"❓ Unknown data type: {type(data)}, value: {data}")
            
    except Exception as e:
        print(f"⚠️ Decode error: {e}")
        print(f"📊 Raw received data: {data}")

def test_ping_pong():
    """ทดสอบส่งและรับแบบ ping-pong"""
    
    lora = test_lora_connection()
    if lora is None:
        return
    
    print("🏓 Starting ping-pong test...")
    print("This will send a message every 5 seconds and listen in between")
    
    counter = 0
    
    for i in range(12):  # รัน 1 นาที (12 x 5 วินาที)
        # ส่งข้อความ
        counter += 1
        message = f"PING-{counter:03d}"
        
        try:
            message_bytes = list(message.encode('utf-8'))
            result = lora.write(message_bytes, len(message_bytes))
            print(f"📤 Sent: {message} (result: {result})")
        except Exception as e:
            print(f"❌ Send error: {e}")
        
        # ฟังข้อความตอบกลับ 5 วินาที
        print("📡 Listening for response...")
        
        for j in range(5):
            try:
                available_bytes = lora.available()
                if available_bytes and available_bytes> 0:
                    data = lora.read()
                    decode_received_data(data)
                    
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