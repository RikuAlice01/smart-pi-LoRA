#!/usr/bin/env python3
"""
SX126x HAT SPI Connection Guide and Setup Tool
Step-by-step guide for connecting SX126x HAT via SPI
"""

import os
import sys
import subprocess
import time
from typing import Dict, List, Tuple, Optional

def print_connection_guide():
    """Print detailed SPI connection guide"""
    print("🔌 SX126x HAT SPI Connection Guide")
    print("=" * 40)
    print()
    
    print("📋 STEP 1: PHYSICAL CONNECTION")
    print("=" * 35)
    print()
    print("🎩 HAT Installation:")
    print("   1. Power OFF your Raspberry Pi completely")
    print("   2. Carefully align the HAT with the 40-pin GPIO header")
    print("   3. Press down firmly until HAT sits flat")
    print("   4. Ensure ALL pins make contact (no gaps)")
    print("   5. Check that HAT doesn't wobble")
    print()
    
    print("📌 Critical SPI Connections (Standard SX126x HAT):")
    print("   ┌─────────────────────────────────────────┐")
    print("   │ Pi Pin │ GPIO │ SPI Signal │ SX126x Pin │")
    print("   ├─────────────────────────────────────────┤")
    print("   │   19   │  10  │ SPI0_MOSI  │    MOSI    │")
    print("   │   21   │   9  │ SPI0_MISO  │    MISO    │")
    print("   │   23   │  11  │ SPI0_SCLK  │    SCLK    │")
    print("   │   24   │   8  │ SPI0_CE0   │    NSS     │")
    print("   │   15   │  22  │   GPIO     │   RESET    │")
    print("   │   16   │  23  │   GPIO     │    BUSY    │")
    print("   │   18   │  24  │   GPIO     │    DIO1    │")
    print("   │  1,17  │ 3.3V │   Power    │    VCC     │")
    print("   │6,9,14,20,25,30,34,39│ GND │   Ground   │    GND     │")
    print("   └─────────────────────────────────────────┘")
    print()
    
    print("📋 STEP 2: ENABLE SPI INTERFACE")
    print("=" * 35)
    print()
    print("🔧 Method 1 - Using raspi-config:")
    print("   sudo raspi-config")
    print("   → Interface Options")
    print("   → SPI")
    print("   → Enable")
    print("   → Finish")
    print("   → Reboot")
    print()
    
    print("🔧 Method 2 - Manual configuration:")
    print("   1. Edit boot config:")
    print("      sudo nano /boot/config.txt")
    print("   2. Add this line:")
    print("      dtparam=spi=on")
    print("   3. Save and reboot:")
    print("      sudo reboot")
    print()
    
    print("📋 STEP 3: VERIFY SPI SETUP")
    print("=" * 30)
    print()
    print("✅ Check SPI devices exist:")
    print("   ls -l /dev/spidev*")
    print("   Expected output:")
    print("   crw-rw---- 1 root spi 153, 0 ... /dev/spidev0.0")
    print("   crw-rw---- 1 root spi 153, 1 ... /dev/spidev0.1")
    print()
    
    print("✅ Check user permissions:")
    print("   groups $USER")
    print("   Should include: spi, gpio")
    print()
    print("   If missing, add user to groups:")
    print("   sudo usermod -a -G spi,gpio $USER")
    print("   Then logout and login again")
    print()

def check_spi_status() -> Dict[str, bool]:
    """Check current SPI configuration status"""
    print("🔍 Checking SPI Configuration Status...")
    print("=" * 40)
    
    status = {
        'spi_enabled': False,
        'spi_devices_exist': False,
        'user_in_spi_group': False,
        'user_in_gpio_group': False,
        'spidev_available': False
    }
    
    # Check if SPI is enabled in device tree
    dt_paths = [
        '/proc/device-tree/soc/spi@7e204000/status',
        '/sys/firmware/devicetree/base/soc/spi@7e204000/status'
    ]
    
    for dt_path in dt_paths:
        if os.path.exists(dt_path):
            try:
                with open(dt_path, 'rb') as f:
                    spi_status = f.read().decode('utf-8', errors='ignore').strip('\x00')
                    if spi_status == 'okay':
                        status['spi_enabled'] = True
                        print("✅ SPI enabled in device tree")
                        break
            except:
                continue
    
    if not status['spi_enabled']:
        print("❌ SPI not enabled in device tree")
    
    # Check SPI device files
    spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1']
    existing_devices = [dev for dev in spi_devices if os.path.exists(dev)]
    
    if existing_devices:
        status['spi_devices_exist'] = True
        print(f"✅ SPI devices found: {existing_devices}")
    else:
        print("❌ No SPI devices found")
    
    # Check user groups
    try:
        import pwd
        import grp
        
        username = pwd.getpwuid(os.getuid()).pw_name
        user_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        
        if 'spi' in user_groups:
            status['user_in_spi_group'] = True
            print("✅ User is in 'spi' group")
        else:
            print("❌ User not in 'spi' group")
        
        if 'gpio' in user_groups:
            status['user_in_gpio_group'] = True
            print("✅ User is in 'gpio' group")
        else:
            print("❌ User not in 'gpio' group")
            
    except Exception as e:
        print(f"⚠️  Could not check user groups: {e}")
    
    # Check spidev library
    try:
        import spidev
        status['spidev_available'] = True
        print("✅ spidev library available")
    except ImportError:
        print("❌ spidev library not installed")
    
    return status

def enable_spi_interface():
    """Enable SPI interface automatically"""
    print("\n🔧 Enabling SPI Interface...")
    print("=" * 30)
    
    try:
        # Check if already enabled
        result = subprocess.run(['sudo', 'raspi-config', 'nonint', 'get_spi'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip() == '0':
            print("✅ SPI already enabled")
            return True
        
        # Enable SPI
        print("🔧 Enabling SPI...")
        result = subprocess.run(['sudo', 'raspi-config', 'nonint', 'do_spi', '0'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SPI enabled successfully")
            print("⚠️  Reboot required for changes to take effect")
            return True
        else:
            print(f"❌ Failed to enable SPI: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("⚠️  raspi-config not found, trying manual method...")
        return enable_spi_manual()
    except Exception as e:
        print(f"❌ Error enabling SPI: {e}")
        return False

def enable_spi_manual():
    """Enable SPI manually by editing config.txt"""
    config_files = ['/boot/config.txt', '/boot/firmware/config.txt']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                # Read current config
                with open(config_file, 'r') as f:
                    config_content = f.read()
                
                # Check if SPI already enabled
                if 'dtparam=spi=on' in config_content:
                    print("✅ SPI already enabled in config.txt")
                    return True
                
                # Add SPI enable line
                print(f"🔧 Adding SPI enable to {config_file}...")
                
                # Backup original
                subprocess.run(['sudo', 'cp', config_file, f'{config_file}.backup'])
                
                # Add SPI enable
                with open('/tmp/config_addition.txt', 'w') as f:
                    f.write('\n# Enable SPI\ndtparam=spi=on\n')
                
                subprocess.run(['sudo', 'sh', '-c', f'cat /tmp/config_addition.txt >> {config_file}'])
                
                print("✅ SPI enabled in config.txt")
                print("⚠️  Reboot required for changes to take effect")
                return True
                
            except Exception as e:
                print(f"❌ Error modifying {config_file}: {e}")
                continue
    
    print("❌ Could not find or modify boot config file")
    return False

def add_user_to_groups():
    """Add current user to required groups"""
    print("\n👤 Adding User to Required Groups...")
    print("=" * 40)
    
    try:
        import pwd
        username = pwd.getpwuid(os.getuid()).pw_name
        
        groups_to_add = ['spi', 'gpio', 'i2c']
        
        for group in groups_to_add:
            try:
                result = subprocess.run(['sudo', 'usermod', '-a', '-G', group, username],
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Added user to '{group}' group")
                else:
                    print(f"⚠️  Could not add user to '{group}' group: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ Error adding user to '{group}' group: {e}")
        
        print("\n⚠️  Logout and login again (or reboot) for group changes to take effect")
        return True
        
    except Exception as e:
        print(f"❌ Error managing user groups: {e}")
        return False

def install_spi_tools():
    """Install required SPI tools and libraries"""
    print("\n📦 Installing SPI Tools and Libraries...")
    print("=" * 45)
    
    packages_to_install = [
        ('python3-spidev', 'SPI device library for Python'),
        ('python3-rpi.gpio', 'GPIO library for Python'),
        ('python3-dev', 'Python development headers'),
    ]
    
    pip_packages = [
        ('spidev', 'SPI device library'),
        ('RPi.GPIO', 'GPIO control library'),
    ]
    
    # Install system packages
    for package, description in packages_to_install:
        try:
            print(f"📦 Installing {package} ({description})...")
            result = subprocess.run(['sudo', 'apt', 'install', '-y', package],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {package} installed successfully")
            else:
                print(f"⚠️  Could not install {package}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error installing {package}: {e}")
    
    # Install pip packages
    for package, description in pip_packages:
        try:
            print(f"🐍 Installing {package} via pip ({description})...")
            result = subprocess.run(['pip3', 'install', '--user', package],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {package} installed successfully")
            else:
                print(f"⚠️  Could not install {package}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error installing {package}: {e}")

def test_spi_communication():
    """Test basic SPI communication"""
    print("\n🧪 Testing SPI Communication...")
    print("=" * 35)
    
    try:
        import spidev
        import RPi.GPIO as GPIO
        
        # Test SPI device opening
        print("🔍 Testing SPI device access...")
        
        spi = spidev.SpiDev()
        spi.open(0, 0)  # Bus 0, Device 0
        
        print("✅ SPI device opened successfully")
        
        # Configure SPI
        spi.max_speed_hz = 1000000  # 1MHz
        spi.mode = 0
        
        print(f"✅ SPI configured: {spi.max_speed_hz}Hz, Mode {spi.mode}")
        
        # Test basic communication
        print("🔍 Testing SPI communication...")
        
        test_data = [0x55, 0xAA, 0xFF, 0x00]
        response = spi.xfer2(test_data)
        
        print(f"📤 Sent: {[hex(x) for x in test_data]}")
        print(f"📥 Received: {[hex(x) for x in response]}")
        
        spi.close()
        
        # Test GPIO access
        print("\n🔍 Testing GPIO access...")
        
        GPIO.setmode(GPIO.BCM)
        
        # Test standard SX126x pins
        test_pins = [22, 23, 24]  # RESET, BUSY, DIO1
        
        for pin in test_pins:
            try:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.01)
                GPIO.output(pin, GPIO.LOW)
                print(f"✅ GPIO{pin} control working")
            except Exception as e:
                print(f"❌ GPIO{pin} error: {e}")
        
        GPIO.cleanup()
        
        print("\n✅ SPI and GPIO communication tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Required library not available: {e}")
        print("   Install with: pip3 install spidev RPi.GPIO")
        return False
    except PermissionError:
        print("❌ Permission denied accessing SPI/GPIO")
        print("   Make sure user is in 'spi' and 'gpio' groups")
        return False
    except Exception as e:
        print(f"❌ SPI communication test failed: {e}")
        return False

def test_sx126x_connection():
    """Test specific SX126x chip connection"""
    print("\n🔍 Testing SX126x Chip Connection...")
    print("=" * 40)
    
    try:
        import spidev
        import RPi.GPIO as GPIO
        
        # Initialize SPI
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 100000  # Start slow
        spi.mode = 0
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(22, GPIO.OUT)  # RESET
        GPIO.setup(23, GPIO.IN)   # BUSY
        
        print("🔄 Performing hardware reset...")
        
        # Hardware reset sequence
        GPIO.output(22, GPIO.LOW)
        time.sleep(0.002)  # 2ms reset pulse
        GPIO.output(22, GPIO.HIGH)
        time.sleep(0.010)  # 10ms wait
        
        # Wait for BUSY to go low
        print("⏳ Waiting for BUSY pin...")
        start_time = time.time()
        while GPIO.input(23) and (time.time() - start_time) < 1.0:
            time.sleep(0.001)
        
        busy_time = time.time() - start_time
        busy_state = GPIO.input(23)
        
        print(f"📍 BUSY pin: {busy_state} after {busy_time*1000:.1f}ms")
        
        if busy_state == 0:
            print("✅ BUSY pin went LOW - chip responding to reset")
        else:
            print("⚠️  BUSY pin stuck HIGH - possible connection issue")
        
        # Test SPI commands
        print("\n🔍 Testing SPI commands...")
        
        commands = [
            (0xC0, "GET_STATUS"),
            (0x80, "SET_STANDBY"),
            (0xC0, "GET_STATUS again")
        ]
        
        responses = []
        for cmd, name in commands:
            try:
                response = spi.xfer2([cmd, 0x00])
                responses.append((name, response))
                print(f"📤 {name}: Sent 0x{cmd:02X}, Got {[hex(x) for x in response]}")
                time.sleep(0.01)
            except Exception as e:
                print(f"❌ {name}: Failed - {e}")
                responses.append((name, None))
        
        # Analyze responses
        valid_responses = [r for r in responses if r[1] is not None]
        
        if not valid_responses:
            print("\n❌ No valid SPI responses - check connections")
            result = False
        elif all(r[1][0] == 0x00 for r in valid_responses):
            print("\n⚠️  All responses are 0x00 - possible issues:")
            print("   • HAT not properly connected")
            print("   • Wrong HAT type (not SX126x)")
            print("   • Power supply issue")
            print("   • Faulty chip")
            result = False
        else:
            print("\n✅ Got valid responses - SX126x chip detected!")
            result = True
        
        spi.close()
        GPIO.cleanup()
        
        return result
        
    except Exception as e:
        print(f"❌ SX126x connection test failed: {e}")
        try:
            spi.close()
            GPIO.cleanup()
        except:
            pass
        return False

def create_test_script():
    """Create a simple SPI test script"""
    test_script = '''#!/usr/bin/env python3
"""
Simple SX126x SPI Test Script
"""

import spidev
import RPi.GPIO as GPIO
import time

def test_sx126x():
    """Test SX126x communication"""
    try:
        # Initialize SPI
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1000000
        spi.mode = 0
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(22, GPIO.OUT)  # RESET
        GPIO.setup(23, GPIO.IN)   # BUSY
        
        print("Testing SX126x communication...")
        
        # Reset chip
        GPIO.output(22, GPIO.LOW)
        time.sleep(0.002)
        GPIO.output(22, GPIO.HIGH)
        time.sleep(0.010)
        
        # Get status
        response = spi.xfer2([0xC0, 0x00])
        print(f"Status: {[hex(x) for x in response]}")
        
        if response[0] != 0x00 or response[1] != 0x00:
            print("✅ SX126x responding!")
        else:
            print("❌ No response from SX126x")
        
        spi.close()
        GPIO.cleanup()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sx126x()
'''
    
    try:
        with open('test_spi_sx126x.py', 'w') as f:
            f.write(test_script)
        
        # Make executable
        os.chmod('test_spi_sx126x.py', 0o755)
        
        print("📝 Created test_spi_sx126x.py")
        print("   Run with: python3 test_spi_sx126x.py")
        return True
        
    except Exception as e:
        print(f"❌ Could not create test script: {e}")
        return False

def main():
    """Main SPI setup function"""
    print("🔌 SX126x HAT SPI Connection Setup")
    print("=" * 40)
    print()
    
    # Print connection guide
    print_connection_guide()
    
    # Check current status
    status = check_spi_status()
    
    print("\n🔧 AUTOMATIC SETUP")
    print("=" * 20)
    
    setup_needed = False
    
    # Enable SPI if needed
    if not status['spi_enabled'] or not status['spi_devices_exist']:
        setup_needed = True
        if enable_spi_interface():
            print("✅ SPI interface enabled")
        else:
            print("❌ Failed to enable SPI interface")
    
    # Add user to groups if needed
    if not status['user_in_spi_group'] or not status['user_in_gpio_group']:
        setup_needed = True
        add_user_to_groups()
    
    # Install libraries if needed
    if not status['spidev_available']:
        setup_needed = True
        install_spi_tools()
    
    if setup_needed:
        print("\n⚠️  REBOOT REQUIRED")
        print("=" * 20)
        print("Changes have been made that require a reboot.")
        print("After rebooting, run this script again to test the connection.")
        print()
        
        reboot_now = input("Reboot now? (y/N): ").strip().lower()
        if reboot_now.startswith('y'):
            print("🔄 Rebooting...")
            subprocess.run(['sudo', 'reboot'])
            return
    
    # Test SPI communication
    print("\n🧪 TESTING SPI CONNECTION")
    print("=" * 30)
    
    if test_spi_communication():
        print("\n✅ Basic SPI communication working")
        
        # Test SX126x specific
        if test_sx126x_connection():
            print("\n🎉 SX126x HAT connection successful!")
            print("\nNext steps:")
            print("1. Run: python3 test_hardware.py")
            print("2. Check antenna connection")
            print("3. Verify frequency settings")
        else:
            print("\n⚠️  SPI working but SX126x not responding")
            print("\nTroubleshooting:")
            print("1. Check HAT is properly seated")
            print("2. Verify HAT is SX126x type (not SX127x or RFM95W)")
            print("3. Check power supply (5V 2.5A minimum)")
            print("4. Run: python3 check_hat_compatibility.py")
    else:
        print("\n❌ SPI communication failed")
        print("\nTroubleshooting:")
        print("1. Reboot if you just enabled SPI")
        print("2. Check user is in 'spi' and 'gpio' groups")
        print("3. Verify HAT physical connection")
        print("4. Check /dev/spidev0.0 exists")
    
    # Create test script
    print("\n📝 CREATING TEST SCRIPT")
    print("=" * 25)
    create_test_script()
    
    print("\n🎯 SUMMARY")
    print("=" * 10)
    print("SPI Setup Status:")
    for key, value in status.items():
        status_icon = "✅" if value else "❌"
        print(f"  {key}: {status_icon}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
