from LoRaRF import SX126x
import time
import sys
import signal

class LoRaTester:
    def __init__(self):
        self.lora = None
        self.running = True
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Stopping LoRa test...")
        self.running = False
        if self.lora:
            try:
                self.lora.end()
                print("✅ LoRa connection closed")
            except:
                pass
        sys.exit(0)
    
    def test_lora_connection(self):
        """ทดสอบการเชื่อมต่อ LoRa แบบละเอียด"""
        
        print("🔧 Testing LoRa Connection...")
        print("=" * 50)
        
        try:
            # สร้าง LoRa object
            self.lora = SX126x()
            print("✅ SX126x object created")
            
            # ลองเชื่อมต่อ
            begin_result = self.lora.begin()
            print(f"✅ LoRa.begin() successful - Result: {begin_result}")
            
            # ตรวจสอบ methods ที่มี
            self.print_available_methods()
            
            # ทดสอบการอ่านสถานะ
            self.test_status_methods()
            
            # กำหนดค่าพื้นฐาน
            self.configure_basic_settings()
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            return False
    
    def print_available_methods(self):
        """แสดง methods ที่มีใน LoRa object"""
        if not self.lora:
            return
            
        print("\n📋 Available Methods:")
        methods = [method for method in dir(self.lora) if not method.startswith('_')]
        
        # จัดกลุ่ม methods
        config_methods = [m for m in methods if any(word in m.lower() for word in ['set', 'config', 'frequency', 'power', 'spread'])]
        status_methods = [m for m in methods if any(word in m.lower() for word in ['get', 'status', 'rssi', 'snr'])]
        comm_methods = [m for m in methods if any(word in m.lower() for word in ['write', 'read', 'send', 'recv', 'available', 'transmit'])]
        
        if config_methods:
            print(f"  🔧 Config: {config_methods}")
        if status_methods:
            print(f"  📊 Status: {status_methods}")
        if comm_methods:
            print(f"  📡 Communication: {comm_methods}")
        
        other_methods = [m for m in methods if m not in config_methods + status_methods + comm_methods]
        if other_methods:
            print(f"  🔹 Other: {other_methods}")
    
    def test_status_methods(self):
        """ทดสอบ methods สำหรับอ่านสถานะ"""
        if not self.lora:
            return
            
        print("\n🔍 Testing Status Methods:")
        
        status_methods = [
            ('getStatus', 'Get general status'),
            ('status', 'Get status'),
            ('getRSSI', 'Get RSSI'),
            ('getSNR', 'Get SNR'),
            ('getFrequency', 'Get frequency'),
            ('getSpreadingFactor', 'Get spreading factor'),
            ('getBandwidth', 'Get bandwidth')
        ]
        
        for method_name, description in status_methods:
            try:
                if hasattr(self.lora, method_name):
                    method = getattr(self.lora, method_name)
                    result = method()
                    print(f"  ✅ {description}: {result}")
                else:
                    print(f"  ⚠️ {method_name} not available")
            except Exception as e:
                print(f"  ❌ {description} error: {e}")
    
    def configure_basic_settings(self):
        """กำหนดค่าพื้นฐานสำหรับ LoRa"""
        if not self.lora:
            return
            
        print("\n⚙️ Configuring Basic Settings:")
        
        configs = [
            ('setFrequency', 915.0, 'Frequency (MHz)'),
            ('setSpreadingFactor', 7, 'Spreading Factor'),
            ('setBandwidth', 9600, 'Bandwidth (Hz)'),
            ('setCodeRate', 5, 'Code Rate'),
            ('setPreambleLength', 8, 'Preamble Length'),
            ('setTxPower', 14, 'TX Power (dBm)'),
            ('setSyncWord', 0x12, 'Sync Word')
        ]
        
        for method_name, value, description in configs:
            try:
                if hasattr(self.lora, method_name):
                    method = getattr(self.lora, method_name)
                    result = method(value)
                    print(f"  ✅ {description}: {value} - Result: {result}")
                else:
                    print(f"  ⚠️ {method_name} not available")
            except Exception as e:
                print(f"  ❌ {description} config error: {e}")
    
    def test_simple_send(self, message="Hello LoRa!"):
        """ทดสอบส่งข้อความพร้อม error handling ที่ดี"""
        
        if not self.test_lora_connection():
            return False
        
        print(f"\n📤 Testing Send Function:")
        print(f"📝 Message: '{message}'")
        print("=" * 50)
        
        # แปลงข้อความเป็นรูปแบบต่างๆ
        message_str = str(message)
        message_bytes = message_str.encode('utf-8')
        message_list = list(message_bytes)
        
        print(f"📊 Data formats:")
        print(f"  String: '{message_str}'")
        print(f"  Bytes: {message_bytes}")
        print(f"  List: {message_list}")
        
        # ลองส่งด้วยวิธีต่างๆ
        send_methods = [
            ('write', message_list, len(message_list), 'Write with list and length'),
            ('write', message_list, None, 'Write with list only'),
            ('write', message_bytes, None, 'Write with bytes'),
            ('write', message_str, None, 'Write with string'),
            ('send', message_list, len(message_list), 'Send with list and length'),
            ('send', message_list, None, 'Send with list only'),
            ('transmit', message_list, len(message_list), 'Transmit with list and length')
        ]
        
        success_count = 0
        
        for method_name, data, length, description in send_methods:
            if not hasattr(self.lora, method_name):
                print(f"  ⚠️ {description}: Method not available")
                continue
                
            try:
                method = getattr(self.lora, method_name)
                
                # เรียกใช้ method ตามจำนวน parameters
                if length is not None:
                    result = method(data, length)
                else:
                    result = method(data)
                
                print(f"  ✅ {description}: Success - Result: {result}")
                success_count += 1
                
                # รออีกสักครู่เพื่อให้การส่งเสร็จสิ้น
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ {description}: Error - {e}")
        
        print(f"\n📊 Send Summary: {success_count}/{len(send_methods)} methods successful")
        return success_count > 0
    
    def test_simple_receive(self, timeout=60):
        """ทดสอบรับข้อความพร้อม timeout และ error handling"""
        
        if not self.test_lora_connection():
            return
        
        print(f"\n📡 Testing Receive Function:")
        print(f"⏰ Timeout: {timeout} seconds")
        print("=" * 50)
        
        # ตั้งค่า signal handler สำหรับ Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # ตรวจสอบ receive methods
        receive_methods = []
        method_names = ['available', 'read', 'readBytes', 'receive', 'listen']
        
        for method_name in method_names:
            if hasattr(self.lora, method_name):
                receive_methods.append(method_name)
        
        print(f"📋 Available receive methods: {receive_methods}")
        
        # เริ่ม receive mode ถ้ามี
        if 'receive' in receive_methods:
            try:
                self.lora.receive()
                print("📡 Set to receive mode")
            except Exception as e:
                print(f"⚠️ Receive mode error: {e}")
        
        start_time = time.time()
        loop_count = 0
        
        print(f"\n🎧 Listening for messages... (Press Ctrl+C to stop)")
        
        while self.running and (time.time() - start_time) < timeout:
            try:
                loop_count += 1
                data_received = False
                
                # ตรวจสอบข้อมูลที่มี
                if 'available' in receive_methods:
                    try:
                        available_bytes = self.lora.available()
                        
                        if available_bytes and available_bytes > 0:
                            print(f"\n📨 Data available: {available_bytes} bytes")
                            data_received = True
                            
                            # ลองอ่านข้อมูลด้วยวิธีต่างๆ
                            self.try_read_data(available_bytes)
                            
                    except Exception as e:
                        if loop_count % 10 == 1:  # แสดง error ทุก 10 loops
                            print(f"⚠️ Available check error: {e}")
                
                # ลองอ่านโดยตรงถ้าไม่มี available method
                elif 'read' in receive_methods:
                    try:
                        data = self.lora.read()
                        if data:
                            print(f"\n📨 Direct read data: {data}")
                            self.decode_received_data(data)
                            data_received = True
                    except Exception as e:
                        if loop_count % 10 == 1:
                            print(f"⚠️ Direct read error: {e}")
                
                # แสดงสถานะทุก 5 วินาที
                if loop_count % 5 == 0 and not data_received:
                    elapsed = int(time.time() - start_time)
                    remaining = timeout - elapsed
                    print(f"⏳ Listening... ({elapsed}s elapsed, {remaining}s remaining)")
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.signal_handler(None, None)
                break
            except Exception as e:
                print(f"⚠️ Loop error: {e}")
                time.sleep(1)
        
        print(f"\n🏁 Receive test completed after {int(time.time() - start_time)} seconds")
    
    def try_read_data(self, available_bytes):
        """ลองอ่านข้อมูลด้วยวิธีต่างๆ"""
        
        read_methods = [
            ('read', None, 'Basic read'),
            ('read', available_bytes, 'Read with length'),
            ('readBytes', available_bytes, 'Read bytes with length')
        ]
        
        data = None
        
        for method_name, param, description in read_methods:
            if not hasattr(self.lora, method_name):
                continue
                
            try:
                method = getattr(self.lora, method_name)
                
                if param is not None:
                    result = method(param)
                else:
                    result = method()
                
                print(f"  📥 {description}: {result} (type: {type(result).__name__})")
                
                if result is not None:
                    data = result
                    break
                    
            except Exception as e:
                print(f"  ❌ {description} error: {e}")
        
        # ถอดรหัสข้อมูลที่อ่านได้
        if data is not None:
            self.decode_received_data(data)
        else:
            print("  📭 No data could be read")
    
    def decode_received_data(self, data):
        """ถอดรหัสข้อมูลที่รับมาอย่างครอบคลุม"""
        
        print(f"\n🔍 Decoding received data:")
        print(f"  📊 Raw data: {data}")
        print(f"  📊 Data type: {type(data).__name__}")
        
        try:
            if isinstance(data, (list, tuple)):
                if len(data) > 0:
                    print(f"  📊 List/Tuple length: {len(data)}")
                    
                    # แสดงข้อมูลดิบ
                    if len(data) <= 20:
                        print(f"  📊 Raw values: {data}")
                    else:
                        print(f"  📊 Raw values (first 20): {data[:20]}...")
                    
                    # ลองแปลงเป็น string
                    try:
                        # ตรวจสอบว่าเป็น valid bytes หรือไม่
                        valid_bytes = all(isinstance(x, int) and 0 <= x <= 255 for x in data)
                        
                        if valid_bytes:
                            byte_data = bytes(data)
                            
                            # ลอง UTF-8
                            try:
                                message = byte_data.decode('utf-8')
                                print(f"  🔤 UTF-8 decoded: '{message}'")
                            except UnicodeDecodeError:
                                # ลอง ASCII
                                try:
                                    message = byte_data.decode('ascii', 'ignore')
                                    print(f"  🔤 ASCII decoded: '{message}'")
                                except:
                                    pass
                            
                            # แสดงเป็น hex
                            hex_data = byte_data.hex()
                            print(f"  🔢 Hex: {hex_data}")
                            
                            # แสดงเป็น printable characters
                            printable = ''.join(chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in data)
                            print(f"  📝 Printable: '{printable}'")
                        else:
                            print(f"  ⚠️ Not valid byte data")
                    except Exception as decode_error:
                        print(f"  ❌ Decode error: {decode_error}")
                else:
                    print(f"  📭 Empty list/tuple")
                    
            elif isinstance(data, int):
                print(f"  📊 Integer value: {data}")
                if data != 0:
                    if 0 <= data <= 255:
                        print(f"  🔢 Hex: 0x{data:02x}")
                        if 32 <= data <= 126:
                            print(f"  🔤 ASCII char: '{chr(data)}'")
                else:
                    print(f"  📭 Zero value")
                    
            elif isinstance(data, bytes):
                print(f"  📊 Bytes length: {len(data)}")
                if len(data) > 0:
                    print(f"  🔢 Hex: {data.hex()}")
                    try:
                        message = data.decode('utf-8')
                        print(f"  🔤 UTF-8 decoded: '{message}'")
                    except:
                        try:
                            message = data.decode('ascii', 'ignore')
                            print(f"  🔤 ASCII decoded: '{message}'")
                        except:
                            pass
                else:
                    print(f"  📭 Empty bytes")
                    
            elif isinstance(data, str):
                print(f"  🔤 String message: '{data}'")
                print(f"  📊 String length: {len(data)}")
                
            else:
                print(f"  ❓ Unknown data type: {type(data).__name__}")
                print(f"  📊 String representation: {str(data)}")
                
        except Exception as e:
            print(f"  ❌ Decode error: {e}")
    
    def run_interactive_test(self):
        """เรียกใช้ทดสอบแบบ interactive"""
        
        print("🚀 LoRa Interactive Test Mode")
        print("=" * 50)
        
        while True:
            print("\nSelect test mode:")
            print("1. Test Connection")
            print("2. Send Message")
            print("3. Receive Messages")
            print("4. Send Custom Message")
            print("5. Exit")
            
            try:
                choice = input("\nEnter choice (1-5): ").strip()
                
                if choice == '1':
                    self.test_lora_connection()
                elif choice == '2':
                    self.test_simple_send()
                elif choice == '3':
                    timeout = input("Enter timeout in seconds (default 60): ").strip()
                    timeout = int(timeout) if timeout.isdigit() else 60
                    self.test_simple_receive(timeout)
                elif choice == '4':
                    message = input("Enter message to send: ").strip()
                    if message:
                        self.test_simple_send(message)
                    else:
                        print("Empty message!")
                elif choice == '5':
                    break
                else:
                    print("Invalid choice!")
                    
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("👋 Goodbye!")


def main():
    """Main function with improved argument handling"""
    
    tester = LoRaTester()
    
    if len(sys.argv) < 2:
        print("🚀 LoRa Testing Tool")
        print("=" * 50)
        print("Usage:")
        print("  python lora_test.py test              - Test connection only")
        print("  python lora_test.py send              - Test sending default message")
        print("  python lora_test.py send 'message'    - Test sending custom message")
        print("  python lora_test.py receive           - Test receiving (60s timeout)")
        print("  python lora_test.py receive 30        - Test receiving (30s timeout)")
        print("  python lora_test.py interactive       - Interactive mode")
        print("  python lora_test.py all               - Run all tests")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "test":
            tester.test_lora_connection()
            
        elif command == "send":
            message = sys.argv[2] if len(sys.argv) > 2 else "Hello LoRa!"
            tester.test_simple_send(message)
            
        elif command == "receive":
            timeout = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 60
            tester.test_simple_receive(timeout)
            
        elif command == "interactive":
            tester.run_interactive_test()
            
        elif command == "all":
            print("🔄 Running all tests...")
            print("\n" + "="*50)
            print("TEST 1: CONNECTION")
            print("="*50)
            if tester.test_lora_connection():
                print("\n" + "="*50)
                print("TEST 2: SENDING")
                print("="*50)
                tester.test_simple_send()
                
                print("\n" + "="*50)
                print("TEST 3: RECEIVING (10 seconds)")
                print("="*50)
                tester.test_simple_receive(10)
            
        else:
            print(f"❌ Invalid command: {command}")
            print("Use 'python lora_test.py' without arguments to see usage")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"🔍 Error type: {type(e).__name__}")


if __name__ == "__main__":
    main()