"""
Enhanced LoRa SX126x Sensor Node for Raspberry Pi Zero 2W
Production-ready implementation with advanced features
"""

import asyncio
import signal
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import argparse

# Import our enhanced modules
from src.core.config import ConfigManager
from src.core.device_id import DeviceIDManager
from src.core.exceptions import LoRaNodeError, ConfigurationError, HardwareError
from src.hardware.sx126x_driver import SX126xDriver
from src.hardware.sensors import SensorManager
from src.hardware.gpio_manager import get_gpio_manager
from src.communication.lora_manager import LoRaManager
from src.communication.encryption import create_encryption_manager
from src.data.buffer import DataBuffer
from src.data.storage import DataStorage
from src.utils.logging import setup_logging, get_logger, TimingLogger
from src.utils.health import HealthMonitor
from src.utils.helpers import retry_on_failure

# Version information
__version__ = "2.0.0"
__author__ = "LoRa Gateway Team"

class LoRaSensorNode:
    """Enhanced LoRa sensor node with production features"""
    
    def __init__(self, config_file: str = "config.json", mock_mode: bool = False):
        """Initialize LoRa sensor node"""
        self.config_file = config_file
        self.mock_mode = mock_mode
        self.running = False
        self.shutdown_requested = False
        
        # Core components
        self.config: Optional[ConfigManager] = None
        self.device_id_manager: Optional[DeviceIDManager] = None
        self.gpio_manager = None
        self.lora_manager: Optional[LoRaManager] = None
        self.sensor_manager: Optional[SensorManager] = None
        self.encryption_manager = None
        self.data_buffer: Optional[DataBuffer] = None
        self.data_storage: Optional[DataStorage] = None
        self.health_monitor: Optional[HealthMonitor] = None
        
        # Statistics
        self.stats = {
            'start_time': time.time(),
            'messages_sent': 0,
            'messages_failed': 0,
            'sensor_readings': 0,
            'errors': 0,
            'last_transmission': None,
            'uptime': 0
        }
        
        self.logger = None
    
    async def initialize(self) -> bool:
        """Initialize all components"""
        try:
            print(f"🚀 Initializing LoRa Sensor Node v{__version__}")
            
            # Load configuration
            self.config = ConfigManager(self.config_file)
            
            # Setup logging
            setup_logging(
                log_level=self.config.logging.log_level,
                log_file=self.config.logging.log_file,
                max_log_size=self.config.logging.max_log_size,
                backup_count=self.config.logging.backup_count,
                console_logging=self.config.logging.console_logging,
                file_logging=self.config.logging.file_logging,
                structured_logging=self.config.logging.structured_logging
            )
            
            self.logger = get_logger(__name__)
            self.logger.info(f"Starting LoRa Sensor Node v{__version__}")
            
            # Initialize device ID manager
            self.device_id_manager = DeviceIDManager(self.config_file)
            device_id = self.device_id_manager.get_device_id("mac")
            self.config.device.device_id = device_id
            
            self.logger.info(f"Device ID: {device_id}")
            
            # Initialize GPIO manager
            self.gpio_manager = get_gpio_manager(self.mock_mode)
            
            # Initialize health monitor
            self.health_monitor = HealthMonitor(
                monitoring_interval=self.config.performance.monitoring_enabled
            )
            
            # Initialize encryption
            self.encryption_manager = create_encryption_manager(self.config)
            
            # Test encryption
            if not self.encryption_manager.test_encryption():
                raise ConfigurationError("Encryption test failed")
            
            self.logger.info("Encryption system validated")
            
            # Initialize data management
            self.data_buffer = DataBuffer(
                max_size=1000,
                auto_save=True,
                save_file="data_buffer.json"
            )
            
            self.data_storage = DataStorage(
                storage_dir="data",
                max_file_size_mb=10,
                compression_enabled=True
            )
            
            # Initialize sensor manager
            self.sensor_manager = SensorManager(
                config=self.config.sensor,
                gpio_manager=self.gpio_manager,
                mock_mode=self.mock_mode
            )
            
            await self.sensor_manager.initialize()
            self.logger.info("Sensor manager initialized")
            
            # Initialize LoRa manager
            self.lora_manager = LoRaManager(
                config=self.config,
                gpio_manager=self.gpio_manager,
                mock_mode=self.mock_mode
            )
            
            await self.lora_manager.initialize()
            self.logger.info("LoRa manager initialized")
            
            # Print configuration
            self.config.print_config()
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Initialization failed: {e}")
            else:
                print(f"❌ Initialization failed: {e}")
            return False
    
    async def run_sensor_loop(self):
        """Main sensor reading and transmission loop"""
        self.logger.info("Starting sensor loop")
        
        while self.running and not self.shutdown_requested:
            try:
                with TimingLogger(self.logger, "sensor reading cycle"):
                    # Read sensors
                    sensor_data = await self.sensor_manager.read_all_sensors()
                    
                    if sensor_data:
                        self.stats['sensor_readings'] += 1
                        
                        # Add metadata
                        message_data = {
                            'device_id': self.config.device.device_id,
                            'timestamp': time.time(),
                            'sequence': self.stats['messages_sent'] + 1,
                            'sensors': sensor_data,
                            'location': self.config.device.location,
                            'firmware_version': self.config.device.firmware_version
                        }
                        
                        # Add to buffer
                        self.data_buffer.add_data(message_data)
                        
                        # Store locally
                        await self.data_storage.store_data(message_data)
                        
                        # Prepare for transmission
                        await self.transmit_data(message_data)
                    
                    # Update statistics
                    self.stats['uptime'] = time.time() - self.stats['start_time']
                    
                    # Health check
                    if self.health_monitor:
                        health_report = self.health_monitor.check_system_health()
                        if health_report['status'] != 'healthy':
                            self.logger.warning(f"System health: {health_report['status']}")
                
                # Wait for next reading
                await asyncio.sleep(self.config.sensor.read_interval)
                
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Error in sensor loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    @retry_on_failure(max_attempts=3, delay=1.0)
    async def transmit_data(self, data: Dict[str, Any]) -> bool:
        """Transmit data via LoRa with retry logic"""
        try:
            # Convert to transmission format
            if self.config.network.encryption_enabled:
                # Create payload string (compatible with sample format)
                payload_parts = []
                payload_parts.append(f"id:{data['device_id']}")
                
                # Add sensor data
                for sensor_name, sensor_value in data['sensors'].items():
                    if isinstance(sensor_value, dict):
                        for key, value in sensor_value.items():
                            payload_parts.append(f"{key}:{value}")
                    else:
                        payload_parts.append(f"{sensor_name}:{sensor_value}")
                
                payload_parts.append(f"count:{data['sequence']}")
                payload_parts.append(f"timestamp:{data['timestamp']}")
                
                payload_string = ",".join(payload_parts)
                
                # Encrypt payload
                encrypted_payload = self.encryption_manager.encrypt(payload_string)
                transmission_data = encrypted_payload
                
            else:
                # Send as JSON
                import json
                transmission_data = json.dumps(data)
            
            # Transmit via LoRa
            success = await self.lora_manager.transmit(transmission_data)
            
            if success:
                self.stats['messages_sent'] += 1
                self.stats['last_transmission'] = time.time()
                self.logger.info(f"Transmitted message #{data['sequence']}")
                return True
            else:
                self.stats['messages_failed'] += 1
                self.logger.error(f"Failed to transmit message #{data['sequence']}")
                return False
                
        except Exception as e:
            self.stats['messages_failed'] += 1
            self.logger.error(f"Transmission error: {e}")
            return False
    
    async def run_health_monitor(self):
        """Background health monitoring"""
        while self.running and not self.shutdown_requested:
            try:
                if self.health_monitor:
                    health_report = self.health_monitor.check_system_health()
                    
                    # Log health status periodically
                    if health_report['status'] != 'healthy':
                        self.logger.warning(f"Health check: {health_report['status']}")
                        for alert in health_report.get('alerts', []):
                            self.logger.warning(f"Health alert: {alert}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)
    
    async def run_statistics_logger(self):
        """Log statistics periodically"""
        while self.running and not self.shutdown_requested:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                self.logger.info("=== Node Statistics ===")
                self.logger.info(f"Uptime: {self.stats['uptime']:.1f}s")
                self.logger.info(f"Messages sent: {self.stats['messages_sent']}")
                self.logger.info(f"Messages failed: {self.stats['messages_failed']}")
                self.logger.info(f"Sensor readings: {self.stats['sensor_readings']}")
                self.logger.info(f"Errors: {self.stats['errors']}")
                
                if self.stats['last_transmission']:
                    last_tx_ago = time.time() - self.stats['last_transmission']
                    self.logger.info(f"Last transmission: {last_tx_ago:.1f}s ago")
                
                # Success rate
                total_attempts = self.stats['messages_sent'] + self.stats['messages_failed']
                if total_attempts > 0:
                    success_rate = (self.stats['messages_sent'] / total_attempts) * 100
                    self.logger.info(f"Success rate: {success_rate:.1f}%")
                
            except Exception as e:
                self.logger.error(f"Statistics logger error: {e}")
    
    async def start(self):
        """Start the sensor node"""
        try:
            self.running = True
            
            # Create tasks for concurrent operations
            tasks = [
                asyncio.create_task(self.run_sensor_loop()),
                asyncio.create_task(self.run_health_monitor()),
                asyncio.create_task(self.run_statistics_logger())
            ]
            
            self.logger.info("LoRa sensor node started successfully")
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"Error running sensor node: {e}")
            raise
    
    async def stop(self):
        """Stop the sensor node gracefully"""
        self.logger.info("Stopping LoRa sensor node...")
        
        self.shutdown_requested = True
        self.running = False
        
        # Stop components
        if self.lora_manager:
            await self.lora_manager.cleanup()
        
        if self.sensor_manager:
            await self.sensor_manager.cleanup()
        
        if self.data_buffer:
            self.data_buffer.save_to_file()
        
        if self.gpio_manager:
            self.gpio_manager.cleanup()
        
        self.logger.info("LoRa sensor node stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        if self.logger:
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
        else:
            print(f"Received signal {signum}, shutting down...")
        
        self.shutdown_requested = True

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description=f"LoRa Sensor Node v{__version__}")
    parser.add_argument('--config', '-c', default='config.json', 
                       help='Configuration file path')
    parser.add_argument('--mock', action='store_true',
                       help='Run in mock mode (no hardware required)')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('mode', nargs='?', default='normal',
                       choices=['normal', 'mockup', 'test'],
                       help='Operating mode')
    
    args = parser.parse_args()
    
    # Determine mock mode
    mock_mode = args.mock or args.mode in ['mockup', 'test']
    
    # Create and initialize node
    node = LoRaSensorNode(args.config, mock_mode)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, node.signal_handler)
    signal.signal(signal.SIGTERM, node.signal_handler)
    
    try:
        # Initialize
        if not await node.initialize():
            print("❌ Failed to initialize sensor node")
            return 1
        
        # Start node
        await node.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ Shutdown requested by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1
    finally:
        await node.stop()
    
    return 0

if __name__ == "__main__":
    """Entry point"""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
