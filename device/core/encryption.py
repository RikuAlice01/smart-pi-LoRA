"""
Encryption and decryption utilities with AES support
"""

import base64
import hashlib
import os
from typing import Union
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

KEYFILE = 'keyfile.bin'

def load_key():
    if not os.path.exists(KEYFILE):
        raise FileNotFoundError(f"Key file '{KEYFILE}' not found.")
    with open(KEYFILE, 'rb') as f:
        key = f.read()
        if len(key) != 32:
            raise ValueError("Key length must be exactly 32 bytes (256 bits).")
        return key

AES_KEY = load_key()

class EncryptionManager:
    """Handles data encryption and decryption"""
    
    def __init__(self, method: str = "AES", key: str = "default_key"):
        self.method = method.upper()
        self.key = key
        self._aes_key = None
        if self.method == "AES":
            self._prepare_aes_key()
    
    def _prepare_aes_key(self):
        """Prepare AES key from the provided key string"""
        # Create a 256-bit key from the provided key string
        key_bytes = self.key.encode('utf-8')
        self._aes_key = hashlib.sha256(key_bytes).digest()
    
    def encrypt(self, data: str) -> str:
        """Encrypt data using the specified method"""
        if self.method == "XOR":
            return self._xor_encrypt(data)
        elif self.method == "AES":
            return self._aes_encrypt(data)
        else:
            return data  # No encryption
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using the specified method"""
        try:
            if self.method == "XOR":
                return self._xor_decrypt(encrypted_data)
            elif self.method == "AES":
                return self._aes_decrypt(encrypted_data)
            else:
                return encrypted_data  # No decryption
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_data
    
    def _xor_encrypt(self, data: str) -> str:
        """Simple XOR encryption"""
        key_bytes = self.key.encode('utf-8')
        data_bytes = data.encode('utf-8')
        
        encrypted = bytearray()
        for i, byte in enumerate(data_bytes):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def _xor_decrypt(self, encrypted_data: str) -> str:
        """Simple XOR decryption"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            key_bytes = self.key.encode('utf-8')
            
            decrypted = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                decrypted.append(byte ^ key_bytes[i % len(key_bytes)])
            
            return decrypted.decode('utf-8')
        except:
            return encrypted_data
    
    def _aes_encrypt(self, plain_text: str) -> str:
        start_time = time.perf_counter()
        backend = default_backend()
        iv = secrets.token_bytes(16)  # สุ่ม IV 16 bytes
        cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=backend)
        encryptor = cipher.encryptor()

        # PKCS#7 padding แบบง่าย
        raw = plain_text.encode('utf-8')
        pad_len = 16 - (len(raw) % 16)
        padded_data = raw + bytes([pad_len] * pad_len)

        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        encoded = base64.b64encode(iv + encrypted).decode('utf-8')

        end_time = time.perf_counter()
        elapsed = end_time - start_time
        print(f"⏱️ Encryption time: {elapsed:.6f} seconds")
        return encoded
    
    def _aes_decrypt(self, encrypted_data: str) -> str:
        """AES decryption using CBC mode"""
        try:
            if not self._aes_key:
                self._prepare_aes_key()
            
            # Decode base64
            combined = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract IV and encrypted data
            iv = combined[:16]
            encrypted_bytes = combined[16:]
            
            # Decrypt
            cipher = Cipher(algorithms.AES(self._aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
            
            # Remove padding
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data)
            data += unpadder.finalize()
            
            return data.decode('utf-8')
            
        except Exception as e:
            print(f"AES decryption error: {e}")
            return encrypted_data
    
    def is_encrypted(self, data: str) -> bool:
        """Check if data appears to be encrypted"""
        try:
            # Simple heuristic: encrypted data is usually base64 encoded
            decoded = base64.b64decode(data)
            # For AES, check if length is reasonable (at least 32 bytes: 16 IV + 16 min encrypted)
            if self.method == "AES":
                return len(decoded) >= 32
            # For XOR, any base64 data longer than 10 chars
            return len(data) > 10 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in data)
        except:
            return False
    
    def set_key(self, new_key: str):
        """Update encryption key"""
        self.key = new_key
        if self.method == "AES":
            self._prepare_aes_key()
    
    def set_method(self, method: str):
        """Update encryption method"""
        self.method = method.upper()
        if self.method == "AES":
            self._prepare_aes_key()
