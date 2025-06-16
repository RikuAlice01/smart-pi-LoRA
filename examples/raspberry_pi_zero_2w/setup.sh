#!/bin/bash

# Enhanced setup script for LoRa SX126x Sensor Node
# Raspberry Pi Zero 2W Setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
        exit 1
    fi
}

# Check system requirements
check_system() {
    log "Checking system requirements..."
    
    # Check OS
    if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        warn "This script is designed for Raspberry Pi"
    fi
    
    # Check Python version
    if ! python3 --version | grep -q "Python 3.[8-9]\|Python 3.1[0-9]"; then
        error "Python 3.8+ is required"
        exit 1
    fi
    
    # Check available space
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # 1GB in KB
        warn "Less than 1GB free space available"
    fi
    
    log "System requirements check passed"
}

# Enable SPI interface
enable_spi() {
    log "Enabling SPI interface..."
    
    # Check if SPI is already enabled
    if lsmod | grep -q spi_bcm2835; then
        info "SPI interface already enabled"
        return
    fi
    
    # Enable SPI via raspi-config
    sudo raspi-config nonint do_spi 0
    
    # Add to /boot/config.txt if not present
    if ! grep -q "dtparam=spi=on" /boot/config.txt; then
        echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
    fi
    
    log "SPI interface enabled (reboot required)"
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        git \
        i2c-tools \
        python3-smbus \
        libgpiod2 \
        python3-libgpiod \
        htop \
        screen \
        vim \
        curl \
        wget
    
    log "System dependencies installed"
}

# Create virtual environment
create_venv() {
    log "Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        warn "Virtual environment already exists"
        return
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    log "Virtual environment created"
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    
    source venv/bin/activate
    
    # Install from requirements.txt
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # Install essential packages
        pip install \
            cryptography \
            psutil \
            jsonschema \
            adafruit-circuitpython-dht \
            adafruit-circuitpython-bmp280 \
            RPi.GPIO \
            spidev
    fi
    
    log "Python dependencies installed"
}

# Setup GPIO permissions
setup_gpio_permissions() {
    log "Setting up GPIO permissions..."
    
    # Add user to gpio and spi groups
    sudo usermod -a -G gpio,spi,i2c "$USER"
    
    # Create udev rules for GPIO access
    sudo tee /etc/udev/rules.d/99-gpio.rules > /dev/null << EOF
KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"
SUBSYSTEM=="spi", GROUP="spi", MODE="0660"
EOF
    
    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    log "GPIO permissions configured"
}

# Create directory structure
create_directories() {
    log "Creating directory structure..."
    
    mkdir -p {data,logs,config,backup,temp}
    mkdir -p src/{core,hardware,communication,data,utils}
    mkdir -p tests
    mkdir -p tools
    mkdir -p docs
    
    log "Directory structure created"
}

# Generate configuration files
generate_config() {
    log "Generating configuration files..."
    
    # Copy default config if it doesn't exist
    if [ ! -f "config.json" ] && [ -f "config/default.json" ]; then
        cp config/default.json config.json
        info "Default configuration copied to config.json"
    fi
    
    # Generate keyfile if it doesn't exist
    if [ ! -f "keyfile.bin" ]; then
        python3 -c "
import secrets
with open('keyfile.bin', 'wb') as f:
    f.write(secrets.token_bytes(32))
print('Generated keyfile.bin')
"
        chmod 600 keyfile.bin
        info "Generated keyfile.bin"
    fi
    
    log "Configuration files ready"
}

# Create systemd service
create_service() {
    log "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/lora-sensor-node.service"
    WORK_DIR=$(pwd)
    
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=LoRa SX126x Sensor Node
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
ExecStart=$WORK_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    log "Systemd service created"
    info "To enable auto-start: sudo systemctl enable lora-sensor-node"
    info "To start service: sudo systemctl start lora-sensor-node"
}

# Run hardware tests
run_tests() {
    log "Running hardware tests..."
    
    source venv/bin/activate
    
    # Test SPI devices
    if [ -e "/dev/spidev0.0" ]; then
        info "SPI device /dev/spidev0.0 found"
    else
        warn "SPI device /dev/spidev0.0 not found"
    fi
    
    # Test I2C devices
    if command -v i2cdetect &> /dev/null; then
        info "Scanning I2C devices..."
        i2cdetect -y 1 || true
    fi
    
    # Test Python imports
    python3 -c "
try:
    import RPi.GPIO
    import spidev
    import cryptography
    print('✅ Essential Python modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
"
    
    log "Hardware tests completed"
}

# Main setup function
main() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "  LoRa SX126x Sensor Node Setup Script v2.0.0"
    echo "=================================================="
    echo -e "${NC}"
    
    check_root
    check_system
    
    log "Starting setup process..."
    
    enable_spi
    install_system_deps
    create_venv
    install_python_deps
    setup_gpio_permissions
    create_directories
    generate_config
    create_service
    run_tests
    
    echo -e "${GREEN}"
    echo "=================================================="
    echo "  Setup completed successfully!"
    echo "=================================================="
    echo -e "${NC}"
    
    info "Next steps:"
    echo "  1. Reboot your Raspberry Pi: sudo reboot"
    echo "  2. Test the installation: python3 main.py --mock"
    echo "  3. Configure your settings in config.json"
    echo "  4. Connect your LoRa hardware"
    echo "  5. Run: python3 main.py"
    
    warn "A reboot is required for SPI changes to take effect"
}

# Run main function
main "$@"
