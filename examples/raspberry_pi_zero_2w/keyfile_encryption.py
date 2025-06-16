"""
Keyfile-based AES encryption module for LoRa communications
Compatible with the sample lora_send.py encryption method
"""

import os
import secrets
import base64
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class KeyfileEncryption:
    """AES encryption using keyfile.bin - compatible with sample code"""
    
    def __init__(self, keyfile_path: str = "keyfile.bin"):
        """Initialize encryption with keyfile"""
        self.keyfile_path = keyfile_path
        self.aes_key = self.load_key()
        self.backend = default_backend()
        
        logger.info(f"Keyfile encryption initialized with {keyfile_path}")
    
    def load_key(self) -> bytes:
        """Load AES key from keyfile.bin"""
        if not os.path.exists(self.keyfile_path):
            raise FileNotFoundError(f"Key file '{self.keyfile_path}' not found.")
        
        with open(self.keyfile_path, 'rb') as f:
            key = f.read()
            if len(key) != 32:
                raise ValueError("Key length must be exactly 32 bytes (256 bits).")
            return key
    
    def generate_keyfile(self) -> None:
        """Generate a new 256-bit AES key and save to keyfile.bin"""
        key = secrets.token_bytes(32)  # 256-bit key
        
        with open(self.keyfile_path, 'wb') as f:
            f.write(key)
        
        logger.info(f"New keyfile generated: {self.keyfile_path}")
        print(f"🔑 Generated new keyfile: {self.keyfile_path}")
        print("⚠️  IMPORTANT: Copy this keyfile to all devices that need to communicate!")
    
    def encrypt_payload(self, plain_text: str) -> str:
        """
        Encrypt payload using AES-256-CBC with random IV
        Compatible with sample lora_send.py encryption
        """
        start_time = time.perf_counter()
        
        # Generate random IV (16 bytes)
        iv = secrets.token_bytes(16)
        
        # Create cipher
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), self.backend)
        encryptor = cipher.encryptor()
        
        # PKCS#7 padding
        raw = plain_text.encode('utf-8')
        pad_len = 16 - (len(raw) % 16)
        padded_data = raw + bytes([pad_len] * pad_len)
        
        # Encrypt
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Encode as base64 (IV + encrypted data)
        encoded = base64.b64encode(iv + encrypted).decode('utf-8')
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        logger.debug(f"Encryption time: {elapsed:.6f} seconds")
        
        return encoded
    
    def decrypt_payload(self, encoded_text: str) -> str:
        """
        Decrypt payload using AES-256-CBC
        Compatible with sample lora_receiver.py decryption
        """
        start_time = time.perf_counter()
        
        try:
            # Decode base64
            raw = base64.b64decode(encoded_text)
            
            # Extract IV and encrypted data
            iv = raw[:16]
            encrypted_data = raw[16:]
            
            # Create cipher
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), self.backend)
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_plain = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Remove PKCS#7 padding
            pad_len = padded_plain[-1]
            if pad_len < 1 or pad_len > 16:
                raise ValueError("Invalid padding length.")
            
            plain = padded_plain[:-pad_len]
            
            end_time = time.perf_counter()
            elapsed = end_time - start_time
            logger.debug(f"Decryption time: {elapsed:.6f} seconds")
            
            return plain.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def test_encryption(self) -> bool:
        """Test encryption/decryption functionality"""
        test_message = "Test message for encryption validation"
        
        try:
            # Encrypt
            encrypted = self.encrypt_payload(test_message)
            logger.debug(f"Test encrypted: {encrypted}")
            
            # Decrypt
            decrypted = self.decrypt_payload(encrypted)
            logger.debug(f"Test decrypted: {decrypted}")
            
            # Verify
            success = test_message == decrypted
            if success:
                logger.info("Encryption test passed")
            else:
                logger.error("Encryption test failed - messages don't match")
            
            return success
            
        except Exception as e:
            logger.error(f"Encryption test failed: {e}")
            return False

def create_keyfile_if_missing(keyfile_path: str = "keyfile.bin") -> bool:
    """Create keyfile if it doesn't exist"""
    if not os.path.exists(keyfile_path):
        print(f"🔑 Keyfile not found: {keyfile_path}")
        response = input("Generate new keyfile? (y/N): ").lower().strip()
        
        if response == 'y':
            encryption = KeyfileEncryption(keyfile_path)
            encryption.generate_keyfile()
            return True
        else:
            print("❌ Cannot proceed without keyfile")
            return False
    
    return True

if __name__ == "__main__":
    """Test the encryption module"""
    print("🧪 Testing Keyfile Encryption")
    
    # Create keyfile if missing
    if not create_keyfile_if_missing():
        exit(1)
    
    # Test encryption
    try:
        encryption = KeyfileEncryption()
        
        if encryption.test_encryption():
            print("✅ Encryption test passed")
        else:
            print("❌ Encryption test failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
