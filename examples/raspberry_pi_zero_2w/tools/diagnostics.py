#!/usr/bin/env python3
"""
Comprehensive diagnostics tool for LoRa Sensor Node
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.health import SystemHealthMonitor
from hardware.gpio_manager import GPIOManager
from communication.encryption import EncryptionManager
from core.config import ConfigManager


class DiagnosticsTool:
    """Comprehensive diagnostics tool"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.results = {}
    
    def run_all_diagnostics(self):
        """Run all diagnostic tests"""
        print("🔍 LoRa Sensor Node Diagnostics")
        print("=" * 40)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        tests = [
            ("System Information", self.check_system_info),
            ("Hardware Status", self.check_hardware),
            ("SPI Interface", self.check_spi),
            ("GPIO Status", self.check_gpio),
            ("Configuration", self.check_configuration),
            ("Encryption", self.check_encryption),
            ("Network", self.check_network),
            ("Performance", self.check_performance),
            ("Logs", self.check_logs)
        ]
        
        for test_name, test_func in tests:
            print(f"🧪 {test_name}...")
            try:
                result = test_func()
                self.results[test_name] = result
                if result.get('status') == 'OK':
                    print(f"✅ {test_name}: OK")
                else:
                    print(f"⚠️  {test_name}: {result.get('message', 'Issues found')}")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                self.results[test_name] = {'status': 'ERROR', 'error': str(e)}
            print()
        
        self.generate_report()
    
    def check_system_info(self):
        """Check system information"""
        info = {}
        
        # OS Information
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        info[key] = value.strip('"')
        except:
            pass
        
        # Hardware information
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo:
                    for line in cpuinfo.split('\n'):
                        if 'Model' in line:
                            info['hardware'] = line.split(':')[1].strip()
                            break
        except:
            pass
        
        # Memory information
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        info['memory'] = line.split()[1] + ' kB'
                        break
        except:
            pass
        
        # Python version
        info['python_version'] = sys.version
        
        print(f"  OS: {info.get('PRETTY_NAME', 'Unknown')}")
        print(f"  Hardware: {info.get('hardware', 'Unknown')}")
        print(f"  Memory: {info.get('memory', 'Unknown')}")
        print(f"  Python: {sys.version.split()[0]}")
        
        return {'status': 'OK', 'info': info}
    
    def check_hardware(self):
        """Check hardware status"""
        issues = []
        
        # Check temperature
        try:
            temp_file = '/sys/class/thermal/thermal_zone0/temp'
            if os.path.exists(temp_file):
                with open(temp_file, 'r') as f:
                    temp = int(f.read().strip()) / 1000
                    print(f"  CPU Temperature: {temp:.1f}°C")
                    if temp > 80:
                        issues.append(f"High CPU temperature: {temp:.1f}°C")
        except:
            issues.append("Could not read CPU temperature")
        
        # Check voltage
        try:
            result = subprocess.run(['vcgencmd', 'measure_volts'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                voltage = result.stdout.strip()
                print(f"  Core Voltage: {voltage}")
        except:
            pass
        
        # Check throttling
        try:
            result = subprocess.run(['vcgencmd', 'get_throttled'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                throttled = result.stdout.strip()
                print(f"  Throttling Status: {throttled}")
                if throttled != "throttled=0x0":
                    issues.append(f"System throttling detected: {throttled}")
        except:
            pass
        
        status = 'OK' if not issues else 'WARNING'
        return {'status': status, 'issues': issues}
    
    def check_spi(self):
        """Check SPI interface"""
        issues = []
        
        # Check SPI devices
        spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1']
        available = []
        
        for device in spi_devices:
            if os.path.exists(device):
                available.append(device)
        
        print(f"  Available SPI devices: {available}")
        
        if not available:
            issues.append("No SPI devices found")
            issues.append("Run: sudo raspi-config -> Interface Options -> SPI -> Enable")
        
        # Check SPI module
        try:
            result = subprocess.run(['lsmod'], capture_output=True, text=True)
            if 'spi_bcm2835' in result.stdout:
                print("  ✅ SPI kernel module loaded")
            else:
                issues.append("SPI kernel module not loaded")
        except:
            pass
        
        # Check user groups
        try:
            result = subprocess.run(['groups'], capture_output=True, text=True)
            groups = result.stdout.strip().split()
            if 'spi' in groups:
                print("  ✅ User in spi group")
            else:
                issues.append("User not in spi group")
                issues.append("Run: sudo usermod -a -G spi $USER")
        except:
            pass
        
        status = 'OK' if not issues else 'ERROR'
        return {'status': status, 'issues': issues}
    
    def check_gpio(self):
        """Check GPIO status"""
        issues = []
        
        try:
            # Test GPIO manager
            gpio_manager = GPIOManager()
            
            # Check critical pins
            critical_pins = [8, 22, 23, 24]  # CS, RESET, BUSY, DIO1
            
            for pin in critical_pins:
                try:
                    gpio_manager.setup_pin(pin, 'input')
                    print(f"  ✅ GPIO {pin}: OK")
                except Exception as e:
                    issues.append(f"GPIO {pin} error: {e}")
            
            gpio_manager.cleanup()
            
        except Exception as e:
            issues.append(f"GPIO manager error: {e}")
        
        status = 'OK' if not issues else 'ERROR'
        return {'status': status, 'issues': issues}
    
    def check_configuration(self):
        """Check configuration files"""
        issues = []
        
        # Check config files
        config_dir = self.base_path / "config"
        config_files = ["default.json", "production.json"]
        
        for config_file in config_files:
            config_path = config_dir / config_file
            if config_path.exists():
                try:
                    config_manager = ConfigManager(str(config_path))
                    print(f"  ✅ {config_file}: Valid")
                except Exception as e:
                    issues.append(f"{config_file}: {e}")
            else:
                print(f"  ⚠️  {config_file}: Not found")
        
        status = 'OK' if not issues else 'ERROR'
        return {'status': status, 'issues': issues}
    
    def check_encryption(self):
        """Check encryption setup"""
        issues = []
        
        keyfile_path = self.base_path / "keyfile.bin"
        
        if keyfile_path.exists():
            try:
                encryption_manager = EncryptionManager(str(keyfile_path))
                
                # Test encryption/decryption
                test_data = "Diagnostic test"
                encrypted = encryption_manager.encrypt(test_data)
                decrypted = encryption_manager.decrypt(encrypted)
                
                if decrypted == test_data:
                    print("  ✅ Encryption: Working")
                else:
                    issues.append("Encryption test failed")
                
                # Check file permissions
                stat = keyfile_path.stat()
                if oct(stat.st_mode)[-3:] == '600':
                    print("  ✅ Keyfile permissions: Secure")
                else:
                    issues.append("Keyfile permissions not secure (should be 600)")
                
            except Exception as e:
                issues.append(f"Encryption error: {e}")
        else:
            issues.append("Keyfile not found")
            issues.append("Run: python3 tools/setup_wizard.py")
        
        status = 'OK' if not issues else 'ERROR'
        return {'status': status, 'issues': issues}
    
    def check_network(self):
        """Check network connectivity"""
        issues = []
        
        # Check network interfaces
        try:
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            if 'wlan0' in result.stdout:
                print("  ✅ WiFi interface available")
            if 'eth0' in result.stdout:
                print("  ✅ Ethernet interface available")
        except:
            pass
        
        # Check internet connectivity
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                print("  ✅ Internet connectivity: OK")
            else:
                issues.append("No internet connectivity")
        except:
            issues.append("Could not test internet connectivity")
        
        status = 'OK' if not issues else 'WARNING'
        return {'status': status, 'issues': issues}
    
    def check_performance(self):
        """Check system performance"""
        issues = []
        
        try:
            health_monitor = SystemHealthMonitor()
            metrics = health_monitor.get_system_metrics()
            
            print(f"  CPU Usage: {metrics['cpu_percent']:.1f}%")
            print(f"  Memory Usage: {metrics['memory_percent']:.1f}%")
            print(f"  Disk Usage: {metrics['disk_percent']:.1f}%")
            
            if metrics['cpu_percent'] > 90:
                issues.append(f"High CPU usage: {metrics['cpu_percent']:.1f}%")
            
            if metrics['memory_percent'] > 90:
                issues.append(f"High memory usage: {metrics['memory_percent']:.1f}%")
            
            if metrics['disk_percent'] > 90:
                issues.append(f"High disk usage: {metrics['disk_percent']:.1f}%")
            
        except Exception as e:
            issues.append(f"Performance check error: {e}")
        
        status = 'OK' if not issues else 'WARNING'
        return {'status': status, 'issues': issues}
    
    def check_logs(self):
        """Check log files"""
        issues = []
        
        log_dir = self.base_path / "logs"
        
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            print(f"  Log files found: {len(log_files)}")
            
            for log_file in log_files:
                size = log_file.stat().st_size
                print(f"    {log_file.name}: {size} bytes")
                
                if size > 100 * 1024 * 1024:  # 100MB
                    issues.append(f"Large log file: {log_file.name} ({size} bytes)")
        else:
            print("  No log directory found")
        
        status = 'OK' if not issues else 'WARNING'
        return {'status': status, 'issues': issues}
    
    def generate_report(self):
        """Generate diagnostic report"""
        print("\n" + "=" * 40)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 40)
        
        total_tests = len(self.results)
        ok_tests = sum(1 for r in self.results.values() if r.get('status') == 'OK')
        warning_tests = sum(1 for r in self.results.values() if r.get('status') == 'WARNING')
        error_tests = sum(1 for r in self.results.values() if r.get('status') == 'ERROR')
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {ok_tests}")
        print(f"⚠️  Warnings: {warning_tests}")
        print(f"❌ Errors: {error_tests}")
        
        if error_tests > 0:
            print("\n🔧 CRITICAL ISSUES TO FIX:")
            for test_name, result in self.results.items():
                if result.get('status') == 'ERROR':
                    print(f"\n{test_name}:")
                    for issue in result.get('issues', []):
                        print(f"  • {issue}")
        
        if warning_tests > 0:
            print("\n⚠️  WARNINGS:")
            for test_name, result in self.results.items():
                if result.get('status') == 'WARNING':
                    print(f"\n{test_name}:")
                    for issue in result.get('issues', []):
                        print(f"  • {issue}")
        
        # Save report
        report_file = self.base_path / f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total_tests,
                    'passed': ok_tests,
                    'warnings': warning_tests,
                    'errors': error_tests
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\n📄 Full report saved: {report_file}")


if __name__ == "__main__":
    diagnostics = DiagnosticsTool()
    diagnostics.run_all_diagnostics()
