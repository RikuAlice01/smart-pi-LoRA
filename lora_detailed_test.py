from LoRaRF import SX126x
import time
import spidev

def test_raw_spi():
    """Test raw SPI communication"""
    print("🔧 Testing Raw SPI...")
    
    try:
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1000000
        spi.mode = 0
        
        # Try to read a register (like device version)
        # SX126x command: Read register 0x0320 (version)
        cmd = [0x1D, 0x03, 0x20, 0x00]  # ReadRegister command
        response = spi.xfer2(cmd)
        print(f"✅ Raw SPI Response: {[hex(x) for x in response]}")
        
        spi.close()
        return True
        
    except Exception as e:
        print(f"❌ Raw SPI Failed: {e}")
        return False

def test_lora_with_delays():
    """Test LoRa initialization with delays"""
    print("🔧 Testing LoRa with Delays...")
    
    lora = SX126x()
    
    # Try with different delays
    delays = [0.1, 0.5, 1.0, 2.0]
    
    for delay in delays:
        try:
            print(f"⏳ Trying with {delay}s delay...")
            time.sleep(delay)
            
            lora.begin(bus=0, cs=0)
            print(f"✅ Success with {delay}s delay!")
            
            # Try to read status
            status = lora.getStatus()
            print(f"📊 Status: 0x{status:02X}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed with {delay}s delay: {e}")
    
    return False

def test_different_spi_settings():
    """Test different SPI configurations"""
    print("🔧 Testing Different SPI Settings...")
    
    lora = SX126x()
    
    # Different SPI configurations to try
    configs = [
        (0, 0, 1000000),  # Default
        (0, 0, 500000),   # Slower
        (0, 0, 2000000),  # Faster
        (0, 1, 1000000),  # Different CS
    ]
    
    for bus, cs, speed in configs:
        try:
            print(f"⚙️ Trying bus={bus}, cs={cs}, speed={speed}...")
            
            # Manual SPI setup
            import spidev
            spi = spidev.SpiDev()
            spi.open(bus, cs)
            spi.max_speed_hz = speed
            spi.mode = 0
            
            # Test basic communication
            test_cmd = [0x00]  # NOP command
            response = spi.xfer2(test_cmd)
            print(f"📡 Response: {[hex(x) for x in response]}")
            
            spi.close()
            
            # Try LoRa initialization
            lora.begin(bus=bus, cs=cs)
            print(f"✅ LoRa Success with bus={bus}, cs={cs}")
            return True
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    return False

def main():
    print("🚀 Detailed LoRa Hardware Test")
    print("=" * 40)
    
    # Test 1: Raw SPI
    if test_raw_spi():
        print("✅ Raw SPI works")
    else:
        print("❌ Raw SPI failed - check connections")
        return
    
    # Test 2: LoRa with delays
    if test_lora_with_delays():
        print("✅ LoRa works with delays")
        return
    
    # Test 3: Different SPI settings
    if test_different_spi_settings():
        print("✅ LoRa works with different settings")
        return
    
    print("\n❌ All tests failed")
    print("🔧 Possible issues:")
    print("   1. Wrong module type (not SX126x)")
    print("   2. Damaged module")
    print("   3. Incorrect wiring")
    print("   4. Power supply issues")
    print("   5. Need RST pin connection")

if __name__ == "__main__":
    main()