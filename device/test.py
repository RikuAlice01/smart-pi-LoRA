import sys
from core.config import AppConfig
from core.serial_manager import SerialManager, SerialData
from core.encryption import EncryptionManager
import time
import select
import termios
import tty
import logging
from threading import Timer

old_settings = termios.tcgetattr(sys.stdin)
tty.setcbreak(sys.stdin.fileno())

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Node:
    """Main Node class for serial communication with encryption support"""
    
    def __init__(self):
        self.config = AppConfig()
        self.running = False
        self._setup_components()
        self._connect_serial()
    
    def _setup_components(self):
        """Initialize core components"""
        self.serial_manager = SerialManager(self.on_serial_data_received)
        self.encryption_manager = EncryptionManager(
            method=self.config.encryption.method,
            key=self.config.encryption.key
        )
        logger.info("Node components initialized")
    
    def _connect_serial(self):
        """Establish serial connection"""
        if self.serial_manager.connect(
            self.config.serial.port, 
            self.config.serial.baudrate
        ):
            logger.info(f"Connected to serial port {self.config.serial.port} at {self.config.serial.baudrate} baud")
            # Send initial greeting
            self.send_message("Hello World")
        else:
            logger.error(f"Failed to connect to serial port {self.config.serial.port}")
    
    def on_serial_data_received(self, data: SerialData):
        """Handle received serial data"""
        logger.info(f"Received from {data.port}: {data.decoded_data}")
        
        try:
            # Process the received data
            if self.encryption_manager.is_encrypted(data.decoded_data):
                decrypted_data = self.encryption_manager.decrypt(data.decoded_data)
                logger.info(f"Decrypted message: {decrypted_data}")
                self._process_message(decrypted_data)
            else:
                logger.info(f"Plain message: {data.decoded_data}")
                self._process_message(data.decoded_data)
                
        except Exception as e:
            logger.error(f"Error processing serial data: {e}")
    
    def send_message(self, message: str, encrypt: bool = False):
        """Send message through serial connection"""
        try:
            if encrypt:
                message = self.encryption_manager.encrypt(message)
            
            if self.serial_manager.send_data(message + "\n"):
                logger.debug(f"Message sent: {message}")
            else:
                logger.error("Failed to send message")
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    def run(self):
        """Main run loop"""
        self.running = True
        logger.info("Node started. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                # Main loop - you can add periodic tasks here
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the node"""
        logger.info("Stopping node...")
        self.running = False
        if hasattr(self, 'serial_manager'):
            self.serial_manager.disconnect()
        logger.info("Node stopped")

def main():
    """Main entry point"""
    node = None
    try:
        node = Node()
        node.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if node:
            node.stop()

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