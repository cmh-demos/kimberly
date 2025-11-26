"""
Encryption-at-rest module using AES-256.

Provides AES-256-GCM encryption for memory data with key management
integration. Uses the cryptography library for secure implementations.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass
class EncryptedData:
    """Container for encrypted data with metadata."""

    ciphertext: bytes
    nonce: bytes
    key_id: str
    algorithm: str = "AES-256-GCM"

    def to_dict(self) -> Dict[str, str]:
        """Serialize to dictionary for storage."""
        return {
            "ciphertext": base64.b64encode(self.ciphertext).decode("utf-8"),
            "nonce": base64.b64encode(self.nonce).decode("utf-8"),
            "key_id": self.key_id,
            "algorithm": self.algorithm,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "EncryptedData":
        """Deserialize from dictionary."""
        return cls(
            ciphertext=base64.b64decode(data["ciphertext"]),
            nonce=base64.b64decode(data["nonce"]),
            key_id=data["key_id"],
            algorithm=data.get("algorithm", "AES-256-GCM"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "EncryptedData":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


class DataEncryptor:
    """
    AES-256-GCM encryptor for data at rest.

    Uses 256-bit keys with GCM mode for authenticated encryption.
    Keys should be provided via a KMS provider.
    """

    NONCE_SIZE = 12  # 96 bits for GCM
    KEY_SIZE = 32  # 256 bits

    def __init__(
        self,
        key: bytes,
        key_id: str = "local",
    ):
        """
        Initialize encryptor with a key.

        Args:
          key: 256-bit encryption key (32 bytes)
          key_id: Identifier for the key (for KMS tracking)
        """
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes (256 bits)")

        self._aesgcm = AESGCM(key)
        self._key_id = key_id

    @property
    def key_id(self) -> str:
        """Return the key identifier."""
        return self._key_id

    def encrypt(
        self,
        plaintext: bytes,
        associated_data: Optional[bytes] = None,
    ) -> EncryptedData:
        """
        Encrypt data using AES-256-GCM.

        Args:
          plaintext: Data to encrypt
          associated_data: Additional authenticated data (AAD)

        Returns:
          EncryptedData containing ciphertext and metadata
        """
        nonce = os.urandom(self.NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, associated_data)

        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            key_id=self._key_id,
        )

    def decrypt(
        self,
        encrypted_data: EncryptedData,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt data using AES-256-GCM.

        Args:
          encrypted_data: Encrypted data container
          associated_data: Additional authenticated data (must match encryption)

        Returns:
          Decrypted plaintext bytes

        Raises:
          cryptography.exceptions.InvalidTag: If decryption fails
        """
        return self._aesgcm.decrypt(
            encrypted_data.nonce,
            encrypted_data.ciphertext,
            associated_data,
        )

    def encrypt_string(
        self,
        plaintext: str,
        associated_data: Optional[str] = None,
    ) -> EncryptedData:
        """
        Encrypt a string using AES-256-GCM.

        Args:
          plaintext: String to encrypt
          associated_data: Optional AAD string

        Returns:
          EncryptedData containing ciphertext and metadata
        """
        aad_bytes = (
            associated_data.encode("utf-8") if associated_data else None
        )
        return self.encrypt(plaintext.encode("utf-8"), aad_bytes)

    def decrypt_string(
        self,
        encrypted_data: EncryptedData,
        associated_data: Optional[str] = None,
    ) -> str:
        """
        Decrypt data to a string.

        Args:
          encrypted_data: Encrypted data container
          associated_data: Optional AAD string (must match encryption)

        Returns:
          Decrypted plaintext string
        """
        aad_bytes = (
            associated_data.encode("utf-8") if associated_data else None
        )
        return self.decrypt(encrypted_data, aad_bytes).decode("utf-8")

    def encrypt_json(
        self,
        data: Dict[str, Any],
        associated_data: Optional[str] = None,
    ) -> EncryptedData:
        """
        Encrypt a JSON-serializable object.

        Args:
          data: Dictionary to encrypt
          associated_data: Optional AAD string

        Returns:
          EncryptedData containing ciphertext and metadata
        """
        return self.encrypt_string(json.dumps(data), associated_data)

    def decrypt_json(
        self,
        encrypted_data: EncryptedData,
        associated_data: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Decrypt data to a JSON object.

        Args:
          encrypted_data: Encrypted data container
          associated_data: Optional AAD string (must match encryption)

        Returns:
          Decrypted dictionary
        """
        return json.loads(self.decrypt_string(encrypted_data, associated_data))

    @staticmethod
    def generate_key() -> bytes:
        """Generate a random 256-bit key."""
        return os.urandom(DataEncryptor.KEY_SIZE)
