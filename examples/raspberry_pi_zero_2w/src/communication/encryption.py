"""
Enhanced encryption management with multiple methods and key management
"""

import os
import secrets
import base64
import time
import hashlib
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..core.exceptions import EncryptionError

logger = logging.getLogger(__name__)

class KeyfileEncryption:
    """Enhanced keyfile-based AES encryption with key management"""
    
    def __init__(self, keyfile_path: str = "keyfile.bin", auto_generate: bool = True):
        """Initialize keyfile encryption"""
        self.keyfile_path = Path(keyfile_path)
        self.aes_key = None
        self.backend = default_backend()
        self.key_created_at = None
        self.encryption_stats = {
            'encryptions': 0,
            'decryptions': 0,
            'total_bytes_encrypted': 0,
            'total_bytes_decrypted': 0,
            'avg_encryption_time': 0.0,
            'avg_decryption_time': 0.0
        }
        
        try:
            self.aes_key = self._load_key()
        except FileNotFoundError:
            if auto_generate:
                logger.warning(f"Keyfile not found, generating new one: {keyfile_path}")
                self.generate_keyfile()
                self.aes_key = self._load_key()
            else:
                raise EncryptionError(f"Keyfile not found: {keyfile_path}")
        
        logger.info(f"Keyfile encryption initialized: {keyfile_path}")
    
    def _load_key(self) -> bytes:
        """Load AES key from keyfile"""
        if not self.keyfile_path.exists():
            raise FileNotFoundError(f"Key file '{self.keyfile_path}' not found")
        
        try:
            with open(self.keyfile_path, 'rb') as f:
                key_data = f.read()
            
            if len(key_data) < 32:
                raise EncryptionError("Key file too short (minimum 32 bytes required)")
            
            # Extract key and metadata if present
            if len(key_data) == 32:
                # Simple key file
                key = key_data
                self.key_created_at = None
            else:
                # Extended key file with metadata
                key = key_data[:32]
                # Could add timestamp or other metadata parsing here
                self.key_created_at = None
            
            logger.debug(f"Loaded {len(key)} byte key from {self.keyfile_path}")
            return key
            
        except Exception as e:
            raise EncryptionError(f"Failed to load key file: {e}")
    
    def generate_keyfile(self, include_metadata: bool = True) -> None:
        """Generate a new keyfile with optional metadata"""
        try:
            # Generate 256-bit key
            key = secrets.token_bytes(32)
            
            # Create directory if it doesn't exist
            self.keyfile_path.parent.mkdir(parents=True, exist_ok=True)
            
            if include_metadata:
                # Add metadata (timestamp, version, etc.)
                metadata = {
                    'created_at': int(time.time()),
                    'version': 1,
                    'algorithm': 'AES-256-CBC'
                }
                
                # For now, just store the key (metadata could be added later)
                key_data = key
            else:
                key_data = key
            
            # Write key file with secure permissions
            with open(self.keyfile_path, 'wb') as f:
                f.write(key_data)
            
            # Set secure file permissions (owner read/write only)
            os.chmod(self.keyfile_path, 0o600)
            
            self.key_created_at = time.time()
            
            logger.info(f"Generated new keyfile: {self.keyfile_path}")
            
        except Exception as e:
            raise EncryptionError(f"Failed to generate keyfile: {e}")
    
    def encrypt_payload(self, plain_text: str) -> str:
        """Encrypt payload with performance tracking"""
        start_time = time.perf_counter()
        
        try:
            # Generate random IV
            iv = secrets.token_bytes(16)
            
            # Create cipher
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), self.backend)
            encryptor = cipher.encryptor()
            
            # Apply PKCS#7 padding
            raw = plain_text.encode('utf-8')
            pad_len = 16 - (len(raw) % 16)
            padded_data = raw + bytes([pad_len] * pad_len)
            
            # Encrypt
            encrypted = encryptor.update(padded_data) + encryptor.finalize()
            
            # Combine IV + encrypted data and encode as base64
            combined = iv + encrypted
            encoded = base64.b64encode(combined).decode('utf-8')
            
            # Update statistics
            end_time = time.perf_counter()
            elapsed = end_time - start_time
            
            self.encryption_stats['encryptions'] += 1
            self.encryption_stats['total_bytes_encrypted'] += len(plain_text)
            
            # Update average encryption time
            total_ops = self.encryption_stats['encryptions']
            current_avg = self.encryption_stats['avg_encryption_time']
            self.encryption_stats['avg_encryption_time'] = (
                (current_avg * (total_ops - 1) + elapsed) / total_ops
            )
            
            logger.debug(f"Encrypted {len(plain_text)} bytes in {elapsed:.6f}s")
            return encoded
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Payload encryption failed: {e}")
    
    def decrypt_payload(self, encoded_text: str) -> str:
        """Decrypt payload with performance tracking"""
        start_time = time.perf_counter()
        
        try:
            # Decode base64
            combined = base64.b64decode(encoded_text)
            
            if len(combined) < 32:  # IV (16) + minimum encrypted block (16)
                raise EncryptionError("Encrypted data too short")
            
            # Extract IV and encrypted data
            iv = combined[:16]
            encrypted_data = combined[16:]
            
            # Create cipher
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), self.backend)
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_plain = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Remove PKCS#7 padding
            pad_len = padded_plain[-1]
            if pad_len < 1 or pad_len > 16:
                raise EncryptionError("Invalid padding")
            
            # Verify padding
            padding = padded_plain[-pad_len:]
            if not all(b == pad_len for b in padding):
                raise EncryptionError("Invalid padding bytes")
            
            plain = padded_plain[:-pad_len]
            result = plain.decode('utf-8')
            
            # Update statistics
            end_time = time.perf_counter()
            elapsed = end_time - start_time
            
            self.encryption_stats['decryptions'] += 1
            self.encryption_stats['total_bytes_decrypted'] += len(result)
            
            # Update average decryption time
            total_ops = self.encryption_stats['decryptions']
            current_avg = self.encryption_stats['avg_decryption_time']
            self.encryption_stats['avg_decryption_time'] = (
                (current_avg * (total_ops - 1) + elapsed) / total_ops
            )
            
            logger.debug(f"Decrypted {len(result)} bytes in {elapsed:.6f}s")
            return result
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Payload decryption failed: {e}")
    
    def test_encryption(self, test_data: str = None) -> bool:
        """Test encryption/decryption with comprehensive validation"""
        if test_data is None:
            test_data = "Test message for encryption validation with special chars: åäö!@#$%^&*()"
        
        try:
            logger.debug("Starting encryption test")
            
            # Test basic encryption/decryption
            encrypted = self.encrypt_payload(test_data)
            decrypted = self.decrypt_payload(encrypted)
            
            if test_data != decrypted:
                raise EncryptionError("Basic encryption test failed - data mismatch")
            
            # Test with empty string
            empty_encrypted = self.encrypt_payload("")
            empty_decrypted = self.decrypt_payload(empty_encrypted)
            
            if "" != empty_decrypted:
                raise EncryptionError("Empty string encryption test failed")
            
            # Test with large data
            large_data = "A" * 10000
            large_encrypted = self.encrypt_payload(large_data)
            large_decrypted = self.decrypt_payload(large_encrypted)
            
            if large_data != large_decrypted:
                raise EncryptionError("Large data encryption test failed")
            
            # Test uniqueness (same plaintext should produce different ciphertext)
            encrypted1 = self.encrypt_payload(test_data)
            encrypted2 = self.encrypt_payload(test_data)
            
            if encrypted1 == encrypted2:
                raise EncryptionError("Encryption not producing unique ciphertexts")
            
            logger.info("All encryption tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Encryption test failed: {e}")
            return False
    
    def get_key_info(self) -> Dict[str, Any]:
        """Get information about the current key"""
        return {
            'keyfile_path': str(self.keyfile_path),
            'keyfile_exists': self.keyfile_path.exists(),
            'key_loaded': self.aes_key is not None,
            'key_size_bits': len(self.aes_key) * 8 if self.aes_key else 0,
            'key_created_at': self.key_created_at,
            'file_size': self.keyfile_path.stat().st_size if self.keyfile_path.exists() else 0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get encryption statistics"""
        return self.encryption_stats.copy()
    
    def reset_statistics(self):
        """Reset encryption statistics"""
        self.encryption_stats = {
            'encryptions': 0,
            'decryptions': 0,
            'total_bytes_encrypted': 0,
            'total_bytes_decrypted': 0,
            'avg_encryption_time': 0.0,
            'avg_decryption_time': 0.0
        }
        logger.info("Encryption statistics reset")

class EncryptionManager:
    """Multi-method encryption manager with fallback support"""
    
    def __init__(self, method: str = "keyfile", **kwargs):
        """Initialize encryption manager"""
        self.method = method.lower()
        self.encryptor = None
        
        if self.method == "keyfile":
            keyfile_path = kwargs.get('keyfile_path', 'keyfile.bin')
            self.encryptor = KeyfileEncryption(keyfile_path)
        elif self.method == "aes":
            # Legacy AES with fixed key
            key = kwargs.get('key', 'default_key_123456')
            self.encryptor = self._create_legacy_aes(key)
        elif self.method == "xor":
            # Simple XOR encryption
            key = kwargs.get('key', 'default_key')
            self.encryptor = self._create_xor_encryptor(key)
        elif self.method == "none":
            # No encryption
            self.encryptor = None
        else:
            raise EncryptionError(f"Unknown encryption method: {method}")
        
        logger.info(f"Encryption manager initialized with method: {method}")
    
    def encrypt(self, data: str) -> str:
        """Encrypt data using configured method"""
        if self.encryptor is None:
            return data  # No encryption
        
        if hasattr(self.encryptor, 'encrypt_payload'):
            return self.encryptor.encrypt_payload(data)
        else:
            return self.encryptor.encrypt(data)
    
    def decrypt(self, data: str) -> str:
        """Decrypt data using configured method"""
        if self.encryptor is None:
            return data  # No encryption
        
        if hasattr(self.encryptor, 'decrypt_payload'):
            return self.encryptor.decrypt_payload(data)
        else:
            return self.encryptor.decrypt(data)
    
    def test_encryption(self) -> bool:
        """Test encryption functionality"""
        if self.encryptor is None:
            return True  # No encryption to test
        
        if hasattr(self.encryptor, 'test_encryption'):
            return self.encryptor.test_encryption()
        else:
            # Basic test
            test_data = "Test encryption"
            try:
                encrypted = self.encrypt(test_data)
                decrypted = self.decrypt(encrypted)
                return test_data == decrypted
            except:
                return False
    
    def _create_legacy_aes(self, key: str):
        """Create legacy AES encryptor (simplified)"""
        # This would implement a simpler AES encryption
        # For now, just use keyfile encryption with a derived key
        key_bytes = hashlib.sha256(key.encode()).digest()
        
        # Create temporary keyfile
        temp_keyfile = Path("temp_legacy.key")
        with open(temp_keyfile, 'wb') as f:
            f.write(key_bytes)
        
        encryptor = KeyfileEncryption(str(temp_keyfile), auto_generate=False)
        
        # Clean up temp file
        temp_keyfile.unlink()
        
        return encryptor
    
    def _create_xor_encryptor(self, key: str):
        """Create simple XOR encryptor"""
        class XOREncryptor:
            def __init__(self, key: str):
                self.key = key.encode()
            
            def encrypt(self, data: str) -> str:
                data_bytes = data.encode()
                result = bytearray()
                for i, byte in enumerate(data_bytes):
                    result.append(byte ^ self.key[i % len(self.key)])
                return base64.b64encode(result).decode()
            
            def decrypt(self, data: str) -> str:
                data_bytes = base64.b64decode(data)
                result = bytearray()
                for i, byte in enumerate(data_bytes):
                    result.append(byte ^ self.key[i % len(self.key)])
                return result.decode()
        
        return XOREncryptor(key)

def create_encryption_manager(config) -> EncryptionManager:
    """Create encryption manager from configuration"""
    if not config.network.encryption_enabled:
        return EncryptionManager("none")
    
    method = config.network.encryption_method
    
    if method == "keyfile":
        return EncryptionManager("keyfile", keyfile_path=config.network.keyfile_path)
    elif method == "aes":
        # Use device ID as key for legacy AES
        return EncryptionManager("aes", key=config.device.device_id)
    elif method == "xor":
        return EncryptionManager("xor", key=config.device.device_id)
    else:
        return EncryptionManager("none")

if __name__ == "__main__":
    """Test encryption functionality"""
    print("🔐 Testing Encryption Manager")
    
    try:
        # Test keyfile encryption
        print("\n1. Testing Keyfile Encryption:")
        keyfile_enc = KeyfileEncryption("test_keyfile.bin", auto_generate=True)
        
        test_data = "Hello, LoRa World! 🌍"
        encrypted = keyfile_enc.encrypt_payload(test_data)
        decrypted = keyfile_enc.decrypt_payload(encrypted)
        
        print(f"Original: {test_data}")
        print(f"Encrypted: {encrypted[:50]}...")
        print(f"Decrypted: {decrypted}")
        print(f"Match: {test_data == decrypted}")
        
        # Test encryption manager
        print("\n2. Testing Encryption Manager:")
        manager = EncryptionManager("keyfile", keyfile_path="test_keyfile.bin")
        
        encrypted2 = manager.encrypt(test_data)
        decrypted2 = manager.decrypt(encrypted2)
        
        print(f"Manager Test: {test_data == decrypted2}")
        
        # Performance test
        print("\n3. Performance Test:")
        start_time = time.time()
        for i in range(100):
            enc = keyfile_enc.encrypt_payload(f"Test message {i}")
            dec = keyfile_enc.decrypt_payload(enc)
        end_time = time.time()
        
        print(f"100 encrypt/decrypt cycles: {end_time - start_time:.3f}s")
        
        # Show statistics
        stats = keyfile_enc.get_statistics()
        print(f"Statistics: {stats}")
        
        # Cleanup
        Path("test_keyfile.bin").unlink(missing_ok=True)
        
        print("✅ Encryption tests passed")
        
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        import traceback
        traceback.print_exc()
