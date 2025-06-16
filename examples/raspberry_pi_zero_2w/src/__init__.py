"""
LoRa SX126x Sensor Node for Raspberry Pi Zero 2W
High-quality, production-ready sensor node implementation
"""

__version__ = "2.0.0"
__author__ = "LoRa Gateway Team"
__description__ = "Professional LoRa sensor node with advanced features"

# Version information
VERSION_INFO = {
    "major": 2,
    "minor": 0,
    "patch": 0,
    "release": "stable"
}

def get_version() -> str:
    """Get version string"""
    return __version__

def get_version_info() -> dict:
    """Get detailed version information"""
    return VERSION_INFO.copy()
