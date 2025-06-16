#!/usr/bin/env python3
"""
Simple connection verification tool for SX126x HAT
Visual guide for checking physical connections
"""

import sys

def print_connection_guide():
    """Print visual connection guide"""
    print("🔌 SX126x LoRa HAT Connection Verification Guide")
    print("=" * 55)
    print()
    
    print("📋 PHYSICAL INSPECTION CHECKLIST:")
    print()
    
    print("1. 🎩 HAT SEATING:")
    print("   □ HAT is firmly seated on all 40 GPIO pins")
    print("   □ No bent or damaged pins visible")
    print("   □ HAT sits flat against the Pi (no gaps)")
    print("   □ All pins make contact (no loose connections)")
    print()
    
    print("2. 🔋 POWER INDICATORS:")
    print("   □ Pi power LED is solid (not flickering)")
    print("   □ HAT power LED is on (if present)")
    print("   □ Using official Pi power supply (5V 2.5A+)")
    print("   □ No undervoltage warnings in dmesg")
    print()
    
    print("3. 📡 ANTENNA CONNECTION:")
    print("   □ Antenna is connected to the correct connector")
    print("   □ Antenna connector is tight (not loose)")
    print("   □ Antenna is appropriate for frequency (915MHz/868MHz)")
    print("   □ Antenna is not damaged or bent")
    print()
    
    print("4. 🔧 CONFIGURATION:")
    print("   □ SPI is enabled (sudo raspi-config)")
    print("   □ System has been rebooted after enabling SPI")
    print("   □ /dev/spidev0.0 device exists")
    print("   □ No GPIO conflicts with other software")
    print()
    
    print("📌 EXPECTED GPIO PIN CONNECTIONS:")
    print("   (Standard SX126x HAT pinout)")
    print()
    print("   ┌─────────────────────────────────────┐")
    print("   │  Pi Pin  │ GPIO │  SX126x Signal   │")
    print("   ├─────────────────────────────────────┤")
    print("   │    15    │  22  │     RESET        │")
    print("   │    16    │  23  │     BUSY         │")
    print("   │    18    │  24  │     DIO1         │")
    print("   │    19    │  10  │   SPI0_MOSI      │")
    print("   │    21    │   9  │   SPI0_MISO      │")
    print("   │    23    │  11  │   SPI0_SCLK      │")
    print("   │    24    │   8  │   SPI0_CE0       │")
    print("   │   1,17   │ 3.3V │     VCC          │")
    print("   │  6,9,14  │ GND  │     GND          │")
    print("   └─────────────────────────────────────┘")
    print()
    
    print("🔍 TROUBLESHOOTING STEPS:")
    print()
    print("If connections look good but tests still fail:")
    print()
    print("1. 🔄 POWER CYCLE:")
    print("   sudo shutdown -h now")
    print("   (Wait 10 seconds, unplug power)")
    print("   (Plug power back in)")
    print()
    
    print("2. 🧪 TEST SEQUENCE:")
    print("   python3 verify_setup.py      # Check system config")
    print("   python3 diagnose_hardware.py # Detailed diagnostics")
    print("   python3 test_hardware.py     # Full hardware test")
    print()
    
    print("3. 🔧 CONFIGURATION CHECK:")
    print("   # Check SPI is enabled:")
    print("   ls -l /dev/spidev*")
    print("   ")
    print("   # Check GPIO exports:")
    print("   ls /sys/class/gpio/")
    print("   ")
    print("   # Check for errors:")
    print("   dmesg | grep -i spi")
    print("   dmesg | grep -i gpio")
    print()
    
    print("4. 🆘 COMMON ISSUES & FIXES:")
    print()
    print("   Issue: All status reads return 0x00")
    print("   Fix: Check power supply, reseat HAT, verify SPI enabled")
    print()
    print("   Issue: BUSY pin always HIGH")
    print("   Fix: Check RESET pin connection, try manual reset")
    print()
    print("   Issue: No SPI device (/dev/spidev0.0)")
    print("   Fix: Enable SPI in raspi-config, reboot")
    print()
    print("   Issue: Permission denied on GPIO")
    print("   Fix: Add user to gpio group, logout/login")
    print()
    
    print("📞 GETTING HELP:")
    print()
    print("If issues persist after checking all items above:")
    print("1. Run: python3 diagnose_hardware.py > diagnostic_report.txt")
    print("2. Check HAT manufacturer documentation")
    print("3. Verify HAT compatibility with your Pi model")
    print("4. Contact HAT manufacturer support with diagnostic report")

def main():
    """Main function"""
    print_connection_guide()
    
    print("\n" + "="*55)
    response = input("Have you checked all the items above? (y/N): ")
    
    if response.lower().startswith('y'):
        print("\n✅ Great! Now run the diagnostic tool:")
        print("python3 diagnose_hardware.py")
    else:
        print("\n📋 Please check the items above first, then run:")
        print("python3 diagnose_hardware.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
