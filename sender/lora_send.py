import time
import configparser
from SX127x.LoRa import *
from SX127x.board_config import BOARD
from SX127x.constants import MODE

BOARD.setup()

# โหลดค่าจาก config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# อ่านค่าจาก config
freq = float(config['lora']['frequency']) * 1e6
tx_power = int(config['lora']['tx_power'])
sf = int(config['lora']['spreading_factor'])
bw = int(config['lora']['bandwidth'])
cr = int(config['lora']['coding_rate'])
preamble_length = int(config['lora']['preamble_length'])

interval = int(config['send']['interval'])
mock_temp = float(config['send']['mock_temp'])
mock_hum = float(config['send']['mock_hum'])
mock_ph = float(config['send']['mock_ph'])

class LoRaSender(LoRa):
    def __init__(self, verbose=False):
        super(LoRaSender, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_freq(freq / 1e6)
        self.set_tx_power(tx_power)
        self.set_spreading_factor(sf)
        self.set_bandwidth(bw)
        self.set_coding_rate(cr)
        self.set_preamble(preamble_length)
        self.set_mode(MODE.STDBY)

lora = LoRaSender(verbose=False)

print("LoRa Sender started")
counter = 0

try:
    while True:
        payload = f"temp:{mock_temp},hum:{mock_hum},ph:{mock_ph},count:{counter}"
        print(f"[SEND] {payload}")
        lora.write_payload([ord(c) for c in payload])
        lora.set_mode(MODE.TX)
        time.sleep(1)
        lora.set_mode(MODE.STDBY)
        counter += 1
        time.sleep(interval)

except KeyboardInterrupt:
    print("Sender stopped by user")
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()
