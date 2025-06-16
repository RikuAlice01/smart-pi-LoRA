import time
from LoRaRF import SX126x
import spidev

# สร้าง SPI object
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI bus 0, device 0
spi.max_speed_hz = 1000000

# กำหนด GPIO pins สำหรับ SX126x HAT
# ปรับตามการเชื่อมต่อจริงของ HAT
pin_config = {
    'reset': 22,    # GPIO22
    'busy': 23,     # GPIO23  
    'dio1': 24,     # GPIO24
    'cs': 8         # GPIO8 (CE0)
}

# สร้าง SX126x object
lora = SX126x()

try:
    print("Initializing SX126x...")
    
    # กำหนดค่าเริ่มต้น
    lora.begin(spi=spi, 
              cs=pin_config['cs'],
              reset=pin_config['reset'], 
              busy=pin_config['busy'],
              dio1=pin_config['dio1'])
    
    print("✓ SX126x initialized successfully!")
    
    # ตั้งค่าพื้นฐาน
    lora.setStandby(SX126x.STDBY_RC)                    # Standby mode
    lora.setPacketType(SX126x.LORA_MODEM)              # LoRa packet
    lora.setRfFrequency(925000000)                      # 923 MHz สำหรับไทย
    lora.setTxParams(14, SX126x.PA_RAMP_200U)          # TX power 14dBm
    lora.setBufferBaseAddress(0x00, 0x00)              # TX/RX buffer
    
    # ตั้งค่า LoRa modulation
    lora.setModulationParams(SX126x.LORA_SF7,          # Spreading Factor 7
                            SX126x.LORA_BW_125,        # Bandwidth 125kHz  
                            SX126x.LORA_CR_4_5)        # Coding Rate 4/5
    
    # ตั้งค่า packet
    lora.setPacketParams(8,                            # Preamble length
                        SX126x.LORA_HEADER_EXPLICIT,   # Header mode
                        255,                           # Payload length
                        SX126x.LORA_CRC_ON,           # CRC on
                        SX126x.LORA_IQ_NORMAL)        # IQ normal
    
    print("✓ Configuration complete!")
    print(f"Frequency: {lora.getRfFrequency()/1000000} MHz")
    
except Exception as e:
    print(f"Error: {e}")
    print("กรุณาตรวจสอบการเชื่อมต่อ GPIO pins")

def send_message(lora, message):
    try:
        # แปลง string เป็น bytes
        data = bytearray(message.encode())
        
        # เขียนข้อมูลลง buffer
        lora.writeBuffer(0x00, data)
        
        # ตั้งค่า payload length
        lora.setPacketParams(8, SX126x.LORA_HEADER_EXPLICIT, 
                           len(data), SX126x.LORA_CRC_ON, 
                           SX126x.LORA_IQ_NORMAL)
        
        # ส่งข้อมูล
        lora.setTx(3000)  # timeout 3 วินาที
        
        print(f"Sent: {message}")
        return True
        
    except Exception as e:
        print(f"Send error: {e}")
        return False

# ทดสอบส่งข้อมูล
send_message(lora, "Hello from Pi Zero 2W!")