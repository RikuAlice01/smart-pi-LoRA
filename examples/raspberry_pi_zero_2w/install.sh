#!/bin/bash
# Installation script for Raspberry Pi Zero 2W LoRa SX126x HAT

echo "LoRa SX126x HAT Installation Script"
echo "==================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root"
    exit 1
fi

# Update system
echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-dev python3-venv git

# Enable SPI
echo "Enabling SPI interface..."
sudo raspi-config nonint do_spi 0

# Enable I2C (for BMP280 sensor)
echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv lora_env
source lora_env/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/lora-node.service > /dev/null <<EOF
[Unit]
Description=LoRa SX126x Sensor Node
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/lora-node
Environment=PATH=/home/pi/lora-node/lora_env/bin
ExecStart=/home/pi/lora-node/lora_env/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
echo "Setting permissions..."
sudo chmod 644 /etc/systemd/system/lora-node.service
sudo systemctl daemon-reload

# Add user to required groups
echo "Adding user to required groups..."
sudo usermod -a -G spi,i2c,gpio pi

echo ""
echo "Installation completed!"
echo ""
echo "Next steps:"
echo "1. Reboot the system: sudo reboot"
echo "2. Test the installation: python3 main.py"
echo "3. Enable auto-start: sudo systemctl enable lora-node"
echo "4. Start the service: sudo systemctl start lora-node"
echo "5. Check status: sudo systemctl status lora-node"
echo ""
echo "Configuration file: config.json"
echo "Log file: lora_node.log"
