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
        else:
            messagebox.showerror("Connection Failed", f"Could not connect to {selected_port}")

    def disconnect(self):
        if self.lora:
            self.lora.disconnect()
        self.running = False
        self.status_label.config(text="Status: Disconnected", fg="red")

    def send_data(self):
        text = self.input_entry.get()
        if self.lora:
            self.lora.send_data(text+ '\n')
            self.text_area.insert(tk.END, f"[Sent] {text}\n")
            self.text_area.yview(tk.END)
            self.input_entry.delete(0, tk.END)

    def receive_data_thread(self):
        while self.running:
            msg = self.lora.read_data()
            if msg:
                print(f"[DEBUG] Received: {msg}")  # Debug output
                self.text_area.insert(tk.END, f"[Received] {msg}\n")
                self.text_area.yview(tk.END)
            time.sleep(0.1)

    def on_close(self):
        self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SX126xGUI(root)
    root.mainloop()
