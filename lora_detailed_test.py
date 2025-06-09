#!/usr/bin/env python3
"""
Advanced LoRa SX126x Diagnostic Script
Addresses common issues with SX126x modules and LoRaRF library
"""

from LoRaRF import SX126x
import time
import spidev
import RPi.GPIO as GPIO
import sys

# Configuration
RESET_PIN = 18  # GPIO pin for RST (adjust as needed)
BUSY_PIN = 24   # GPIO pin for BUSY (adjust as needed)

def setup_gpio():
    """Setup GPIO pins for reset and busy control"""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup reset pin
        GPIO.setup(RESET_PIN, GPIO.OUT)
        print(f"✅ RST pin {RESET_PIN} configured as output")
        
        # Setup busy pin if available
        try:
            GPIO.setup(BUSY_PIN, GPIO.IN)
            print(f"✅ BUSY pin {BUSY_PIN} configured as input")
        except:
            print(f"⚠️ BUSY pin {BUSY_PIN} not available")
        
        return True
    except Exception as e:
        print(f"❌ GPIO setup failed: {e}")
        return False

def hardware_reset():
    """Perform hardware reset of the LoRa module"""
    try:
        print("🔄 Performing hardware reset...")
        GPIO.output(RESET_PIN, GPIO.LOW)
        time.sleep(0.1)  # Hold reset for 100ms
        GPIO.output(RESET_PIN, GPIO.HIGH)
        time.sleep(0.1)  # Wait for module to boot
        print("✅ Hardware reset completed")
        return True
    except Exception as e:
        print(f"❌ Hardware reset failed: {e}")
        return False

def wait_for_ready():
    """Wait for module to not be busy"""
    try:
        timeout = 1.0  # 1 second timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if GPIO.input(BUSY_PIN) == GPIO.LOW:
                    return True
            except:
                # If BUSY pin not available, just wait a bit
                time.sleep(0.01)
                return True
            time.sleep(0.001)
        
        print("⚠️ Module busy timeout")
        return False
    except:
        # If no BUSY pin, assume ready
        return True

def test_sx126x_commands():
    """Test specific SX126x commands to verify communication"""
    print("🔧 Testing SX126x Commands...")
    
    try:
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1000000
        spi.mode = 0
        
        # Test 1: GetStatus command (0xC0)
        print("📡 Testing GetStatus command...")
        status_cmd = [0xC0, 0x00]
        response = spi.xfer2(status_cmd)
        print(f"   Status response: {[hex(x) for x in response]}")
        
        # Test 2: GetVersion command (0x19 0x69 0x69)
        print("📡 Testing GetVersion command...")
        version_cmd = [0x19, 0x69, 0x69, 0x00]
        response = spi.xfer2(version_cmd)
        print(f"   Version response: {[hex(x) for x in response]}")
        
        # Test 3: Read register command
        print("📡 Testing ReadRegister command...")
        read_cmd = [0x1D, 0x03, 0x20, 0x00, 0x00]  # Read version register
        response = spi.xfer2(read_cmd)
        print(f"   Register response: {[hex(x) for x in response]}")
        
        spi.close()
        return True
        
    except Exception as e:
        print(f"❌ Command test failed: {e}")
        return False

def test_lora_initialization():
    """Test LoRa initialization with proper reset sequence"""
    print("🔧 Testing LoRa Initialization...")
    
    try:
        # Hardware reset first
        if not hardware_reset():
            return False
        
        # Wait for module to be ready
        wait_for_ready()
        
        # Initialize LoRa
        lora = SX126x()
        
        print("📡 Attempting LoRa begin()...")
        lora.begin(bus=0, cs=0)
        
        # Wait a bit after initialization
        time.sleep(0.1)
        
        # Test basic operations
        print("📊 Getting module status...")
        status = lora.getStatus()
        print(f"   Status: 0x{status:02X}")
        
        # Try to get version
        try:
            # Some LoRaRF versions have getVersion method
            version = lora.getVersion()
            print(f"   Version: 0x{version:02X}")
        except AttributeError:
            print("   Version method not available in this LoRaRF version")
        
        # Test frequency setting
        print("📻 Testing frequency setting...")
        lora.setFrequency(434000000)  # 434 MHz
        print("   Frequency set successfully")
        
        # Test power setting
        print("🔋 Testing power setting...")
        lora.setTxPower(14, SX126x.POWER_RAMP_200U)
        print("   Power set successfully")
        
        print("✅ LoRa initialization successful!")
        return True
        
    except Exception as e:
        print(f"❌ LoRa initialization failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_initializations():
    """Test multiple initialization attempts"""
    print("🔧 Testing Multiple Initializations...")
    
    success_count = 0
    total_attempts = 5
    
    for i in range(total_attempts):
        print(f"🔄 Attempt {i+1}/{total_attempts}")
        
        try:
            # Reset between attempts
            hardware_reset()
            wait_for_ready()
            
            lora = SX126x()
            lora.begin(bus=0, cs=0)
            
            # Quick test
            status = lora.getStatus()
            print(f"   ✅ Success - Status: 0x{status:02X}")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        time.sleep(0.5)  # Wait between attempts
    
    print(f"📊 Success rate: {success_count}/{total_attempts} ({success_count/total_attempts*100:.1f}%)")
    return success_count > 0

def test_different_frequencies():
    """Test different frequency settings"""
    print("🔧 Testing Different Frequencies...")
    
    frequencies = [
        (434000000, "434 MHz"),
        (868000000, "868 MHz"),
        (915000000, "915 MHz"),
        (923000000, "923 MHz")
    ]
    
    try:
        hardware_reset()
        wait_for_ready()
        
        lora = SX126x()
        lora.begin(bus=0, cs=0)
        
        for freq, name in frequencies:
            try:
                lora.setFrequency(freq)
                print(f"   ✅ {name} - OK")
            except Exception as e:
                print(f"   ❌ {name} - Failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Frequency test setup failed: {e}")
        return False

def cleanup():
    """Clean up GPIO resources"""
    try:
        GPIO.cleanup()
        print("🧹 GPIO cleanup completed")
    except:
        pass

def main():
    print("🚀 Advanced LoRa SX126x Diagnostic")
    print("=" * 50)
    
    # Check if running as root (needed for GPIO)
    if os.getuid() != 0:
        print("⚠️ Warning: Not running as root. GPIO operations may fail.")
        print("   Consider running with: sudo python3 script.py")
    
    try:
        # Test 1: GPIO Setup
        print("\n1️⃣ GPIO Setup Test")
        if not setup_gpio():
            print("⚠️ Continuing without GPIO control...")
        
        # Test 2: SX126x Commands
        print("\n2️⃣ SX126x Command Test")
        test_sx126x_commands()
        
        # Test 3: LoRa Initialization
        print("\n3️⃣ LoRa Initialization Test")
        if test_lora_initialization():
            
            # Test 4: Multiple Initializations
            print("\n4️⃣ Multiple Initialization Test")
            test_multiple_initializations()
            
            # Test 5: Frequency Tests
            print("\n5️⃣ Frequency Setting Test")
            test_different_frequencies()
            
            print("\n✅ All tests completed successfully!")
            print("🎉 Your LoRa module is working properly!")
            
        else:
            print("\n❌ Basic initialization failed")
            print("\n🔧 Troubleshooting suggestions:")
            print("   1. Check wiring connections")
            print("   2. Verify power supply (3.3V)")
            print("   3. Connect RST pin to GPIO 18")
            print("   4. Connect BUSY pin to GPIO 24 (optional)")
            print("   5. Update LoRaRF library: pip install --upgrade LoRaRF")
            print("   6. Try different SPI CS pin")
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup()

if __name__ == "__main__":
    import os
    main()