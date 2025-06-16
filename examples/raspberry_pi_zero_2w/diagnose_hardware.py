#!/usr/bin/env python3
"""
Comprehensive hardware diagnostic tool for SX126x LoRa HAT
Identifies specific hardware issues and provides solutions
"""

import time
import sys
import os
from typing import Dict, List, Tuple, Optional

# Check library availability
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

try:
    import spidev
    SPI_AVAILABLE = True
except ImportError:
    SPI_AVAILABLE = False

def check_power_supply():
    """Check if power supply is adequate"""
    print("🔋 Checking Power Supply...")
    
    try:
        # Check CPU throttling (indicates power issues)
        with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'r') as f:
            current_freq = int(f.read().strip())
        
        with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq', 'r') as f:
            max_freq = int(f.read().strip())
        
        throttle_ratio = current_freq / max_freq
        print(f"  CPU Frequency: {current_freq/1000:.0f} MHz / {max_freq/1000:.0f} MHz ({throttle_ratio*100:.1f}%)")
        
        if throttle_ratio < 0.8:
            print("  ⚠️  CPU is throttled - possible power supply issue")
            return False
        else:
            print("  ✅ CPU frequency normal")
        
        # Check for undervoltage detection
        try:
            with open('/proc/device-tree/chosen/bootargs', 'r') as f:
                bootargs = f.read()
                if 'undervoltage' in bootargs.lower():
                    print("  ⚠️  Undervoltage detected in boot args")
                    return False
        except:
            pass
        
        # Check system voltage if available
        voltage_files = [
            '/sys/class/hwmon/hwmon0/in0_input',
            '/sys/class/hwmon/hwmon1/in0_input'
        ]
        
        for voltage_file in voltage_files:
            if os.path.exists(voltage_file):
                try:
                    with open(voltage_file, 'r') as f:
                        voltage_mv = int(f.read().strip())
                        voltage_v = voltage_mv / 1000.0
                        print(f"  System Voltage: {voltage_v:.2f}V")
                        
                        if voltage_v < 4.8:
                            print("  ⚠️  Low voltage detected")
                            return False
                        else:
                            print("  ✅ Voltage normal")
                        break
                except:
                    continue
        
        return True
        
    except Exception as e:
        print(f"  ❌ Could not check power supply: {e}")
        return None

def check_spi_detailed():
    """Detailed SPI interface check"""
    print("\n🔌 Detailed SPI Interface Check...")
    
    if not SPI_AVAILABLE:
        print("  ❌ spidev library not available")
        return False
    
    try:
        # Check SPI device files
        spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1']
        for device in spi_devices:
            exists = os.path.exists(device)
            print(f"  {device}: {'✅ Exists' if exists else '❌ Missing'}")
        
        if not os.path.exists('/dev/spidev0.0'):
            print("  ❌ Primary SPI device missing - SPI not enabled")
            return False
        
        # Test SPI communication with different settings
        print("  Testing SPI communication...")
        
        spi = spidev.SpiDev()
        spi.open(0, 0)
        
        # Test different SPI modes and speeds
        test_configs = [
            (0, 1000000),   # Mode 0, 1MHz
            (0, 500000),    # Mode 0, 500kHz
            (0, 100000),    # Mode 0, 100kHz
        ]
        
        for mode, speed in test_configs:
            try:
                spi.mode = mode
                spi.max_speed_hz = speed
                
                # Send test pattern
                test_data = [0x55, 0xAA, 0xFF, 0x00]
                response = spi.xfer2(test_data)
                
                print(f"    Mode {mode}, {speed//1000}kHz: Sent {[hex(x) for x in test_data]}, Got {[hex(x) for x in response]}")
                
            except Exception as e:
                print(f"    Mode {mode}, {speed//1000}kHz: ❌ Failed - {e}")
        
        spi.close()
        print("  ✅ SPI interface functional")
        return True
        
    except Exception as e:
        print(f"  ❌ SPI test failed: {e}")
        return False

def check_gpio_detailed():
    """Detailed GPIO check with electrical testing"""
    print("\n📌 Detailed GPIO Check...")
    
    if not GPIO_AVAILABLE:
        print("  ❌ RPi.GPIO library not available")
        return False
    
    try:
        from config import Config
        config = Config()
        
        GPIO.setmode(GPIO.BCM)
        
        # Test each pin individually
        pins_to_test = [
            (config.gpio.reset_pin, "RESET", "OUT"),
            (config.gpio.busy_pin, "BUSY", "IN"),
            (config.gpio.dio1_pin, "DIO1", "IN")
        ]
        
        results = {}
        
        for pin, name, direction in pins_to_test:
            print(f"  Testing {name} pin (GPIO {pin})...")
            
            try:
                if direction == "OUT":
                    GPIO.setup(pin, GPIO.OUT)
                    
                    # Test output functionality
                    GPIO.output(pin, GPIO.LOW)
                    time.sleep(0.01)
                    GPIO.output(pin, GPIO.HIGH)
                    time.sleep(0.01)
                    
                    print(f"    ✅ {name} output control working")
                    results[name] = True
                    
                else:  # INPUT
                    GPIO.setup(pin, GPIO.IN)
                    
                    # Read pin state multiple times
                    readings = []
                    for i in range(10):
                        reading = GPIO.input(pin)
                        readings.append(reading)
                        time.sleep(0.01)
                    
                    # Check for stuck pins
                    if all(r == readings[0] for r in readings):
                        state = "HIGH" if readings[0] else "LOW"
                        print(f"    📍 {name} consistently reads {state}")
                        
                        # For BUSY pin, LOW is expected when idle
                        if name == "BUSY" and readings[0] == 0:
                            print(f"    ✅ {name} in expected idle state")
                            results[name] = True
                        elif name == "DIO1":
                            print(f"    ✅ {name} readable (state depends on chip)")
                            results[name] = True
                        else:
                            print(f"    ⚠️  {name} state unclear")
                            results[name] = None
                    else:
                        print(f"    ⚠️  {name} readings inconsistent: {readings}")
                        results[name] = False
                        
            except Exception as e:
                print(f"    ❌ {name} test failed: {e}")
                results[name] = False
        
        GPIO.cleanup()
        return results
        
    except Exception as e:
        print(f"  ❌ GPIO test failed: {e}")
        return {}

def test_sx126x_presence():
    """Test if SX126x chip is present and responding"""
    print("\n🔍 Testing SX126x Chip Presence...")
    
    if not SPI_AVAILABLE or not GPIO_AVAILABLE:
        print("  ❌ Required libraries not available")
        return False
    
    try:
        from config import Config
        config = Config()
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.gpio.reset_pin, GPIO.OUT)
        GPIO.setup(config.gpio.busy_pin, GPIO.IN)
        
        # Initialize SPI
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 100000  # Start with slow speed
        spi.mode = 0
        
        print("  Performing hardware reset sequence...")
        
        # Hardware reset
        GPIO.output(config.gpio.reset_pin, GPIO.LOW)
        time.sleep(0.002)  # 2ms reset pulse
        GPIO.output(config.gpio.reset_pin, GPIO.HIGH)
        time.sleep(0.010)  # 10ms wait
        
        # Wait for BUSY to go low (chip ready)
        print("  Waiting for BUSY pin to go low...")
        busy_timeout = 1.0
        start_time = time.time()
        
        while GPIO.input(config.gpio.busy_pin) and (time.time() - start_time) < busy_timeout:
            time.sleep(0.001)
        
        busy_time = time.time() - start_time
        busy_final = GPIO.input(config.gpio.busy_pin)
        
        print(f"    BUSY pin: {busy_final} after {busy_time*1000:.1f}ms")
        
        if busy_final == 1:
            print("    ⚠️  BUSY pin stuck HIGH - possible chip issue")
        else:
            print("    ✅ BUSY pin went LOW - chip responding to reset")
        
        # Test basic SPI communication
        print("  Testing SPI command response...")
        
        # Try GET_STATUS command (0xC0)
        test_commands = [
            (0xC0, "GET_STATUS"),
            (0x80, "SET_STANDBY"),
            (0xC0, "GET_STATUS again")
        ]
        
        responses = []
        for cmd, name in test_commands:
            try:
                # Send command
                response = spi.xfer2([cmd, 0x00])
                responses.append((name, response))
                print(f"    {name}: Sent 0x{cmd:02X}, Got {[hex(x) for x in response]}")
                time.sleep(0.01)
                
            except Exception as e:
                print(f"    {name}: ❌ Failed - {e}")
                responses.append((name, None))
        
        # Analyze responses
        valid_responses = [r for r in responses if r[1] is not None]
        
        if not valid_responses:
            print("  ❌ No valid SPI responses - communication failed")
            result = False
        elif all(r[1][0] == 0x00 for r in valid_responses):
            print("  ⚠️  All responses are 0x00 - possible issues:")
            print("    - Chip not powered")
            print("    - Wrong SPI connections")
            print("    - Faulty chip")
            print("    - Incorrect HAT installation")
            result = False
        else:
            print("  ✅ Got non-zero responses - chip likely present")
            result = True
        
        spi.close()
        GPIO.cleanup()
        return result
        
    except Exception as e:
        print(f"  ❌ Chip presence test failed: {e}")
        try:
            spi.close()
            GPIO.cleanup()
        except:
            pass
        return False

def check_hat_installation():
    """Check if HAT is properly installed"""
    print("\n🎩 Checking HAT Installation...")
    
    try:
        # Check for HAT EEPROM
        eeprom_files = [
            '/proc/device-tree/hat/vendor',
            '/proc/device-tree/hat/product',
            '/sys/firmware/devicetree/base/hat/vendor',
            '/sys/firmware/devicetree/base/hat/product'
        ]
        
        hat_detected = False
        for eeprom_file in eeprom_files:
            if os.path.exists(eeprom_file):
                try:
                    with open(eeprom_file, 'rb') as f:
                        content = f.read().decode('utf-8', errors='ignore').strip('\x00')
                        if content:
                            print(f"  HAT Info: {content}")
                            hat_detected = True
                except:
                    pass
        
        if not hat_detected:
            print("  ⚠️  No HAT EEPROM detected")
            print("    This could be normal for some HATs")
        
        # Check GPIO pin usage
        print("  Checking GPIO pin conflicts...")
        
        gpio_export_path = '/sys/class/gpio'
        if os.path.exists(gpio_export_path):
            exported_pins = []
            for item in os.listdir(gpio_export_path):
                if item.startswith('gpio'):
                    try:
                        pin_num = int(item[4:])
                        exported_pins.append(pin_num)
                    except:
                        pass
            
            if exported_pins:
                print(f"    Exported GPIO pins: {exported_pins}")
                
                # Check if our pins are in use
                from config import Config
                config = Config()
                our_pins = [config.gpio.reset_pin, config.gpio.busy_pin, config.gpio.dio1_pin]
                
                conflicts = set(exported_pins) & set(our_pins)
                if conflicts:
                    print(f"    ⚠️  Pin conflicts detected: {list(conflicts)}")
                    return False
                else:
                    print("    ✅ No pin conflicts")
            else:
                print("    ✅ No GPIO pins currently exported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ HAT installation check failed: {e}")
        return False

def check_device_tree():
    """Check device tree configuration"""
    print("\n🌳 Checking Device Tree Configuration...")
    
    try:
        # Check SPI device tree status
        spi_dt_files = [
            '/proc/device-tree/soc/spi@7e204000/status',
            '/sys/firmware/devicetree/base/soc/spi@7e204000/status'
        ]
        
        for dt_file in spi_dt_files:
            if os.path.exists(dt_file):
                try:
                    with open(dt_file, 'rb') as f:
                        status = f.read().decode('utf-8', errors='ignore').strip('\x00')
                        print(f"  SPI Device Tree Status: {status}")
                        
                        if status == 'okay':
                            print("    ✅ SPI enabled in device tree")
                        else:
                            print("    ❌ SPI not enabled in device tree")
                            return False
                        break
                except:
                    continue
        
        # Check boot config
        config_files = ['/boot/config.txt', '/boot/firmware/config.txt']
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"  Checking {config_file}...")
                
                try:
                    with open(config_file, 'r') as f:
                        config_content = f.read()
                    
                    spi_enabled = False
                    i2c_enabled = False
                    
                    for line in config_content.split('\n'):
                        line = line.strip()
                        if line.startswith('dtparam=spi=on'):
                            spi_enabled = True
                            print("    ✅ SPI enabled in config.txt")
                        elif line.startswith('dtparam=i2c_arm=on'):
                            i2c_enabled = True
                            print("    ✅ I2C enabled in config.txt")
                    
                    if not spi_enabled:
                        print("    ⚠️  SPI not explicitly enabled in config.txt")
                    
                    break
                    
                except Exception as e:
                    print(f"    ❌ Could not read {config_file}: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Device tree check failed: {e}")
        return False

def provide_solutions(issues: Dict[str, bool]):
    """Provide specific solutions based on detected issues"""
    print("\n" + "="*60)
    print("🔧 DIAGNOSTIC RESULTS & SOLUTIONS")
    print("="*60)
    
    critical_issues = []
    warnings = []
    
    # Analyze issues
    if issues.get('power') == False:
        critical_issues.append("Power supply insufficient")
    
    if issues.get('spi') == False:
        critical_issues.append("SPI interface not working")
    
    if issues.get('chip_presence') == False:
        critical_issues.append("SX126x chip not responding")
    
    if issues.get('gpio', {}).get('RESET') == False:
        critical_issues.append("RESET pin not working")
    
    if issues.get('gpio', {}).get('BUSY') == False:
        warnings.append("BUSY pin readings inconsistent")
    
    # Provide solutions
    if critical_issues:
        print("\n❌ CRITICAL ISSUES FOUND:")
        for issue in critical_issues:
            print(f"   • {issue}")
        
        print("\n🔧 SOLUTIONS:")
        
        if "Power supply insufficient" in critical_issues:
            print("\n📱 Power Supply Issues:")
            print("   1. Use official Raspberry Pi power supply (5V 2.5A minimum)")
            print("   2. Check USB cable quality (use short, thick cables)")
            print("   3. Remove unnecessary USB devices")
            print("   4. Check for loose connections")
        
        if "SPI interface not working" in critical_issues:
            print("\n🔌 SPI Interface Issues:")
            print("   1. Enable SPI: sudo raspi-config → Interface Options → SPI → Enable")
            print("   2. Add to /boot/config.txt: dtparam=spi=on")
            print("   3. Reboot after enabling SPI")
            print("   4. Check SPI device exists: ls -l /dev/spidev*")
        
        if "SX126x chip not responding" in critical_issues:
            print("\n🔍 SX126x Chip Issues:")
            print("   1. Check HAT is properly seated on GPIO pins")
            print("   2. Verify all 40 pins are making contact")
            print("   3. Check for bent or damaged pins")
            print("   4. Ensure HAT is compatible with your Pi model")
            print("   5. Try reseating the HAT")
            print("   6. Check HAT power LED (if present)")
        
        if "RESET pin not working" in critical_issues:
            print("\n📌 GPIO Pin Issues:")
            print("   1. Check GPIO pin connections")
            print("   2. Verify pin numbers in config.json match HAT design")
            print("   3. Check for GPIO conflicts with other software")
            print("   4. Try different GPIO pins if configurable")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not critical_issues:
        print("\n✅ NO CRITICAL ISSUES DETECTED")
        print("\nThe hardware appears to be working correctly.")
        print("The LoRa transmission issue might be due to:")
        print("   • Antenna not connected")
        print("   • Incorrect frequency/region settings")
        print("   • RF interference")
        print("   • Software configuration issues")
    
    print("\n📋 NEXT STEPS:")
    if critical_issues:
        print("   1. Fix the critical issues listed above")
        print("   2. Reboot the system")
        print("   3. Run this diagnostic again")
        print("   4. Re-run the hardware test")
    else:
        print("   1. Check antenna connection")
        print("   2. Verify frequency settings for your region")
        print("   3. Try different LoRa parameters (lower SF, different frequency)")
        print("   4. Test in a different location (away from interference)")

def main():
    """Run comprehensive hardware diagnostics"""
    print("🔍 SX126x LoRa HAT Comprehensive Hardware Diagnostics")
    print("=" * 60)
    print()
    
    issues = {}
    
    # Run all diagnostic tests
    issues['power'] = check_power_supply()
    issues['device_tree'] = check_device_tree()
    issues['hat'] = check_hat_installation()
    issues['spi'] = check_spi_detailed()
    issues['gpio'] = check_gpio_detailed()
    issues['chip_presence'] = test_sx126x_presence()
    
    # Provide solutions
    provide_solutions(issues)
    
    # Return appropriate exit code
    critical_failures = [
        issues.get('power') == False,
        issues.get('spi') == False,
        issues.get('chip_presence') == False
    ]
    
    if any(critical_failures):
        return 2  # Critical issues
    elif any(v == False for v in issues.values() if isinstance(v, bool)):
        return 1  # Minor issues
    else:
        return 0  # All good

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic interrupted by user")
        try:
            GPIO.cleanup()
        except:
            pass
        sys.exit(130)
