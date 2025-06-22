import sys
from core.config import AppConfig
from core.serial_manager import SerialManager, SerialData
from core.encryption import EncryptionManager
import time
import select
import termios
import tty
from threading import Timer

old_settings = termios.tcgetattr(sys.stdin)
tty.setcbreak(sys.stdin.fileno())


class Node:
    def __init__(self, config: AppConfig):
        self.config = config

        if self.serial_manager.connect(self.config.serial.port, self.config.serial.baudrate):
            print(f"Connected to serial port {self.config.serial.port} at {self.config.serial.baudrate} baud.")
            self.serial_manager.send_data("Hello World" + "\n")
        else:
            print(f"Failed to connect to serial port {self.config.serial.port}. Please check the connection.")

        # Core components
        self.serial_manager = SerialManager(self.on_serial_data_received)
        self.encryption_manager = EncryptionManager(
            method=config.encryption.method,
            key=config.encryption.key
        )

def main():
    config = AppConfig()
    node = Node(config)
    node.run()

if __name__ == "__main__":
    main()

    



# node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=433,addr=0,power=22,rssi=False,air_speed=2400,relay=False)
# node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=868,addr=0,power=22,rssi=True,air_speed=2400,relay=False)

# def send_deal():
#     get_rec = ""
#     print("")
#     print("input a string such as \033[1;32m0,868,Hello World\033[0m,it will send `Hello World` to lora node device of address 0 with 868M ")
#     print("please input and press Enter key:",end='',flush=True)

#     while True:
#         rec = sys.stdin.read(1)
#         if rec != None:
#             if rec == '\x0a': break
#             get_rec += rec
#             sys.stdout.write(rec)
#             sys.stdout.flush()

#     get_t = get_rec.split(",")

#     offset_frequence = int(get_t[1])-(850 if int(get_t[1])>850 else 410)
#     #
#     # the sending message format
#     #
#     #         receiving node              receiving node                   receiving node           own high 8bit           own low 8bit                 own 
#     #         high 8bit address           low 8bit address                    frequency                address                 address                  frequency             message payload
#     data = bytes([int(get_t[0])>>8]) + bytes([int(get_t[0])&0xff]) + bytes([offset_frequence]) + bytes([node.addr>>8]) + bytes([node.addr&0xff]) + bytes([node.offset_freq]) + get_t[2].encode()

#     node.send(data)
#     print('\x1b[2A',end='\r')
#     print(" "*200)
#     print(" "*200)
#     print(" "*200)
#     print('\x1b[3A',end='\r')

# try:
#     time.sleep(1)
#     print("Press \033[1;32mEsc\033[0m to exit")
#     print("Press \033[1;32mi\033[0m   to send")
#     print("Press \033[1;32ms\033[0m   to send cpu temperature every 10 seconds")
    
#     # it will send rpi cpu temperature every 10 seconds 
#     seconds = 10
    
#     while True:

#         if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
#             c = sys.stdin.read(1)

#             # dectect key Esc
#             if c == '\x1b': break
#             # dectect key i
#             if c == '\x69':
#                 send_deal()
#             # dectect key s
#             if c == '\x73':
#                 print("Press \033[1;32mc\033[0m   to exit the send task")
#                 timer_task = Timer(seconds,send_cpu_continue)
#                 timer_task.start()
                
#                 while True:
#                     if sys.stdin.read(1) == '\x63':
#                         timer_task.cancel()
#                         print('\x1b[1A',end='\r')
#                         print(" "*100)
#                         print('\x1b[1A',end='\r')
#                         break

#             sys.stdout.flush()
            
#         node.receive()
        
#         # timer,send messages automatically
        
# except:
#     termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


# termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)