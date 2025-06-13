import serial
import time

class SX126x:
    def __init__(self, port="/dev/tty.usbserial-0001", baudrate=125000):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            return True
        except serial.SerialException as e:
            print(f"Error connecting to SX126x: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send_data(self, data: str):
        if self.ser and self.ser.is_open:
            self.ser.write(data.encode('utf-8'))
            self.ser.flush()

    def read_data(self):
        if self.ser and self.ser.is_open:
            if self.ser.in_waiting:
                return self.ser.readline().decode('utf-8').strip()
        return ""
