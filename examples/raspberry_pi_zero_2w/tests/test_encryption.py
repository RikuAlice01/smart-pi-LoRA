"""
Tests for encryption functionality
"""

import pytest
import os
from unittest.mock import patch, mock_open

from communication.encryption import EncryptionManager, EncryptionError


class TestEncryptionManager:
    """Test encryption management"""
    
    def test_keyfile_loading(self, mock_keyfile):
        """Test keyfile loading"""
        encryption_manager = EncryptionManager(mock_keyfile)
        assert encryption_manager.key is not None
        assert len(encryption_manager.key) == 32
    
    def test_missing_keyfile(self):
        """Test handling missing keyfile"""
        with pytest.raises(EncryptionError):
            EncryptionManager("nonexistent_keyfile.bin")
    
    def test_invalid_keyfile_size(self, temp_dir):
        """Test handling invalid keyfile size"""
        keyfile_path = os.path.join(temp_dir, "invalid_keyfile.bin")
        with open(keyfile_path, 'wb') as f:
            f.write(b'\x01' * 16)  # Wrong size (16 bytes instead of 32)
        
        with pytest.raises(EncryptionError):
            EncryptionManager(keyfile_path)
    
    def test_encrypt_decrypt_cycle(self, mock_keyfile):
        """Test encryption and decryption cycle"""
        encryption_manager = EncryptionManager(mock_keyfile)
        
        original_text = "Hello, LoRa World!"
        encrypted = encryption_manager.encrypt(original_text)
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == original_text
        assert encrypted != original_text
    
    def test_encrypt_empty_string(self, mock_keyfile):
        """Test encrypting empty string"""
        encryption_manager = EncryptionManager(mock_keyfile)
        
        encrypted = encryption_manager.encrypt("")
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == ""
    
    def test_decrypt_invalid_data(self, mock_keyfile):
        """Test decrypting invalid data"""
        encryption_manager = EncryptionManager(mock_keyfile)
        
        with pytest.raises(EncryptionError):
            encryption_manager.decrypt("invalid_encrypted_data")
    
    def test_performance_tracking(self, mock_keyfile):
        """Test encryption performance tracking"""
        encryption_manager = EncryptionManager(mock_keyfile)
        
        text = "Performance test data" * 100
        encrypted = encryption_manager.encrypt(text)
        
        # Check that performance metrics are recorded
        assert hasattr(encryption_manager, '_last_encrypt_time')
        assert encryption_manager._last_encrypt_time > 0
