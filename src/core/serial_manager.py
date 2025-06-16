"""
Serial port management for USB UART communication
"""

import serial
import serial.tools.list_ports
import threading
import time
from typing import List, Optional, Callable
from dataclasses import dataclass

@dataclass
class SerialData:
    """Container for received serial data"""
    timestamp: float
    raw_data: bytes
    decoded_data: str
    is_encrypted: bool = False

class SerialManager:
    """Manages serial port communication"""
    
    def __init__(self, data_callback: Optional[Callable] = None):
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.is_reading = False
        self.read_thread: Optional[threading.Thread] = None
        self.data_callback = data_callback
        
    def get_available_ports(self) -> List[str]:
        """Get list of available serial ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def connect(self, port: str, baudrate: int = 9600, timeout: float = 1.0) -> bool:
        """Connect to serial port"""
        try:
            if self.is_connected:
                self.disconnect()
                
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            self.is_connected = True
            self.start_reading()
            return True
            
        except Exception as e:
            print(f"Error connecting to {port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        self.stop_reading()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.is_connected = False
    
    def start_reading(self):
        """Start reading data in a separate thread"""
        if not self.is_reading and self.is_connected:
            self.is_reading = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
    
    def stop_reading(self):
        """Stop reading data"""
        self.is_reading = False
        if self.read_thread:
            self.read_thread.join(timeout=2.0)
    
    def _read_loop(self):
        """Main reading loop"""
        while self.is_reading and self.is_connected:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    raw_data = self.serial_port.readline()
                    if raw_data:
                        decoded_data = raw_data.decode('utf-8', errors='ignore').strip()
                        
                        serial_data = SerialData(
                            timestamp=time.time(),
                            raw_data=raw_data,
                            decoded_data=decoded_data
                        )
                        
                        if self.data_callback:
                            self.data_callback(serial_data)
                            
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                print(f"Error reading serial data: {e}")
                break
    
    def send_data(self, data: str) -> bool:
        """Send data through serial port"""
        try:
            if self.is_connected and self.serial_port:
                self.serial_port.write(data.encode('utf-8'))
                return True
        except Exception as e:
            print(f"Error sending data: {e}")
        return False
