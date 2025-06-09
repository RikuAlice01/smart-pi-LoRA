#!/usr/bin/env python3

import spidev
import time
import RPi.GPIO as GPIO

def test_spi_communication():
    """Test basic SPI communication"""
    print("🔧 Testing SPI Communication")
    
    try:
        # Test SPI 0.0
        spi0 = spidev.SpiDev()
        spi0.open(0, 0)
        spi0.max_speed_hz = 1000000
        spi0.mode = 0
        
        # Send test data
        test_data = [0x00, 0x01, 0x02]
        response = spi0.xfer2(test_data)
        print(f"✅ SPI 0.0 Response: {response}")
        spi0.close()
        
        # Test SPI 0.1  
        spi1 = spidev.SpiDev()
        spi1.open(0, 1)
        spi1.max_speed_hz = 1000000
        spi1.mode = 0
        
        response = spi1.xfer2(test_data)
        print(f"✅ SPI 0.1 Response: {response}")
        spi1.close()
        
        return True
        
    except Exception as e:
        print(f"❌ SPI Test Failed: {e}")
        return False

def test_gpio_pins():
    """Test GPIO pins used for LoRa"""
    print("🔧 Testing GPIO Pins")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Test CS pins
    cs_pins = [8, 7]  # CE0, CE1
    
    for pin in cs_pins:
        try:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.1)
            state = GPIO.input(pin)
            print(f"✅ GPIO {pin} (CS): {state}")
            GPIO.cleanup(pin)
        except Exception as e:
            print(f"❌ GPIO {pin} Test Failed: {e}")

def check_power_pins():
    """Guide for checking power connections"""
    print("🔋 Power Connection Check:")
    print("   Use multimeter to verify:")
    print("   Pin 1 (3.3V): Should read ~3.3V")
    print("   Pin 6 (GND):  Should read 0V")
    print("   Between Pin 1 & 6: Should read ~3.3V")

def main():
    print("🚀 LoRa Hardware Diagnostic Tool")
    print("=" * 40)
    
    # Test 1: SPI Communication
    if test_spi_communication():
        print("✅ SPI is working")
    else:
        print("❌ SPI has issues")
        return
    
    # Test 2: GPIO Pins
    test_gpio_pins()
    
    # Test 3: Power guidance
    check_power_pins()
    
    print("\n🔧 Common LoRa Module Types and Pinouts:")
    print("📡 Waveshare SX1262 LoRa HAT:")
    print("   - Should plug directly into 40-pin header")
    print("   - No jumper wires needed")
    print("   - Has onboard power LED")
    
    print("\n📡 Generic SX126x Breakout:")
    print("   LoRa Pin → Pi Pin")
    print("   VCC      → Pin 1  (3.3V)")
    print("   GND      → Pin 6  (GND)")
    print("   SCK      → Pin 23 (GPIO 11)")
    print("   MISO     → Pin 21 (GPIO 9)")
    print("   MOSI     → Pin 19 (GPIO 10)")
    print("   NSS/CS   → Pin 24 (GPIO 8)")
    print("   RST      → Pin 22 (GPIO 25) [Optional]")
    print("   DIO1     → Pin 18 (GPIO 24) [Optional]")
    
    print("\n❓ Troubleshooting Questions:")
    print("   1. What LoRa module are you using?")
    print("   2. Is there a power LED on the module?")
    print("   3. Are you using jumper wires or HAT?")
    print("   4. Did you double-check all connections?")

if __name__ == "__main__":
    main()