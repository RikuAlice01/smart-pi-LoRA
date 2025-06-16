"""
Tests for configuration management
"""

import pytest
import json
import os
from unittest.mock import patch, mock_open

from core.config import ConfigManager, ConfigError


class TestConfigManager:
    """Test configuration management"""
    
    def test_load_valid_config(self, temp_dir, mock_config):
        """Test loading valid configuration"""
        config_file = os.path.join(temp_dir, "test_config.json")
        with open(config_file, 'w') as f:
            json.dump(mock_config, f)
        
        config_manager = ConfigManager(config_file)
        assert config_manager.get('device.id_prefix') == "test_"
        assert config_manager.get('lora.frequency') == 915.0
    
    def test_load_invalid_config(self, temp_dir):
        """Test loading invalid configuration"""
        config_file = os.path.join(temp_dir, "invalid_config.json")
        with open(config_file, 'w') as f:
            f.write("invalid json")
        
        with pytest.raises(ConfigError):
            ConfigManager(config_file)
    
    def test_missing_config_file(self):
        """Test handling missing configuration file"""
        with pytest.raises(ConfigError):
            ConfigManager("nonexistent.json")
    
    def test_environment_variable_override(self, temp_dir, mock_config):
        """Test environment variable override"""
        config_file = os.path.join(temp_dir, "test_config.json")
        with open(config_file, 'w') as f:
            json.dump(mock_config, f)
        
        with patch.dict(os.environ, {'LORA_FREQUENCY': '868.0'}):
            config_manager = ConfigManager(config_file)
            assert config_manager.get('lora.frequency') == 868.0
    
    def test_nested_config_access(self, temp_dir, mock_config):
        """Test nested configuration access"""
        config_file = os.path.join(temp_dir, "test_config.json")
        with open(config_file, 'w') as f:
            json.dump(mock_config, f)
        
        config_manager = ConfigManager(config_file)
        assert config_manager.get('sensors.mock_data.temperature') == 25.0
        assert config_manager.get('nonexistent.key', 'default') == 'default'
    
    def test_config_validation(self, temp_dir):
        """Test configuration validation"""
        invalid_config = {
            "lora": {
                "frequency": "invalid_frequency"  # Should be float
            }
        }
        
        config_file = os.path.join(temp_dir, "invalid_config.json")
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f)
        
        with pytest.raises(ConfigError):
            ConfigManager(config_file)
