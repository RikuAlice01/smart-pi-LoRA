"""
Application configuration management
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class LoRaConfig:
    """LoRa configuration parameters"""
    frequency: float = 915.0  # MHz
    bandwidth: int = 125  # kHz
    spreading_factor: int = 7
    coding_rate: int = 5
    power_level: int = 14  # dBm
    preamble_length: int = 8
    sync_word: int = 0x12

@dataclass
class SerialConfig:
    """Serial port configuration"""
    port: str = ""
    baudrate: int = 9600
    timeout: float = 1.0
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1

@dataclass
class EncryptionConfig:
    """Encryption configuration"""
    enabled: bool = False
    method: str = "AES"  # XOR, AES

class AppConfig:
    """Main application configuration"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.lora = LoRaConfig()
        self.serial = SerialConfig()
        self.encryption = EncryptionConfig()
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                if 'lora' in data:
                    self.lora = LoRaConfig(**data['lora'])
                if 'serial' in data:
                    self.serial = SerialConfig(**data['serial'])
                if 'encryption' in data:
                    self.encryption = EncryptionConfig(**data['encryption'])
                    
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            data = {
                'lora': asdict(self.lora),
                'serial': asdict(self.serial),
                'encryption': asdict(self.encryption)
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
