import time
from LoRaRF import SX126x

# การตั้งค่า pins
busId = 0
csId = 0
resetPin = 22
busyPin = 23
irqPin = 24
txenPin = -1
rxenPin = -1

# สร้างและเริ่มต้น LoRa
LoRa = SX126x()
begin = LoRa.begin(busId, csId, resetPin, busyPin, irqPin, txenPin, rxenPin)

if begin:
    print("SX126x initialized for sending")
    LoRa.LoRaConfig(923000000, 500000, 9, 7, 8, 14)
    
    message = "Hello from Pi Zero 2W!"
    counter = 0
    
    try:
        while True:
            # เตรียมข้อมูล
            data = f"{message} #{counter}"
            print(f"Sending: {data}")
            
            # ส่งข้อมูล
            LoRa.beginPacket()
            LoRa.put(data)
            LoRa.endPacket()
            
            counter += 1
            time.sleep(5)  # ส่งทุก 5 วินาที
            
    except KeyboardInterrupt:
        print("\nStopping sender...")
        
else:
    print("SX126x initialization failed!")