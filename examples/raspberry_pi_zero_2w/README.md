# LoRa Sensor Node for Raspberry Pi Zero 2W

A production-ready LoRa sensor node implementation for Raspberry Pi Zero 2W with SX126x LoRa HAT, featuring AES encryption, device management, and comprehensive monitoring.

## 🚀 Features

### Core Functionality
- **LoRa Communication**: SX126x-based long-range wireless communication
- **AES Encryption**: Secure data transmission using keyfile.bin
- **Device ID Management**: MAC-based unique device identification
- **Sensor Integration**: Temperature, humidity, pH sensors with mock data support
- **Data Buffering**: Local storage with retry mechanisms
- **Health Monitoring**: System performance and hardware monitoring

### Production Features
- **Async Architecture**: Non-blocking operations with concurrent processing
- **Error Handling**: Comprehensive error recovery and logging
- **Configuration Management**: JSON-based configuration with validation
- **Service Integration**: Systemd service for auto-start
- **Maintenance Tools**: Automated maintenance and diagnostics
- **Testing Suite**: Comprehensive unit tests

## 📁 Project Structure

\`\`\`
raspberry_pi_zero_2w/
├── src/                    # Source code
│   ├── core/              # Core modules (config, device_id, exceptions)
│   ├── hardware/          # Hardware interfaces (GPIO, sensors, LoRa)
│   ├── communication/     # Communication (LoRa, encryption, protocol)
│   ├── data/              # Data management (buffer, storage, export)
│   └── utils/             # Utilities (logging, health, helpers)
├── config/                # Configuration files
│   ├── default.json       # Default configuration
│   └── production.json    # Production configuration
├── tests/                 # Unit tests
├── tools/                 # Maintenance and setup tools
├── logs/                  # Log files (created at runtime)
├── main.py               # Main application
├── requirements.txt      # Python dependencies
└── setup.sh             # Installation script
\`\`\`

## 🔧 Hardware Requirements

### Required Components
- **Raspberry Pi Zero 2W**
- **SX126x LoRa HAT** (e.g., Waveshare SX1262 LoRa HAT)
- **MicroSD Card** (16GB+ recommended)
- **Power Supply** (5V 2.5A recommended)

### Pin Connections
\`\`\`
┌─────────────────────────────────────────┐
│ Pi Pin │ GPIO │ SPI Signal │ SX126x Pin │
├─────────────────────────────────────────┤
│   19   │  10  │ SPI0_MOSI  │    MOSI    │
│   21   │   9  │ SPI0_MISO  │    MISO    │
│   23   │  11  │ SPI0_SCLK  │    SCLK    │
│   24   │   8  │ SPI0_CE0   │    NSS     │
│   15   │  22  │   GPIO     │   RESET    │
│   16   │  23  │   GPIO     │    BUSY    │
│   18   │  24  │   GPIO     │    DIO1    │
│  1,17  │ 3.3V │   Power    │    VCC     │
│ 6,9,14,20,25,30,34,39 │ GND │ Ground │    GND     │
└─────────────────────────────────────────┘
\`\`\`

## 🚀 Quick Start

### 1. Automated Setup (Recommended)
\`\`\`bash
# Clone and setup
git clone <repository>
cd raspberry_pi_zero_2w

# Run setup wizard
chmod +x setup.sh
./setup.sh

# Reboot system
sudo reboot

# Start application
python3 main.py
\`\`\`

### 2. Manual Setup

#### Install Dependencies
\`\`\`bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python packages
pip3 install -r requirements.txt

# Enable SPI
sudo raspi-config
# → Interface Options → SPI → Enable
\`\`\`

#### Generate Encryption Key
\`\`\`bash
python3 tools/setup_wizard.py
\`\`\`

#### Configure Device
\`\`\`bash
# Edit configuration
nano config/production.json

# Test configuration
python3 -c "from src.core.config import ConfigManager; ConfigManager('config/production.json')"
\`\`\`

## 🔐 Security Setup

### Keyfile Generation
The system uses AES-256-CBC encryption with a 32-byte keyfile:

\`\`\`bash
# Generate new keyfile
python3 -c "import secrets; open('keyfile.bin', 'wb').write(secrets.token_bytes(32))"

# Set secure permissions
chmod 600 keyfile.bin

# Verify keyfile
python3 -c "
key = open('keyfile.bin', 'rb').read()
print(f'Key length: {len(key)} bytes')
print(f'Key (hex): {key.hex()[:16]}...')
"
\`\`\`

### Device ID Generation
Device IDs are generated from MAC address:
\`\`\`bash
# Check device ID
python3 -c "
from src.core.device_id import DeviceIDManager
print(f'Device ID: {DeviceIDManager.generate_mac_based_id(\"node_\")}')"
\`\`\`

## 🎮 Usage

### Basic Operation
\`\`\`bash
# Normal mode (with LoRa hardware)
python3 main.py

# Mock mode (without hardware)
python3 main.py mockup

# Custom configuration
python3 main.py --config config/custom.json

# Debug mode
python3 main.py --debug
\`\`\`

### Service Mode
\`\`\`bash
# Install as system service
sudo python3 tools/setup_wizard.py

# Control service
sudo systemctl start lora-sensor-node
sudo systemctl stop lora-sensor-node
sudo systemctl status lora-sensor-node

# View logs
journalctl -u lora-sensor-node -f
\`\`\`

## 🔧 Configuration

### Main Configuration (`config/production.json`)
\`\`\`json
{
  "device": {
    "id": "node_ABC123",
    "id_prefix": "node_",
    "name": "LoRa Sensor Node"
  },
  "lora": {
    "frequency": 915.0,
    "tx_power": 14,
    "spreading_factor": 7,
    "bandwidth": 125000,
    "coding_rate": 5,
    "preamble_length": 8
  },
  "sensors": {
    "enabled": ["temperature", "humidity", "ph"],
    "interval": 30,
    "mock_data": {
      "temperature": 25.0,
      "humidity": 60.0,
      "ph": 7.0
    }
  },
  "encryption": {
    "enabled": true,
    "keyfile": "keyfile.bin"
  }
}
\`\`\`

### Environment Variables
\`\`\`bash
# Override configuration with environment variables
export LORA_FREQUENCY=868.0
export SENSOR_INTERVAL=60
export LOG_LEVEL=DEBUG
\`\`\`

## 🧪 Testing

### Run Unit Tests
\`\`\`bash
# Install test dependencies
pip3 install pytest pytest-cov

# Run all tests
python3 -m pytest tests/

# Run with coverage
python3 -m pytest tests/ --cov=src --cov-report=html

# Run specific test
python3 -m pytest tests/test_encryption.py -v
\`\`\`

### Hardware Testing
\`\`\`bash
# Run diagnostics
python3 tools/diagnostics.py

# Test LoRa communication
python3 test_hardware.py

# Check connections
python3 verify_connections.py
\`\`\`

## 🔧 Maintenance

### Automated Maintenance
\`\`\`bash
# Run maintenance tasks
python3 tools/maintenance.py

# Schedule maintenance (add to crontab)
0 2 * * 0 /usr/bin/python3 /home/pi/raspberry_pi_zero_2w/tools/maintenance.py
\`\`\`

### Manual Maintenance
\`\`\`bash
# View logs
tail -f logs/sensor_node.log

# Check system health
python3 -c "
from src.utils.health import SystemHealthMonitor
monitor = SystemHealthMonitor()
print(monitor.get_system_metrics())
"

# Backup configuration
cp -r config/ backups/config_$(date +%Y%m%d_%H%M%S)/
cp keyfile.bin backups/
\`\`\`

## 📊 Monitoring

### System Health
The system continuously monitors:
- **CPU Usage**: Processor utilization
- **Memory Usage**: RAM consumption
- **Disk Space**: Storage utilization
- **Temperature**: CPU temperature
- **Network**: Connectivity status

### Performance Metrics
- **Encryption Speed**: AES encryption/decryption timing
- **LoRa Transmission**: Success/failure rates
- **Sensor Reading**: Data collection timing
- **Buffer Status**: Data queue status

## 🐛 Troubleshooting

### Common Issues

#### SPI Not Working
\`\`\`bash
# Check SPI devices
ls -la /dev/spidev*

# Enable SPI
echo 'dtparam=spi=on' | sudo tee -a /boot/config.txt
sudo reboot

# Check user permissions
sudo usermod -a -G spi,gpio $USER
\`\`\`

#### LoRa Communication Failed
\`\`\`bash
# Run diagnostics
python3 tools/diagnostics.py

# Check connections
python3 verify_connections.py

# Test with different HAT
python3 check_hat_compatibility.py
\`\`\`

#### Encryption Errors
\`\`\`bash
# Verify keyfile
ls -la keyfile.bin
python3 -c "print(len(open('keyfile.bin', 'rb').read()))"

# Regenerate keyfile
python3 tools/setup_wizard.py
\`\`\`

### Debug Mode
\`\`\`bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 main.py

# View detailed logs
tail -f logs/sensor_node.log | grep DEBUG
\`\`\`

## 📚 API Reference

### Core Classes

#### ConfigManager
```python
from src.core.config import ConfigManager

config = ConfigManager('config/production.json')
frequency = config.get('lora.frequency')
config.set('lora.tx_power', 20)
