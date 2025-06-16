"""
Pytest configuration and fixtures
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "device": {
            "id_prefix": "test_",
            "name": "Test Node"
        },
        "lora": {
            "frequency": 915.0,
            "tx_power": 14,
            "spreading_factor": 7,
            "bandwidth": 125000,
            "coding_rate": 5,
            "preamble_length": 8
        },
        "sensors": {
            "enabled": ["temperature", "humidity"],
            "interval": 30,
            "mock_data": {
                "temperature": 25.0,
                "humidity": 60.0,
                "ph": 7.0
            }
        },
        "encryption": {
            "enabled": True,
            "keyfile": "test_keyfile.bin"
        }
    }

@pytest.fixture
def mock_keyfile(temp_dir):
    """Create mock keyfile for testing"""
    keyfile_path = os.path.join(temp_dir, "test_keyfile.bin")
    # Generate 32-byte key
    key = b'\x01' * 32
    with open(keyfile_path, 'wb') as f:
        f.write(key)
    return keyfile_path

@pytest.fixture
def mock_gpio():
    """Mock GPIO for testing"""
    with patch('RPi.GPIO') as mock:
        yield mock

@pytest.fixture
def mock_spi():
    """Mock SPI for testing"""
    with patch('spidev.SpiDev') as mock:
        yield mock
