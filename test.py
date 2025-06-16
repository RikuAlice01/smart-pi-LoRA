import board
import busio
import digitalio
import adafruit_rfm9x

# กำหนด SPI และ pins
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.CE1)
reset = digitalio.DigitalInOut(board.D25)

# สร้าง RFM object
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915.0)  # ความถี่ 915MHz

# ส่งข้อมูล
rfm9x.send(bytes("Hello World!", "utf-8"))

# รับข้อมูล
packet = rfm9x.receive()
if packet is not None:
    print(f"Received: {packet}")