import sys
from core.config import AppConfig
from core.serial_manager import SerialManager, SerialData
from core.encryption import EncryptionManager
import time
import termios
import tty
import logging

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
