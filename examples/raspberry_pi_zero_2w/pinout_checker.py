#!/usr/bin/env python3
"""
Visual pinout checker and comparison tool
Shows expected vs actual pin usage for different HAT types
"""

import sys
from typing import Dict, List, Optional
from enum import Enum

class PinType(Enum):
    POWER_3V3 = "3.3V"
    POWER_5V = "5V"
    GROUND = "GND"
    SPI = "SPI"
    I2C = "I2C"
    UART = "UART"
    GPIO = "GPIO"
    SPECIAL = "SPECIAL"

def get_pi_zero_2w_pinout() -> Dict[int, Dict[str, str]]:
    """Get Pi Zero 2W standard pinout"""
    return {
        1: {"name": "3.3V", "type": PinType.POWER_3V3, "gpio": None},
        2: {"name": "5V", "type": PinType.POWER_5V, "gpio": None},
        3: {"name": "SDA1", "type": PinType.I2C, "gpio": 2},
        4: {"name": "5V", "type": PinType.POWER_5V, "gpio": None},
        5: {"name": "SCL1", "type": PinType.I2C, "gpio": 3},
        6: {"name": "GND", "type": PinType.GROUND, "gpio": None},
        7: {"name": "GPIO4", "type": PinType.GPIO, "gpio": 4},
        8: {"name": "TXD0", "type": PinType.UART, "gpio": 14},
        9: {"name": "GND", "type": PinType.GROUND, "gpio": None},
        10: {"name": "RXD0", "type": PinType.UART, "gpio": 15},
        11: {"name": "GPIO17", "type": PinType.GPIO, "gpio": 17},
        12: {"name": "GPIO18", "type": PinType.GPIO, "gpio": 18},
        13: {"name": "GPIO27", "type": PinType.GPIO, "gpio": 27},
        14: {"name": "GND", "type": PinType.GROUND, "gpio": None},
        15: {"name": "GPIO22", "type": PinType.GPIO, "gpio": 22},
        16: {"name": "GPIO23", "type": PinType.GPIO, "gpio": 23},
        17: {"name": "3.3V", "type": PinType.POWER_3V3, "gpio": None},
        18: {"name": "GPIO24", "type": PinType.GPIO, "gpio": 24},
        19: {"name": "MOSI", "type": PinType.SPI, "gpio": 10},
        20: {"name": "GND", "type": PinType.GROUND, "gpio": None},
        21: {"name": "MISO", "type": PinType.SPI, "gpio": 9},
        22: {"name": "GPIO25", "type": PinType.GPIO, "gpio": 25},
        23: {"name": "SCLK", "type": PinType.SPI, "gpio": 11},
        24: {"name": "CE0", "type": PinType.SPI, "gpio": 8},
        25: {"name": "GND", "type": PinType.GROUND, "gpio": None},
        26: {"name": "CE1", "type": PinType.SPI, "gpio": 7},
        27: {"name": "ID_SD", "type": PinType.SPECIAL, "gpio": 0},
        28: {"name": "ID_SC", "type": PinType.SPECIAL, "gpio": 1},
        29: {"name": "GPIO5", "type": PinType.GPIO, "gpio": 5},
        30: {"name": "GND", "type": PinType.GROUND, "gpio": None},
        31: {"name": "GPIO6", "type": PinType.GPIO, "gpio": 6},
        32: {"name": "GPIO12", "type": PinType.GPIO, "gpio": 12},
        33: {"name": "GPIO13", "type": PinType.GPIO, "gpio": 13},
        34: {"name": "GND", "type": PinType.GROUND, "gpio": None},
        35: {"name": "GPIO19", "type": PinType.GPIO, "gpio": 19},
        36: {"name": "GPIO16", "type": PinType.GPIO, "gpio": 16},
        37: {"name": "GPIO26", "type": PinType.GPIO, "gpio": 26},
        38: {"name": "GPIO20", "type": PinType.GPIO, "gpio": 20},
        39: {"name": "GND", "type": PinType.GROUND, "gpio": None},
        40: {"name": "GPIO21", "type": PinType.GPIO, "gpio": 21},
    }

def get_hat_pinout_usage(hat_name: str) -> Dict[int, str]:
    """Get HAT-specific pin usage"""
    hat_configs = {
        "Waveshare SX1262": {
            15: "RESET (GPIO22)",
            16: "BUSY (GPIO23)", 
            18: "DIO1 (GPIO24)",
            19: "SPI MOSI",
            21: "SPI MISO",
            23: "SPI SCLK",
            24: "SPI CE0",
            1: "3.3V Power",
            17: "3.3V Power",
            6: "Ground",
            9: "Ground",
            14: "Ground",
            20: "Ground",
            25: "Ground",
            30: "Ground",
            34: "Ground",
            39: "Ground"
        },
        
        "Waveshare SX1268": {
            15: "RESET (GPIO22)",
            16: "BUSY (GPIO23)",
            18: "DIO1 (GPIO24)",
            12: "LED (GPIO18)",
            19: "SPI MOSI",
            21: "SPI MISO", 
            23: "SPI SCLK",
            24: "SPI CE0",
            1: "3.3V Power",
            17: "3.3V Power",
            6: "Ground",
            9: "Ground",
            14: "Ground",
            20: "Ground",
            25: "Ground",
            30: "Ground",
            34: "Ground",
            39: "Ground"
        },
        
        "Adafruit RFM95W": {
            22: "DIO1 (GPIO25)",  # Different pinout!
            16: "DIO2 (GPIO23)",
            18: "DIO3 (GPIO24)",
            11: "RESET (GPIO17)",  # Different reset pin!
            19: "SPI MOSI",
            21: "SPI MISO",
            23: "SPI SCLK", 
            24: "SPI CE0",
            1: "3.3V Power",
            17: "3.3V Power",
            6: "Ground",
            9: "Ground",
            14: "Ground",
            20: "Ground",
            25: "Ground",
            30: "Ground",
            34: "Ground",
            39: "Ground"
        },
        
        "Generic SX126x": {
            15: "RESET (GPIO22)",
            16: "BUSY (GPIO23)",
            18: "DIO1 (GPIO24)",
            19: "SPI MOSI",
            21: "SPI MISO",
            23: "SPI SCLK",
            24: "SPI CE0",
            1: "3.3V Power",
            17: "3.3V Power",
            6: "Ground",
            9: "Ground",
            14: "Ground",
            20: "Ground",
            25: "Ground",
            30: "Ground",
            34: "Ground",
            39: "Ground"
        }
    }
    
    return hat_configs.get(hat_name, hat_configs["Generic SX126x"])

def print_pinout_diagram(hat_name: str):
    """Print visual pinout diagram"""
    pi_pinout = get_pi_zero_2w_pinout()
    hat_usage = get_hat_pinout_usage(hat_name)
    
    print(f"📌 Pi Zero 2W Pinout with {hat_name} HAT")
    print("=" * 70)
    print()
    
    # Color codes for different pin types
    colors = {
        PinType.POWER_3V3: "🟡",
        PinType.POWER_5V: "🔴", 
        PinType.GROUND: "⚫",
        PinType.SPI: "🔵",
        PinType.I2C: "🟢",
        PinType.UART: "🟣",
        PinType.GPIO: "⚪",
        PinType.SPECIAL: "🟠"
    }
    
    print("   Pi Pin Layout (40-pin GPIO header)")
    print("   ===================================")
    print()
    
    # Print header
    print("   Pin │ GPIO │  Pi Function  │     HAT Usage")
    print("   ────┼──────┼───────────────┼─────────────────────")
    
    # Print pins in pairs (odd on left, even on right)
    for i in range(1, 41, 2):
        left_pin = i
        right_pin = i + 1
        
        # Left pin info
        left_info = pi_pinout[left_pin]
        left_gpio = f"GPIO{left_info['gpio']}" if left_info['gpio'] is not None else "  -  "
        left_color = colors.get(left_info['type'], "⚪")
        left_hat = hat_usage.get(left_pin, "")
        
        # Right pin info  
        right_info = pi_pinout[right_pin]
        right_gpio = f"GPIO{right_info['gpio']}" if right_info['gpio'] is not None else "  -  "
        right_color = colors.get(right_info['type'], "⚪")
        right_hat = hat_usage.get(right_pin, "")
        
        # Format and print
        print(f"   {left_pin:2d} │ {left_gpio:4s} │ {left_color} {left_info['name']:11s} │ {left_hat}")
        print(f"   {right_pin:2d} │ {right_gpio:4s} │ {right_color} {right_info['name']:11s} │ {right_hat}")
        
        if i < 39:  # Don't print separator after last pair
            print("   ────┼──────┼───────────────┼─────────────────────")
    
    print()
    print("   Legend:")
    print("   🔴 5V Power    🟡 3.3V Power   ⚫ Ground")
    print("   🔵 SPI         🟢 I2C          🟣 UART")
    print("   ⚪ GPIO        🟠 Special      ")
    print()

def compare_hat_pinouts():
    """Compare pinouts between different HAT types"""
    print("🔍 HAT Pinout Comparison")
    print("=" * 50)
    print()
    
    hat_types = ["Waveshare SX1262", "Waveshare SX1268", "Adafruit RFM95W"]
    
    # Get critical pins for each HAT
    critical_pins = {}
    for hat in hat_types:
        usage = get_hat_pinout_usage(hat)
        critical_pins[hat] = {}
        
        for pin, function in usage.items():
            if any(keyword in function.upper() for keyword in ["RESET", "BUSY", "DIO", "LED"]):
                critical_pins[hat][pin] = function
    
    print("Critical Pin Differences:")
    print("=" * 30)
    
    # Find all unique pins used
    all_pins = set()
    for hat_pins in critical_pins.values():
        all_pins.update(hat_pins.keys())
    
    # Print comparison table
    print(f"{'Pin':>3} │ {'Waveshare SX1262':^18} │ {'Waveshare SX1268':^18} │ {'Adafruit RFM95W':^18}")
    print("────┼────────────────────┼────────────────────┼────────────────────")
    
    for pin in sorted(all_pins):
        sx1262 = critical_pins["Waveshare SX1262"].get(pin, "")
        sx1268 = critical_pins["Waveshare SX1268"].get(pin, "")
        rfm95w = critical_pins["Adafruit RFM95W"].get(pin, "")
        
        # Highlight differences
        if sx1262 != rfm95w or sx1268 != rfm95w:
            marker = " ⚠️ "
        else:
            marker = "   "
        
        print(f"{pin:3d} │ {sx1262:^18} │ {sx1268:^18} │ {rfm95w:^18}{marker}")
    
    print()
    print("⚠️  = Pinout difference detected")
    print()
    
    # Highlight major differences
    print("🚨 CRITICAL DIFFERENCES:")
    print("=" * 25)
    print("• Adafruit RFM95W uses GPIO17 for RESET (Pin 11)")
    print("  Waveshare HATs use GPIO22 for RESET (Pin 15)")
    print()
    print("• Adafruit RFM95W uses GPIO25 for DIO1 (Pin 22)")
    print("  Waveshare HATs use GPIO24 for DIO1 (Pin 18)")
    print()
    print("• Adafruit RFM95W has NO BUSY pin")
    print("  Waveshare HATs use GPIO23 for BUSY (Pin 16)")
    print()
    print("💡 Always verify your HAT's specific pinout!")

def check_current_gpio_usage():
    """Check what GPIO pins are currently in use"""
    print("🔍 Current GPIO Pin Usage")
    print("=" * 30)
    
    try:
        import os
        
        gpio_path = "/sys/class/gpio"
        if not os.path.exists(gpio_path):
            print("❌ GPIO sysfs not available")
            return
        
        # Check exported pins
        exported_pins = []
        for item in os.listdir(gpio_path):
            if item.startswith("gpio"):
                try:
                    pin_num = int(item[4:])
                    exported_pins.append(pin_num)
                except:
                    continue
        
        if exported_pins:
            print("📌 Currently exported GPIO pins:")
            pi_pinout = get_pi_zero_2w_pinout()
            
            for pin_num in sorted(exported_pins):
                # Find physical pin number
                physical_pin = None
                for phys_pin, info in pi_pinout.items():
                    if info["gpio"] == pin_num:
                        physical_pin = phys_pin
                        break
                
                if physical_pin:
                    print(f"   GPIO{pin_num:2d} (Pin {physical_pin:2d})")
                else:
                    print(f"   GPIO{pin_num:2d} (Pin ?)")
        else:
            print("✅ No GPIO pins currently exported")
        
        # Check for potential conflicts with common HAT pins
        common_hat_pins = [22, 23, 24, 25]  # RESET, BUSY, DIO1, DIO2
        conflicts = set(exported_pins) & set(common_hat_pins)
        
        if conflicts:
            print(f"\n⚠️  Potential conflicts with HAT pins: GPIO{list(conflicts)}")
            print("   Consider stopping other GPIO-using services")
        else:
            print("\n✅ No conflicts with common HAT pins")
            
    except Exception as e:
        print(f"❌ Error checking GPIO usage: {e}")

def main():
    """Main pinout checker"""
    print("📌 LoRa HAT Pinout Checker for Pi Zero 2W")
    print("=" * 45)
    print()
    
    while True:
        print("Choose an option:")
        print("1. Show Waveshare SX1262 pinout")
        print("2. Show Waveshare SX1268 pinout") 
        print("3. Show Adafruit RFM95W pinout")
        print("4. Show Generic SX126x pinout")
        print("5. Compare HAT pinouts")
        print("6. Check current GPIO usage")
        print("7. Exit")
        print()
        
        try:
            choice = input("Enter choice (1-7): ").strip()
            print()
            
            if choice == "1":
                print_pinout_diagram("Waveshare SX1262")
            elif choice == "2":
                print_pinout_diagram("Waveshare SX1268")
            elif choice == "3":
                print_pinout_diagram("Adafruit RFM95W")
            elif choice == "4":
                print_pinout_diagram("Generic SX126x")
            elif choice == "5":
                compare_hat_pinouts()
            elif choice == "6":
                check_current_gpio_usage()
            elif choice == "7":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-7.")
            
            print("\n" + "="*60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

if __name__ == "__main__":
    sys.exit(main())
