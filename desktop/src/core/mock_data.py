"""
Mock data generator for development and testing
"""

import random
import time
import json
import threading
from typing import Callable, Optional

class MockDataGenerator:
    """Generates mock sensor data for development"""

    def __init__(self, data_callback: Optional[Callable] = None):
        self.data_callback = data_callback
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.devices = ["sensor_001", "sensor_002", "sensor_003"]

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
                device_id = random.choice(self.devices)
                mock_data = self._generate_mock_data(device_id)
                
                data_json = json.dumps(mock_data)
                
                if self.data_callback:
                    self.data_callback(data_json)
                
                time.sleep(interval + random.uniform(-1, 1))

            except Exception as e:
                print(f"Error generating mock data: {e}")
                break

    def _generate_mock_data(self, device_id: str) -> dict:
        """Generate a single mock data payload"""
        return {
            "timestamp": time.time(),
            "device_id": device_id,
            "sensors": {
                "ph": round(random.uniform(6.5, 8.5), 2),
                "ec": random.randint(600, 1200),
                "tds": random.randint(300, 600),
                "salinity": round(random.uniform(0.1, 0.6), 2),
                "do": round(random.uniform(5.0, 9.0), 2),
                "saturation": round(random.uniform(70.0, 100.0), 1)
            },
        }

# ทดสอบใช้งาน
if __name__ == "__main__":
    def print_callback(data):
        print(json.dumps(json.loads(data), indent=2))

    mocker = MockDataGenerator(data_callback=print_callback)
    mocker.start(interval=2.0)

    try:
        time.sleep(10)  # รัน 10 วินาที
    finally:
        mocker.stop()
