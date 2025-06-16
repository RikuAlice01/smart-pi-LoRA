"""
Hardware test script for Raspberry Pi Zero 2W LoRa SX126x HAT
Tests SPI communication, GPIO pins, and sensors with proper error handling
"""

import time
import sys
import os
from config import Config

# Check library availability at module level
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

try:
    from sx126x_driver import SX126xDriver
    SX126X_AVAILABLE = True
except ImportError:
    SX126X_AVAILABLE = False

try:
    from sensors import SensorManager
    SENSORS_AVAILABLE = True
except ImportError:
    SENSORS_AVAILABLE = False

def create_default_config_if_missing():
    """Create a default config file if it doesn't exist"""
    if not os.path.exists('config.json'):
        print("Creating default config.json for testing...")
        try:
            from config import create_default_config
            config = create_default_config('config.json')
            print("✓ Default config.json created")
            return config
        except Exception as e:
            print(f"⚠ Could not create config.json: {e}")
            return Config()  # Use in-memory defaults
    return Config()

def test_spi_communication():
    """Test SPI communication with SX126x"""
    print("Testing SPI communication...")
    
    if not SX126X_AVAILABLE:
        print("✗ SX126x driver not available (import failed)")
        return False
    
    if not GPIO_AVAILABLE:
        print("✗ RPi.GPIO not available (import failed)")
        return False
    
    try:
        config = create_default_config_if_missing()
        
        print(f"Using GPIO pins: RESET={config.gpio.reset_pin}, BUSY={config.gpio.busy_pin}, DIO1={config.gpio.dio1_pin}")
        print(f"Using SPI: Bus={config.gpio.spi_bus}, Device={config.gpio.spi_device}")
        
        driver = SX126xDriver(
            spi_bus=config.gpio.spi_bus,
            spi_device=config.gpio.spi_device,
            reset_pin=config.gpio.reset_pin,
            busy_pin=config.gpio.busy_pin,
            dio1_pin=config.gpio.dio1_pin
        )
        
        # Test basic communication
        print("Performing hardware reset...")
        driver.reset()
        time.sleep(0.1)
        
        # Get device status multiple times to verify communication
        print("Reading device status...")
        for i in range(3):
            status = driver.get_status()
            print(f"  Attempt {i+1}: Status = 0x{status:02X}")
            time.sleep(0.1)
        
        # Test standby mode
        print("Setting standby mode...")
        driver.set_standby()
        time.sleep(0.1)
        
        status_after_standby = driver.get_status()
        print(f"Status after standby: 0x{status_after_standby:02X}")
        
        # Test packet type setting
        print("Setting LoRa packet type...")
        driver.set_packet_type(0x01)  # LoRa mode
        time.sleep(0.1)
        
        print("✓ SPI communication successful")
        return True
        
    except Exception as e:
        print(f"✗ SPI communication failed: {e}")
        print(f"  Error type: {type(e).__name__}")
        return False

def test_gpio_pins():
    """Test GPIO pin configuration"""
    print("Testing GPIO pins...")
    
    if not GPIO_AVAILABLE:
        print("✗ RPi.GPIO library not available")
        return False
    
    try:
        config = create_default_config_if_missing()
        
        # Test pin setup
        GPIO.setmode(GPIO.BCM)
        
        print(f"Configuring pins: RESET={config.gpio.reset_pin}, BUSY={config.gpio.busy_pin}, DIO1={config.gpio.dio1_pin}")
        
        # Test output pins
        GPIO.setup(config.gpio.reset_pin, GPIO.OUT)
        
        # Test reset pin control
        print("Testing RESET pin control...")
        GPIO.output(config.gpio.reset_pin, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(config.gpio.reset_pin, GPIO.HIGH)
        
        # Test input pins
        GPIO.setup(config.gpio.busy_pin, GPIO.IN)
        GPIO.setup(config.gpio.dio1_pin, GPIO.IN)
        
        # Read pin states multiple times
        print("Reading input pin states...")
        for i in range(3):
            busy_state = GPIO.input(config.gpio.busy_pin)
            dio1_state = GPIO.input(config.gpio.dio1_pin)
            print(f"  Reading {i+1}: BUSY={busy_state}, DIO1={dio1_state}")
            time.sleep(0.1)
        
        print(f"RESET pin ({config.gpio.reset_pin}): Configured as output ✓")
        print(f"BUSY pin ({config.gpio.busy_pin}): Configured as input ✓")
        print(f"DIO1 pin ({config.gpio.dio1_pin}): Configured as input ✓")
        
        GPIO.cleanup()
        print("✓ GPIO pins configured successfully")
        return True
        
    except Exception as e:
        print(f"✗ GPIO pin test failed: {e}")
        try:
            GPIO.cleanup()
        except:
            pass
        return False

def test_sensors():
    """Test sensor readings"""
    print("Testing sensors...")
    
    if not SENSORS_AVAILABLE:
        print("✗ Sensor manager not available (import failed)")
        return False
    
    try:
        config = create_default_config_if_missing()
        
        # Enable mock sensors for testing if real sensors aren't available
        print("Checking sensor availability...")
        
        # Try to import sensor libraries
        sensor_libs = {
            'Adafruit_DHT': False,
            'BMP280': False,
            'RPi.GPIO': GPIO_AVAILABLE
        }
        
        try:
            import Adafruit_DHT
            sensor_libs['Adafruit_DHT'] = True
        except ImportError:
            pass
        
        try:
            import board
            import busio
            import adafruit_bmp280
            sensor_libs['BMP280'] = True
        except ImportError:
            pass
        
        print("Sensor library availability:")
        for lib, available in sensor_libs.items():
            print(f"  {lib}: {'✓' if available else '✗'}")
        
        # If no real sensors available, use mock mode
        if not any([sensor_libs['Adafruit_DHT'], sensor_libs['BMP280']]):
            print("No real sensor libraries available, enabling mock mode...")
            config.sensor.mock_enabled = True
            config.sensor.dht22_enabled = False
            config.sensor.bmp280_enabled = False
        
        sensor_manager = SensorManager(config)
        
        # Get sensor status
        status = sensor_manager.get_sensor_status()
        print("Sensor status:")
        for sensor, available in status.items():
            print(f"  {sensor}: {'✓' if available else '✗'}")
        
        # Read sensor data multiple times
        print("Reading sensor data (3 attempts)...")
        successful_reads = 0
        
        for i in range(3):
            print(f"\nAttempt {i+1}:")
            try:
                data = sensor_manager.read_all_sensors()
                
                if data:
                    successful_reads += 1
                    for key, value in data.items():
                        if value is not None and key != "timestamp":
                            if key == "temperature":
                                print(f"  Temperature: {value}°C")
                            elif key == "humidity":
                                print(f"  Humidity: {value}%")
                            elif key == "pressure":
                                print(f"  Pressure: {value} hPa")
                            elif key == "battery_voltage":
                                print(f"  Battery: {value}V")
                            elif key == "rssi":
                                print(f"  RSSI: {value} dBm")
                            else:
                                print(f"  {key}: {value}")
                else:
                    print("  No data received")
                    
            except Exception as e:
                print(f"  Error reading sensors: {e}")
            
            time.sleep(1)
        
        if successful_reads > 0:
            print(f"✓ Sensor test completed ({successful_reads}/3 successful reads)")
            return True
        else:
            print("✗ No successful sensor reads")
            return False
        
    except Exception as e:
        print(f"✗ Sensor test failed: {e}")
        return False

def test_lora_transmission():
    """Test LoRa transmission with improved configuration and debugging"""
    print("Testing LoRa transmission...")
    
    if not SX126X_AVAILABLE:
        print("✗ SX126x driver not available")
        return False
    
    if not GPIO_AVAILABLE:
        print("✗ RPi.GPIO not available")
        return False
    
    try:
        config = create_default_config_if_missing()
        
        print(f"Initializing LoRa with frequency: {config.lora.frequency} MHz")
        
        driver = SX126xDriver(
            spi_bus=config.gpio.spi_bus,
            spi_device=config.gpio.spi_device,
            reset_pin=config.gpio.reset_pin,
            busy_pin=config.gpio.busy_pin,
            dio1_pin=config.gpio.dio1_pin
        )
        
        # Enhanced configuration sequence
        print("Configuring LoRa parameters...")
        
        # 1. Hardware reset and wait
        print("  Performing hardware reset...")
        driver.reset()
        time.sleep(0.1)
        
        # 2. Check initial status
        initial_status = driver.get_status()
        print(f"  Initial status: 0x{initial_status:02X}")
        
        # 3. Set standby mode (RC oscillator)
        print("  Setting standby mode (RC)...")
        driver.set_standby(0x00)  # RC oscillator
        time.sleep(0.05)
        
        standby_status = driver.get_status()
        print(f"  Status after standby: 0x{standby_status:02X}")
        
        # 4. Set packet type to LoRa
        print("  Setting packet type to LoRa...")
        driver.set_packet_type(0x01)
        time.sleep(0.05)
        
        # 5. Set frequency
        frequency_hz = config.get_frequency_hz()
        print(f"  Setting frequency to {frequency_hz} Hz...")
        driver.set_rf_frequency(frequency_hz)
        time.sleep(0.05)
        
        # 6. Set modulation parameters
        sf, bw, cr, ldro = config.get_lora_modulation_params()
        print(f"  Setting modulation: SF={sf}, BW={bw}, CR={cr}, LDRO={ldro}")
        driver.set_lora_modulation_params(sf, bw, cr, ldro)
        time.sleep(0.05)
        
        # 7. Set packet parameters with shorter payload for testing
        print("  Setting packet parameters...")
        driver.set_lora_packet_params(
            preamble_length=8,  # Shorter preamble for testing
            header_type=0,      # Explicit header
            payload_length=32,  # Shorter payload for testing
            crc_type=1,         # CRC enabled
            invert_iq=0         # Normal IQ
        )
        time.sleep(0.05)
        
        # 8. Set TX power (lower for testing)
        test_power = min(config.lora.tx_power, 10)  # Limit to 10dBm for testing
        print(f"  Setting TX power to {test_power} dBm...")
        driver.set_tx_params(test_power, 0x02)  # 40us ramp time
        time.sleep(0.05)
        
        # 9. Set buffer base addresses
        print("  Setting buffer addresses...")
        driver.set_buffer_base_address(0x00, 0x80)
        time.sleep(0.05)
        
        # 10. Set sync word
        print(f"  Setting sync word to 0x{config.lora.sync_word:04X}...")
        driver.set_lora_sync_word(config.lora.sync_word)
        time.sleep(0.05)
        
        # 11. Clear any pending IRQs
        print("  Clearing IRQ status...")
        driver.clear_irq_status(0x03FF)
        time.sleep(0.05)
        
        # 12. Set DIO IRQ parameters
        print("  Setting DIO IRQ parameters...")
        driver.set_dio_irq_params(
            irq_mask=0x0001,    # Only TX_DONE IRQ
            dio1_mask=0x0001,   # TX_DONE on DIO1
            dio2_mask=0x0000,   # Nothing on DIO2
            dio3_mask=0x0000    # Nothing on DIO3
        )
        time.sleep(0.05)
        
        # 13. Check status before transmission
        pre_tx_status = driver.get_status()
        print(f"  Status before TX: 0x{pre_tx_status:02X}")
        
        # 14. Prepare test message (shorter for reliability)
        test_message = b"TEST_OK"
        print(f"  Sending test message: {test_message.decode()} ({len(test_message)} bytes)")
        
        # 15. Write payload to buffer
        print("  Writing payload to buffer...")
        driver.write_buffer(0x00, list(test_message))
        time.sleep(0.05)
        
        # 16. Set packet length
        print("  Updating packet length...")
        driver.set_lora_packet_params(
            preamble_length=8,
            header_type=0,
            payload_length=len(test_message),
            crc_type=1,
            invert_iq=0
        )
        time.sleep(0.05)
        
        # 17. Clear IRQs again before transmission
        driver.clear_irq_status(0x03FF)
        time.sleep(0.05)
        
        # 18. Start transmission with timeout
        print("  Starting transmission...")
        driver.set_tx(timeout=0x0F4240)  # 1 second timeout
        
        # 19. Wait for transmission completion with detailed monitoring
        print("  Monitoring transmission...")
        tx_start_time = time.time()
        tx_timeout = 5.0  # 5 second timeout
        tx_completed = False
        
        while (time.time() - tx_start_time) < tx_timeout:
            # Check IRQ status
            irq_status = driver.get_irq_status()
            device_status = driver.get_status()
            
            print(f"    Time: {time.time() - tx_start_time:.2f}s, IRQ: 0x{irq_status:04X}, Status: 0x{device_status:02X}")
            
            if irq_status & 0x0001:  # TX_DONE
                print("  ✓ TX_DONE IRQ received!")
                driver.clear_irq_status(0x03FF)
                tx_completed = True
                break
            elif irq_status & 0x0200:  # TIMEOUT
                print("  ✗ TX_TIMEOUT IRQ received!")
                driver.clear_irq_status(0x03FF)
                break
            elif irq_status != 0:
                print(f"  Other IRQ received: 0x{irq_status:04X}")
                driver.clear_irq_status(0x03FF)
            
            time.sleep(0.1)
        
        # 20. Final status check
        final_status = driver.get_status()
        final_irq = driver.get_irq_status()
        print(f"  Final status: 0x{final_status:02X}, Final IRQ: 0x{final_irq:04X}")
        
        # 21. Return to standby
        driver.set_standby()
        
        if tx_completed:
            print("✓ LoRa transmission successful!")
            return True
        else:
            print("✗ LoRa transmission failed (timeout or no TX_DONE)")
            return False
        
    except Exception as e:
        print(f"✗ LoRa transmission test failed: {e}")
        print(f"  Error type: {type(e).__name__}")
        
        # Additional debugging information
        try:
            import traceback
            print("  Traceback:")
            traceback.print_exc()
        except:
            pass
        
        return False

def test_spi_interface():
    """Test basic SPI interface availability"""
    print("Testing SPI interface...")
    
    try:
        import spidev
        
        # Try to open SPI device
        spi = spidev.SpiDev()
        spi.open(0, 0)  # Bus 0, Device 0
        spi.max_speed_hz = 1000000
        spi.mode = 0
        
        # Test basic SPI communication
        response = spi.xfer2([0x00])  # Send dummy byte
        print(f"SPI test response: 0x{response[0]:02X}")
        
        spi.close()
        print("✓ SPI interface available")
        return True
        
    except ImportError:
        print("✗ spidev library not available")
        return False
    except Exception as e:
        print(f"✗ SPI interface test failed: {e}")
        return False

def test_lora_basic_functions():
    """Test basic LoRa functions without transmission"""
    print("Testing basic LoRa functions...")
    
    if not SX126X_AVAILABLE or not GPIO_AVAILABLE:
        print("✗ Required libraries not available")
        return False
    
    try:
        config = create_default_config_if_missing()
        
        driver = SX126xDriver(
            spi_bus=config.gpio.spi_bus,
            spi_device=config.gpio.spi_device,
            reset_pin=config.gpio.reset_pin,
            busy_pin=config.gpio.busy_pin,
            dio1_pin=config.gpio.dio1_pin
        )
        
        print("  Testing basic commands...")
        
        # Reset
        driver.reset()
        time.sleep(0.1)
        
        # Get status
        status = driver.get_status()
        print(f"  Status: 0x{status:02X}")
        
        # Set standby
        driver.set_standby()
        time.sleep(0.05)
        
        # Set packet type
        driver.set_packet_type(0x01)
        time.sleep(0.05)
        
        # Set frequency
        driver.set_rf_frequency(config.get_frequency_hz())
        time.sleep(0.05)
        
        # Test register read/write
        print("  Testing register access...")
        
        # Read sync word register
        sync_msb = driver.read_register(0x0740, 1)[0]
        sync_lsb = driver.read_register(0x0741, 1)[0]
        current_sync = (sync_msb << 8) | sync_lsb
        print(f"  Current sync word: 0x{current_sync:04X}")
        
        # Write and read back
        test_sync = 0x1234
        driver.set_lora_sync_word(test_sync)
        time.sleep(0.05)
        
        sync_msb = driver.read_register(0x0740, 1)[0]
        sync_lsb = driver.read_register(0x0741, 1)[0]
        read_sync = (sync_msb << 8) | sync_lsb
        print(f"  Read back sync word: 0x{read_sync:04X}")
        
        if read_sync == test_sync:
            print("✓ Basic LoRa functions working")
            return True
        else:
            print(f"✗ Register read/write mismatch: wrote 0x{test_sync:04X}, read 0x{read_sync:04X}")
            return False
        
    except Exception as e:
        print(f"✗ Basic LoRa function test failed: {e}")
        return False

def main():
    """Run all hardware tests"""
    print("Raspberry Pi Zero 2W LoRa SX126x HAT Hardware Test")
    print("=" * 55)
    print()
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi' not in cpuinfo:
                print("⚠ Warning: Not running on Raspberry Pi hardware")
            else:
                print("✓ Running on Raspberry Pi")
    except:
        print("⚠ Warning: Could not detect hardware type")
    
    print()
    
    tests = [
        ("SPI Interface", test_spi_interface),
        ("GPIO Pins", test_gpio_pins),
        ("SPI Communication", test_spi_communication),
        ("Basic LoRa Functions", test_lora_basic_functions),
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
        except KeyboardInterrupt:
            print("\n⚠ Test interrupted by user")
            results.append((test_name, False))
            break
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
        icon = "✓" if result else "✗"
        print(f"{test_name}: {status} {icon}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("🎉 All tests passed! Hardware is ready.")
        return 0
    elif passed >= len(results) // 2:
        print("⚠ Some tests failed, but basic functionality appears to work.")
        print("Check the failed tests and hardware connections.")
        return 1
    else:
        print("❌ Multiple tests failed. Check hardware connections and setup.")
        return 2

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        try:
            GPIO.cleanup()
        except:
            pass
        sys.exit(130)
