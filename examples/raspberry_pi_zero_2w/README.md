# Raspberry Pi Zero 2W LoRa SX126x HAT Example

This directory contains example code for using a Raspberry Pi Zero 2W with a LoRa SX126x HAT over SPI connection.

## Hardware Setup

### Required Components
- Raspberry Pi Zero 2W
- LoRa SX126x HAT (e.g., Waveshare SX1262 LoRa HAT)
- MicroSD card (16GB+ recommended)
- Power supply (5V 2.5A recommended)

### Pin Connections
The SX126x HAT typically uses the following GPIO pins:
- **SPI0 MOSI**: GPIO 10 (Pin 19)
- **SPI0 MISO**: GPIO 9 (Pin 21)
- **SPI0 SCLK**: GPIO 11 (Pin 23)
- **SPI0 CE0**: GPIO 8 (Pin 24) - Chip Select
- **RESET**: GPIO 22 (Pin 15)
- **BUSY**: GPIO 23 (Pin 16)
- **DIO1**: GPIO 24 (Pin 18)
- **3.3V**: Pin 1 or 17
- **GND**: Pin 6, 9, 14, 20, 25, 30, 34, or 39

## Software Setup

### 1. Enable SPI
```bash
sudo raspi-config
# Navigate to Interfacing Options > SPI > Enable
