import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from sx126x_driver import SX126x, list_serial_ports
import threading
import time

class SX126xGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SX126x USB GUI")
        self.root.geometry("800x450")

        self.lora = None
        self.running = False

        # ==== Layout Frame ====
        self.left_frame = tk.Frame(root, padx=10, pady=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(root, padx=10, pady=10, width=250)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # ==== LEFT: Display Console ====
        self.text_area = scrolledtext.ScrolledText(self.left_frame, width=70, height=25, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        self.send_frame = tk.Frame(self.left_frame)
        self.send_frame.pack(fill=tk.X, pady=5)

        self.input_entry = tk.Entry(self.send_frame)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        # เพิ่ม Enter key binding
        self.input_entry.bind('<Return>', lambda event: self.send_data())

        self.send_btn = tk.Button(self.send_frame, text="📤 Send", width=10, command=self.send_data)
        self.send_btn.pack(side=tk.RIGHT)

        # ==== RIGHT: Settings ====
        tk.Label(self.right_frame, text="Serial Port").pack(anchor="w")
        self.port_combo = ttk.Combobox(self.right_frame, values=list_serial_ports(), width=25)
        self.port_combo.pack(pady=5, fill=tk.X)

        self.refresh_btn = tk.Button(self.right_frame, text="🔄 Refresh Ports", command=self.refresh_ports)
        self.refresh_btn.pack(pady=2, fill=tk.X)

        tk.Label(self.right_frame, text="Baudrate").pack(anchor="w", pady=(10, 0))
        self.baudrate_entry = ttk.Entry(self.right_frame)
        self.baudrate_entry.insert(0, "115200")
        self.baudrate_entry.pack(pady=5, fill=tk.X)

        self.connect_btn = tk.Button(self.right_frame, text="🔌 Connect", command=self.connect)
        self.connect_btn.pack(pady=10, fill=tk.X)

        self.disconnect_btn = tk.Button(self.right_frame, text="❌ Disconnect", command=self.disconnect)
        self.disconnect_btn.pack(pady=2, fill=tk.X)

        self.status_label = tk.Label(self.right_frame, text="Status: Disconnected", fg="red", anchor="w")
        self.status_label.pack(pady=10, anchor="w")

        # เพิ่ม Debug button
        self.debug_btn = tk.Button(self.right_frame, text="🐛 Debug Info", command=self.show_debug)
        self.debug_btn.pack(pady=2, fill=tk.X)
        
        # เพิ่มปุ่มทดสอบ
        self.test_btn = tk.Button(self.right_frame, text="🔍 Test LoRa", command=self.test_lora)
        self.test_btn.pack(pady=2, fill=tk.X)
        
        # เพิ่มปุ่มส่งข้อมูลทดสอบ
        self.test_send_btn = tk.Button(self.right_frame, text="📡 Send Test", command=self.send_test_data)
        self.test_send_btn.pack(pady=2, fill=tk.X)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def refresh_ports(self):
        ports = list_serial_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def connect(self):
        selected_port = self.port_combo.get()
        baudrate_str = self.baudrate_entry.get()

        if not selected_port or not baudrate_str:
            messagebox.showerror("Error", "Please select a port and enter baudrate.")
            return

        try:
            baudrate = int(baudrate_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid baudrate.")
            return

        self.lora = SX126x(port=selected_port, baudrate=baudrate)
        if self.lora.connect():
            self.running = True
            threading.Thread(target=self.receive_data_thread, daemon=True).start()
            self.status_label.config(text=f"Status: Connected to {selected_port}", fg="green")
            self.append_to_console(f"[System] Connected to {selected_port} at {baudrate} baud")
        else:
            messagebox.showerror("Connection Failed", f"Could not connect to {selected_port}")

    def disconnect(self):
        if self.lora:
            self.lora.disconnect()
        self.running = False
        self.status_label.config(text="Status: Disconnected", fg="red")
        self.append_to_console("[System] Disconnected")

    def send_data(self):
        text = self.input_entry.get().strip()
        if not text:
            return
            
        if self.lora and self.running:
            try:
                # Debug: แสดงข้อมูลที่ส่ง
                send_text = text + '\n'
                print(f"[DEBUG] Sending: {repr(send_text)}")
                print(f"[DEBUG] Sending bytes: {send_text.encode('utf-8')}")
                
                # ลองส่งแบบต่างๆ
                self.lora.send_data(send_text)
                self.append_to_console(f"[Sent] {text}")
                self.input_entry.delete(0, tk.END)
                
                # เพิ่มข้อมูล timing
                self.append_to_console(f"[Debug] Sent at {time.strftime('%H:%M:%S')}")
                
            except Exception as e:
                print(f"[DEBUG] Send exception: {e}")
                self.append_to_console(f"[Error] Send failed: {str(e)}")
        else:
            messagebox.showwarning("Warning", "Not connected to device")

    def receive_data_thread(self):
        """แก้ไขฟังก์ชันรับข้อมูลให้รับมือกับปัญหาต่างๆ"""
        consecutive_empty_reads = 0
        max_empty_reads = 100  # ป้องกัน busy loop
        
        while self.running:
            try:
                if not self.lora:
                    break
                    
                # อ่านข้อมูล
                msg = self.lora.read_data()
                
                # ตรวจสอบข้อมูลที่อ่านได้
                if msg is not None:
                    # Reset counter เมื่อได้ข้อมูล
                    consecutive_empty_reads = 0
                    
                    # กรองข้อมูลที่เป็น null bytes หรือ control characters
                    if isinstance(msg, bytes):
                        try:
                            # Debug: แสดงข้อมูล raw ทั้งหมด
                            print(f"[DEBUG] Raw data type: {type(msg)}")
                            print(f"[DEBUG] Raw data: {repr(msg)}")
                            # ลบ null bytes และ control characters
                            cleaned_msg = msg.replace(b'\x00', b'').strip()
                            if cleaned_msg:
                                decoded_msg = cleaned_msg.decode('utf-8', errors='ignore').strip()
                                if decoded_msg:
                                    print(f"[DEBUG] Cleaned message: {repr(decoded_msg)}")
                                    self.root.after(0, lambda m=decoded_msg: self.append_to_console(f"[Received] {m}"))
                                else:
                                    print(f"[DEBUG] Empty after cleaning: {repr(cleaned_msg)}")
                            else:
                                print(f"[DEBUG] Only null bytes received")
                        except Exception as decode_error:
                            print(f"[DEBUG] Decode error: {decode_error}")
                            # แสดงเป็น hex ถ้า decode ไม่ได้
                            hex_data = msg.hex() if hasattr(msg, 'hex') else str(msg)
                            self.root.after(0, lambda h=hex_data: self.append_to_console(f"[Received HEX] {h}"))
                    else:
                        # ถ้าไม่ใช่ bytes
                        msg_str = str(msg).strip()
                        if msg_str and msg_str != '\x00':
                            print(f"[DEBUG] String message: {repr(msg_str)}")
                            self.root.after(0, lambda m=msg_str: self.append_to_console(f"[Received] {m}"))
                else:
                    consecutive_empty_reads += 1
                    if consecutive_empty_reads > max_empty_reads:
                        # ลด CPU usage เมื่ออ่านข้อมูลว่างติดต่อกันหลายครั้ง
                        time.sleep(0.5)
                        consecutive_empty_reads = 0
                
            except Exception as e:
                print(f"[DEBUG] Exception in receive thread: {e}")
                self.root.after(0, lambda: self.append_to_console(f"[Error] Receive error: {str(e)}"))
                time.sleep(1)  # รอสักครู่เมื่อเกิด error
                
            time.sleep(0.1)
        
        print("[DEBUG] Receive thread ended")

    def append_to_console(self, message):
        """Thread-safe method สำหรับเพิ่มข้อความใน console"""
        try:
            self.text_area.insert(tk.END, f"{message}\n")
            self.text_area.yview(tk.END)
        except Exception as e:
            print(f"[DEBUG] Error updating console: {e}")

    def test_lora(self):
        """ทดสอบการทำงานของ LoRa module"""
        if not self.lora:
            messagebox.showwarning("Warning", "Not connected to device")
            return
            
        try:
            # ลองเรียกใช้ method ต่างๆ ของ LoRa
            test_results = []
            test_results.append("=== LoRa Test Results ===")
            
            # ตรวจสอบการเชื่อมต่อ
            if hasattr(self.lora, 'is_connected'):
                test_results.append(f"Connected: {self.lora.is_connected()}")
            
            # ตรวจสอบการตั้งค่า
            if hasattr(self.lora, 'get_config'):
                config = self.lora.get_config()
                test_results.append(f"Config: {config}")
            
            # ส่งข้อมูลทดสอบ
            test_msg = "TEST_" + str(int(time.time()))
            test_results.append(f"Sending test message: {test_msg}")
            self.lora.send_data(test_msg)
            
            result_text = "\n".join(test_results)
            self.append_to_console(f"[Test] {result_text}")
            
        except Exception as e:
            self.append_to_console(f"[Test Error] {str(e)}")
    
    def send_test_data(self):
        """ส่งข้อมูลทดสอบหลายรูปแบบ"""
        if not self.lora or not self.running:
            messagebox.showwarning("Warning", "Not connected to device")
            return
        
        test_messages = [
            "HELLO",
            "123",
            "TEST",
            "ABCD",
            "Hello World!"
        ]
        
        for i, msg in enumerate(test_messages):
            try:
                print(f"[DEBUG] Test {i+1}: Sending '{msg}'")
                self.lora.send_data(msg)
                self.append_to_console(f"[Test {i+1}] Sent: {msg}")
                time.sleep(1)  # รอระหว่างการส่ง
            except Exception as e:
                self.append_to_console(f"[Test {i+1} Error] {str(e)}")

    def show_debug(self):
        """แสดงข้อมูล debug"""
        debug_info = []
        debug_info.append(f"Running: {self.running}")
        debug_info.append(f"LoRa object: {self.lora}")
        
        if self.lora:
            try:
                # ลองเรียกใช้ method ต่างๆ เพื่อดูสถานะ
                debug_info.append(f"Port: {getattr(self.lora, 'port', 'Unknown')}")
                debug_info.append(f"Baudrate: {getattr(self.lora, 'baudrate', 'Unknown')}")
                # เพิ่มข้อมูล debug อื่นๆ ตามที่ SX126x class รองรับ
            except Exception as e:
                debug_info.append(f"Error getting LoRa info: {e}")
        
        messagebox.showinfo("Debug Info", "\n".join(debug_info))

    def on_close(self):
        self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SX126xGUI(root)
    root.mainloop()