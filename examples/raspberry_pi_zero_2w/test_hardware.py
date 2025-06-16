"""
Hardware test script for Raspberry Pi Zero 2W LoRa SX126x HAT
Tests SPI communication, GPIO pins, and sensors
"""

import time
import sys
from config import Config
from sx126x_driver import SX126xDriver
from sensors import SensorManager

def test_spi_communication():
    """Test SPI communication with SX126x"""
    print("Testing SPI communication...")
    
    try:
        config = Config()
        driver = SX126xDriver(
            spi_bus=config.gpio.spi_bus,
            spi_device=config.gpio.spi_device,
            reset_pin=config.gpio.reset_pin,
            busy_pin=config.gpio.busy_pin,
            dio1_pin=config.gpio.dio1_pin
        )
        
        # Get device status
        status = driver.get_status()
        print(f"SX126x Status: 0x{status:02X}")
        
        # Test basic configuration
        driver.set_standby()
        driver.set_packet_type(0x01)  # LoRa mode
        
        print("✓ SPI communication successful")
        return True
        
    except Exception as e:
        print(f"✗ SPI communication failed: {e}")
        return False

def test_gpio_pins():
    """Test GPIO pin configuration"""
    print("Testing GPIO pins...")
    
    try:
        import RPi.GPIO as GPIO
        
        config = Config()
        
        # Test pin setup
        GPIO.setmode(GPIO.BCM)
        
        # Test output pins
        GPIO.setup(config.gpio.reset_pin, GPIO.OUT)
        GPIO.output(config.gpio.reset_pin, GPIO.HIGH)
        
        # Test input pins
        GPIO.setup(config.gpio.busy_pin, GPIO.IN)
        GPIO.setup(config.gpio.dio1_pin, GPIO.IN)
        
        busy_state = GPIO.input(config.gpio.busy_pin)
        dio1_state = GPIO.input(config.gpio.dio1_pin)
        
        print(f"RESET pin ({config.gpio.reset_pin}): Configured as output")
        print(f"BUSY pin ({config.gpio.busy_pin}): {busy_state}")
        print(f"DIO1 pin ({config.gpio.dio1_pin}): {dio1_state}")
        
        GPIO.cleanup()
        print("✓ GPIO pins configured successfully")
        return True
        
    except Exception as e:
        print(f"✗ GPIO pin test failed: {e}")
        return False

def test_sensors():
    """Test sensor readings"""
    print("Testing sensors...")
    
    try:
        config = Config()
        sensor_manager = SensorManager(config)
        
        # Get sensor status
        status = sensor_manager.get_sensor_status()
        print("Sensor availability:")
        for sensor, available in status.items():
            print(f"  {sensor}: {'✓' if available else '✗'}")
        
        # Read sensor data
        print("Reading sensor data...")
        data = sensor_manager.read_all_sensors()
        
        for key, value in data.items():
            if value is not None and key != "timestamp":
                print(f"  {key}: {value}")
        
        print("✓ Sensor test completed")
        return True
        
    except Exception as e:
        print(f"✗ Sensor test failed: {e}")
        return False

def test_lora_transmission():
    """Test LoRa transmission"""
    print("Testing LoRa transmission...")
    
    try:
        config = Config()
        driver = SX126xDriver(
            spi_bus=config.gpio.spi_bus,
            spi_device=config.gpio.spi_device,
            reset_pin=config.gpio.reset_pin,
            busy_pin=config.gpio.busy_pin,
            dio1_pin=config.gpio.dio1_pin
        )
        
        # Configure LoRa
        driver.set_standby()
        driver.set_packet_type(0x01)
        driver.set_rf_frequency(config.get_frequency_hz())
        
        sf, bw, cr, ldro = config.get_lora_modulation_params()
        driver.set_lora_modulation_params(sf, bw, cr, ldro)
        
        driver.set_lora_packet_params(
            preamble_length=config.lora.preamble_length,
            header_type=0,
            payload_length=255,
            crc_type=1,
            invert_iq=0
        )
        
        driver.set_tx_params(config.lora.tx_power)
        driver.set_buffer_base_address(0x00, 0x80)
        
        # Send test message
        test_message = b"Hello from Raspberry Pi LoRa!"
        success = driver.send_payload(test_message)
        
        if success:
            print("✓ LoRa transmission successful")
            return True
        else:
            print("✗ LoRa transmission failed")
            return False
        
    except Exception as e:
        print(f"✗ LoRa transmission test failed: {e}")
        return False

def main():
    """Run all hardware tests"""
    print("Raspberry Pi Zero 2W LoRa SX126x HAT Hardware Test")
    print("=" * 55)
    print()
    
    tests = [
        ("GPIO Pins", test_gpio_pins),
        ("SPI Communication", test_spi_communication),
        ("Sensors", test_sensors),
        ("LoRa Transmission", test_lora_transmission)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
        
        print()
        time.sleep(1)
    
    # Print summary
    print("Test Summary")
    print("=" * 20)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("✓ All tests passed! Hardware is ready.")
        return 0
    else:
        print("✗ Some tests failed. Check hardware connections.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
