#!/usr/bin/env python3
"""
HAT Compatibility Checker for Raspberry Pi Zero 2W
Identifies HAT model and verifies compatibility, pinout, and configuration
"""

import os
import sys
import subprocess
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class HATType(Enum):
    """Known HAT types"""
    WAVESHARE_SX1262 = "waveshare_sx1262"
    WAVESHARE_SX1268 = "waveshare_sx1268"
    DRAGINO_LG01N = "dragino_lg01n"
    ADAFRUIT_RFM95W = "adafruit_rfm95w"
    RAK2245 = "rak2245"
    GENERIC_SX126X = "generic_sx126x"
    UNKNOWN = "unknown"

@dataclass
class PinConfiguration:
    """HAT pin configuration"""
    reset_pin: int
    busy_pin: int
    dio1_pin: int
    dio2_pin: Optional[int] = None
    dio3_pin: Optional[int] = None
    spi_bus: int = 0
    spi_device: int = 0
    power_pin: Optional[int] = None
    led_pin: Optional[int] = None

@dataclass
class HATInfo:
    """Complete HAT information"""
    hat_type: HATType
    name: str
    manufacturer: str
    chip_model: str
    pin_config: PinConfiguration
    frequency_bands: List[str]
    max_power: int
    compatible_with_zero2w: bool
    notes: str
    documentation_url: Optional[str] = None

# Known HAT configurations
KNOWN_HATS = {
    HATType.WAVESHARE_SX1262: HATInfo(
        hat_type=HATType.WAVESHARE_SX1262,
        name="Waveshare SX1262 LoRa HAT",
        manufacturer="Waveshare",
        chip_model="SX1262",
        pin_config=PinConfiguration(
            reset_pin=22,
            busy_pin=23,
            dio1_pin=24,
            dio2_pin=25,
            spi_bus=0,
            spi_device=0
        ),
        frequency_bands=["433MHz", "470MHz", "868MHz", "915MHz"],
        max_power=22,
        compatible_with_zero2w=True,
        notes="Standard Waveshare HAT with good Pi Zero 2W compatibility",
        documentation_url="https://www.waveshare.com/wiki/SX1262_LoRa_HAT"
    ),
    
    HATType.WAVESHARE_SX1268: HATInfo(
        hat_type=HATType.WAVESHARE_SX1268,
        name="Waveshare SX1268 LoRa HAT",
        manufacturer="Waveshare",
        chip_model="SX1268",
        pin_config=PinConfiguration(
            reset_pin=22,
            busy_pin=23,
            dio1_pin=24,
            spi_bus=0,
            spi_device=0,
            led_pin=18
        ),
        frequency_bands=["433MHz", "470MHz", "868MHz", "915MHz"],
        max_power=22,
        compatible_with_zero2w=True,
        notes="Newer Waveshare model with LED indicator",
        documentation_url="https://www.waveshare.com/wiki/SX1268_LoRa_HAT"
    ),
    
    HATType.DRAGINO_LG01N: HATInfo(
        hat_type=HATType.DRAGINO_LG01N,
        name="Dragino LG01-N LoRa Gateway HAT",
        manufacturer="Dragino",
        chip_model="SX1276/SX1278",
        pin_config=PinConfiguration(
            reset_pin=22,
            busy_pin=23,
            dio1_pin=24,
            dio2_pin=25,
            spi_bus=0,
            spi_device=0
        ),
        frequency_bands=["433MHz", "868MHz", "915MHz"],
        max_power=20,
        compatible_with_zero2w=False,
        notes="WARNING: Uses SX127x chip, not SX126x. Requires different driver!",
        documentation_url="https://wiki.dragino.com/index.php?title=LG01-N"
    ),
    
    HATType.ADAFRUIT_RFM95W: HATInfo(
        hat_type=HATType.ADAFRUIT_RFM95W,
        name="Adafruit RFM95W LoRa Radio Bonnet",
        manufacturer="Adafruit",
        chip_model="RFM95W (SX1276)",
        pin_config=PinConfiguration(
            reset_pin=25,
            busy_pin=None,  # RFM95W doesn't have BUSY pin
            dio1_pin=22,
            dio2_pin=23,
            dio3_pin=24,
            spi_bus=0,
            spi_device=0
        ),
        frequency_bands=["433MHz", "868MHz", "915MHz"],
        max_power=20,
        compatible_with_zero2w=False,
        notes="WARNING: Uses RFM95W (SX1276), not SX126x. Different pinout and driver needed!",
        documentation_url="https://learn.adafruit.com/adafruit-radio-bonnets"
    ),
    
    HATType.RAK2245: HATInfo(
        hat_type=HATType.RAK2245,
        name="RAK2245 Pi HAT",
        manufacturer="RAKwireless",
        chip_model="SX1301 + SX1257",
        pin_config=PinConfiguration(
            reset_pin=17,
            busy_pin=None,
            dio1_pin=None,
            spi_bus=0,
            spi_device=0,
            power_pin=18
        ),
        frequency_bands=["433MHz", "470MHz", "868MHz", "915MHz"],
        max_power=27,
        compatible_with_zero2w=False,
        notes="WARNING: LoRaWAN concentrator HAT, not point-to-point LoRa. Uses SX1301, not SX126x!",
        documentation_url="https://docs.rakwireless.com/Product-Categories/WisLink/RAK2245-Pi-HAT/"
    )
}

def detect_raspberry_pi_model() -> Tuple[str, str, bool]:
    """Detect Raspberry Pi model and check Zero 2W compatibility"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        # Extract model information
        model_match = re.search(r'Model\s*:\s*(.+)', cpuinfo)
        revision_match = re.search(r'Revision\s*:\s*([a-fA-F0-9]+)', cpuinfo)
        
        model = model_match.group(1).strip() if model_match else "Unknown"
        revision = revision_match.group(1).strip() if revision_match else "Unknown"
        
        # Check if it's a Pi Zero 2W
        is_zero_2w = "Pi Zero 2" in model or revision.lower() in ['902120']
        
        return model, revision, is_zero_2w
        
    except Exception as e:
        return "Unknown", "Unknown", False

def read_hat_eeprom() -> Dict[str, str]:
    """Read HAT EEPROM information"""
    eeprom_info = {}
    
    # Possible EEPROM locations
    eeprom_paths = [
        '/proc/device-tree/hat/',
        '/sys/firmware/devicetree/base/hat/',
        '/proc/device-tree/hat@0/',
    ]
    
    eeprom_fields = [
        'vendor', 'product', 'product_id', 'product_ver', 
        'uuid', 'pid', 'pver', 'name'
    ]
    
    for base_path in eeprom_paths:
        if os.path.exists(base_path):
            for field in eeprom_fields:
                field_path = os.path.join(base_path, field)
                if os.path.exists(field_path):
                    try:
                        with open(field_path, 'rb') as f:
                            value = f.read().decode('utf-8', errors='ignore').strip('\x00')
                            if value:
                                eeprom_info[field] = value
                    except:
                        continue
            break
    
    return eeprom_info

def detect_hat_from_eeprom(eeprom_info: Dict[str, str]) -> Optional[HATType]:
    """Detect HAT type from EEPROM information"""
    if not eeprom_info:
        return None
    
    vendor = eeprom_info.get('vendor', '').lower()
    product = eeprom_info.get('product', '').lower()
    name = eeprom_info.get('name', '').lower()
    
    # Match against known patterns
    if 'waveshare' in vendor:
        if 'sx1262' in product or 'sx1262' in name:
            return HATType.WAVESHARE_SX1262
        elif 'sx1268' in product or 'sx1268' in name:
            return HATType.WAVESHARE_SX1268
    
    elif 'dragino' in vendor:
        if 'lg01' in product or 'lg01' in name:
            return HATType.DRAGINO_LG01N
    
    elif 'adafruit' in vendor:
        if 'rfm95' in product or 'lora' in product:
            return HATType.ADAFRUIT_RFM95W
    
    elif 'rak' in vendor or 'rakwireless' in vendor:
        if '2245' in product or '2245' in name:
            return HATType.RAK2245
    
    return None

def detect_hat_from_gpio_usage() -> Optional[HATType]:
    """Try to detect HAT type from GPIO pin usage patterns"""
    try:
        # Check which GPIO pins are being used
        gpio_path = '/sys/class/gpio'
        if not os.path.exists(gpio_path):
            return None
        
        exported_pins = []
        for item in os.listdir(gpio_path):
            if item.startswith('gpio'):
                try:
                    pin_num = int(item[4:])
                    exported_pins.append(pin_num)
                except:
                    continue
        
        # Match against known pin patterns
        for hat_type, hat_info in KNOWN_HATS.items():
            config = hat_info.pin_config
            required_pins = [config.reset_pin, config.dio1_pin]
            if config.busy_pin:
                required_pins.append(config.busy_pin)
            
            if all(pin in exported_pins for pin in required_pins):
                return hat_type
        
        return None
        
    except Exception:
        return None

def test_spi_device_response() -> Dict[str, any]:
    """Test SPI device to identify chip type"""
    try:
        import spidev
        import RPi.GPIO as GPIO
        
        # Try to communicate with potential SX126x chip
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 100000
        spi.mode = 0
        
        # Test different reset pin configurations
        test_configs = [
            {'reset': 22, 'busy': 23},  # Waveshare standard
            {'reset': 25, 'busy': None},  # Adafruit RFM95W
            {'reset': 17, 'busy': None},  # RAK2245
        ]
        
        results = {}
        
        GPIO.setmode(GPIO.BCM)
        
        for i, config in enumerate(test_configs):
            try:
                reset_pin = config['reset']
                busy_pin = config['busy']
                
                # Setup pins
                GPIO.setup(reset_pin, GPIO.OUT)
                if busy_pin:
                    GPIO.setup(busy_pin, GPIO.IN)
                
                # Reset sequence
                GPIO.output(reset_pin, GPIO.LOW)
                time.sleep(0.002)
                GPIO.output(reset_pin, GPIO.HIGH)
                time.sleep(0.010)
                
                # Wait for BUSY if available
                if busy_pin:
                    start_time = time.time()
                    while GPIO.input(busy_pin) and (time.time() - start_time) < 0.1:
                        time.sleep(0.001)
                
                # Try to get status
                response = spi.xfer2([0xC0, 0x00])  # GET_STATUS command
                
                results[f'config_{i}'] = {
                    'reset_pin': reset_pin,
                    'busy_pin': busy_pin,
                    'response': response,
                    'success': response[0] != 0x00 or response[1] != 0x00
                }
                
            except Exception as e:
                results[f'config_{i}'] = {
                    'reset_pin': reset_pin,
                    'busy_pin': busy_pin,
                    'error': str(e),
                    'success': False
                }
        
        spi.close()
        GPIO.cleanup()
        
        return results
        
    except ImportError:
        return {'error': 'Required libraries not available'}
    except Exception as e:
        return {'error': str(e)}

def check_power_requirements(hat_info: HATInfo, pi_model: str) -> Dict[str, any]:
    """Check if Pi can provide adequate power for the HAT"""
    # Pi Zero 2W power specifications
    pi_zero_2w_specs = {
        'max_current_3v3': 500,  # mA
        'max_current_5v': 1200,  # mA (from GPIO pins)
        'recommended_psu': 2500,  # mA total
    }
    
    # Estimated power consumption for different HATs
    hat_power_consumption = {
        HATType.WAVESHARE_SX1262: {'idle': 50, 'tx_max': 120, 'voltage': 3.3},
        HATType.WAVESHARE_SX1268: {'idle': 50, 'tx_max': 120, 'voltage': 3.3},
        HATType.DRAGINO_LG01N: {'idle': 100, 'tx_max': 200, 'voltage': 3.3},
        HATType.ADAFRUIT_RFM95W: {'idle': 30, 'tx_max': 120, 'voltage': 3.3},
        HATType.RAK2245: {'idle': 300, 'tx_max': 500, 'voltage': 5.0},
    }
    
    power_info = hat_power_consumption.get(hat_info.hat_type, {'idle': 100, 'tx_max': 200, 'voltage': 3.3})
    
    # Check compatibility
    is_zero_2w = "Zero 2" in pi_model
    power_adequate = True
    warnings = []
    
    if power_info['voltage'] == 3.3:
        if power_info['tx_max'] > pi_zero_2w_specs['max_current_3v3']:
            power_adequate = False
            warnings.append(f"HAT requires {power_info['tx_max']}mA at 3.3V, Pi Zero 2W can provide max {pi_zero_2w_specs['max_current_3v3']}mA")
    
    if power_info['tx_max'] > 300 and is_zero_2w:
        warnings.append("High power consumption HAT - ensure adequate power supply (5V 3A recommended)")
    
    return {
        'adequate': power_adequate,
        'warnings': warnings,
        'hat_consumption': power_info,
        'pi_specs': pi_zero_2w_specs if is_zero_2w else None
    }

def check_pin_conflicts(hat_info: HATInfo) -> Dict[str, any]:
    """Check for potential GPIO pin conflicts"""
    # Pi Zero 2W reserved/special pins
    reserved_pins = {
        0: "ID_SD (HAT EEPROM)",
        1: "ID_SC (HAT EEPROM)",
        2: "SDA1 (I2C)",
        3: "SCL1 (I2C)",
        7: "SPI0_CE1",
        8: "SPI0_CE0",
        9: "SPI0_MISO",
        10: "SPI0_MOSI",
        11: "SPI0_SCLK",
        14: "UART0_TXD",
        15: "UART0_RXD",
    }
    
    # Common pins used by other HATs/devices
    commonly_used_pins = {
        4: "1-Wire, often used for temperature sensors",
        17: "Often used for status LEDs",
        18: "PWM0, often used for audio/servos",
        19: "SPI1_MOSI",
        20: "SPI1_MISO",
        21: "SPI1_SCLK",
        27: "Often used for camera/display",
    }
    
    config = hat_info.pin_config
    used_pins = [config.reset_pin, config.dio1_pin]
    if config.busy_pin:
        used_pins.append(config.busy_pin)
    if config.dio2_pin:
        used_pins.append(config.dio2_pin)
    if config.dio3_pin:
        used_pins.append(config.dio3_pin)
    if config.power_pin:
        used_pins.append(config.power_pin)
    if config.led_pin:
        used_pins.append(config.led_pin)
    
    conflicts = []
    warnings = []
    
    for pin in used_pins:
        if pin in reserved_pins:
            conflicts.append(f"GPIO {pin}: {reserved_pins[pin]} - CRITICAL CONFLICT!")
        elif pin in commonly_used_pins:
            warnings.append(f"GPIO {pin}: {commonly_used_pins[pin]} - potential conflict")
    
    return {
        'conflicts': conflicts,
        'warnings': warnings,
        'used_pins': used_pins,
        'safe': len(conflicts) == 0
    }

def generate_config_file(hat_info: HATInfo) -> str:
    """Generate appropriate config.json for detected HAT"""
    config = hat_info.pin_config
    
    # Determine appropriate frequency for region
    # Default to 915MHz for US, but include common alternatives
    frequency = 915.0
    if "868MHz" in hat_info.frequency_bands:
        frequency = 868.0  # EU default
    
    config_template = f'''{{
  "lora": {{
    "frequency": {frequency},
    "spreading_factor": 7,
    "bandwidth": 125,
    "coding_rate": 5,
    "tx_power": {min(14, hat_info.max_power)},
    "preamble_length": 8,
    "sync_word": 5140,
    "crc_enabled": true,
    "header_type": 0,
    "tx_timeout": 5000,
    "rx_timeout": 30000
  }},
  "gpio": {{
    "reset_pin": {config.reset_pin},
    "busy_pin": {config.busy_pin if config.busy_pin else 'null'},
    "dio1_pin": {config.dio1_pin},
    "spi_bus": {config.spi_bus},
    "spi_device": {config.spi_device}
  }},
  "sensor": {{
    "dht22_enabled": false,
    "dht22_pin": 4,
    "bmp280_enabled": false,
    "bmp280_address": 118,
    "read_interval": 30.0,
    "mock_enabled": false
  }},
  "device": {{
    "device_id": "HAT_{hat_info.hat_type.value.upper()}_001",
    "device_name": "{hat_info.name}",
    "location": "Unknown",
    "battery_monitoring": false,
    "battery_pin": 26
  }},
  "network": {{
    "uart_enabled": true,
    "uart_port": "/dev/ttyUSB0",
    "uart_baudrate": 9600,
    "encryption_enabled": false,
    "encryption_method": "AES",
    "encryption_key": "MySecretKey123456",
    "network_id": 1,
    "node_address": 1
  }},
  "logging": {{
    "log_level": "INFO",
    "log_file": "lora_node.log",
    "max_log_size": 10,
    "backup_count": 5
  }}
}}'''
    
    return config_template

def main():
    """Main compatibility checker"""
    print("🎩 HAT Compatibility Checker for Raspberry Pi Zero 2W")
    print("=" * 60)
    print()
    
    # Detect Pi model
    pi_model, pi_revision, is_zero_2w = detect_raspberry_pi_model()
    print(f"📱 Detected Raspberry Pi: {pi_model}")
    print(f"📋 Revision: {pi_revision}")
    print(f"🎯 Pi Zero 2W: {'✅ Yes' if is_zero_2w else '❌ No'}")
    print()
    
    if not is_zero_2w:
        print("⚠️  WARNING: This tool is designed for Pi Zero 2W compatibility")
        print("   Results may not be accurate for other Pi models")
        print()
    
    # Read HAT EEPROM
    print("🔍 Reading HAT EEPROM...")
    eeprom_info = read_hat_eeprom()
    
    if eeprom_info:
        print("✅ HAT EEPROM found:")
        for key, value in eeprom_info.items():
            print(f"   {key}: {value}")
    else:
        print("⚠️  No HAT EEPROM detected")
        print("   This is normal for some HATs")
    print()
    
    # Detect HAT type
    print("🔍 Detecting HAT type...")
    detected_hat = detect_hat_from_eeprom(eeprom_info)
    
    if not detected_hat:
        print("⚠️  Could not identify HAT from EEPROM")
        print("   Trying GPIO pattern detection...")
        detected_hat = detect_hat_from_gpio_usage()
    
    if not detected_hat:
        print("⚠️  Could not auto-detect HAT type")
        print("   Assuming generic SX126x HAT")
        detected_hat = HATType.GENERIC_SX126X
        
        # Add generic SX126x configuration
        KNOWN_HATS[HATType.GENERIC_SX126X] = HATInfo(
            hat_type=HATType.GENERIC_SX126X,
            name="Generic SX126x LoRa HAT",
            manufacturer="Unknown",
            chip_model="SX126x",
            pin_config=PinConfiguration(
                reset_pin=22,
                busy_pin=23,
                dio1_pin=24,
                spi_bus=0,
                spi_device=0
            ),
            frequency_bands=["433MHz", "868MHz", "915MHz"],
            max_power=22,
            compatible_with_zero2w=True,
            notes="Generic configuration - verify pinout with HAT documentation"
        )
    
    hat_info = KNOWN_HATS[detected_hat]
    print(f"🎩 Detected HAT: {hat_info.name}")
    print(f"🏭 Manufacturer: {hat_info.manufacturer}")
    print(f"🔧 Chip: {hat_info.chip_model}")
    print()
    
    # Compatibility check
    print("🔍 Compatibility Analysis:")
    print("=" * 30)
    
    # Basic compatibility
    if hat_info.compatible_with_zero2w:
        print("✅ HAT is compatible with Pi Zero 2W")
    else:
        print("❌ HAT has known compatibility issues with Pi Zero 2W")
        print(f"   Issue: {hat_info.notes}")
    
    # Power requirements
    power_check = check_power_requirements(hat_info, pi_model)
    if power_check['adequate']:
        print("✅ Power requirements are adequate")
    else:
        print("⚠️  Power requirements may be marginal")
        for warning in power_check['warnings']:
            print(f"   • {warning}")
    
    # Pin conflicts
    pin_check = check_pin_conflicts(hat_info)
    if pin_check['safe']:
        print("✅ No critical GPIO pin conflicts detected")
    else:
        print("❌ GPIO pin conflicts detected:")
        for conflict in pin_check['conflicts']:
            print(f"   • {conflict}")
    
    if pin_check['warnings']:
        print("⚠️  Potential GPIO conflicts:")
        for warning in pin_check['warnings']:
            print(f"   • {warning}")
    
    print()
    
    # Configuration details
    print("📋 HAT Configuration Details:")
    print("=" * 35)
    config = hat_info.pin_config
    print(f"RESET Pin: GPIO {config.reset_pin}")
    print(f"BUSY Pin: GPIO {config.busy_pin if config.busy_pin else 'Not used'}")
    print(f"DIO1 Pin: GPIO {config.dio1_pin}")
    if config.dio2_pin:
        print(f"DIO2 Pin: GPIO {config.dio2_pin}")
    if config.dio3_pin:
        print(f"DIO3 Pin: GPIO {config.dio3_pin}")
    print(f"SPI Bus: {config.spi_bus}")
    print(f"SPI Device: {config.spi_device}")
    print(f"Frequency Bands: {', '.join(hat_info.frequency_bands)}")
    print(f"Max TX Power: {hat_info.max_power} dBm")
    print()
    
    # Test SPI communication
    print("🔍 Testing SPI Communication...")
    import time
    spi_test = test_spi_device_response()
    
    if 'error' in spi_test:
        print(f"❌ SPI test failed: {spi_test['error']}")
    else:
        working_configs = [k for k, v in spi_test.items() if v.get('success', False)]
        if working_configs:
            print("✅ SPI communication working with detected configuration")
        else:
            print("⚠️  No SPI response detected - check connections")
    print()
    
    # Recommendations
    print("💡 Recommendations:")
    print("=" * 20)
    
    if hat_info.compatible_with_zero2w and pin_check['safe'] and power_check['adequate']:
        print("✅ This HAT should work well with your Pi Zero 2W")
        print("   Recommended actions:")
        print("   1. Use the generated config file below")
        print("   2. Ensure SPI is enabled: sudo raspi-config")
        print("   3. Connect appropriate antenna for your frequency")
        print("   4. Run hardware test: python3 test_hardware.py")
    else:
        print("⚠️  This HAT may have compatibility issues")
        print("   Recommended actions:")
        print("   1. Check HAT documentation for Pi Zero 2W compatibility")
        print("   2. Verify pin connections match HAT specifications")
        print("   3. Consider using a different HAT if issues persist")
        
        if not hat_info.compatible_with_zero2w:
            print("   4. ⚠️  CRITICAL: This HAT may use different chip/protocol!")
            print("      Check if you need different driver software")
    
    if hat_info.documentation_url:
        print(f"   📚 Documentation: {hat_info.documentation_url}")
    
    print()
    
    # Generate config file
    print("📝 Generated Configuration File:")
    print("=" * 35)
    config_content = generate_config_file(hat_info)
    print(config_content)
    
    # Offer to save config
    print("\n" + "="*60)
    save_config = input("Save this configuration to config.json? (y/N): ")
    
    if save_config.lower().startswith('y'):
        try:
            with open('config.json', 'w') as f:
                f.write(config_content)
            print("✅ Configuration saved to config.json")
        except Exception as e:
            print(f"❌ Failed to save config: {e}")
    
    # Final summary
    print(f"\n🎯 COMPATIBILITY SUMMARY:")
    print(f"HAT: {hat_info.name}")
    print(f"Pi Zero 2W Compatible: {'✅ Yes' if hat_info.compatible_with_zero2w else '❌ No'}")
    print(f"Power Adequate: {'✅ Yes' if power_check['adequate'] else '⚠️  Marginal'}")
    print(f"Pin Conflicts: {'✅ None' if pin_check['safe'] else '❌ Yes'}")
    
    if hat_info.compatible_with_zero2w and pin_check['safe'] and power_check['adequate']:
        return 0  # Success
    elif hat_info.compatible_with_zero2w:
        return 1  # Minor issues
    else:
        return 2  # Major compatibility issues

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Compatibility check interrupted by user")
        sys.exit(130)
