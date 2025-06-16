"""
Enhanced configuration management with validation and environment support
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
import jsonschema
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

@dataclass
class LoRaConfig:
    """LoRa radio configuration with validation"""
    frequency: float = 915.0
    spreading_factor: int = 7
    bandwidth: int = 125
    coding_rate: int = 5
    tx_power: int = 14
    preamble_length: int = 8
    sync_word: int = 0x1424
    crc_enabled: bool = True
    header_type: int = 0
    tx_timeout: int = 5000
    rx_timeout: int = 30000
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self.validate()
    
    def validate(self):
        """Validate LoRa configuration parameters"""
        errors = []
        
        if not (6 <= self.spreading_factor <= 12):
            errors.append("Spreading factor must be between 6 and 12")
        
        if self.bandwidth not in [125, 250, 500]:
            errors.append("Bandwidth must be 125, 250, or 500 kHz")
        
        if not (5 <= self.coding_rate <= 8):
            errors.append("Coding rate must be between 5 and 8")
        
        if not (-9 <= self.tx_power <= 22):
            errors.append("TX power must be between -9 and 22 dBm")
        
        if not (470.0 <= self.frequency <= 928.0):
            errors.append("Frequency must be between 470.0 and 928.0 MHz")
        
        if errors:
            raise ConfigurationError(f"LoRa configuration errors: {'; '.join(errors)}")

@dataclass
class GPIOConfig:
    """GPIO pin configuration with validation"""
    reset_pin: int = 22
    busy_pin: int = 23
    dio1_pin: int = 24
    spi_bus: int = 0
    spi_device: int = 0
    
    def __post_init__(self):
        """Validate GPIO configuration"""
        self.validate()
    
    def validate(self):
        """Validate GPIO pin assignments"""
        valid_pins = list(range(2, 28))
        errors = []
        
        if self.reset_pin not in valid_pins:
            errors.append(f"Invalid reset pin: {self.reset_pin}")
        
        if self.busy_pin not in valid_pins:
            errors.append(f"Invalid busy pin: {self.busy_pin}")
        
        if self.dio1_pin not in valid_pins:
            errors.append(f"Invalid DIO1 pin: {self.dio1_pin}")
        
        # Check for pin conflicts
        pins = [self.reset_pin, self.busy_pin, self.dio1_pin]
        if len(pins) != len(set(pins)):
            errors.append("GPIO pins must be unique")
        
        if errors:
            raise ConfigurationError(f"GPIO configuration errors: {'; '.join(errors)}")

@dataclass
class SensorConfig:
    """Sensor configuration with advanced options"""
    dht22_enabled: bool = True
    dht22_pin: int = 4
    bmp280_enabled: bool = True
    bmp280_address: int = 0x76
    read_interval: float = 30.0
    mock_enabled: bool = False
    calibration_enabled: bool = True
    outlier_detection: bool = True
    smoothing_enabled: bool = True
    smoothing_window: int = 5
    
    def validate(self):
        """Validate sensor configuration"""
        errors = []
        
        if self.read_interval < 1.0:
            errors.append("Read interval must be at least 1.0 seconds")
        
        if not (1 <= self.smoothing_window <= 20):
            errors.append("Smoothing window must be between 1 and 20")
        
        if errors:
            raise ConfigurationError(f"Sensor configuration errors: {'; '.join(errors)}")

@dataclass
class DeviceConfig:
    """Device identification and metadata"""
    device_id: str = ""
    device_name: str = "Raspberry Pi LoRa Node"
    location: str = "Unknown"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    battery_monitoring: bool = False
    battery_pin: int = 26
    firmware_version: str = "2.0.0"
    
    def validate(self):
        """Validate device configuration"""
        errors = []
        
        if not self.device_id:
            errors.append("Device ID cannot be empty")
        
        if len(self.device_id) > 50:
            errors.append("Device ID must be 50 characters or less")
        
        if errors:
            raise ConfigurationError(f"Device configuration errors: {'; '.join(errors)}")

@dataclass
class NetworkConfig:
    """Network and communication settings"""
    uart_enabled: bool = True
    uart_port: str = "/dev/ttyUSB0"
    uart_baudrate: int = 9600
    encryption_enabled: bool = True
    encryption_method: str = "keyfile"
    keyfile_path: str = "keyfile.bin"
    network_id: int = 1
    node_address: int = 1
    heartbeat_interval: int = 300
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    def validate(self):
        """Validate network configuration"""
        errors = []
        
        if self.uart_baudrate not in [9600, 19200, 38400, 57600, 115200]:
            errors.append("Invalid UART baudrate")
        
        if self.encryption_method not in ["keyfile", "aes", "xor", "none"]:
            errors.append("Invalid encryption method")
        
        if self.retry_attempts < 0:
            errors.append("Retry attempts cannot be negative")
        
        if errors:
            raise ConfigurationError(f"Network configuration errors: {'; '.join(errors)}")

@dataclass
class LoggingConfig:
    """Logging configuration with advanced options"""
    log_level: str = "INFO"
    log_file: str = "lora_node.log"
    max_log_size: int = 10
    backup_count: int = 5
    console_logging: bool = True
    file_logging: bool = True
    structured_logging: bool = False
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def validate(self):
        """Validate logging configuration"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ConfigurationError(f"Invalid log level: {self.log_level}")

@dataclass
class PerformanceConfig:
    """Performance and optimization settings"""
    cpu_limit: float = 80.0
    memory_limit: int = 512
    disk_space_limit: int = 1024
    monitoring_enabled: bool = True
    profiling_enabled: bool = False
    optimization_level: str = "balanced"
    thread_pool_size: int = 4
    
    def validate(self):
        """Validate performance configuration"""
        errors = []
        
        if not (10.0 <= self.cpu_limit <= 100.0):
            errors.append("CPU limit must be between 10.0 and 100.0")
        
        if self.optimization_level not in ["performance", "balanced", "power_save"]:
            errors.append("Invalid optimization level")
        
        if errors:
            raise ConfigurationError(f"Performance configuration errors: {'; '.join(errors)}")

class ConfigManager:
    """Advanced configuration manager with schema validation"""
    
    # JSON Schema for configuration validation
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "lora": {"type": "object"},
            "gpio": {"type": "object"},
            "sensor": {"type": "object"},
            "device": {"type": "object"},
            "network": {"type": "object"},
            "logging": {"type": "object"},
            "performance": {"type": "object"}
        },
        "required": ["lora", "gpio", "sensor", "device"]
    }
    
    def __init__(self, config_file: str = "config.json", environment: str = "production"):
        """Initialize configuration manager"""
        self.config_file = Path(config_file)
        self.environment = environment
        self.config_dir = self.config_file.parent / "config"
        
        # Initialize configuration sections
        self.lora = LoRaConfig()
        self.gpio = GPIOConfig()
        self.sensor = SensorConfig()
        self.device = DeviceConfig()
        self.network = NetworkConfig()
        self.logging = LoggingConfig()
        self.performance = PerformanceConfig()
        
        # Load configuration
        self.load_config()
        
        logger.info(f"Configuration manager initialized for {environment} environment")
    
    def load_config(self) -> bool:
        """Load configuration with environment support"""
        try:
            # Load base configuration
            if self.config_file.exists():
                self._load_from_file(self.config_file)
            
            # Load environment-specific configuration
            env_config_file = self.config_dir / f"{self.environment}.json"
            if env_config_file.exists():
                self._load_from_file(env_config_file)
                logger.info(f"Loaded environment config: {env_config_file}")
            
            # Load environment variables
            self._load_from_environment()
            
            # Validate all configurations
            self.validate_all()
            
            logger.info("Configuration loaded and validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")
    
    def _load_from_file(self, file_path: Path):
        """Load configuration from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate against schema
            jsonschema.validate(data, self.CONFIG_SCHEMA)
            
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
            if 'performance' in data:
                self.performance = PerformanceConfig(**data['performance'])
            
            logger.debug(f"Configuration loaded from {file_path}")
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {file_path}: {e}")
        except jsonschema.ValidationError as e:
            raise ConfigurationError(f"Schema validation failed: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'LORA_FREQUENCY': ('lora', 'frequency', float),
            'LORA_TX_POWER': ('lora', 'tx_power', int),
            'DEVICE_ID': ('device', 'device_id', str),
            'DEVICE_LOCATION': ('device', 'location', str),
            'LOG_LEVEL': ('logging', 'log_level', str),
            'SENSOR_INTERVAL': ('sensor', 'read_interval', float),
        }
        
        for env_var, (section, key, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    converted_value = type_func(value)
                    setattr(getattr(self, section), key, converted_value)
                    logger.debug(f"Set {section}.{key} = {converted_value} from environment")
                except ValueError as e:
                    logger.warning(f"Invalid environment variable {env_var}: {e}")
    
    def validate_all(self):
        """Validate all configuration sections"""
        try:
            self.lora.validate()
            self.gpio.validate()
            self.sensor.validate()
            self.device.validate()
            self.network.validate()
            self.logging.validate()
            self.performance.validate()
            
            logger.info("All configuration sections validated successfully")
            
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")
    
    def save_config(self, file_path: Optional[Path] = None) -> bool:
        """Save configuration to file"""
        try:
            target_file = file_path or self.config_file
            
            data = {
                'lora': asdict(self.lora),
                'gpio': asdict(self.gpio),
                'sensor': asdict(self.sensor),
                'device': asdict(self.device),
                'network': asdict(self.network),
                'logging': asdict(self.logging),
                'performance': asdict(self.performance)
            }
            
            # Create directory if it doesn't exist
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_file, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
            
            logger.info(f"Configuration saved to {target_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_lora_modulation_params(self) -> tuple:
        """Get LoRa modulation parameters for SX126x"""
        sf_map = {6: 0x06, 7: 0x07, 8: 0x08, 9: 0x09, 10: 0x0A, 11: 0x0B, 12: 0x0C}
        bw_map = {125: 0x04, 250: 0x05, 500: 0x06}
        cr_map = {5: 0x01, 6: 0x02, 7: 0x03, 8: 0x04}
        
        sf = sf_map.get(self.lora.spreading_factor, 0x07)
        bw = bw_map.get(self.lora.bandwidth, 0x04)
        cr = cr_map.get(self.lora.coding_rate, 0x01)
        ldro = 1 if self.lora.spreading_factor >= 11 else 0
        
        return sf, bw, cr, ldro
    
    def get_frequency_hz(self) -> int:
        """Get frequency in Hz"""
        return int(self.lora.frequency * 1000000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'lora': asdict(self.lora),
            'gpio': asdict(self.gpio),
            'sensor': asdict(self.sensor),
            'device': asdict(self.device),
            'network': asdict(self.network),
            'logging': asdict(self.logging),
            'performance': asdict(self.performance)
        }
    
    def print_config(self):
        """Print current configuration in a formatted way"""
        print("\n" + "="*60)
        print("LoRa SX126x Sensor Node Configuration")
        print("="*60)
        
        print(f"\n📱 Device Information:")
        print(f"  ID: {self.device.device_id}")
        print(f"  Name: {self.device.device_name}")
        print(f"  Location: {self.device.location}")
        print(f"  Firmware: {self.device.firmware_version}")
        
        print(f"\n📡 LoRa Settings:")
        print(f"  Frequency: {self.lora.frequency} MHz")
        print(f"  Spreading Factor: {self.lora.spreading_factor}")
        print(f"  Bandwidth: {self.lora.bandwidth} kHz")
        print(f"  Coding Rate: 4/{self.lora.coding_rate}")
        print(f"  TX Power: {self.lora.tx_power} dBm")
        
        print(f"\n🔌 GPIO Settings:")
        print(f"  Reset Pin: {self.gpio.reset_pin}")
        print(f"  Busy Pin: {self.gpio.busy_pin}")
        print(f"  DIO1 Pin: {self.gpio.dio1_pin}")
        print(f"  SPI Bus: {self.gpio.spi_bus}")
        
        print(f"\n🌡️ Sensor Settings:")
        print(f"  DHT22: {'Enabled' if self.sensor.dht22_enabled else 'Disabled'}")
        print(f"  BMP280: {'Enabled' if self.sensor.bmp280_enabled else 'Disabled'}")
        print(f"  Read Interval: {self.sensor.read_interval}s")
        print(f"  Mock Mode: {'Enabled' if self.sensor.mock_enabled else 'Disabled'}")
        
        print(f"\n🔐 Network Settings:")
        print(f"  Encryption: {'Enabled' if self.network.encryption_enabled else 'Disabled'}")
        print(f"  Method: {self.network.encryption_method}")
        print(f"  UART: {'Enabled' if self.network.uart_enabled else 'Disabled'}")
        
        print("="*60 + "\n")

# Backward compatibility
Config = ConfigManager

def create_default_config(filename: str = "config.json") -> ConfigManager:
    """Create a default configuration file"""
    config = ConfigManager(filename)
    
    # Set reasonable defaults
    config.device.device_id = "RPI_001"
    config.device.device_name = "Raspberry Pi LoRa Sensor Node"
    config.device.location = "Home"
    
    # Save the configuration
    config.save_config()
    
    return config

if __name__ == "__main__":
    # Test configuration management
    try:
        config = create_default_config("test_config.json")
        config.print_config()
        print("✅ Configuration test passed")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
