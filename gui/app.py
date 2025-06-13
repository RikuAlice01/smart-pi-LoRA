import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from sx126x_driver import SX126x, list_serial_ports
import threading
import time

class SX126xGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SX126x USB GUI")
        self.root.geometry("600x500")

        self.lora = None
        self.running = False

        # Port Selection
        self.port_label = tk.Label(root, text="Select Serial Port:")
        self.port_label.pack()

        self.port_combo = ttk.Combobox(root, values=list_serial_ports(), width=40)
        self.port_combo.pack(pady=5)

        self.refresh_btn = tk.Button(root, text="🔄 Refresh Ports", command=self.refresh_ports)
        self.refresh_btn.pack(pady=2)

        self.connect_btn = tk.Button(root, text="🔌 Connect", command=self.connect)
        self.connect_btn.pack(pady=5)

        # Text area
        self.text_area = scrolledtext.ScrolledText(root, width=70, height=15, wrap=tk.WORD)
        self.text_area.pack(pady=10)

        # Input + send
        frame = tk.Frame(root)
        frame.pack()
        self.input_entry = tk.Entry(frame, width=50)
        self.input_entry.pack(side=tk.LEFT, padx=5)
        self.send_btn = tk.Button(frame, text="📤 Send", command=self.send_data)
        self.send_btn.pack(side=tk.LEFT)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def refresh_ports(self):
        ports = list_serial_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def connect(self):
        selected_port = self.port_combo.get()
        if not selected_port:
            messagebox.showerror("Error", "Please select a port.")
            return

        self.lora = SX126x(port=selected_port)
        if self.lora.connect():
            self.running = True
            threading.Thread(target=self.receive_data_thread, daemon=True).start()
            messagebox.showinfo("Connected", f"Connected to {selected_port}")
        else:
            messagebox.showerror("Connection Failed", f"Could not connect to {selected_port}")

    def send_data(self):
        text = self.input_entry.get()
        if self.lora:
            self.lora.send_data(text)
            self.text_area.insert(tk.END, f"[Sent] {text}\n")
            self.input_entry.delete(0, tk.END)

    def receive_data_thread(self):
        while self.running:
            msg = self.lora.read_data()
            if msg:
                self.text_area.insert(tk.END, f"[Received] {msg}\n")
                self.text_area.yview(tk.END)
            time.sleep(0.1)

    def on_close(self):
        self.running = False
        if self.lora:
            self.lora.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SX126xGUI(root)
    root.mainloop()
