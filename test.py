import board
import busio
import digitalio
import adafruit_rfm9x

try:
    # กำหนด SPI
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    
    # กำหนด pins สำหรับ SX126x HAT (ปรับตามของจริง)
    cs = digitalio.DigitalInOut(board.D8)    # GPIO8 (CE0)
    reset = digitalio.DigitalInOut(board.D22) # GPIO22
    
    print("Initializing RFM9x...")
    
    # ลองความถี่ที่เหมาะสมกับไทย
    rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915.0)  # 923MHz
    
    print("RFM9x initialized successfully!")
    print(f"Frequency: {rfm9x.frequency_mhz} MHz")
    
except Exception as e:
    print(f"Error: {e}")