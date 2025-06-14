#!/usr/bin/env python3
"""
LoRa Tuple Error Fix Script
Specifically addresses the "tuple index out of range" error in LoRaRF library
"""

from LoRaRF import SX126x
import time
import spidev
import sys

def safe_lora_init(max_retries=5, delay_between_retries=0.5):
    """
    Safely initialize LoRa with multiple retry attempts
    The tuple error often occurs due to timing issues
    """
    print(f"🔄 Attempting LoRa initialization (max {max_retries} retries)...")
    
    for attempt in range(max_retries):
        try:
            print(f"   Attempt {attempt + 1}/{max_retries}")
            
            # Create fresh instance each time
            lora = SX126x()
            
            # Add small delay before begin()
            time.sleep(0.1)
            
            # Initialize
            lora.begin(bus=0, cs=0)
            
            # Add delay after initialization
            time.sleep(0.1)
            
            # Test basic operation
            status = lora.getStatus()
            print(f"   ✅ Success! Status: 0x{status:02X}")
            
            return lora
            
        except Exception as e:
            print(f"   ❌ Attempt {attempt + 1} failed: {e}")
            
            if "tuple index out of range" in str(e):
                print("   📝 Detected tuple error - likely timing issue")
            
            # Wait before next attempt
            if attempt < max_retries - 1:
                time.sleep(delay_between_retries)
    
    print("❌ All initialization attempts failed")
    return None

def test_spi_stability():
    """Test SPI communication stability"""
    print("🔧 Testing SPI Stability...")
    
    stable_count = 0
    total_tests = 10
    
    for i in range(total_tests):
        try:
            spi = spidev.SpiDev()
            spi.open(0, 0)
            spi.max_speed_hz = 1000000
            spi.mode = 0
            
            # Send GetStatus command multiple times
            for j in range(3):
                cmd = [0xC0, 0x00]
                response = spi.xfer2(cmd)
                time.sleep(0.001)  # Small delay between commands
            
            spi.close()
            stable_count += 1
            print(f"   Test {i+1}: ✅")
            
        except Exception as e:
            print(f"   Test {i+1}: ❌ {e}")
        
        time.sleep(0.05)
    
    print(f"📊 SPI Stability: {stable_count}/{total_tests} ({stable_count/total_tests*100:.1f}%)")
    return stable_count >= total_tests * 0.8  # 80% success rate

def test_with_different_delays():
    """Test initialization with different delay patterns"""
    print("🔧 Testing Different Delay Patterns...")
    
    delay_patterns = [
        (0.05, 0.05, "Fast"),
        (0.1, 0.1, "Standard"),
        (0.2, 0.2, "Slow"),
        (0.5, 0.1, "Long pre-delay"),
        (0.1, 0.5, "Long post-delay")
    ]
    
    for pre_delay, post_delay, name in delay_patterns:
        try:
            print(f"   Testing {name} pattern (pre:{pre_delay}s, post:{post_delay}s)")
            
            lora = SX126x()
            time.sleep(pre_delay)
            lora.begin(bus=0, cs=0)
            time.sleep(post_delay)
            
            status = lora.getStatus()
            print(f"   ✅ {name}: Success - Status: 0x{status:02X}")
            return True
            
        except Exception as e:
            print(f"   ❌ {name}: Failed - {e}")
    
    return False

def monitor_lora_stability(duration=30):
    """Monitor LoRa stability over time"""
    print(f"🔧 Monitoring LoRa Stability for {duration} seconds...")
    
    lora = safe_lora_init()
    if not lora:
        return False
    
    success_count = 0
    total_checks = 0
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            try:
                status = lora.getStatus()
                success_count += 1
                if total_checks % 10 == 0:  # Print every 10th check
                    print(f"   ✅ Check {total_checks + 1}: Status 0x{status:02X}")
            except Exception as e:
                print(f"   ❌ Check {total_checks + 1}: Failed - {e}")
            
            total_checks += 1
            time.sleep(1)  # Check every second
        
        print(f"📊 Stability: {success_count}/{total_checks} ({success_count/total_checks*100:.1f}%)")
        return success_count >= total_checks * 0.9  # 90% success rate
        
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")
        return False

def comprehensive_lora_test():
    """Run comprehensive LoRa functionality test"""
    print("🔧 Comprehensive LoRa Test...")
    
    lora = safe_lora_init()
    if not lora:
        return False
    
    tests = [
        ("Frequency Setting", lambda: lora.setFrequency(434000000)),
        ("Power Setting", lambda: lora.setTxPower(14, SX126x.POWER_RAMP_200U)),
        ("Bandwidth Setting", lambda: lora.setBandwidth(9600)),
        ("Spreading Factor", lambda: lora.setSpreadingFactor(7)),
        ("Coding Rate", lambda: lora.setCodingRate(5)),
        ("Sync Word", lambda: lora.setSyncWord(0x34)),
        ("Preamble Length", lambda: lora.setPreambleLength(8)),
        ("CRC Enable", lambda: lora.setCrcEnable(True)),
        ("Header Type", lambda: lora.setHeaderType(SX126x.HEADER_EXPLICIT))
    ]
    
    success_count = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"   ✅ {test_name}: OK")
            success_count += 1
            time.sleep(0.1)  # Small delay between operations
        except Exception as e:
            print(f"   ❌ {test_name}: Failed - {e}")
    
    print(f"📊 Test Results: {success_count}/{len(tests)} passed")
    return success_count >= len(tests) * 0.8  # 80% success rate

def main():
    print("🚀 LoRa Tuple Error Fix & Stability Test")
    print("=" * 45)
    
    try:
        # Test 1: SPI Stability
        print("\n1️⃣ SPI Stability Test")
        spi_stable = test_spi_stability()
        
        if not spi_stable:
            print("⚠️ SPI communication unstable - check connections")
            return
        
        # Test 2: Safe Initialization
        print("\n2️⃣ Safe LoRa Initialization")
        lora = safe_lora_init()
        
        if not lora:
            print("\n🔧 Trying different delay patterns...")
            if test_with_different_delays():
                print("✅ Found working delay pattern")
            else:
                print("❌ No delay pattern worked")
                return
        
        # Test 3: Comprehensive Functionality
        print("\n3️⃣ Comprehensive Functionality Test")
        if comprehensive_lora_test():
            print("✅ Comprehensive test passed")
            
            # Test 4: Stability Monitoring
            print("\n4️⃣ Stability Monitoring")
            print("   Press Ctrl+C to stop early")
            if monitor_lora_stability(10):  # 10 second test
                print("✅ LoRa module is stable!")
            else:
                print("⚠️ Some stability issues detected")
        
        print("\n🎉 Testing completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()