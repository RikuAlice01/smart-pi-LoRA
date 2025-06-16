from LoRa import *
from machine import Pin, SPI
import time

# ตั้งค่า SPI
spi = SPI(0, baudrate=1000000, polarity=0, phase=0)
lora = LoRa(spi, cs=Pin(8), rst=Pin(22), dio=Pin(23))

try:
    lora.init()
    print("LoRa initialized successfully!")
except Exception as e:
    print(f"Error: {e}")