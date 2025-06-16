"""
Enhanced device ID management with MAC address and configuration support
"""

import uuid
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import json
import configparser
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class DeviceIDManager:
    """Enhanced device ID management with multiple generation methods"""
    
    def __init__(self, config_file: Optional[str] = None, prefix: str = "node_"):
        """Initialize device ID manager"""
        self.config_file = config_file
        self.prefix = prefix
        self.device_id = None
        self.mac_address = None
        self.serial_number = None
        
        # Load configuration
        self._load_config()
        
        logger.info("Device ID manager initialized")
    
    def _load_config(self):
        """Load configuration for device ID generation"""
        try:
            if self.config_file and Path(self.config_file).exists():
                if self.config_file.endswith('.json'):
                    self._load_json_config()
                elif self.config_file.endswith('.ini'):
                    self._load_ini_config()
                else:
                    logger.warning(f"Unsupported config file format: {self.config_file}")
            
        except Exception as e:
            logger.warning(f"Could not load config for device ID: {e}")
    
    def _load_json_config(self):
        """Load configuration from JSON file"""
        with open(self.config_file, 'r') as f:
            config_data = json.load(f)
            device_config = config_data.get('device', {})
            self.prefix = device_config.get('id_prefix', self.prefix)
            
            # Load pre-configured device ID if available
            if 'device_id' in device_config and device_config['device_id']:
                self.device_id = device_config['device_id']
    
    def _load_ini_config(self):
        """Load configuration from INI file"""
        config = configparser.ConfigParser()
        config.read(self.config_file)
        
        if 'device' in config:
            self.prefix = config.get('device', 'id_prefix', fallback=self.prefix)
            
            # Load pre-configured device ID if available
            device_id = config.get('device', 'device_id', fallback='')
            if device_id:
                self.device_id = device_id
    
    def get_mac_address(self) -> str:
        """Get MAC address of the device"""
        if self.mac_address is None:
            try:
                # Get MAC address
                mac = uuid.getnode()
                self.mac_address = hex(mac)[2:].upper().zfill(12)
                logger.debug(f"MAC address: {self.mac_address}")
            except Exception as e:
                logger.error(f"Failed to get MAC address: {e}")
                # Fallback to a deterministic value
                self.mac_address = "000000000000"
        
        return self.mac_address
    
    def get_cpu_serial(self) -> Optional[str]:
        """Get Raspberry Pi CPU serial number"""
        if self.serial_number is None:
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('Serial'):
                            self.serial_number = line.split(':')[1].strip()[-8:].upper()
                            logger.debug(f"CPU serial: {self.serial_number}")
                            break
            except Exception as e:
                logger.warning(f"Could not read CPU serial: {e}")
                self.serial_number = None
        
        return self.serial_number
    
    def generate_mac_based_id(self, suffix_length: int = 6) -> str:
        """Generate device ID based on MAC address"""
        mac = self.get_mac_address()
        suffix = mac[-suffix_length:]
        return f"{self.prefix}{suffix}"
    
    def generate_serial_based_id(self) -> Optional[str]:
        """Generate device ID based on CPU serial number"""
        serial = self.get_cpu_serial()
        if serial:
            return f"{self.prefix}{serial}"
        return None
    
    def generate_hybrid_id(self) -> str:
        """Generate device ID using both MAC and serial (if available)"""
        mac = self.get_mac_address()
        serial = self.get_cpu_serial()
        
        if serial:
            # Use combination of serial and MAC
            combined = f"{serial}{mac[-4:]}"
            return f"{self.prefix}{combined}"
        else:
            # Fallback to MAC-based ID
            return self.generate_mac_based_id()
    
    def generate_hash_based_id(self, data: str = None) -> str:
        """Generate device ID using hash of system information"""
        if data is None:
            # Combine multiple system identifiers
            mac = self.get_mac_address()
            serial = self.get_cpu_serial() or "unknown"
            
            # Add hostname if available
            try:
                import socket
                hostname = socket.gethostname()
            except:
                hostname = "unknown"
            
            data = f"{mac}{serial}{hostname}"
        
        # Create hash
        hash_obj = hashlib.sha256(data.encode())
        hash_hex = hash_obj.hexdigest()[:8].upper()
        
        return f"{self.prefix}{hash_hex}"
    
    def get_device_id(self, method: str = "mac") -> str:
        """
        Get device ID using specified method
        
        Args:
            method: Generation method ("mac", "serial", "hybrid", "hash", "config")
        """
        if self.device_id and method == "config":
            return self.device_id
        
        if method == "mac":
            return self.generate_mac_based_id()
        elif method == "serial":
            serial_id = self.generate_serial_based_id()
            return serial_id if serial_id else self.generate_mac_based_id()
        elif method == "hybrid":
            return self.generate_hybrid_id()
        elif method == "hash":
            return self.generate_hash_based_id()
        elif method == "config":
            return self.device_id or self.generate_mac_based_id()
        else:
            raise ValueError(f"Unknown device ID generation method: {method}")
    
    def set_device_id(self, device_id: str):
        """Set device ID manually"""
        if not device_id:
            raise ValueError("Device ID cannot be empty")
        
        if len(device_id) > 50:
            raise ValueError("Device ID too long (max 50 characters)")
        
        self.device_id = device_id
        logger.info(f"Device ID set manually: {device_id}")
    
    def set_prefix(self, prefix: str):
        """Set device ID prefix"""
        if not prefix:
            raise ValueError("Prefix cannot be empty")
        
        self.prefix = prefix
        self.device_id = None  # Reset cached device ID
        logger.info(f"Device ID prefix set to: {prefix}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get comprehensive device information"""
        return {
            "device_id": self.get_device_id(),
            "mac_address": self.get_mac_address(),
            "cpu_serial": self.get_cpu_serial(),
            "prefix": self.prefix,
            "generation_methods": {
                "mac": self.generate_mac_based_id(),
                "serial": self.generate_serial_based_id(),
                "hybrid": self.generate_hybrid_id(),
                "hash": self.generate_hash_based_id()
            }
        }
    
    def validate_device_id(self, device_id: str) -> bool:
        """Validate device ID format"""
        if not device_id:
            return False
        
        if len(device_id) > 50:
            return False
        
        # Check if it contains only valid characters
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        if not all(c in valid_chars for c in device_id.upper()):
            return False
        
        return True
    
    def save_to_config(self, config_file: str = None):
        """Save device ID to configuration file"""
        target_file = config_file or self.config_file
        
        if not target_file:
            raise ValueError("No configuration file specified")
        
        try:
            config_path = Path(target_file)
            
            if config_path.suffix == '.json':
                self._save_to_json(config_path)
            elif config_path.suffix == '.ini':
                self._save_to_ini(config_path)
            else:
                raise ValueError(f"Unsupported config file format: {target_file}")
            
            logger.info(f"Device ID saved to {target_file}")
            
        except Exception as e:
            logger.error(f"Failed to save device ID to config: {e}")
            raise
    
    def _save_to_json(self, config_path: Path):
        """Save device ID to JSON configuration file"""
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        else:
            config_data = {}
        
        if 'device' not in config_data:
            config_data['device'] = {}
        
        config_data['device']['device_id'] = self.get_device_id()
        config_data['device']['id_prefix'] = self.prefix
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def _save_to_ini(self, config_path: Path):
        """Save device ID to INI configuration file"""
        config = configparser.ConfigParser()
        
        if config_path.exists():
            config.read(config_path)
        
        if 'device' not in config:
            config.add_section('device')
        
        config.set('device', 'device_id', self.get_device_id())
        config.set('device', 'id_prefix', self.prefix)
        
        with open(config_path, 'w') as f:
            config.write(f)

def get_device_id(config_file: str = None, method: str = "mac") -> str:
    """Convenience function to get device ID"""
    manager = DeviceIDManager(config_file)
    return manager.get_device_id(method)

if __name__ == "__main__":
    """Test device ID generation"""
    print("🆔 Testing Device ID Generation")
    
    manager = DeviceIDManager()
    
    print(f"MAC Address: {manager.get_mac_address()}")
    print(f"CPU Serial: {manager.get_cpu_serial()}")
    
    print("\nGeneration Methods:")
    for method in ["mac", "serial", "hybrid", "hash"]:
        try:
            device_id = manager.get_device_id(method)
            print(f"  {method.upper()}: {device_id}")
        except Exception as e:
            print(f"  {method.upper()}: Error - {e}")
    
    print(f"\nDevice Info:")
    info = manager.get_device_info()
    for key, value in info.items():
        if key != "generation_methods":
            print(f"  {key}: {value}")
