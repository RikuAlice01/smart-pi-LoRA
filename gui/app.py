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
                self.lora.send_data(text + '\n')
                self.append_to_console(f"[Sent] {text}")
                self.input_entry.delete(0, tk.END)
            except Exception as e:
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
                    
                    # แปลงข้อมูลให้เป็น string ถ้าจำเป็น
                    if isinstance(msg, bytes):
                        try:
                            msg = msg.decode('utf-8', errors='ignore').strip()
                        except:
                            msg = str(msg)
                    else:
                        msg = str(msg).strip()
                    
                    # แสดงข้อมูลถ้าไม่ใช่ string ว่าง
                    if msg:
                        print(f"[DEBUG] Raw received: {repr(msg)}")  # Debug รูปแบบ raw
                        # ใช้ thread-safe method ในการอัปเดต GUI
                        self.root.after(0, lambda m=msg: self.append_to_console(f"[Received] {m}"))
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