"""
Configuration management for Raspberry Pi LoRa SX126x
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class LoRaConfig:
    """LoRa radio configuration"""
    # Frequency settings
    frequency: float = 915.0  # MHz
    
    # Modulation parameters
    spreading_factor: int = 7  # 6-12
    bandwidth: int = 125  # kHz: 125, 250, 500
    coding_rate: int = 5  # 5-8 (4/5 to 4/8)
    
    # Power settings
    tx_power: int = 14  # dBm: -9 to 22
    
    # Packet parameters
    preamble_length: int = 8
    sync_word: int = 0x1424  # LoRa sync word
    crc_enabled: bool = True
    header_type: int = 0  # 0=explicit, 1=implicit
    
    # Timing
    tx_timeout: int = 5000  # ms
    rx_timeout: int = 30000  # ms

@dataclass
class GPIOConfig:
    """GPIO pin configuration"""
    reset_pin: int = 22
    busy_pin: int = 23
    dio1_pin: int = 24
    
    # SPI configuration
    spi_bus: int = 0
    spi_device: int = 0

@dataclass
class SensorConfig:
    """Sensor configuration"""
    # DHT22 sensor
    dht22_enabled: bool = True
    dht22_pin: int = 4
    
    # BMP280 sensor (I2C)
    bmp280_enabled: bool = True
    bmp280_address: int = 0x76
    
    # Reading interval
    read_interval: float = 30.0  # seconds
    
    # Mock data (for testing)
    mock_enabled: bool = False

@dataclass
class DeviceConfig:
    """Device identification"""
    device_id: str = "RPI_001"
    device_name: str = "Raspberry Pi LoRa Node"
    location: str = "Unknown"
    
    # Battery monitoring (if available)
    battery_monitoring: bool = False
    battery_pin: int = 26  # ADC pin for battery voltage

@dataclass
class NetworkConfig:
    """Network and communication settings"""
    # UART forwarding (to desktop application)
    uart_enabled: bool = True
    uart_port: str = "/dev/ttyUSB0"
    uart_baudrate: int = 9600
    
    # Encryption
    encryption_enabled: bool = False
    encryption_method: str = "AES"  # XOR, AES
    encryption_key: str = "MySecretKey123456"
    
    # Network settings
    network_id: int = 1
    node_address: int = 1

@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_file: str = "lora_node.log"
    max_log_size: int = 10  # MB
    backup_count: int = 5

# Regional frequency bands
FREQUENCY_BANDS = {
    "US915": {
        "frequency": 915.0,
        "description": "North America ISM band"
    },
    "EU868": {
        "frequency": 868.0,
        "description": "Europe ISM band"
    },
    "AS923": {
        "frequency": 923.0,
        "description": "Asia ISM band"
    },
    "AU915": {
        "frequency": 915.0,
        "description": "Australia ISM band"
    },
    "CN470": {
        "frequency": 470.0,
        "description": "China ISM band"
    },
    "IN865": {
        "frequency": 865.0,
        "description": "India ISM band"
    }
}

# Bandwidth mappings for SX126x
BANDWIDTH_MAP = {
    125: 0x04,
    250: 0x05,
    500: 0x06
}

# Spreading factor mappings
SPREADING_FACTOR_MAP = {
    6: 0x06,
    7: 0x07,
    8: 0x08,
    9: 0x09,
    10: 0x0A,
    11: 0x0B,
    12: 0x0C
}

# Coding rate mappings
CODING_RATE_MAP = {
    5: 0x01,  # 4/5
    6: 0x02,  # 4/6
    7: 0x03,  # 4/7
    8: 0x04   # 4/8
}

class Config:
    """Main configuration class"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        
        # Initialize configuration sections
        self.lora = LoRaConfig()
        self.gpio = GPIOConfig()
        self.sensor = SensorConfig()
        self.device = DeviceConfig()
        self.network = NetworkConfig()
        self.logging = LoggingConfig()
        
        # Load configuration if file exists
        self.load_config()
    
    def load_config(self) -> bool:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_file):
            print(f"Config file {self.config_file} not found, using defaults")
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Load each section
            if 'lora' in data:
                self.lora = LoRaConfig(**data['lora'])
            if 'gpio' in data:
                self.gpio = GPIOConfig(**data['gpio'])
            if 'sensor' in data:
                self.sensor = SensorConfig(**data['sensor'])
            if 'device' in data:
                self.device = DeviceConfig(**data['device'])
            if 'network' in data:
                self.network = NetworkConfig(**data['network'])
            if 'logging' in data:
                self.logging = LoggingConfig(**data['logging'])
            
            print(f"Configuration loaded from {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save configuration to JSON file"""
        try:
            data = {
                'lora': asdict(self.lora),
                'gpio': asdict(self.gpio),
                'sensor': asdict(self.sensor),
                'device': asdict(self.device),
                'network': asdict(self.network),
                'logging': asdict(self.logging)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def set_frequency_band(self, band: str) -> bool:
        """Set frequency band by region"""
        if band in FREQUENCY_BANDS:
            self.lora.frequency = FREQUENCY_BANDS[band]["frequency"]
            print(f"Frequency set to {self.lora.frequency} MHz ({band})")
            return True
        else:
            print(f"Unknown frequency band: {band}")
            print(f"Available bands: {list(FREQUENCY_BANDS.keys())}")
            return False
    
    def get_lora_modulation_params(self) -> tuple:
        """Get LoRa modulation parameters for SX126x"""
        sf = SPREADING_FACTOR_MAP.get(self.lora.spreading_factor, 0x07)
        bw = BANDWIDTH_MAP.get(self.lora.bandwidth, 0x04)
        cr = CODING_RATE_MAP.get(self.lora.coding_rate, 0x01)
        ldro = 1 if self.lora.spreading_factor >= 11 else 0  # Low Data Rate Optimize
        
        return sf, bw, cr, ldro
    
    def get_frequency_hz(self) -> int:
        """Get frequency in Hz"""
        return int(self.lora.frequency * 1000000)
    
    def validate_config(self) -> bool:
        """Validate configuration parameters"""
        errors = []
        
        # Validate LoRa parameters
        if not (6 <= self.lora.spreading_factor <= 12):
            errors.append("Spreading factor must be between 6 and 12")
        
        if self.lora.bandwidth not in [125, 250, 500]:
            errors.append("Bandwidth must be 125, 250, or 500 kHz")
        
        if not (5 <= self.lora.coding_rate <= 8):
            errors.append("Coding rate must be between 5 and 8")
        
        if not (-9 <= self.lora.tx_power <= 22):
            errors.append("TX power must be between -9 and 22 dBm")
        
        # Validate GPIO pins
        valid_pins = list(range(2, 28))  # Valid GPIO pins on Raspberry Pi
        if self.gpio.reset_pin not in valid_pins:
            errors.append(f"Invalid reset pin: {self.gpio.reset_pin}")
        
        if self.gpio.busy_pin not in valid_pins:
            errors.append(f"Invalid busy pin: {self.gpio.busy_pin}")
        
        if self.gpio.dio1_pin not in valid_pins:
            errors.append(f"Invalid DIO1 pin: {self.gpio.dio1_pin}")
        
        # Print errors
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("Configuration validation passed")
        return True
    
    def print_config(self):
        """Print current configuration"""
        print("\n=== LoRa SX126x Configuration ===")
        print(f"Device: {self.device.device_id} ({self.device.device_name})")
        print(f"Location: {self.device.location}")
        print(f"\nLoRa Settings:")
        print(f"  Frequency: {self.lora.frequency} MHz")
        print(f"  Spreading Factor: {self.lora.spreading_factor}")
        print(f"  Bandwidth: {self.lora.bandwidth} kHz")
        print(f"  Coding Rate: 4/{self.lora.coding_rate}")
        print(f"  TX Power: {self.lora.tx_power} dBm")
        print(f"  Sync Word: 0x{self.lora.sync_word:04X}")
        print(f"\nGPIO Settings:")
        print(f"  Reset Pin: {self.gpio.reset_pin}")
        print(f"  Busy Pin: {self.gpio.busy_pin}")
        print(f"  DIO1 Pin: {self.gpio.dio1_pin}")
        print(f"  SPI Bus: {self.gpio.spi_bus}")
        print(f"\nSensor Settings:")
        print(f"  DHT22 Enabled: {self.sensor.dht22_enabled} (Pin {self.sensor.dht22_pin})")
        print(f"  BMP280 Enabled: {self.sensor.bmp280_enabled} (I2C 0x{self.sensor.bmp280_address:02X})")
        print(f"  Read Interval: {self.sensor.read_interval}s")
        print(f"  Mock Mode: {self.sensor.mock_enabled}")
        print(f"\nNetwork Settings:")
        print(f"  UART Enabled: {self.network.uart_enabled}")
        print(f"  Encryption: {self.network.encryption_enabled} ({self.network.encryption_method})")
        print("================================\n")

def create_default_config(filename: str = "config.json") -> Config:
    """Create a default configuration file"""
    config = Config(filename)
    
    # Set some reasonable defaults for Raspberry Pi
    config.device.device_id = "RPI_001"
    config.device.device_name = "Raspberry Pi LoRa Sensor Node"
    config.device.location = "Home"
    
    # US915 frequency band
    config.lora.frequency = 915.0
    config.lora.spreading_factor = 7
    config.lora.bandwidth = 125
    config.lora.tx_power = 14
    
    # Enable sensors
    config.sensor.dht22_enabled = True
    config.sensor.bmp280_enabled = True
    config.sensor.read_interval = 30.0
    
    # Save the configuration
    config.save_config()
    
    return config

if __name__ == "__main__":
    # Create and test configuration
    config = create_default_config()
    config.print_config()
    
    # Test validation
    config.validate_config()
    
    # Test frequency band setting
    config.set_frequency_band("EU868")
    config.print_config()
