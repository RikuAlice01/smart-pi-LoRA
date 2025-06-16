"""
Device ID generation using MAC address
Compatible with the sample lora_send.py device ID method
"""

import uuid
import configparser
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DeviceIDGenerator:
    """Generate device ID from MAC address with configurable prefix"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize device ID generator"""
        self.config_file = config_file
        self.device_id = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration for device ID generation"""
        try:
            # Try to load from JSON config first
            if os.path.exists(self.config_file) and self.config_file.endswith('.json'):
                import json
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    self.id_prefix = config_data.get('device', {}).get('id_prefix', 'node_')
            else:
                # Fallback to INI config (compatible with sample)
                config = configparser.ConfigParser()
                if os.path.exists('config.ini'):
                    config.read('config.ini')
                    self.id_prefix = config.get('device', 'id_prefix', fallback='node_')
                else:
                    self.id_prefix = 'node_'
                    
        except Exception as e:
            logger.warning(f"Could not load config for device ID: {e}")
            self.id_prefix = 'node_'
    
    def get_device_id(self) -> str:
        """
        Generate device ID from MAC address
        Compatible with sample lora_send.py method
        """
        if self.device_id is None:
            # Get MAC address and format like sample code
            mac = hex(uuid.getnode())[2:].upper().zfill(12)
            # Use last 6 characters of MAC address
            self.device_id = f"{self.id_prefix}{mac[-6:]}"
            
            logger.info(f"Generated device ID: {self.device_id}")
        
        return self.device_id
    
    def get_full_mac(self) -> str:
        """Get full MAC address"""
        return hex(uuid.getnode())[2:].upper().zfill(12)
    
    def get_mac_suffix(self, length: int = 6) -> str:
        """Get MAC address suffix of specified length"""
        mac = self.get_full_mac()
        return mac[-length:]
    
    def set_prefix(self, prefix: str):
        """Set device ID prefix"""
        self.id_prefix = prefix
        self.device_id = None  # Reset cached device ID
        logger.info(f"Device ID prefix set to: {prefix}")
    
    def create_config_ini(self, filename: str = "config.ini"):
        """Create config.ini file with device ID settings"""
        config = configparser.ConfigParser()
        
        # Add device section
        config.add_section('device')
        config.set('device', 'id_prefix', self.id_prefix)
        
        # Add LoRa section with sample values
        config.add_section('lora')
        config.set('lora', 'frequency', '915.0')
        config.set('lora', 'tx_power', '14')
        config.set('lora', 'spreading_factor', '7')
        config.set('lora', 'bandwidth', '125')
        config.set('lora', 'coding_rate', '5')
        config.set('lora', 'preamble_length', '8')
        
        # Add send section with sample values
        config.add_section('send')
        config.set('send', 'mock_temp', '25.5')
        config.set('send', 'mock_hum', '60.0')
        config.set('send', 'mock_ph', '7.2')
        config.set('send', 'interval', '30')
        
        # Write config file
        with open(filename, 'w') as f:
            config.write(f)
        
        logger.info(f"Created config file: {filename}")
        print(f"📝 Created config file: {filename}")

def get_device_id(config_file: str = "config.json") -> str:
    """Convenience function to get device ID"""
    generator = DeviceIDGenerator(config_file)
    return generator.get_device_id()

if __name__ == "__main__":
    """Test device ID generation"""
    print("🆔 Testing Device ID Generation")
    
    generator = DeviceIDGenerator()
    
    print(f"Full MAC: {generator.get_full_mac()}")
    print(f"MAC Suffix (6): {generator.get_mac_suffix(6)}")
    print(f"MAC Suffix (8): {generator.get_mac_suffix(8)}")
    print(f"Device ID: {generator.get_device_id()}")
    
    # Test with different prefix
    generator.set_prefix("sensor_")
    print(f"Device ID (sensor_): {generator.get_device_id()}")
    
    # Create sample config
    generator.create_config_ini("sample_config.ini")
