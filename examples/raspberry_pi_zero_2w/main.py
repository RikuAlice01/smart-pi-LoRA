"""
Main application for Raspberry Pi Zero 2W LoRa SX126x HAT
Sensor data collection and LoRa transmission with data buffering
"""

import time
import json
import threading
import signal
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import argparse

# Try to import serial with fallback
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial library not available")

# Local imports
from config import Config
from sx126x_driver import SX126xDriver
from sensors import SensorManager
from encryption import EncryptionManager
from data_buffer import DataBuffer, BufferConfig, OfflineManager

class LoRaNode:
    """Main LoRa sensor node application with data buffering"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize LoRa node"""
        self.config = Config(config_file)
        self.running = False
        self.lora_disabled = False
        
        # Initialize components
        self.lora_driver: Optional[SX126xDriver] = None
        self.sensor_manager: Optional[SensorManager] = None
        self.encryption_manager: Optional[EncryptionManager] = None
        self.uart_connection: Optional['serial.Serial'] = None
        
        # Data buffering
        self.buffer_config = BufferConfig()
        self.data_buffer: Optional[DataBuffer] = None
        self.offline_manager: Optional[OfflineManager] = None
        
        # Threading
        self.sensor_thread: Optional[threading.Thread] = None
        self.lora_thread: Optional[threading.Thread] = None
        self.sync_thread: Optional[threading.Thread] = None
        
        # Data queues (for immediate transmission)
        self.sensor_data_queue = []
        self.queue_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            "packets_sent": 0,
            "packets_failed": 0,
            "sensor_readings": 0,
            "start_time": time.time(),
            "last_transmission": None,
            "offline_periods": 0,
            "buffered_records": 0
        }
        
        # Setup logging
        self.setup_logging()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.logging.log_level.upper())
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.logging.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("LoRa Node starting up...")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def initialize_components(self) -> bool:
        """Initialize all components"""
        try:
            # Validate configuration
            if not self.config.validate_config():
                self.logger.error("Configuration validation failed")
                return False
            
            # Initialize data buffer
            self.logger.info("Initializing data buffer...")
            self.data_buffer = DataBuffer(self.buffer_config)
            self.offline_manager = OfflineManager(self.data_buffer)
            self.data_buffer.start()
        
            # Initialize LoRa driver (skip if disabled)
            if not self.lora_disabled:
                self.logger.info("Initializing LoRa driver...")
                try:
                    self.lora_driver = SX126xDriver(
                        spi_bus=self.config.gpio.spi_bus,
                        spi_device=self.config.gpio.spi_device,
                        reset_pin=self.config.gpio.reset_pin,
                        busy_pin=self.config.gpio.busy_pin,
                        dio1_pin=self.config.gpio.dio1_pin
                    )
                    
                    # Configure LoRa parameters
                    self.configure_lora()
                    self.offline_manager.set_online()
                except Exception as e:
                    self.logger.warning(f"LoRa initialization failed: {e}")
                    self.logger.info("Continuing in offline mode with data buffering")
                    self.lora_disabled = True
                    self.offline_manager.set_offline()
            else:
                self.logger.info("LoRa driver disabled - offline mode with buffering")
                self.offline_manager.set_offline()
        
            # Initialize sensor manager
            self.logger.info("Initializing sensors...")
            self.sensor_manager = SensorManager(self.config)
        
            # Initialize encryption if enabled
            if self.config.network.encryption_enabled:
                self.logger.info("Initializing encryption...")
                self.encryption_manager = EncryptionManager(
                    method=self.config.network.encryption_method,
                    key=self.config.network.encryption_key
                )
        
            # Initialize UART connection if enabled
            if self.config.network.uart_enabled:
                self.logger.info("Initializing UART connection...")
                self.initialize_uart()
        
            self.logger.info("All components initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    def configure_lora(self):
        """Configure LoRa parameters"""
        try:
            # Set standby mode
            self.lora_driver.set_standby()
            
            # Set packet type to LoRa
            self.lora_driver.set_packet_type(0x01)
            
            # Set frequency
            frequency_hz = self.config.get_frequency_hz()
            self.lora_driver.set_rf_frequency(frequency_hz)
            self.logger.info(f"LoRa frequency set to {frequency_hz} Hz")
            
            # Set modulation parameters
            sf, bw, cr, ldro = self.config.get_lora_modulation_params()
            self.lora_driver.set_lora_modulation_params(sf, bw, cr, ldro)
            self.logger.info(f"LoRa modulation: SF{self.config.lora.spreading_factor}, "
                           f"BW{self.config.lora.bandwidth}kHz, CR4/{self.config.lora.coding_rate}")
            
            # Set packet parameters
            self.lora_driver.set_lora_packet_params(
                preamble_length=self.config.lora.preamble_length,
                header_type=self.config.lora.header_type,
                payload_length=255,  # Maximum payload length
                crc_type=1 if self.config.lora.crc_enabled else 0,
                invert_iq=0
            )
            
            # Set TX power
            self.lora_driver.set_tx_params(self.config.lora.tx_power)
            self.logger.info(f"LoRa TX power set to {self.config.lora.tx_power} dBm")
            
            # Set buffer base addresses
            self.lora_driver.set_buffer_base_address(0x00, 0x80)
            
            # Set sync word
            self.lora_driver.set_lora_sync_word(self.config.lora.sync_word)
            
            # Set DIO IRQ parameters
            self.lora_driver.set_dio_irq_params(
                irq_mask=0x03FF,  # All IRQs
                dio1_mask=0x03FF,  # All IRQs on DIO1
                dio2_mask=0x0000,
                dio3_mask=0x0000
            )
            
            self.logger.info("LoRa configuration completed")
            
        except Exception as e:
            self.logger.error(f"Failed to configure LoRa: {e}")
            raise
    
    def initialize_uart(self):
        """Initialize UART connection"""
        if not SERIAL_AVAILABLE:
            self.logger.warning("UART disabled: pyserial library not available")
            return
            
        try:
            self.uart_connection = serial.Serial(
                port=self.config.network.uart_port,
                baudrate=self.config.network.uart_baudrate,
                timeout=1.0
            )
            self.logger.info(f"UART connection established on {self.config.network.uart_port}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize UART: {e}")
            self.uart_connection = None
    
    def sensor_loop(self):
        """Main sensor reading loop with buffering"""
        self.logger.info("Sensor loop started")
        
        while self.running:
            try:
                # Read sensor data
                sensor_data = self.sensor_manager.read_all_sensors()
                
                if sensor_data:
                    # Create full packet for buffering
                    full_packet = {
                        "device_id": self.config.device.device_id,
                        "timestamp": time.time(),
                        "location": self.config.device.location,
                        **sensor_data
                    }
                    
                    # Always buffer the data
                    self.data_buffer.add_sensor_data(full_packet)
                    self.stats["buffered_records"] += 1
                    
                    # Create compact packet for immediate transmission (if online)
                    if not self.lora_disabled and self.offline_manager.is_online:
                        compact_packet = {
                            "id": self.config.device.device_id,
                            "ts": int(time.time()),
                            "loc": self.config.device.location[:10],
                        }
                        
                        # Add only essential sensor data
                        if "temperature" in sensor_data and sensor_data["temperature"] is not None:
                            compact_packet["temp"] = sensor_data["temperature"]
                        if "humidity" in sensor_data and sensor_data["humidity"] is not None:
                            compact_packet["hum"] = sensor_data["humidity"]
                        if "pressure" in sensor_data and sensor_data["pressure"] is not None:
                            compact_packet["pres"] = sensor_data["pressure"]
                        if "battery_voltage" in sensor_data and sensor_data["battery_voltage"] is not None:
                            compact_packet["bat"] = sensor_data["battery_voltage"]
                        if "rssi" in sensor_data and sensor_data["rssi"] is not None:
                            compact_packet["rssi"] = sensor_data["rssi"]
                        
                        # Add to transmission queue
                        with self.queue_lock:
                            self.sensor_data_queue.append(compact_packet)
                            # Limit queue size
                            if len(self.sensor_data_queue) > 100:
                                self.sensor_data_queue.pop(0)
                    
                    self.stats["sensor_readings"] += 1
                    self.logger.debug(f"Sensor data processed: {self.config.device.device_id}")
                    
                    # Forward full packet to UART if enabled
                    if self.uart_connection:
                        self.forward_to_uart(full_packet)
                
                # Wait for next reading
                time.sleep(self.config.sensor.read_interval)
                
            except Exception as e:
                self.logger.error(f"Error in sensor loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def lora_transmission_loop(self):
        """Main LoRa transmission loop with buffering support"""
        self.logger.info("LoRa transmission loop started")
        
        while self.running:
            try:
                # Check if there's immediate data to transmit
                packet_data = None
                with self.queue_lock:
                    if self.sensor_data_queue:
                        packet_data = self.sensor_data_queue.pop(0)
                
                if packet_data and self.lora_driver and self.offline_manager.is_online:
                    success = self.transmit_packet(packet_data)
                    
                    # Log transmission result
                    payload_size = len(json.dumps(packet_data, separators=(',', ':')).encode('utf-8'))
                    self.data_buffer.add_transmission_log(
                        device_id=self.config.device.device_id,
                        payload_size=payload_size,
                        success=success,
                        error_message=None if success else "Transmission failed"
                    )
                
                # Try to send buffered data if online
                if self.offline_manager.is_online and not self.offline_manager.sync_in_progress:
                    self.process_buffered_data()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error in LoRa transmission loop: {e}")
                time.sleep(1)
    
    def transmit_packet(self, packet_data: Dict[str, Any]) -> bool:
        """Transmit a single packet"""
        try:
            # Convert to JSON
            json_data = json.dumps(packet_data, separators=(',', ':'))  # Compact JSON
            
            # Encrypt if enabled
            if self.encryption_manager:
                json_data = self.encryption_manager.encrypt(json_data)
                self.logger.debug("Data encrypted")
            
            # Transmit via LoRa
            payload = json_data.encode('utf-8')
            
            if len(payload) <= 255:  # Check payload size limit
                success = self.lora_driver.send_payload(payload)
                
                if success:
                    self.stats["packets_sent"] += 1
                    self.stats["last_transmission"] = time.time()
                    self.logger.info(f"Packet transmitted successfully: {self.config.device.device_id}")
                    return True
                else:
                    self.stats["packets_failed"] += 1
                    self.logger.warning("Failed to transmit packet")
                    return False
            else:
                self.logger.warning(f"Payload too large: {len(payload)} bytes")
                self.stats["packets_failed"] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"Error transmitting packet: {e}")
            self.stats["packets_failed"] += 1
            return False
    
    def process_buffered_data(self):
        """Process buffered data for transmission"""
        try:
            # Get a small batch of unsent data
            unsent_data = self.data_buffer.get_unsent_data(limit=5)
            
            if unsent_data:
                transmitted_ids = []
                
                for record in unsent_data:
                    # Create compact packet from buffered data
                    data = record['data']
                    compact_packet = {
                        "id": data.get('device_id', 'unknown'),
                        "ts": int(record['timestamp']),
                        "loc": data.get('location', '')[:10],
                    }
                    
                    # Add sensor data
                    if "temperature" in data:
                        compact_packet["temp"] = data["temperature"]
                    if "humidity" in data:
                        compact_packet["hum"] = data["humidity"]
                    if "pressure" in data:
                        compact_packet["pres"] = data["pressure"]
                    if "battery_voltage" in data:
                        compact_packet["bat"] = data["battery_voltage"]
                    
                    # Try to transmit
                    if self.transmit_packet(compact_packet):
                        transmitted_ids.append(record['id'])
                    else:
                        # If transmission fails, go offline
                        self.offline_manager.set_offline()
                        break
                
                # Mark successfully transmitted records
                if transmitted_ids:
                    self.data_buffer.mark_as_transmitted(transmitted_ids)
                    self.logger.info(f"Transmitted {len(transmitted_ids)} buffered records")
                    
        except Exception as e:
            self.logger.error(f"Error processing buffered data: {e}")
    
    def forward_to_uart(self, data: Dict[str, Any]):
        """Forward data to UART connection"""
        try:
            if self.uart_connection and self.uart_connection.is_open:
                json_data = json.dumps(data) + "\n"
                self.uart_connection.write(json_data.encode('utf-8'))
                self.logger.debug("Data forwarded to UART")
        except Exception as e:
            self.logger.warning(f"Failed to forward data to UART: {e}")
    
    def print_statistics(self):
        """Print current statistics including buffer info"""
        uptime = time.time() - self.stats["start_time"]
        uptime_str = str(timedelta(seconds=int(uptime)))
        
        # Get buffer statistics
        buffer_stats = self.data_buffer.get_statistics() if self.data_buffer else {}
        
        print("\n=== LoRa Node Statistics ===")
        print(f"Device ID: {self.config.device.device_id}")
        print(f"Mode: {'MOCKUP' if self.config.sensor.mock_enabled else 'REAL'}")
        print(f"LoRa: {'OFFLINE' if not self.offline_manager.is_online else 'ONLINE' if not self.lora_disabled else 'DISABLED'}")
        print(f"Uptime: {uptime_str}")
        print(f"Sensor Readings: {self.stats['sensor_readings']}")
        print(f"Packets Sent: {self.stats['packets_sent']}")
        print(f"Packets Failed: {self.stats['packets_failed']}")
        
        if self.stats["last_transmission"]:
            last_tx = datetime.fromtimestamp(self.stats["last_transmission"])
            print(f"Last Transmission: {last_tx.strftime('%Y-%m-%d %H:%M:%S')}")
        
        success_rate = 0
        if self.stats["packets_sent"] + self.stats["packets_failed"] > 0:
            success_rate = (self.stats["packets_sent"] / 
                          (self.stats["packets_sent"] + self.stats["packets_failed"])) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Buffer statistics
        print(f"\n--- Buffer Statistics ---")
        print(f"Total Records: {buffer_stats.get('total_records', 0)}")
        print(f"Unsent Records: {buffer_stats.get('unsent_records', 0)}")
        print(f"Memory Buffer: {buffer_stats.get('memory_buffer_size', 0)}")
        print(f"Database Size: {buffer_stats.get('db_size_mb', 0):.1f} MB")
        print(f"Failed Transmissions: {buffer_stats.get('failed_transmissions', 0)}")
        
        # Queue status
        with self.queue_lock:
            queue_size = len(self.sensor_data_queue)
        print(f"Immediate Queue: {queue_size}")
        print("============================\n")
    
    def export_data(self, hours: int = 24, format: str = 'json') -> str:
        """Export buffered data"""
        if not self.data_buffer:
            self.logger.warning("Data buffer not available")
            return None
        
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        filename = self.data_buffer.export_data(start_time, end_time, format)
        if filename:
            self.logger.info(f"Data exported to: {filename}")
        
        return filename
    
    def start(self):
        """Start the LoRa node"""
        self.logger.info("Starting LoRa node...")
    
        # Initialize components
        if not self.initialize_components():
            self.logger.error("Failed to initialize components")
            return False
    
        # Print configuration
        self.config.print_config()
    
        # Print mode information
        if self.config.sensor.mock_enabled:
            self.logger.info("🎭 Running in MOCKUP mode with simulated sensors")
    
        if self.lora_disabled:
            self.logger.info("📡 LoRa transmission DISABLED - buffering data locally")
        elif not self.offline_manager.is_online:
            self.logger.info("📡 LoRa OFFLINE - buffering data for later transmission")
    
        # Set running flag
        self.running = True
    
        # Start sensor thread
        self.sensor_thread = threading.Thread(target=self.sensor_loop, daemon=True)
        self.sensor_thread.start()
    
        # Start LoRa transmission thread (only if LoRa is enabled)
        if not self.lora_disabled:
            self.lora_thread = threading.Thread(target=self.lora_transmission_loop, daemon=True)
            self.lora_thread.start()
        else:
            self.logger.info("LoRa transmission thread not started (disabled)")
    
        self.logger.info("LoRa node started successfully")
    
        # Main loop
        try:
            while self.running:
                time.sleep(10)  # Print stats every 10 seconds
                self.print_statistics()
        
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
    
        return True
    
    def stop(self):
        """Stop the LoRa node"""
        self.logger.info("Stopping LoRa node...")
        
        # Set running flag to False
        self.running = False
        
        # Wait for threads to finish
        if self.sensor_thread and self.sensor_thread.is_alive():
            self.sensor_thread.join(timeout=5)
        
        if self.lora_thread and self.lora_thread.is_alive():
            self.lora_thread.join(timeout=5)
        
        # Stop data buffer
        if self.data_buffer:
            self.data_buffer.stop()
        
        # Close UART connection
        if self.uart_connection and self.uart_connection.is_open:
            self.uart_connection.close()
        
        # Cleanup LoRa driver
        if self.lora_driver:
            try:
                del self.lora_driver
            except:
                pass
        
        self.logger.info("LoRa node stopped")

def print_usage():
    """Print usage examples"""
    print("\nUsage Examples:")
    print("  python main.py                    # Normal mode with real sensors")
    print("  python main.py mockup             # Mockup mode with simulated data")
    print("  python main.py test               # Hardware test mode")
    print("  python main.py mockup --no-lora   # Mockup mode without LoRa")
    print("  python main.py --interval 10      # Override sensor interval to 10s")
    print("  python main.py --log-level DEBUG  # Enable debug logging")
    print("  python main.py --export 24        # Export last 24 hours of data")
    print()

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='LoRa SX126x Sensor Node for Raspberry Pi Zero 2W')
    parser.add_argument('mode', nargs='?', default='normal', 
                       choices=['normal', 'mockup', 'test'],
                       help='Operation mode: normal (default), mockup, or test')
    parser.add_argument('--config', default='config.json',
                       help='Configuration file path (default: config.json)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Override log level')
    parser.add_argument('--no-lora', action='store_true',
                       help='Disable LoRa transmission (sensors only)')
    parser.add_argument('--interval', type=float,
                       help='Override sensor reading interval in seconds')
    parser.add_argument('--export', type=int, metavar='HOURS',
                       help='Export data from last N hours and exit')
    
    args = parser.parse_args()
    
    print("LoRa SX126x Sensor Node for Raspberry Pi Zero 2W")
    print("=" * 50)
    print(f"Mode: {args.mode.upper()}")
    
    # Handle export mode
    if args.export:
        return export_data_only(args)
    
    # Handle different modes
    if args.mode == 'mockup':
        print("🎭 MOCKUP MODE: Using simulated sensor data")
        return run_mockup_mode(args)
    elif args.mode == 'test':
        print("🧪 TEST MODE: Hardware testing")
        return run_test_mode(args)
    else:
        print("🚀 NORMAL MODE: Real sensor operation")
        return run_normal_mode(args)

def export_data_only(args):
    """Export data and exit"""
    try:
        from data_buffer import DataBuffer, BufferConfig
        
        print(f"📤 Exporting last {args.export} hours of data...")
        
        buffer_config = BufferConfig()
        data_buffer = DataBuffer(buffer_config)
        
        end_time = time.time()
        start_time = end_time - (args.export * 3600)
        
        filename = data_buffer.export_data(start_time, end_time, 'json')
        
        if filename:
            print(f"✅ Data exported to: {filename}")
            return 0
        else:
            print("❌ Export failed")
            return 1
            
    except Exception as e:
        print(f"❌ Export error: {e}")
        return 1

def run_mockup_mode(args):
    """Run in mockup mode with simulated data"""
    try:
        # Create and configure node for mockup mode
        node = LoRaNode(args.config)
        
        # Override configuration for mockup mode
        node.config.sensor.mock_enabled = True
        node.config.sensor.dht22_enabled = False
        node.config.sensor.bmp280_enabled = False
        
        # Override log level if specified
        if args.log_level:
            node.config.logging.log_level = args.log_level
        
        # Override sensor interval if specified
        if args.interval:
            node.config.sensor.read_interval = args.interval
        
        # Disable LoRa if requested
        if args.no_lora:
            node.lora_disabled = True
            print("📡 LoRa transmission disabled")
        
        print(f"📊 Sensor interval: {node.config.sensor.read_interval}s")
        print(f"🔧 Config file: {args.config}")
        print(f"💾 Data buffering: ENABLED")
        print()
        
        # Start the node
        node.start()
        return 0
        
    except Exception as e:
        print(f"Error in mockup mode: {e}")
        return 1

def run_test_mode(args):
    """Run hardware test mode"""
    try:
        from test_hardware import main as test_main
        print("Running hardware tests...")
        return test_main()
    except ImportError:
        print("Error: test_hardware.py not found")
        return 1
    except Exception as e:
        print(f"Error in test mode: {e}")
        return 1

def run_normal_mode(args):
    """Run in normal mode"""
    try:
        # Create and start LoRa node
        node = LoRaNode(args.config)
        
        # Override log level if specified
        if args.log_level:
            node.config.logging.log_level = args.log_level
        
        # Override sensor interval if specified
        if args.interval:
            node.config.sensor.read_interval = args.interval
        
        # Disable LoRa if requested
        if args.no_lora:
            node.lora_disabled = True
            print("📡 LoRa transmission disabled")
        
        print(f"💾 Data buffering: ENABLED")
        
        node.start()
        return 0
        
    except Exception as e:
        print(f"Error starting LoRa node: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
