import board
import busio
import digitalio
import time

print("Testing SPI connection...")

try:
    # ทดสอบ SPI
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    print("✓ SPI initialized")
    
    # ทดสอบ GPIO pins ต่างๆ
    pin_configs = [
        {"name": "CS (GPIO8)", "pin": board.D8},
        {"name": "CS (GPIO7)", "pin": board.D7},
        {"name": "RST (GPIO22)", "pin": board.D22},
        {"name": "RST (GPIO25)", "pin": board.D25},
    ]
    
    for config in pin_configs:
        try:
            pin = digitalio.DigitalInOut(config["pin"])
            pin.direction = digitalio.Direction.OUTPUT
            print(f"✓ {config['name']} - OK")
            pin.deinit()
        except Exception as e:
            print(f"✗ {config['name']} - Error: {e}")
    
    print("\nTrying RFM9x initialization with different pin combinations...")
    
    # ลองหลายแบบ
    combinations = [
        {"cs": board.D8, "rst": board.D22, "name": "GPIO8/GPIO22"},
        {"cs": board.D7, "rst": board.D25, "name": "GPIO7/GPIO25"},
        {"cs": board.CE1, "rst": board.D22, "name": "CE1/GPIO22"},
    ]
    
    import adafruit_rfm9x
    
    for combo in combinations:
        try:
            print(f"\nTrying {combo['name']}...")
            cs = digitalio.DigitalInOut(combo["cs"])
            reset = digitalio.DigitalInOut(combo["rst"])
            
            rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 923.0)
            print(f"✓ SUCCESS with {combo['name']}!")
            print(f"Frequency: {rfm9x.frequency_mhz} MHz")
            break
            
        except Exception as e:
            print(f"✗ Failed with {combo['name']}: {e}")
    
except Exception as e:
    print(f"Error: {e}")