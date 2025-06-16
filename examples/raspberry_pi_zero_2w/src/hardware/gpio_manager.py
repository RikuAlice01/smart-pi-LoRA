"""
Enhanced GPIO management with safety features and monitoring
"""

import logging
import time
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from ..core.exceptions import HardwareError

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available - using mock GPIO")

class MockGPIO:
    """Mock GPIO for testing without hardware"""
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    PUD_UP = "PUD_UP"
    PUD_DOWN = "PUD_DOWN"
    HIGH = 1
    LOW = 0
    
    @staticmethod
    def setmode(mode): pass
    @staticmethod
    def setup(pin, mode, pull_up_down=None): pass
    @staticmethod
    def output(pin, value): pass
    @staticmethod
    def input(pin): return 0
    @staticmethod
    def cleanup(): pass
    @staticmethod
    def setwarnings(enabled): pass

class GPIOManager:
    """Enhanced GPIO management with safety and monitoring"""
    
    def __init__(self, mock_mode: bool = False):
        """Initialize GPIO manager"""
        self.mock_mode = mock_mode or not GPIO_AVAILABLE
        self.gpio = MockGPIO if self.mock_mode else GPIO
        self.initialized = False
        self.allocated_pins: Dict[int, str] = {}
        self.pin_states: Dict[int, Any] = {}
        
        if self.mock_mode:
            logger.warning("GPIO manager running in mock mode")
        
        self._initialize_gpio()
    
    def _initialize_gpio(self):
        """Initialize GPIO system"""
        try:
            if not self.mock_mode:
                self.gpio.setwarnings(False)
                self.gpio.setmode(self.gpio.BCM)
            
            self.initialized = True
            logger.info("GPIO system initialized")
            
        except Exception as e:
            raise HardwareError(f"Failed to initialize GPIO: {e}")
    
    def allocate_pin(self, pin: int, mode: str, purpose: str, 
                    pull_up_down: Optional[str] = None) -> bool:
        """
        Allocate a GPIO pin with conflict checking
        
        Args:
            pin: GPIO pin number
            mode: Pin mode ('OUT', 'IN')
            purpose: Description of pin usage
            pull_up_down: Pull-up/down resistor setting
        """
        try:
            # Check if pin is already allocated
            if pin in self.allocated_pins:
                existing_purpose = self.allocated_pins[pin]
                if existing_purpose != purpose:
                    raise HardwareError(
                        f"Pin {pin} already allocated for {existing_purpose}, "
                        f"cannot allocate for {purpose}"
                    )
                return True
            
            # Validate pin number
            if not self._is_valid_pin(pin):
                raise HardwareError(f"Invalid GPIO pin number: {pin}")
            
            # Setup pin
            gpio_mode = getattr(self.gpio, mode)
            setup_kwargs = {}
            
            if pull_up_down:
                setup_kwargs['pull_up_down'] = getattr(self.gpio, pull_up_down)
            
            self.gpio.setup(pin, gpio_mode, **setup_kwargs)
            
            # Track allocation
            self.allocated_pins[pin] = purpose
            self.pin_states[pin] = {
                'mode': mode,
                'purpose': purpose,
                'pull_up_down': pull_up_down,
                'allocated_at': time.time()
            }
            
            logger.debug(f"Allocated GPIO pin {pin} for {purpose} ({mode})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to allocate GPIO pin {pin}: {e}")
            raise HardwareError(f"GPIO pin allocation failed: {e}")
    
    def deallocate_pin(self, pin: int):
        """Deallocate a GPIO pin"""
        try:
            if pin in self.allocated_pins:
                purpose = self.allocated_pins[pin]
                del self.allocated_pins[pin]
                del self.pin_states[pin]
                logger.debug(f"Deallocated GPIO pin {pin} (was: {purpose})")
            
        except Exception as e:
            logger.error(f"Failed to deallocate GPIO pin {pin}: {e}")
    
    def set_output(self, pin: int, value: bool):
        """Set output pin value with validation"""
        try:
            if pin not in self.allocated_pins:
                raise HardwareError(f"Pin {pin} not allocated")
            
            pin_info = self.pin_states[pin]
            if pin_info['mode'] != 'OUT':
                raise HardwareError(f"Pin {pin} not configured as output")
            
            gpio_value = self.gpio.HIGH if value else self.gpio.LOW
            self.gpio.output(pin, gpio_value)
            
            # Update state tracking
            pin_info['last_value'] = value
            pin_info['last_update'] = time.time()
            
            logger.debug(f"Set GPIO pin {pin} to {'HIGH' if value else 'LOW'}")
            
        except Exception as e:
            logger.error(f"Failed to set GPIO pin {pin}: {e}")
            raise HardwareError(f"GPIO output failed: {e}")
    
    def get_input(self, pin: int) -> bool:
        """Read input pin value with validation"""
        try:
            if pin not in self.allocated_pins:
                raise HardwareError(f"Pin {pin} not allocated")
            
            pin_info = self.pin_states[pin]
            if pin_info['mode'] != 'IN':
                raise HardwareError(f"Pin {pin} not configured as input")
            
            value = self.gpio.input(pin)
            
            # Update state tracking
            pin_info['last_value'] = bool(value)
            pin_info['last_read'] = time.time()
            
            return bool(value)
            
        except Exception as e:
            logger.error(f"Failed to read GPIO pin {pin}: {e}")
            raise HardwareError(f"GPIO input failed: {e}")
    
    def pulse_output(self, pin: int, duration: float = 0.1, active_high: bool = True):
        """Generate a pulse on output pin"""
        try:
            initial_state = not active_high
            pulse_state = active_high
            
            self.set_output(pin, initial_state)
            time.sleep(0.001)  # Small delay
            self.set_output(pin, pulse_state)
            time.sleep(duration)
            self.set_output(pin, initial_state)
            
            logger.debug(f"Generated {duration}s pulse on GPIO pin {pin}")
            
        except Exception as e:
            logger.error(f"Failed to pulse GPIO pin {pin}: {e}")
            raise HardwareError(f"GPIO pulse failed: {e}")
    
    def wait_for_edge(self, pin: int, edge: str, timeout: float = 1.0) -> bool:
        """
        Wait for edge on input pin (simplified implementation)
        
        Args:
            pin: GPIO pin number
            edge: Edge type ('RISING', 'FALLING', 'BOTH')
            timeout: Timeout in seconds
        
        Returns:
            True if edge detected, False if timeout
        """
        try:
            if pin not in self.allocated_pins:
                raise HardwareError(f"Pin {pin} not allocated")
            
            if self.mock_mode:
                # Mock implementation - just wait and return True
                time.sleep(min(timeout, 0.1))
                return True
            
            # Simple polling implementation
            start_time = time.time()
            last_state = self.get_input(pin)
            
            while time.time() - start_time < timeout:
                current_state = self.get_input(pin)
                
                if edge == 'RISING' and not last_state and current_state:
                    return True
                elif edge == 'FALLING' and last_state and not current_state:
                    return True
                elif edge == 'BOTH' and last_state != current_state:
                    return True
                
                last_state = current_state
                time.sleep(0.001)  # Small delay to prevent excessive CPU usage
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to wait for edge on GPIO pin {pin}: {e}")
            raise HardwareError(f"GPIO edge detection failed: {e}")
    
    def get_pin_info(self, pin: int) -> Optional[Dict[str, Any]]:
        """Get information about allocated pin"""
        return self.pin_states.get(pin)
    
    def get_allocated_pins(self) -> Dict[int, str]:
        """Get all allocated pins"""
        return self.allocated_pins.copy()
    
    def get_pin_status(self) -> Dict[str, Any]:
        """Get comprehensive GPIO status"""
        return {
            'initialized': self.initialized,
            'mock_mode': self.mock_mode,
            'allocated_pins': len(self.allocated_pins),
            'pins': self.pin_states.copy()
        }
    
    def _is_valid_pin(self, pin: int) -> bool:
        """Check if pin number is valid for Raspberry Pi"""
        # Valid GPIO pins on Raspberry Pi (BCM numbering)
        valid_pins = list(range(2, 28))  # GPIO 2-27
        return pin in valid_pins
    
    @contextmanager
    def pin_context(self, pin: int, mode: str, purpose: str, **kwargs):
        """Context manager for temporary pin allocation"""
        try:
            self.allocate_pin(pin, mode, purpose, **kwargs)
            yield self
        finally:
            self.deallocate_pin(pin)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            if not self.mock_mode and self.initialized:
                self.gpio.cleanup()
            
            self.allocated_pins.clear()
            self.pin_states.clear()
            self.initialized = False
            
            logger.info("GPIO cleanup completed")
            
        except Exception as e:
            logger.error(f"GPIO cleanup failed: {e}")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass

# Global GPIO manager instance
_gpio_manager = None

def get_gpio_manager(mock_mode: bool = False) -> GPIOManager:
    """Get global GPIO manager instance"""
    global _gpio_manager
    
    if _gpio_manager is None:
        _gpio_manager = GPIOManager(mock_mode)
    
    return _gpio_manager

if __name__ == "__main__":
    """Test GPIO manager"""
    print("🔌 Testing GPIO Manager")
    
    try:
        gpio_mgr = GPIOManager(mock_mode=True)
        
        # Test pin allocation
        gpio_mgr.allocate_pin(18, 'OUT', 'LED Test')
        gpio_mgr.allocate_pin(24, 'IN', 'Button Test', 'PUD_UP')
        
        # Test operations
        gpio_mgr.set_output(18, True)
        time.sleep(0.1)
        gpio_mgr.set_output(18, False)
        
        button_state = gpio_mgr.get_input(24)
        print(f"Button state: {button_state}")
        
        # Test pulse
        gpio_mgr.pulse_output(18, 0.05)
        
        # Show status
        status = gpio_mgr.get_pin_status()
        print(f"GPIO Status: {status}")
        
        print("✅ GPIO manager test passed")
        
    except Exception as e:
        print(f"❌ GPIO manager test failed: {e}")
    finally:
        if 'gpio_mgr' in locals():
            gpio_mgr.cleanup()
