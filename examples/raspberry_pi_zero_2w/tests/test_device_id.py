"""
Tests for device ID generation
"""

import pytest
from unittest.mock import patch

from core.device_id import DeviceIDManager, DeviceIDError


class TestDeviceIDManager:
    """Test device ID management"""
    
    @patch('uuid.getnode')
    def test_mac_based_id_generation(self, mock_getnode):
        """Test MAC-based device ID generation"""
        mock_getnode.return_value = 0x123456789ABC
        
        device_id = DeviceIDManager.generate_mac_based_id("node_")
        assert device_id == "node_789ABC"
    
    @patch('uuid.getnode')
    def test_mac_based_id_with_different_prefix(self, mock_getnode):
        """Test MAC-based ID with different prefix"""
        mock_getnode.return_value = 0x123456789ABC
        
        device_id = DeviceIDManager.generate_mac_based_id("sensor_")
        assert device_id == "sensor_789ABC"
    
    def test_random_id_generation(self):
        """Test random device ID generation"""
        device_id = DeviceIDManager.generate_random_id("test_")
        assert device_id.startswith("test_")
        assert len(device_id) == 13  # "test_" + 8 random chars
    
    def test_custom_id_validation(self):
        """Test custom device ID validation"""
        # Valid IDs
        assert DeviceIDManager.validate_device_id("node_123456")
        assert DeviceIDManager.validate_device_id("sensor_ABC123")
        
        # Invalid IDs
        assert not DeviceIDManager.validate_device_id("")
        assert not DeviceIDManager.validate_device_id("toolong_" + "x" * 50)
        assert not DeviceIDManager.validate_device_id("invalid chars!")
    
    def test_id_conflict_detection(self):
        """Test device ID conflict detection"""
        existing_ids = ["node_123456", "sensor_789ABC"]
        
        # Should detect conflict
        assert DeviceIDManager.check_conflict("node_123456", existing_ids)
        
        # Should not detect conflict
        assert not DeviceIDManager.check_conflict("node_NEWID", existing_ids)
