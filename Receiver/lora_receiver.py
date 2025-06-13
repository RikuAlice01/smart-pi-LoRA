import configparser
from SX127x.LoRa import *
from SX127x.board_config import BOARD
from SX127x.constants import MODE, IRQ

import time

BOARD.setup()

# โหลดค่าจาก config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# อ่านค่าจาก config
freq = float(config['lora']['frequency']) * 1e6
sf = int(config['lora']['spreading_factor'])
bw = int(config['lora']['bandwidth'])
cr = int(config['lora']['coding_rate'])
preamble_length = int(config['lora']['preamble_length'])

class LoRaReceiver(LoRa):
    def __init__(self, verbose=False):
        super(LoRaReceiver, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_freq(freq / 1e6)
        self.set_spreading_factor(sf)
        self.set_bandwidth(bw)
        self.set_coding_rate(cr)
        self.set_preamble(preamble_length)
        self.set_mode(MODE.STDBY)

    def on_rx_done(self):
        self.clear_irq_flags(IRQ.RX_DONE)
        payload = self.read_payload(nocheck=True)
        message = ''.join([chr(x) for x in payload])
        print(f"[RECEIVED] {message}")
        self.set_mode(MODE.RXCONT)

lora = LoRaReceiver(verbose=False)

print("LoRa Receiver started")
lora.reset_ptr_rx()
lora.set_mode(MODE.RXCONT)

try:
    while True:
        if lora.get_irq_flags()['rx_done']:
            lora.on_rx_done()
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Receiver stopped by user")
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()
