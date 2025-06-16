"""
SX126x LoRa Driver for Raspberry Pi
Low-level driver for SX1261/SX1262/SX1268 LoRa transceivers over SPI
"""

import time
import spidev
import RPi.GPIO as GPIO
from typing import List, Optional, Tuple
from enum import IntEnum

class SX126xCommands(IntEnum):
    """SX126x command definitions"""
    # Operational Modes Functions
    SET_SLEEP = 0x84
    SET_STANDBY = 0x80
    SET_FS = 0x8C
    SET_TX = 0x83
    SET_RX = 0x82
    SET_RXDUTYCYCLE = 0x94
    SET_CAD = 0xC5
    
    # Registers and buffer Access
    WRITE_REGISTER = 0x0D
    READ_REGISTER = 0x1D
    WRITE_BUFFER = 0x0E
    READ_BUFFER = 0x1E
    
    # DIO and IRQ Control Functions
    SET_DIOIRQPARAMS = 0x08
    GET_IRQSTATUS = 0x12
    CLR_IRQSTATUS = 0x02
    SET_DIO2ASRFSWITCHCTRL = 0x9D
    SET_DIO3ASTCXOCTRL = 0x97
    
    # RF Modulation and Packet-Related Functions
    SET_RFFREQUENCY = 0x86
    SET_PACKETTYPE = 0x8A
    GET_PACKETTYPE = 0x11
    SET_TXPARAMS = 0x8E
    SET_MODULATIONPARAMS = 0x8B
    SET_PACKETPARAMS = 0x8C
    SET_CADPARAMS = 0x88
    SET_BUFFERBASEADDRESS = 0x8F
    SET_LORASYMBNUMTIMEOUT = 0xA0
    
    # Communication Status Information
    GET_STATUS = 0xC0
    GET_RSSIINST = 0x15
    GET_RXBUFFERSTATUS = 0x13
    GET_PACKETSTATUS = 0x14
    GET_DEVICEERRORS = 0x17
    CLR_DEVICEERRORS = 0x07
    GET_STATS = 0x10
    RESET_STATS = 0x00

class SX126xRegisters(IntEnum):
    """SX126x register addresses"""
    REG_WHITENING_INITIAL_MSB = 0x06B8
    REG_WHITENING_INITIAL_LSB = 0x06B9
    REG_CRC_INITIAL_MSB = 0x06BC
    REG_CRC_INITIAL_LSB = 0x06BD
    REG_CRC_POLYNOMIAL_MSB = 0x06BE
    REG_CRC_POLYNOMIAL_LSB = 0x06BF
    REG_SYNC_WORD_0 = 0x06C0
    REG_SYNC_WORD_1 = 0x06C1
    REG_SYNC_WORD_2 = 0x06C2
    REG_SYNC_WORD_3 = 0x06C3
    REG_SYNC_WORD_4 = 0x06C4
    REG_SYNC_WORD_5 = 0x06C5
    REG_SYNC_WORD_6 = 0x06C6
    REG_SYNC_WORD_7 = 0x06C7
    REG_NODE_ADDRESS = 0x06CD
    REG_BROADCAST_ADDRESS = 0x06CE
    REG_LORA_SYNC_WORD_MSB = 0x0740
    REG_LORA_SYNC_WORD_LSB = 0x0741
    REG_RANDOM_NUMBER_0 = 0x0819
    REG_RANDOM_NUMBER_1 = 0x081A
    REG_RANDOM_NUMBER_2 = 0x081B
    REG_RANDOM_NUMBER_3 = 0x081C
    REG_TX_MODULATION = 0x0889
    REG_RX_GAIN = 0x08AC
    REG_TX_CLAMP_CONFIG = 0x08D8
    REG_OCP_CONFIGURATION = 0x08E7
    REG_RTC_CONTROL = 0x0902
    REG_XTA_TRIM = 0x0911
    REG_XTB_TRIM = 0x0912

class SX126xIRQ(IntEnum):
    """SX126x IRQ mask definitions"""
    IRQ_TX_DONE = 0x01
    IRQ_RX_DONE = 0x02
    IRQ_PREAMBLE_DETECTED = 0x04
    IRQ_SYNC_WORD_VALID = 0x08
    IRQ_HEADER_VALID = 0x10
    IRQ_HEADER_ERROR = 0x20
    IRQ_CRC_ERROR = 0x40
    IRQ_CAD_DONE = 0x80
    IRQ_CAD_DETECTED = 0x100
    IRQ_TIMEOUT = 0x200
    IRQ_ALL = 0x3FF

class SX126xDriver:
    """SX126x LoRa driver class"""
    
    def __init__(self, spi_bus=0, spi_device=0, reset_pin=22, busy_pin=23, dio1_pin=24):
        """
        Initialize SX126x driver
        
        Args:
            spi_bus: SPI bus number (0 or 1)
            spi_device: SPI device number (0 or 1)
            reset_pin: GPIO pin for RESET
            busy_pin: GPIO pin for BUSY
            dio1_pin: GPIO pin for DIO1
        """
        self.spi_bus = spi_bus
        self.spi_device = spi_device
        self.reset_pin = reset_pin
        self.busy_pin = busy_pin
        self.dio1_pin = dio1_pin
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.reset_pin, GPIO.OUT)
        GPIO.setup(self.busy_pin, GPIO.IN)
        GPIO.setup(self.dio1_pin, GPIO.IN)
        
        # Initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = 1000000  # 1MHz
        self.spi.mode = 0
        
        # Reset the module
        self.reset()
        
    def __del__(self):
        """Cleanup resources"""
        try:
            self.spi.close()
            GPIO.cleanup()
        except:
            pass
    
    def reset(self):
        """Hardware reset of SX126x"""
        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.001)  # 1ms
        GPIO.output(self.reset_pin, GPIO.HIGH)
        time.sleep(0.005)  # 5ms
        self.wait_on_busy()
    
    def wait_on_busy(self, timeout=1.0):
        """Wait for BUSY pin to go low"""
        start_time = time.time()
        while GPIO.input(self.busy_pin) and (time.time() - start_time) < timeout:
            time.sleep(0.001)
        
        if GPIO.input(self.busy_pin):
            raise TimeoutError("Timeout waiting for BUSY pin")
    
    def write_command(self, command: int, data: List[int] = None):
        """Write command to SX126x"""
        self.wait_on_busy()
        
        if data is None:
            data = []
        
        # Prepare command packet
        packet = [command] + data
        self.spi.xfer2(packet)
        
        # Some commands need additional wait
        if command in [SX126xCommands.SET_SLEEP, SX126xCommands.SET_STANDBY, 
                      SX126xCommands.SET_FS, SX126xCommands.SET_TX, SX126xCommands.SET_RX]:
            time.sleep(0.001)
    
    def read_command(self, command: int, length: int) -> List[int]:
        """Read command response from SX126x"""
        self.wait_on_busy()
        
        # Send command
        self.spi.xfer2([command])
        
        # Read status byte
        status = self.spi.xfer2([0x00])[0]
        
        # Read data
        if length > 0:
            data = self.spi.xfer2([0x00] * length)
            return [status] + data
        else:
            return [status]
    
    def write_register(self, address: int, data: List[int]):
        """Write to SX126x register"""
        self.wait_on_busy()
        
        # Prepare write register command
        packet = [SX126xCommands.WRITE_REGISTER, 
                 (address >> 8) & 0xFF, address & 0xFF] + data
        self.spi.xfer2(packet)
    
    def read_register(self, address: int, length: int = 1) -> List[int]:
        """Read from SX126x register"""
        self.wait_on_busy()
        
        # Send read register command
        packet = [SX126xCommands.READ_REGISTER, 
                 (address >> 8) & 0xFF, address & 0xFF, 0x00]
        self.spi.xfer2(packet)
        
        # Read data
        data = self.spi.xfer2([0x00] * length)
        return data
    
    def write_buffer(self, offset: int, data: List[int]):
        """Write data to SX126x buffer"""
        self.wait_on_busy()
        
        packet = [SX126xCommands.WRITE_BUFFER, offset] + data
        self.spi.xfer2(packet)
    
    def read_buffer(self, offset: int, length: int) -> List[int]:
        """Read data from SX126x buffer"""
        self.wait_on_busy()
        
        # Send read buffer command
        packet = [SX126xCommands.READ_BUFFER, offset, 0x00]
        self.spi.xfer2(packet)
        
        # Read data
        data = self.spi.xfer2([0x00] * length)
        return data
    
    def get_status(self) -> int:
        """Get device status"""
        response = self.read_command(SX126xCommands.GET_STATUS, 0)
        return response[0]
    
    def set_standby(self, standby_config=0x00):
        """Set device to standby mode"""
        self.write_command(SX126xCommands.SET_STANDBY, [standby_config])
    
    def set_packet_type(self, packet_type=0x01):
        """Set packet type (0x00=GFSK, 0x01=LoRa)"""
        self.write_command(SX126xCommands.SET_PACKETTYPE, [packet_type])
    
    def set_rf_frequency(self, frequency_hz: int):
        """Set RF frequency in Hz"""
        # Calculate frequency register value
        # freq_reg = (frequency_hz * 2^25) / 32000000
        freq_reg = int((frequency_hz * (1 << 25)) / 32000000)
        
        freq_bytes = [
            (freq_reg >> 24) & 0xFF,
            (freq_reg >> 16) & 0xFF,
            (freq_reg >> 8) & 0xFF,
            freq_reg & 0xFF
        ]
        
        self.write_command(SX126xCommands.SET_RFFREQUENCY, freq_bytes)
    
    def set_tx_params(self, power: int, ramp_time=0x02):
        """Set TX parameters"""
        self.write_command(SX126xCommands.SET_TXPARAMS, [power, ramp_time])
    
    def set_buffer_base_address(self, tx_base=0x00, rx_base=0x80):
        """Set buffer base addresses"""
        self.write_command(SX126xCommands.SET_BUFFERBASEADDRESS, [tx_base, rx_base])
    
    def set_lora_modulation_params(self, sf: int, bw: int, cr: int, ldro: int = 0):
        """Set LoRa modulation parameters"""
        params = [sf, bw, cr, ldro]
        self.write_command(SX126xCommands.SET_MODULATIONPARAMS, params)
    
    def set_lora_packet_params(self, preamble_length: int, header_type: int, 
                              payload_length: int, crc_type: int, invert_iq: int):
        """Set LoRa packet parameters"""
        params = [
            (preamble_length >> 8) & 0xFF,
            preamble_length & 0xFF,
            header_type,
            payload_length,
            crc_type,
            invert_iq
        ]
        self.write_command(SX126xCommands.SET_PACKETPARAMS, params)
    
    def set_dio_irq_params(self, irq_mask: int, dio1_mask: int, dio2_mask: int, dio3_mask: int):
        """Set DIO IRQ parameters"""
        params = [
            (irq_mask >> 8) & 0xFF,
            irq_mask & 0xFF,
            (dio1_mask >> 8) & 0xFF,
            dio1_mask & 0xFF,
            (dio2_mask >> 8) & 0xFF,
            dio2_mask & 0xFF,
            (dio3_mask >> 8) & 0xFF,
            dio3_mask & 0xFF
        ]
        self.write_command(SX126xCommands.SET_DIOIRQPARAMS, params)
    
    def get_irq_status(self) -> int:
        """Get IRQ status"""
        response = self.read_command(SX126xCommands.GET_IRQSTATUS, 2)
        return (response[1] << 8) | response[2]
    
    def clear_irq_status(self, irq_mask: int):
        """Clear IRQ status"""
        params = [(irq_mask >> 8) & 0xFF, irq_mask & 0xFF]
        self.write_command(SX126xCommands.CLR_IRQSTATUS, params)
    
    def set_tx(self, timeout=0x000000):
        """Set device to TX mode"""
        timeout_bytes = [
            (timeout >> 16) & 0xFF,
            (timeout >> 8) & 0xFF,
            timeout & 0xFF
        ]
        self.write_command(SX126xCommands.SET_TX, timeout_bytes)
    
    def set_rx(self, timeout=0x000000):
        """Set device to RX mode"""
        timeout_bytes = [
            (timeout >> 16) & 0xFF,
            (timeout >> 8) & 0xFF,
            timeout & 0xFF
        ]
        self.write_command(SX126xCommands.SET_RX, timeout_bytes)
    
    def get_rx_buffer_status(self) -> Tuple[int, int]:
        """Get RX buffer status"""
        response = self.read_command(SX126xCommands.GET_RXBUFFERSTATUS, 2)
        payload_length = response[1]
        rx_start_buffer_pointer = response[2]
        return payload_length, rx_start_buffer_pointer
    
    def get_packet_status(self) -> Tuple[int, int, int]:
        """Get packet status (RSSI, SNR, Signal RSSI)"""
        response = self.read_command(SX126xCommands.GET_PACKETSTATUS, 3)
        rssi_pkt = -response[1] // 2
        snr_pkt = response[2] // 4 if response[2] < 128 else (response[2] - 256) // 4
        signal_rssi_pkt = -response[3] // 2
        return rssi_pkt, snr_pkt, signal_rssi_pkt
    
    def set_lora_sync_word(self, sync_word: int):
        """Set LoRa sync word"""
        self.write_register(SX126xRegisters.REG_LORA_SYNC_WORD_MSB, 
                           [(sync_word >> 8) & 0xFF])
        self.write_register(SX126xRegisters.REG_LORA_SYNC_WORD_LSB, 
                           [sync_word & 0xFF])
    
    def send_payload(self, payload: bytes) -> bool:
        """Send LoRa payload"""
        try:
            # Write payload to buffer
            self.write_buffer(0x00, list(payload))
            
            # Set TX mode
            self.set_tx(timeout=0x0F4240)  # 1 second timeout
            
            # Wait for TX done
            start_time = time.time()
            while time.time() - start_time < 5.0:  # 5 second timeout
                irq_status = self.get_irq_status()
                if irq_status & SX126xIRQ.IRQ_TX_DONE:
                    self.clear_irq_status(SX126xIRQ.IRQ_ALL)
                    return True
                elif irq_status & SX126xIRQ.IRQ_TIMEOUT:
                    self.clear_irq_status(SX126xIRQ.IRQ_ALL)
                    return False
                time.sleep(0.01)
            
            return False
            
        except Exception as e:
            print(f"Error sending payload: {e}")
            return False
    
    def receive_payload(self, timeout=30.0) -> Optional[Tuple[bytes, int, int, int]]:
        """Receive LoRa payload"""
        try:
            # Set RX mode
            self.set_rx(timeout=0x0F4240)  # 1 second timeout
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                irq_status = self.get_irq_status()
                
                if irq_status & SX126xIRQ.IRQ_RX_DONE:
                    # Get packet status
                    rssi, snr, signal_rssi = self.get_packet_status()
                    
                    # Get buffer status
                    payload_length, rx_start_buffer = self.get_rx_buffer_status()
                    
                    # Read payload
                    payload_data = self.read_buffer(rx_start_buffer, payload_length)
                    payload = bytes(payload_data)
                    
                    self.clear_irq_status(SX126xIRQ.IRQ_ALL)
                    return payload, rssi, snr, signal_rssi
                
                elif irq_status & (SX126xIRQ.IRQ_TIMEOUT | SX126xIRQ.IRQ_CRC_ERROR):
                    self.clear_irq_status(SX126xIRQ.IRQ_ALL)
                    # Continue listening
                    self.set_rx(timeout=0x0F4240)
                
                time.sleep(0.01)
            
            return None
            
        except Exception as e:
            print(f"Error receiving payload: {e}")
            return None
