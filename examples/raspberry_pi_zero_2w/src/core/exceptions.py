"""
Custom exceptions for LoRa sensor node
"""

class LoRaNodeError(Exception):
    """Base exception for LoRa node errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = None
        
    def to_dict(self) -> dict:
        """Convert exception to dictionary"""
        return {
            "error": self.__class__.__name__,
            "message": str(self),
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": self.timestamp
        }

class ConfigurationError(LoRaNodeError):
    """Configuration related errors"""
    pass

class HardwareError(LoRaNodeError):
    """Hardware related errors"""
    pass

class CommunicationError(LoRaNodeError):
    """Communication related errors"""
    pass

class SensorError(LoRaNodeError):
    """Sensor related errors"""
    pass

class EncryptionError(LoRaNodeError):
    """Encryption related errors"""
    pass

class StorageError(LoRaNodeError):
    """Data storage related errors"""
    pass

class ValidationError(LoRaNodeError):
    """Data validation errors"""
    pass
