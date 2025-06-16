#!/bin/bash
# Quick setup script for Raspberry Pi Zero 2W LoRa SX126x HAT

echo "🚀 Quick Setup for LoRa SX126x HAT"
echo "=================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please do not run this script as root"
    echo "   Run as regular user (pi), it will ask for sudo when needed"
    exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📋 Checking current setup..."

# Check if SPI is enabled
if [ ! -e /dev/spidev0.0 ]; then
    echo "🔧 Enabling SPI interface..."
    sudo raspi-config nonint do_spi 0
    SPI_ENABLED=1
else
    echo "✅ SPI already enabled"
    SPI_ENABLED=0
fi

# Check if I2C is enabled
if [ ! -e /dev/i2c-1 ]; then
    echo "🔧 Enabling I2C interface..."
    sudo raspi-config nonint do_i2c 0
    I2C_ENABLED=1
else
    echo "✅ I2C already enabled"
    I2C_ENABLED=0
fi

# Check user groups
echo "👤 Checking user groups..."
CURRENT_USER=$(whoami)
GROUPS_TO_ADD=""

if ! groups $CURRENT_USER | grep -q "spi"; then
    GROUPS_TO_ADD="$GROUPS_TO_ADD spi"
fi

if ! groups $CURRENT_USER | grep -q "i2c"; then
    GROUPS_TO_ADD="$GROUPS_TO_ADD i2c"
fi

if ! groups $CURRENT_USER | grep -q "gpio"; then
    GROUPS_TO_ADD="$GROUPS_TO_ADD gpio"
fi

if [ -n "$GROUPS_TO_ADD" ]; then
    echo "🔧 Adding user to groups:$GROUPS_TO_ADD"
    for group in $GROUPS_TO_ADD; do
        sudo usermod -a -G $group $CURRENT_USER
    done
    GROUPS_CHANGED=1
else
    echo "✅ User already in required groups"
    GROUPS_CHANGED=0
fi

# Install Python packages
echo "📦 Installing Python packages..."

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "🔧 Installing pip..."
    sudo apt update
    sudo apt install -y python3-pip
fi

# Install basic requirements
echo "📦 Installing basic requirements..."
pip3 install --user spidev RPi.GPIO pyserial

# Try to install optional sensor libraries
echo "📦 Installing optional sensor libraries..."
pip3 install --user Adafruit-DHT || echo "⚠️  Could not install Adafruit-DHT"

# Try to install CircuitPython libraries
pip3 install --user adafruit-blinka adafruit-circuitpython-bmp280 || echo "⚠️  Could not install CircuitPython libraries"

# Install encryption support
pip3 install --user cryptography || echo "⚠️  Could not install cryptography"

# Create default config if it doesn't exist
if [ ! -f config.json ]; then
    echo "📝 Creating default configuration..."
    python3 -c "
from config import create_default_config
config = create_default_config('config.json')
print('✅ Default config.json created')
" 2>/dev/null || echo "⚠️  Could not create config.json (will be created on first run)"
fi

# Create mockup config
if [ ! -f mockup_config.json ]; then
    echo "📝 Creating mockup configuration..."
    cat > mockup_config.json << 'EOF'
{
  "lora": {
    "frequency": 915.0,
    "spreading_factor": 7,
    "bandwidth": 125,
    "coding_rate": 5,
    "tx_power": 14,
    "preamble_length": 8,
    "sync_word": 5140,
    "crc_enabled": true,
    "header_type": 0,
    "tx_timeout": 5000,
    "rx_timeout": 30000
  },
  "gpio": {
    "reset_pin": 22,
    "busy_pin": 23,
    "dio1_pin": 24,
    "spi_bus": 0,
    "spi_device": 0
  },
  "sensor": {
    "dht22_enabled": false,
    "dht22_pin": 4,
    "bmp280_enabled": false,
    "bmp280_address": 118,
    "read_interval": 5.0,
    "mock_enabled": true
  },
  "device": {
    "device_id": "SETUP_TEST_001",
    "device_name": "Raspberry Pi LoRa Setup Test",
    "location": "Setup Test",
    "battery_monitoring": false,
    "battery_pin": 26
  },
  "network": {
    "uart_enabled": false,
    "uart_port": "/dev/ttyUSB0",
    "uart_baudrate": 9600,
    "encryption_enabled": false,
    "encryption_method": "AES",
    "encryption_key": "SetupTestKey123",
    "network_id": 1,
    "node_address": 1
  },
  "logging": {
    "log_level": "INFO",
    "log_file": "setup_test.log",
    "max_log_size": 10,
    "backup_count": 5
  }
}
EOF
    echo "✅ Mockup config created"
fi

# Summary
echo ""
echo "🎯 Setup Summary"
echo "==============="

REBOOT_NEEDED=0

if [ $SPI_ENABLED -eq 1 ]; then
    echo "✅ SPI interface enabled"
    REBOOT_NEEDED=1
fi

if [ $I2C_ENABLED -eq 1 ]; then
    echo "✅ I2C interface enabled"
    REBOOT_NEEDED=1
fi

if [ $GROUPS_CHANGED -eq 1 ]; then
    echo "✅ User groups updated"
    REBOOT_NEEDED=1
fi

echo "✅ Python packages installed"
echo "✅ Configuration files created"

if [ $REBOOT_NEEDED -eq 1 ]; then
    echo ""
    echo "🔄 REBOOT REQUIRED"
    echo "=================="
    echo "System changes require a reboot to take effect."
    echo ""
    read -p "Reboot now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Rebooting..."
        sudo reboot
    else
        echo "⚠️  Please reboot manually before testing: sudo reboot"
    fi
else
    echo ""
    echo "🎉 Setup completed! No reboot required."
    echo ""
    echo "Next steps:"
    echo "1. Run hardware test: python3 test_hardware.py"
    echo "2. Run setup verification: python3 verify_setup.py"
    echo "3. Test mockup mode: python3 main.py mockup"
fi

echo ""
echo "📚 Quick Commands:"
echo "  python3 verify_setup.py     # Verify setup"
echo "  python3 test_hardware.py    # Test hardware"
echo "  python3 main.py mockup      # Test with mock data"
echo "  python3 main.py test        # Hardware test mode"
