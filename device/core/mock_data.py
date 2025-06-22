"""
Mock data generator for development and testing
"""

import random
import time
import json
import threading
from typing import Callable, Optional
from dataclasses import dataclass

@dataclass
class SensorReading:
    """Represents a sensor reading"""
    device_id: str
    timestamp: float
    temperature: float
    humidity: float
    pressure: float
    battery_level: float
    signal_strength: int

class MockDataGenerator:
    """Generates mock sensor data for development"""
    
    def __init__(self, data_callback: Optional[Callable] = None):
        self.data_callback = data_callback
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.devices = ["DEV001", "DEV002", "DEV003", "DEV004"]
        
    def start(self, interval: float = 5.0):
        """Start generating mock data"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(
                target=self._generate_loop, 
                args=(interval,), 
                daemon=True
            )
            self.thread.start()
    
    def stop(self):
        """Stop generating mock data"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def _generate_loop(self, interval: float):
        """Main data generation loop"""
        while self.is_running:
            try:
                # Generate data for a random device
                device_id = random.choice(self.devices)
                reading = self._generate_sensor_reading(device_id)
                
                # Convert to JSON string (simulating serial data)
                data_json = json.dumps({
                    "device_id": reading.device_id,
                    "timestamp": reading.timestamp,
                    "temperature": reading.temperature,
                    "humidity": reading.humidity,
                    "pressure": reading.pressure,
                    "battery": reading.battery_level,
                    "rssi": reading.signal_strength
                })
                
                if self.data_callback:
                    self.data_callback(data_json)
                
                time.sleep(interval + random.uniform(-1, 1))  # Add some randomness
                
            except Exception as e:
                print(f"Error generating mock data: {e}")
                break
    
    def _generate_sensor_reading(self, device_id: str) -> SensorReading:
        """Generate a single sensor reading"""
        return SensorReading(
            device_id=device_id,
            timestamp=time.time(),
            temperature=random.uniform(18.0, 35.0),  # Celsius
            humidity=random.uniform(30.0, 80.0),     # Percentage
            pressure=random.uniform(980.0, 1020.0),  # hPa
            battery_level=random.uniform(20.0, 100.0), # Percentage
            signal_strength=random.randint(-120, -60)   # dBm
        )
