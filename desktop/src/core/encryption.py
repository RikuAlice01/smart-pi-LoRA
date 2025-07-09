import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

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
        key_bytes = self.key.encode('utf-8')
        self._aes_key = hashlib.sha256(key_bytes).digest()

    def encrypt(self, data: str) -> str:
        """Encrypt data using the specified method"""
        if self.method == "AES":
            return self._aes_encrypt(data)
        else:
            return data  # No encryption for other methods

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using the specified method"""
        try:
            if self.method == "AES":
                return self._aes_decrypt(encrypted_data)
            else:
                return encrypted_data  # No decryption for other methods
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_data

    def _aes_encrypt(self, data: str) -> str:
        """AES encryption using CBC mode with PKCS7 padding"""
        try:
            if not self._aes_key:
                self._prepare_aes_key()

            iv = os.urandom(16)  # 16 bytes IV for AES-CBC

            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data.encode('utf-8')) + padder.finalize()

            cipher = Cipher(algorithms.AES(self._aes_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

            combined = iv + encrypted_data
            return base64.b64encode(combined).decode('utf-8')

        except Exception as e:
            print(f"AES encryption error: {e}")
            return data

    def _aes_decrypt(self, encrypted_data: str) -> str:
        """AES decryption using CBC mode with PKCS7 unpadding"""
        try:
            if not self._aes_key:
                self._prepare_aes_key()

            combined = base64.b64decode(encrypted_data.encode('utf-8'))

            iv = combined[:16]
            encrypted_bytes = combined[16:]

            cipher = Cipher(algorithms.AES(self._aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()

            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()

            return data.decode('utf-8')

        except Exception as e:
            print(f"AES decryption error: {e}")
            return encrypted_data

    def is_encrypted(self, data: str) -> bool:
        """Check if data appears to be encrypted"""
        try:
            decoded = base64.b64decode(data)
            if self.method == "AES":
                return len(decoded) >= 32  # 16 bytes IV + at least 16 bytes ciphertext
            # For other methods or simple heuristic
            return len(data) > 10 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in data)
        except Exception:
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
