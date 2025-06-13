import serial
import serial.tools.list_ports

class SX126x:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            return True
        except serial.SerialException as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send_data(self, data: str):
        if self.ser and self.ser.is_open:
            self.ser.write(data.encode('utf-8') + b'\n')
            self.ser.flush()

    def read_data(self):
        if self.ser and self.ser.is_open and self.ser.in_waiting:
            try:
                return self.ser.readline().decode('utf-8', errors='ignore').strip()
            except Exception as e:
                print(f"[READ ERROR] {e}")
        return ""

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports if "usb" in port.device.lower() or "ttyUSB" in port.device.lower()]
