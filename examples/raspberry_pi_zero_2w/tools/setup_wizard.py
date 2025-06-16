#!/usr/bin/env python3
"""
Interactive setup wizard for LoRa Sensor Node
"""

import os
import sys
import json
import subprocess
import secrets
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config import ConfigManager
from core.device_id import DeviceIDManager
from communication.encryption import EncryptionManager


class SetupWizard:
    """Interactive setup wizard"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.config_path = self.base_path / "config"
        self.keyfile_path = self.base_path / "keyfile.bin"
    
    def run(self):
        """Run the setup wizard"""
        print("🚀 LoRa Sensor Node Setup Wizard")
        print("=" * 40)
        
        try:
            self.check_system_requirements()
            self.setup_spi()
            self.generate_keyfile()
            self.configure_device()
            self.setup_systemd_service()
            self.run_tests()
            
            print("\n✅ Setup completed successfully!")
            print("🔄 Please reboot your system: sudo reboot")
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)
    
    def check_system_requirements(self):
        """Check system requirements"""
        print("\n🔍 Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3.7, 0):
            raise Exception("Python 3.7+ required")
        print("✅ Python version OK")
        
        # Check if running on Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' not in f.read():
                    print("⚠️  Warning: Not running on Raspberry Pi")
        except:
            pass
        
        # Check required packages
        required_packages = ['spidev', 'RPi.GPIO', 'cryptography']
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} installed")
            except ImportError:
                print(f"📦 Installing {package}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True)
    
    def setup_spi(self):
        """Setup SPI interface"""
        print("\n🔧 Setting up SPI interface...")
        
        # Check if SPI is enabled
        if not os.path.exists('/dev/spidev0.0'):
            print("🔧 Enabling SPI interface...")
            
            # Enable SPI in config.txt
            config_txt = '/boot/config.txt'
            if os.path.exists(config_txt):
                with open(config_txt, 'r') as f:
                    content = f.read()
                
                if 'dtparam=spi=on' not in content:
                    with open(config_txt, 'a') as f:
                        f.write('\n# Enable SPI\ndtparam=spi=on\n')
                    print("✅ SPI enabled in /boot/config.txt")
            
            # Add user to spi group
            try:
                subprocess.run(['sudo', 'usermod', '-a', '-G', 'spi,gpio', 
                              os.getenv('USER')], check=True)
                print("✅ User added to spi and gpio groups")
            except subprocess.CalledProcessError:
                print("⚠️  Could not add user to groups (may need manual setup)")
        else:
            print("✅ SPI interface already enabled")
    
    def generate_keyfile(self):
        """Generate encryption keyfile"""
        print("\n🔐 Setting up encryption...")
        
        if self.keyfile_path.exists():
            response = input("Keyfile already exists. Regenerate? (y/N): ")
            if response.lower() != 'y':
                print("✅ Using existing keyfile")
                return
        
        # Generate 32-byte key
        key = secrets.token_bytes(32)
        
        with open(self.keyfile_path, 'wb') as f:
            f.write(key)
        
        # Set secure permissions
        os.chmod(self.keyfile_path, 0o600)
        
        print(f"✅ Generated keyfile: {self.keyfile_path}")
        print("🔒 Key permissions set to 600 (owner read/write only)")
    
    def configure_device(self):
        """Configure device settings"""
        print("\n⚙️  Configuring device...")
        
        # Generate device ID
        device_id = DeviceIDManager.generate_mac_based_id("node_")
        print(f"🆔 Generated device ID: {device_id}")
        
        # Get user preferences
        print("\nLoRa Configuration:")
        frequency = float(input("Frequency (MHz) [915.0]: ") or "915.0")
        tx_power = int(input("TX Power (dBm) [14]: ") or "14")
        
        print("\nSensor Configuration:")
        sensor_interval = int(input("Sensor reading interval (seconds) [30]: ") or "30")
        
        # Create configuration
        config = {
            "device": {
                "id": device_id,
                "id_prefix": "node_",
                "name": f"LoRa Node {device_id}"
            },
            "lora": {
                "frequency": frequency,
                "tx_power": tx_power,
                "spreading_factor": 7,
                "bandwidth": 125000,
                "coding_rate": 5,
                "preamble_length": 8
            },
            "sensors": {
                "enabled": ["temperature", "humidity", "ph"],
                "interval": sensor_interval,
                "mock_data": {
                    "temperature": 25.0,
                    "humidity": 60.0,
                    "ph": 7.0
                }
            },
            "encryption": {
                "enabled": True,
                "keyfile": "keyfile.bin"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/sensor_node.log",
                "max_size": "10MB",
                "backup_count": 5
            }
        }
        
        # Save configuration
        self.config_path.mkdir(exist_ok=True)
        config_file = self.config_path / "production.json"
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration saved: {config_file}")
    
    def setup_systemd_service(self):
        """Setup systemd service for auto-start"""
        print("\n🔄 Setting up systemd service...")
        
        response = input("Setup auto-start service? (Y/n): ")
        if response.lower() == 'n':
            return
        
        service_content = f"""[Unit]
Description=LoRa Sensor Node
After=network.target
Wants=network.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={self.base_path}
ExecStart={sys.executable} {self.base_path}/main.py
Restart=always
RestartSec=10
Environment=PYTHONPATH={self.base_path}/src

[Install]
WantedBy=multi-user.target
"""
        
        service_file = "/etc/systemd/system/lora-sensor-node.service"
        
        try:
            with open("/tmp/lora-sensor-node.service", "w") as f:
                f.write(service_content)
            
            subprocess.run(['sudo', 'mv', '/tmp/lora-sensor-node.service', 
                          service_file], check=True)
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'lora-sensor-node'], 
                         check=True)
            
            print("✅ Systemd service installed and enabled")
            print("🔄 Service will start automatically on boot")
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Could not setup systemd service: {e}")
    
    def run_tests(self):
        """Run basic tests"""
        print("\n🧪 Running basic tests...")
        
        try:
            # Test configuration loading
            config_file = self.config_path / "production.json"
            config_manager = ConfigManager(str(config_file))
            print("✅ Configuration loading test passed")
            
            # Test encryption
            encryption_manager = EncryptionManager(str(self.keyfile_path))
            test_data = "Hello, LoRa!"
            encrypted = encryption_manager.encrypt(test_data)
            decrypted = encryption_manager.decrypt(encrypted)
            assert decrypted == test_data
            print("✅ Encryption test passed")
            
            print("✅ All tests passed")
            
        except Exception as e:
            print(f"⚠️  Test failed: {e}")


if __name__ == "__main__":
    wizard = SetupWizard()
    wizard.run()
