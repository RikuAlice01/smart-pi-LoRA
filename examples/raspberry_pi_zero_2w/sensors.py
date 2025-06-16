"""
Sensor management for Raspberry Pi LoRa node
Supports DHT22, BMP280, and mock sensors
"""

import time
import random
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Try to import sensor libraries
try:
    import Adafruit_DHT
    DHT_AVAILABLE = True
except ImportError:
    DHT_AVAILABLE = False
    print("Warning: Adafruit_DHT library not available")

try:
    import board
    import busio
    import adafruit_bmp280
    BMP280_AVAILABLE = True
except ImportError:
    BMP280_AVAILABLE = False
    print("Warning: BMP280 library not available")

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO library not available")

@dataclass
class SensorReading:
    """Container for sensor readings"""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    altitude: Optional[float] = None
    battery_voltage: Optional[float] = None
    rssi: Optional[int] = None
    timestamp: float = 0.0

class DHT22Sensor:
    """DHT22 temperature and humidity sensor"""
    
    def __init__(self, pin: int):
        self.pin = pin
        self.sensor_type = Adafruit_DHT.DHT22
        self.logger = logging.getLogger(__name__)
        self.available = DHT_AVAILABLE
        
        if not self.available:
            self.logger.warning("DHT22 sensor not available (library missing)")
    
    def read(self) -> Dict[str, Optional[float]]:
        """Read temperature and humidity"""
        if not self.available:
            return {"temperature": None, "humidity": None}
        
        try:
            humidity, temperature = Adafruit_DHT.read_retry(self.sensor_type, self.pin)
            
            if humidity is not None and temperature is not None:
                # Validate readings
                if 0 <= humidity <= 100 and -40 <= temperature <= 80:
                    self.logger.debug(f"DHT22: T={temperature:.1f}°C, H={humidity:.1f}%")
                    return {
                        "temperature": round(temperature, 1),
                        "humidity": round(humidity, 1)
                    }
                else:
                    self.logger.warning(f"DHT22 readings out of range: T={temperature}, H={humidity}")
            else:
                self.logger.warning("DHT22 failed to read data")
            
        except Exception as e:
            self.logger.error(f"DHT22 read error: {e}")
        
        return {"temperature": None, "humidity": None}

class BMP280Sensor:
    """BMP280 pressure and temperature sensor"""
    
    def __init__(self, address: int = 0x76):
        self.address = address
        self.sensor = None
        self.logger = logging.getLogger(__name__)
        self.available = BMP280_AVAILABLE
        
        if self.available:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=address)
                
                # Configure sensor
                self.sensor.sea_level_pressure = 1013.25  # Standard sea level pressure
                
                self.logger.info(f"BMP280 sensor initialized at address 0x{address:02X}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize BMP280: {e}")
                self.available = False
        else:
            self.logger.warning("BMP280 sensor not available (library missing)")
    
    def read(self) -> Dict[str, Optional[float]]:
        """Read pressure, temperature, and altitude"""
        if not self.available or not self.sensor:
            return {"pressure": None, "altitude": None, "temperature_bmp": None}
        
        try:
            temperature = self.sensor.temperature
            pressure = self.sensor.pressure
            altitude = self.sensor.altitude
            
            # Validate readings
            if 300 <= pressure <= 1100 and -40 <= temperature <= 85:
                self.logger.debug(f"BMP280: T={temperature:.1f}°C, P={pressure:.1f}hPa, A={altitude:.1f}m")
                return {
                    "pressure": round(pressure, 1),
                    "altitude": round(altitude, 1),
                    "temperature_bmp": round(temperature, 1)
                }
            else:
                self.logger.warning(f"BMP280 readings out of range: T={temperature}, P={pressure}")
                
        except Exception as e:
            self.logger.error(f"BMP280 read error: {e}")
        
        return {"pressure": None, "altitude": None, "temperature_bmp": None}

class BatteryMonitor:
    """Battery voltage monitoring using ADC"""
    
    def __init__(self, pin: int):
        self.pin = pin
        self.logger = logging.getLogger(__name__)
        self.available = GPIO_AVAILABLE
        
        # Note: Raspberry Pi doesn't have built-in ADC
        # This would require an external ADC like MCP3008
        # For now, we'll simulate battery readings
        self.logger.warning("Battery monitoring not implemented (requires external ADC)")
        self.available = False
    
    def read(self) -> Dict[str, Optional[float]]:
        """Read battery voltage"""
        if not self.available:
            return {"battery_voltage": None}
        
        # Placeholder for actual ADC reading
        # In real implementation, you would:
        # 1. Read ADC value
        # 2. Convert to voltage using voltage divider formula
        # 3. Apply calibration
        
        return {"battery_voltage": None}

class MockSensor:
    """Mock sensor for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_temp = 22.0
        self.base_humidity = 50.0
        self.base_pressure = 1013.25
        
    def read(self) -> Dict[str, Any]:
        """Generate mock sensor data"""
        # Generate realistic variations
        temp_variation = random.uniform(-2, 2)
        humidity_variation = random.uniform(-5, 5)
        pressure_variation = random.uniform(-10, 10)
        
        temperature = self.base_temp + temp_variation
        humidity = max(0, min(100, self.base_humidity + humidity_variation))
        pressure = self.base_pressure + pressure_variation
        altitude = 44330 * (1 - (pressure / 1013.25) ** 0.1903)
        
        # Simulate battery voltage (3.3V to 4.2V for Li-ion)
        battery_voltage = random.uniform(3.3, 4.2)
        
        # Simulate RSSI
        rssi = random.randint(-120, -60)
        
        return {
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "pressure": round(pressure, 1),
            "altitude": round(altitude, 1),
            "temperature_bmp": round(temperature + random.uniform(-0.5, 0.5), 1),
            "battery_voltage": round(battery_voltage, 2),
            "rssi": rssi
        }

class SensorManager:
    """Manages all sensors"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize sensors
        self.dht22 = None
        self.bmp280 = None
        self.battery_monitor = None
        self.mock_sensor = MockSensor()
        
        # Initialize real sensors if enabled and available
        if config.sensor.dht22_enabled:
            self.dht22 = DHT22Sensor(config.sensor.dht22_pin)
        
        if config.sensor.bmp280_enabled:
            self.bmp280 = BMP280Sensor(config.sensor.bmp280_address)
        
        if config.device.battery_monitoring:
            self.battery_monitor = BatteryMonitor(config.device.battery_pin)
        
        self.logger.info("Sensor manager initialized")
    
    def read_all_sensors(self) -> Dict[str, Any]:
        """Read all enabled sensors"""
        sensor_data = {
            "timestamp": time.time()
        }
        
        # Use mock data if enabled
        if self.config.sensor.mock_enabled:
            mock_data = self.mock_sensor.read()
            sensor_data.update(mock_data)
            self.logger.debug("Using mock sensor data")
            return sensor_data
        
        # Read real sensors
        try:
            # DHT22 sensor
            if self.dht22:
                dht_data = self.dht22.read()
                sensor_data.update(dht_data)
            
            # BMP280 sensor
            if self.bmp280:
                bmp_data = self.bmp280.read()
                sensor_data.update(bmp_data)
            
            # Battery monitor
            if self.battery_monitor:
                battery_data = self.battery_monitor.read()
                sensor_data.update(battery_data)
            
            # If no real sensor data available, use mock data
            if not any(v is not None for k, v in sensor_data.items() if k != "timestamp"):
                self.logger.warning("No sensor data available, using mock data")
                mock_data = self.mock_sensor.read()
                sensor_data.update(mock_data)
            
        except Exception as e:
            self.logger.error(f"Error reading sensors: {e}")
            # Fallback to mock data
            mock_data = self.mock_sensor.read()
            sensor_data.update(mock_data)
        
        return sensor_data
    
    def get_sensor_status(self) -> Dict[str, bool]:
        """Get status of all sensors"""
        status = {
            "dht22": self.dht22.available if self.dht22 else False,
            "bmp280": self.bmp280.available if self.bmp280 else False,
            "battery_monitor": self.battery_monitor.available if self.battery_monitor else False,
            "mock_enabled": self.config.sensor.mock_enabled
        }
        
        return status
    
    def test_sensors(self):
        """Test all sensors and print results"""
        print("\n=== Sensor Test ===")
        
        status = self.get_sensor_status()
        for sensor, available in status.items():
            print(f"{sensor}: {'Available' if available else 'Not Available'}")
        
        print("\nReading sensors...")
        data = self.read_all_sensors()
        
        for key, value in data.items():
            if value is not None:
                if key == "temperature":
                    print(f"Temperature (DHT22): {value}°C")
                elif key == "humidity":
                    print(f"Humidity: {value}%")
                elif key == "temperature_bmp":
                    print(f"Temperature (BMP280): {value}°C")
                elif key == "pressure":
                    print(f"Pressure: {value} hPa")
                elif key == "altitude":
                    print(f"Altitude: {value} m")
                elif key == "battery_voltage":
                    print(f"Battery Voltage: {value} V")
                elif key == "rssi":
                    print(f"RSSI: {value} dBm")
        
        print("==================\n")

if __name__ == "__main__":
    # Test sensor manager
    from config import Config
    
    config = Config()
    config.sensor.mock_enabled = True  # Enable mock data for testing
    
    sensor_manager = SensorManager(config)
    sensor_manager.test_sensors()
