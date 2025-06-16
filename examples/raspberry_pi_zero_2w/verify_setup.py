#!/usr/bin/env python3
"""
Setup verification script for Raspberry Pi Zero 2W LoRa SX126x HAT
Checks system configuration and requirements
"""

import os
import sys
import subprocess
import importlib

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 7:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.7+)")
        return False

def check_system_interfaces():
    """Check if SPI and I2C are enabled"""
    print("\nChecking system interfaces...")
    
    results = {}
    
    # Check SPI
    spi_enabled = os.path.exists('/dev/spidev0.0')
    print(f"SPI Interface: {'✓ Enabled' if spi_enabled else '✗ Disabled'}")
    results['spi'] = spi_enabled
    
    # Check I2C
    i2c_enabled = os.path.exists('/dev/i2c-1')
    print(f"I2C Interface: {'✓ Enabled' if i2c_enabled else '✗ Disabled'}")
    results['i2c'] = i2c_enabled
    
    # Check GPIO
    gpio_available = os.path.exists('/sys/class/gpio')
    print(f"GPIO Interface: {'✓ Available' if gpio_available else '✗ Not Available'}")
    results['gpio'] = gpio_available
    
    return results

def check_required_packages():
    """Check if required Python packages are installed"""
    print("\nChecking required Python packages...")
    
    required_packages = [
        ('spidev', 'SPI communication'),
        ('RPi.GPIO', 'GPIO control'),
        ('serial', 'Serial communication'),
        ('json', 'JSON handling'),
        ('sqlite3', 'Database support'),
        ('threading', 'Multi-threading'),
        ('time', 'Time functions'),
        ('logging', 'Logging support')
    ]
    
    optional_packages = [
        ('Adafruit_DHT', 'DHT22 sensor support'),
        ('board', 'CircuitPython board support'),
        ('busio', 'CircuitPython I2C/SPI'),
        ('adafruit_bmp280', 'BMP280 sensor support'),
        ('cryptography', 'Encryption support'),
        ('psutil', 'System monitoring')
    ]
    
    results = {'required': {}, 'optional': {}}
    
    print("Required packages:")
    for package, description in required_packages:
        try:
            importlib.import_module(package)
            print(f"  {package}: ✓ Available ({description})")
            results['required'][package] = True
        except ImportError:
            print(f"  {package}: ✗ Missing ({description})")
            results['required'][package] = False
    
    print("\nOptional packages:")
    for package, description in optional_packages:
        try:
            importlib.import_module(package)
            print(f"  {package}: ✓ Available ({description})")
            results['optional'][package] = True
        except ImportError:
            print(f"  {package}: ✗ Missing ({description})")
            results['optional'][package] = False
    
    return results

def check_permissions():
    """Check user permissions for GPIO and SPI"""
    print("\nChecking user permissions...")
    
    import pwd
    import grp
    
    username = pwd.getpwuid(os.getuid()).pw_name
    user_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
    
    print(f"Current user: {username}")
    print(f"User groups: {', '.join(user_groups)}")
    
    required_groups = ['spi', 'i2c', 'gpio']
    missing_groups = []
    
    for group in required_groups:
        if group in user_groups:
            print(f"  {group} group: ✓ Member")
        else:
            print(f"  {group} group: ✗ Not a member")
            missing_groups.append(group)
    
    return len(missing_groups) == 0, missing_groups

def check_config_files():
    """Check if configuration files exist"""
    print("\nChecking configuration files...")
    
    files_to_check = [
        ('config.json', 'Main configuration file'),
        ('mockup_config.json', 'Mockup configuration file'),
    ]
    
    results = {}
    
    for filename, description in files_to_check:
        exists = os.path.exists(filename)
        print(f"  {filename}: {'✓ Exists' if exists else '✗ Missing'} ({description})")
        results[filename] = exists
    
    return results

def check_hardware_files():
    """Check if hardware-related files exist"""
    print("\nChecking hardware interface files...")
    
    files_to_check = [
        ('/boot/config.txt', 'Boot configuration'),
        ('/proc/device-tree/soc/spi@7e204000/status', 'SPI device tree'),
        ('/proc/device-tree/soc/i2c@7e804000/status', 'I2C device tree'),
    ]
    
    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            print(f"  {filepath}: ✓ Exists ({description})")
            
            # For device tree files, check if enabled
            if 'device-tree' in filepath and 'status' in filepath:
                try:
                    with open(filepath, 'rb') as f:
                        content = f.read().decode('utf-8', errors='ignore').strip('\x00')
                        if 'okay' in content:
                            print(f"    Status: ✓ Enabled")
                        else:
                            print(f"    Status: ✗ Disabled")
                except:
                    print(f"    Status: ? Could not read")
        else:
            print(f"  {filepath}: ✗ Missing ({description})")

def provide_setup_instructions(issues):
    """Provide setup instructions for common issues"""
    print("\n" + "="*50)
    print("SETUP INSTRUCTIONS")
    print("="*50)
    
    if not issues['interfaces']['spi']:
        print("\n🔧 To enable SPI:")
        print("  sudo raspi-config")
        print("  Navigate to: Interfacing Options > SPI > Enable")
        print("  Or add 'dtparam=spi=on' to /boot/config.txt")
    
    if not issues['interfaces']['i2c']:
        print("\n🔧 To enable I2C:")
        print("  sudo raspi-config")
        print("  Navigate to: Interfacing Options > I2C > Enable")
        print("  Or add 'dtparam=i2c_arm=on' to /boot/config.txt")
    
    missing_required = [pkg for pkg, available in issues['packages']['required'].items() if not available]
    if missing_required:
        print(f"\n📦 To install missing required packages:")
        print("  pip install -r requirements.txt")
        print("  Or individually:")
        for pkg in missing_required:
            if pkg == 'RPi.GPIO':
                print(f"    pip install {pkg}")
            elif pkg == 'spidev':
                print(f"    pip install {pkg}")
    
    missing_optional = [pkg for pkg, available in issues['packages']['optional'].items() if not available]
    if missing_optional:
        print(f"\n📦 Optional packages (for full functionality):")
        for pkg in missing_optional:
            if pkg == 'Adafruit_DHT':
                print(f"    pip install {pkg}")
            elif pkg.startswith('adafruit_'):
                print(f"    pip install {pkg}")
    
    if issues['permissions']['missing_groups']:
        print(f"\n👤 To add user to required groups:")
        for group in issues['permissions']['missing_groups']:
            print(f"    sudo usermod -a -G {group} $USER")
        print("  Then logout and login again, or reboot")
    
    print(f"\n🔄 After making changes, reboot the system:")
    print("  sudo reboot")

def main():
    """Main verification function"""
    print("Raspberry Pi Zero 2W LoRa SX126x HAT Setup Verification")
    print("=" * 60)
    
    issues = {
        'python': False,
        'interfaces': {},
        'packages': {},
        'permissions': {'ok': True, 'missing_groups': []},
        'config': {}
    }
    
    # Check Python version
    issues['python'] = not check_python_version()
    
    # Check system interfaces
    issues['interfaces'] = check_system_interfaces()
    
    # Check packages
    issues['packages'] = check_required_packages()
    
    # Check permissions
    perm_ok, missing_groups = check_permissions()
    issues['permissions']['ok'] = perm_ok
    issues['permissions']['missing_groups'] = missing_groups
    
    # Check config files
    issues['config'] = check_config_files()
    
    # Check hardware files
    check_hardware_files()
    
    # Summary
    print("\n" + "="*50)
    print("VERIFICATION SUMMARY")
    print("="*50)
    
    total_issues = 0
    
    if issues['python']:
        print("❌ Python version issue")
        total_issues += 1
    else:
        print("✅ Python version OK")
    
    if not all(issues['interfaces'].values()):
        print("❌ System interfaces need configuration")
        total_issues += 1
    else:
        print("✅ System interfaces OK")
    
    if not all(issues['packages']['required'].values()):
        print("❌ Missing required packages")
        total_issues += 1
    else:
        print("✅ Required packages OK")
    
    if not issues['permissions']['ok']:
        print("❌ User permissions need configuration")
        total_issues += 1
    else:
        print("✅ User permissions OK")
    
    missing_optional = sum(1 for available in issues['packages']['optional'].values() if not available)
    if missing_optional > 0:
        print(f"⚠️  {missing_optional} optional packages missing (reduced functionality)")
    else:
        print("✅ All optional packages available")
    
    if total_issues == 0:
        print(f"\n🎉 Setup verification PASSED! System is ready for LoRa operation.")
        return 0
    else:
        print(f"\n⚠️  Setup verification found {total_issues} issue(s) that need attention.")
        provide_setup_instructions(issues)
        return 1

if __name__ == "__main__":
    sys.exit(main())
