import tkinter as tk
from tkinter import messagebox, scrolledtext
from sx126x_driver import SX126x
import threading
import time

class SX126xApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SX126x GUI - LoRa Communication")
        self.root.geometry("600x400")

        # Communication object
        self.lora = None
        self.running = False

        # UI Elements
        self.port_entry = tk.Entry(root, width=40)
        self.port_entry.insert(0, "/dev/tty.usbserial-0001")
        self.port_entry.pack(pady=10)

        self.connect_btn = tk.Button(root, text="Connect", command=self.connect)
        self.connect_btn.pack()

        self.text_area = scrolledtext.ScrolledText(root, width=70, height=15)
        self.text_area.pack(pady=10)

        self.input_entry = tk.Entry(root, width=50)
        self.input_entry.pack(side=tk.LEFT, padx=10)
        self.send_btn = tk.Button(root, text="Send", command=self.send_data)
        self.send_btn.pack(side=tk.LEFT)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def connect(self):
        port = self.port_entry.get()
        self.lora = SX126x(port=port)
        if self.lora.connect():
            self.running = True
            threading.Thread(target=self.receive_data_thread, daemon=True).start()
            messagebox.showinfo("Success", "Connected to SX126x!")
        else:
            messagebox.showerror("Error", f"Cannot open port {port}")

    def send_data(self):
        data = self.input_entry.get()
        if self.lora:
            self.lora.send_data(data + "\n")  # Add newline if protocol expects it
            self.text_area.insert(tk.END, f"[Sent] {data}\n")
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
    app = SX126xApp(root)
    root.mainloop()
