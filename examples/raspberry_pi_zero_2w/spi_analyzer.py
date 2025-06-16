#!/usr/bin/env python3
"""
Real-time SPI Communication Analyzer for SX126x
Monitors and analyzes SPI traffic for debugging
"""

import time
import sys
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import spidev
    import RPi.GPIO as GPIO
    LIBRARIES_AVAILABLE = True
except ImportError:
    LIBRARIES_AVAILABLE = False

@dataclass
class SPITransaction:
    """Represents a single SPI transaction"""
    timestamp: float
    command: int
    data_sent: List[int]
    data_received: List[int]
    command_name: str
    success: bool
    notes: str = ""

class SX126xSPIAnalyzer:
    """SPI analyzer for SX126x communication"""
    
    def __init__(self, spi_bus=0, spi_device=0, reset_pin=22, busy_pin=23):
        self.spi_bus = spi_bus
        self.spi_device = spi_device
        self.reset_pin = reset_pin
        self.busy_pin = busy_pin
        
        self.spi = None
        self.transactions = []
        
        # SX126x command definitions
        self.commands = {
            0x84: "SET_SLEEP",
            0x80: "SET_STANDBY", 
            0x8C: "SET_FS",
            0x83: "SET_TX",
            0x82: "SET_RX",
            0x94: "SET_RXDUTYCYCLE",
            0xC5: "SET_CAD",
            0x0D: "WRITE_REGISTER",
            0x1D: "READ_REGISTER",
            0x0E: "WRITE_BUFFER",
            0x1E: "READ_BUFFER",
            0x08: "SET_DIOIRQPARAMS",
            0x12: "GET_IRQSTATUS",
            0x02: "CLR_IRQSTATUS",
            0x9D: "SET_DIO2ASRFSWITCHCTRL",
            0x97: "SET_DIO3ASTCXOCTRL",
            0x86: "SET_RFFREQUENCY",
            0x8A: "SET_PACKETTYPE",
            0x11: "GET_PACKETTYPE",
            0x8E: "SET_TXPARAMS",
            0x8B: "SET_MODULATIONPARAMS",
            0x8C: "SET_PACKETPARAMS",
            0x88: "SET_CADPARAMS",
            0x8F: "SET_BUFFERBASEADDRESS",
            0xA0: "SET_LORASYMBNUMTIMEOUT",
            0xC0: "GET_STATUS",
            0x15: "GET_RSSIINST",
            0x13: "GET_RXBUFFERSTATUS",
            0x14: "GET_PACKETSTATUS",
            0x17: "GET_DEVICEERRORS",
            0x07: "CLR_DEVICEERRORS",
            0x10: "GET_STATS",
            0x00: "RESET_STATS"
        }
    
    def initialize(self) -> bool:
        """Initialize SPI and GPIO"""
        if not LIBRARIES_AVAILABLE:
            print("❌ Required libraries not available")
            return False
        
        try:
            # Initialize SPI
            self.spi = spidev.SpiDev()
            self.spi.open(self.spi_bus, self.spi_device)
            self.spi.max_speed_hz = 1000000
            self.spi.mode = 0
            
            # Initialize GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.reset_pin, GPIO.OUT)
            GPIO.setup(self.busy_pin, GPIO.IN)
            
            print("✅ SPI analyzer initialized")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize SPI analyzer: {e}")
            return False
    
    def wait_for_busy(self, timeout=1.0) -> bool:
        """Wait for BUSY pin to go low"""
        start_time = time.time()
        while GPIO.input(self.busy_pin) and (time.time() - start_time) < timeout:
            time.sleep(0.001)
        
        return not GPIO.input(self.busy_pin)
    
    def send_command(self, command: int, data: List[int] = None, 
                    read_length: int = 0) -> SPITransaction:
        """Send command and analyze the transaction"""
        if data is None:
            data = []
        
        transaction = SPITransaction(
            timestamp=time.time(),
            command=command,
            data_sent=data.copy(),
            data_received=[],
            command_name=self.commands.get(command, f"UNKNOWN_0x{command:02X}"),
            success=False
        )
        
        try:
            # Wait for BUSY before sending
            if not self.wait_for_busy():
                transaction.notes = "BUSY timeout before command"
                return transaction
            
            # Send command
            if read_length > 0:
                # Read command
                packet = [command] + [0x00] * (read_length + 1)
                response = self.spi.xfer2(packet)
                transaction.data_received = response[1:]  # Skip status byte
            else:
                # Write command
                packet = [command] + data
                response = self.spi.xfer2(packet)
                transaction.data_received = response
            
            # Wait for BUSY after command (for some commands)
            if command in [0x80, 0x83, 0x82, 0x84]:  # Mode change commands
                busy_cleared = self.wait_for_busy(timeout=0.1)
                if not busy_cleared:
                    transaction.notes += " BUSY timeout after command"
            
            transaction.success = True
            
        except Exception as e:
            transaction.notes = f"SPI error: {e}"
        
        self.transactions.append(transaction)
        return transaction
    
    def reset_chip(self) -> bool:
        """Reset the SX126x chip and analyze"""
        print("🔄 Performing chip reset...")
        
        try:
            # Reset sequence
            GPIO.output(self.reset_pin, GPIO.LOW)
            time.sleep(0.002)  # 2ms
            GPIO.output(self.reset_pin, GPIO.HIGH)
            time.sleep(0.010)  # 10ms
            
            # Wait for BUSY to clear
            busy_cleared = self.wait_for_busy(timeout=1.0)
            
            if busy_cleared:
                print("✅ Reset successful - BUSY cleared")
                return True
            else:
                print("⚠️  Reset completed but BUSY still high")
                return False
                
        except Exception as e:
            print(f"❌ Reset failed: {e}")
            return False
    
    def analyze_basic_communication(self):
        """Analyze basic SPI communication patterns"""
        print("\n🔍 Analyzing Basic Communication...")
        print("=" * 40)
        
        # Test sequence
        test_commands = [
            (0xC0, [], 1, "Get initial status"),
            (0x80, [0x00], 0, "Set standby mode (RC)"),
            (0xC0, [], 1, "Get status after standby"),
            (0x8A, [0x01], 0, "Set packet type (LoRa)"),
            (0xC0, [], 1, "Get status after packet type"),
        ]
        
        for command, data, read_len, description in test_commands:
            print(f"\n📤 {description}")
            transaction = self.send_command(command, data, read_len)
            self.print_transaction(transaction)
            time.sleep(0.05)  # Small delay between commands
    
    def analyze_register_access(self):
        """Test register read/write operations"""
        print("\n🔍 Analyzing Register Access...")
        print("=" * 35)
        
        # Test register operations
        sync_word_addr = 0x0740  # LoRa sync word register
        
        # Read current sync word
        print("\n📖 Reading sync word register...")
        read_cmd = [0x1D, (sync_word_addr >> 8) & 0xFF, sync_word_addr & 0xFF, 0x00]
        response = self.spi.xfer2(read_cmd + [0x00, 0x00])  # Read 2 bytes
        
        current_sync = (response[4] << 8) | response[5]
        print(f"   Current sync word: 0x{current_sync:04X}")
        
        # Write test sync word
        test_sync = 0x1234
        print(f"\n📝 Writing test sync word: 0x{test_sync:04X}")
        write_cmd = [0x0D, (sync_word_addr >> 8) & 0xFF, sync_word_addr & 0xFF, 
                    (test_sync >> 8) & 0xFF, test_sync & 0xFF]
        self.spi.xfer2(write_cmd)
        
        # Read back
        print("\n📖 Reading back sync word...")
        response = self.spi.xfer2(read_cmd + [0x00, 0x00])
        readback_sync = (response[4] << 8) | response[5]
        
        print(f"   Read back: 0x{readback_sync:04X}")
        
        if readback_sync == test_sync:
            print("✅ Register read/write working correctly")
        else:
            print("❌ Register read/write mismatch")
    
    def print_transaction(self, transaction: SPITransaction):
        """Print formatted transaction details"""
        timestamp = datetime.fromtimestamp(transaction.timestamp)
        time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]
        
        status_icon = "✅" if transaction.success else "❌"
        
        print(f"   {status_icon} [{time_str}] {transaction.command_name}")
        print(f"      Command: 0x{transaction.command:02X}")
        
        if transaction.data_sent:
            print(f"      Sent: {[hex(x) for x in transaction.data_sent]}")
        
        if transaction.data_received:
            print(f"      Received: {[hex(x) for x in transaction.data_received]}")
        
        if transaction.notes:
            print(f"      Notes: {transaction.notes}")
    
    def print_summary(self):
        """Print analysis summary"""
        print("\n📊 ANALYSIS SUMMARY")
        print("=" * 25)
        
        if not self.transactions:
            print("No transactions recorded")
            return
        
        total = len(self.transactions)
        successful = sum(1 for t in self.transactions if t.success)
        failed = total - successful
        
        print(f"Total transactions: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(successful/total)*100:.1f}%")
        
        # Analyze response patterns
        print(f"\n📈 Response Patterns:")
        
        status_responses = []
        for t in self.transactions:
            if t.command == 0xC0 and t.data_received:  # GET_STATUS
                status_responses.append(t.data_received[0])
        
        if status_responses:
            unique_status = set(status_responses)
            print(f"   Status responses: {[hex(x) for x in unique_status]}")
            
            if len(unique_status) == 1 and 0x00 in unique_status:
                print("   ⚠️  All status responses are 0x00 - possible issues:")
                print("      • Chip not responding")
                print("      • Wrong HAT type")
                print("      • Power/connection issue")
            elif 0x00 not in unique_status:
                print("   ✅ Valid status responses - chip communicating")
            else:
                print("   ⚠️  Mixed responses - intermittent communication")
        
        # Check for common issues
        busy_timeouts = sum(1 for t in self.transactions if "BUSY timeout" in t.notes)
        if busy_timeouts > 0:
            print(f"   ⚠️  BUSY timeouts: {busy_timeouts}")
            print("      • Check BUSY pin connection")
            print("      • Verify GPIO pin number")
        
        spi_errors = sum(1 for t in self.transactions if "SPI error" in t.notes)
        if spi_errors > 0:
            print(f"   ❌ SPI errors: {spi_errors}")
            print("      • Check SPI connections")
            print("      • Verify SPI is enabled")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.spi:
                self.spi.close()
            GPIO.cleanup()
        except:
            pass

def main():
    """Main analyzer function"""
    print("🔍 SX126x SPI Communication Analyzer")
    print("=" * 40)
    
    if not LIBRARIES_AVAILABLE:
        print("❌ Required libraries not available")
        print("Install with: pip3 install spidev RPi.GPIO")
        return 1
    
    analyzer = SX126xSPIAnalyzer()
    
    try:
        # Initialize
        if not analyzer.initialize():
            return 1
        
        # Reset chip
        if not analyzer.reset_chip():
            print("⚠️  Reset issues detected, continuing anyway...")
        
        # Analyze communication
        analyzer.analyze_basic_communication()
        
        # Test register access
        analyzer.analyze_register_access()
        
        # Print summary
        analyzer.print_summary()
        
        print("\n💡 RECOMMENDATIONS")
        print("=" * 20)
        
        if analyzer.transactions:
            successful_rate = sum(1 for t in analyzer.transactions if t.success) / len(analyzer.transactions)
            
            if successful_rate > 0.8:
                print("✅ SPI communication appears to be working well")
                print("   If LoRa transmission still fails, check:")
                print("   • Antenna connection")
                print("   • Frequency settings")
                print("   • Power levels")
            elif successful_rate > 0.5:
                print("⚠️  Intermittent SPI communication issues")
                print("   • Check physical connections")
                print("   • Verify power supply stability")
                print("   • Check for electromagnetic interference")
            else:
                print("❌ Significant SPI communication problems")
                print("   • Verify HAT is properly connected")
                print("   • Check SPI is enabled")
                print("   • Confirm correct HAT type (SX126x)")
                print("   • Test with different power supply")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        return 1
    finally:
        analyzer.cleanup()

if __name__ == "__main__":
    sys.exit(main())
