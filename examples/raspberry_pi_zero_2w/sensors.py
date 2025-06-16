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
    """Enhanced mock sensor for testing with realistic variations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Base values with realistic ranges
        self.base_temp = 22.0
        self.base_humidity = 50.0
        self.base_pressure = 1013.25
        
        # Simulation state
        self.time_offset = 0
        self.weather_pattern = "stable"  # stable, warming, cooling, stormy
        self.pattern_duration = 0
        
        # Device simulation
        self.device_health = 100.0  # Simulated device health percentage
        self.battery_drain_rate = 0.001  # Battery drain per reading
        self.current_battery = 4.1  # Start with good battery
        
        self.logger.info("Enhanced mock sensor initialized")
    
    def _simulate_weather_pattern(self):
        """Simulate realistic weather patterns"""
        import random
        
        # Change weather pattern occasionally
        if self.pattern_duration <= 0:
            patterns = ["stable", "warming", "cooling", "stormy", "humid", "dry"]
            self.weather_pattern = random.choice(patterns)
            self.pattern_duration = random.randint(10, 50)  # Pattern lasts 10-50 readings
            self.logger.debug(f"Weather pattern changed to: {self.weather_pattern}")
        
        self.pattern_duration -= 1
        
        # Apply pattern effects
        temp_trend = 0
        humidity_trend = 0
        pressure_trend = 0
        
        if self.weather_pattern == "warming":
            temp_trend = 0.1
            humidity_trend = -0.2
            pressure_trend = 0.05
        elif self.weather_pattern == "cooling":
            temp_trend = -0.1
            humidity_trend = 0.1
            pressure_trend = -0.05
        elif self.weather_pattern == "stormy":
            temp_trend = random.uniform(-0.2, 0.1)
            humidity_trend = 0.3
            pressure_trend = -0.2
        elif self.weather_pattern == "humid":
            humidity_trend = 0.2
            temp_trend = 0.05
        elif self.weather_pattern == "dry":
            humidity_trend = -0.2
            temp_trend = 0.1
        
        return temp_trend, humidity_trend, pressure_trend
    
    def _simulate_daily_cycle(self):
        """Simulate daily temperature and humidity cycles"""
        import math
        
        # Simulate time of day effect (24-hour cycle)
        hour_of_day = (self.time_offset % 1440) / 60  # Convert to hours (1440 min = 24h)
        
        # Temperature varies throughout the day (peak at 2 PM, low at 6 AM)
        temp_cycle = 3 * math.sin((hour_of_day - 6) * math.pi / 12)
        
        # Humidity is inverse to temperature (high at night, low during day)
        humidity_cycle = -10 * math.sin((hour_of_day - 6) * math.pi / 12)
        
        return temp_cycle, humidity_cycle
    
    def read(self) -> Dict[str, Any]:
        """Generate enhanced mock sensor data with realistic patterns"""
        self.time_offset += 1
        
        # Get weather pattern effects
        temp_trend, humidity_trend, pressure_trend = self._simulate_weather_pattern()
        
        # Get daily cycle effects
        temp_cycle, humidity_cycle = self._simulate_daily_cycle()
        
        # Generate base variations
        temp_variation = random.uniform(-1, 1) + temp_trend + temp_cycle
        humidity_variation = random.uniform(-3, 3) + humidity_trend + humidity_cycle
        pressure_variation = random.uniform(-5, 5) + pressure_trend
        
        # Calculate final values
        temperature = self.base_temp + temp_variation
        humidity = max(0, min(100, self.base_humidity + humidity_variation))
        pressure = self.base_pressure + pressure_variation
        
        # Calculate altitude from pressure
        altitude = 44330 * (1 - (pressure / 1013.25) ** 0.1903)
        
        # Simulate battery drain
        self.current_battery -= self.battery_drain_rate
        if self.current_battery < 3.0:
            self.current_battery = 4.2  # "Replace battery"
        
        # Add some noise to battery reading
        battery_voltage = self.current_battery + random.uniform(-0.05, 0.05)
        
        # Simulate RSSI based on "distance" and "interference"
        base_rssi = -75
        rssi_variation = random.randint(-15, 10)
        rssi = base_rssi + rssi_variation
        
        # Simulate device health degradation
        self.device_health -= random.uniform(0, 0.01)
        if self.device_health < 50:
            self.device_health = 100  # "Maintenance performed"
        
        data = {
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "pressure": round(pressure, 1),
            "altitude": round(altitude, 1),
            "temperature_bmp": round(temperature + random.uniform(-0.5, 0.5), 1),
            "battery_voltage": round(battery_voltage, 2),
            "rssi": rssi,
            "device_health": round(self.device_health, 1),
            "weather_pattern": self.weather_pattern,
            "readings_count": self.time_offset
        }
        
        # Occasionally simulate sensor errors
        if random.random() < 0.02:  # 2% chance of error
            error_type = random.choice(["temp_error", "humidity_error", "pressure_error"])
            if error_type == "temp_error":
                data["temperature"] = None
                self.logger.warning("Simulated temperature sensor error")
            elif error_type == "humidity_error":
                data["humidity"] = None
                self.logger.warning("Simulated humidity sensor error")
            elif error_type == "pressure_error":
                data["pressure"] = None
                data["altitude"] = None
                self.logger.warning("Simulated pressure sensor error")
        
        return data

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
                elif key == "device_health":
                    print(f"Device Health: {value}%")
                elif key == "weather_pattern":
                    print(f"Weather Pattern: {value}")
                elif key == "readings_count":
                    print(f"Readings Count: {value}")
        
        print("==================\n")

if __name__ == "__main__":
    # Test sensor manager
    from config import Config
    
    config = Config()
    config.sensor.mock_enabled = True  # Enable mock data for testing
    
    sensor_manager = SensorManager(config)
    sensor_manager.test_sensors()
