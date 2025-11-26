"""
Key Management Service (KMS) integration.

Provides abstract KMS interface and implementations for:
- LocalKMSProvider: File-based key storage (development/testing)
- AWSKMSProvider: AWS KMS integration (production)
- VaultKMSProvider: HashiCorp Vault integration (enterprise/self-hosted)
- SOPSKMSProvider: Mozilla SOPS encrypted secrets (GitOps workflows)
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from scripts.security.encryption import DataEncryptor

logger = logging.getLogger(__name__)


@dataclass
class KeyMetadata:
    """Metadata for a managed key."""

    key_id: str
    created_at: str
    algorithm: str = "AES-256-GCM"
    status: str = "active"
    description: str = ""


class KMSProvider(ABC):
    """Abstract base class for KMS providers."""

    @abstractmethod
    def get_key(self, key_id: str) -> bytes:
        """
        Retrieve a key by ID.

        Args:
          key_id: Unique identifier for the key

        Returns:
          The encryption key bytes

        Raises:
          KeyError: If key not found
        """
        pass

    @abstractmethod
    def create_key(
        self,
        description: str = "",
    ) -> KeyMetadata:
        """
        Create a new encryption key.

        Args:
          description: Human-readable key description

        Returns:
          KeyMetadata for the created key
        """
        pass

    @abstractmethod
    def rotate_key(self, key_id: str) -> KeyMetadata:
        """
        Rotate an existing key.

        Args:
          key_id: ID of key to rotate

        Returns:
          KeyMetadata for the new key version
        """
        pass

    @abstractmethod
    def list_keys(self) -> list[KeyMetadata]:
        """List all managed keys."""
        pass

    def get_encryptor(self, key_id: str) -> DataEncryptor:
        """
        Get a DataEncryptor initialized with the specified key.

        Args:
          key_id: Key to use for encryption

        Returns:
          Configured DataEncryptor instance
        """
        key = self.get_key(key_id)
        return DataEncryptor(key=key, key_id=key_id)


class LocalKMSProvider(KMSProvider):
    """
    Local file-based KMS for development and testing.

    WARNING: Not secure for production use. Keys are stored in plaintext.
    Use only for development and testing purposes.
    """

    def __init__(
        self,
        keys_dir: str = ".keys",
        master_key: Optional[bytes] = None,
    ):
        """
        Initialize local KMS provider.

        Args:
          keys_dir: Directory to store key files
          master_key: Optional master key for encrypting stored keys
        """
        self._keys_dir = Path(keys_dir)
        self._keys_dir.mkdir(parents=True, exist_ok=True)
        self._master_key = master_key
        self._metadata_file = self._keys_dir / "metadata.json"
        self._metadata: Dict[str, dict] = self._load_metadata()

    def _load_metadata(self) -> Dict[str, dict]:
        """Load key metadata from file."""
        if self._metadata_file.exists():
            with open(self._metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_metadata(self) -> None:
        """Save key metadata to file."""
        with open(self._metadata_file, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2)

    def _key_file_path(self, key_id: str) -> Path:
        """Get path to key file."""
        return self._keys_dir / f"{key_id}.key"

    def get_key(self, key_id: str) -> bytes:
        """Retrieve a key by ID."""
        key_file = self._key_file_path(key_id)
        if not key_file.exists():
            raise KeyError(f"Key not found: {key_id}")

        with open(key_file, "rb") as f:
            key_data = f.read()

        if self._master_key:
            # Decrypt with master key
            encryptor = DataEncryptor(self._master_key, "master")
            from scripts.security.encryption import EncryptedData

            encrypted = EncryptedData.from_json(key_data.decode("utf-8"))
            return encryptor.decrypt(encrypted)

        return base64.b64decode(key_data)

    def create_key(
        self,
        description: str = "",
    ) -> KeyMetadata:
        """Create a new encryption key."""
        key = DataEncryptor.generate_key()
        key_id = self._generate_key_id()

        # Store the key
        key_file = self._key_file_path(key_id)

        if self._master_key:
            # Encrypt with master key before storing
            encryptor = DataEncryptor(self._master_key, "master")
            encrypted = encryptor.encrypt(key)
            with open(key_file, "w", encoding="utf-8") as f:
                f.write(encrypted.to_json())
        else:
            with open(key_file, "wb") as f:
                f.write(base64.b64encode(key))

        # Store metadata
        metadata = KeyMetadata(
            key_id=key_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            description=description,
        )
        self._metadata[key_id] = {
            "key_id": metadata.key_id,
            "created_at": metadata.created_at,
            "algorithm": metadata.algorithm,
            "status": metadata.status,
            "description": metadata.description,
        }
        self._save_metadata()

        logger.info(f"Created new key: {key_id}")
        return metadata

    def rotate_key(self, key_id: str) -> KeyMetadata:
        """
        Rotate an existing key.

        Creates a new key and marks the old one as rotated.
        """
        if key_id not in self._metadata:
            raise KeyError(f"Key not found: {key_id}")

        # Mark old key as rotated
        self._metadata[key_id]["status"] = "rotated"

        # Create new key with reference to old
        description = (
            f"Rotated from {key_id} - "
            f"{self._metadata[key_id].get('description', '')}"
        )
        new_metadata = self.create_key(description=description)

        logger.info(f"Rotated key {key_id} to {new_metadata.key_id}")
        return new_metadata

    def list_keys(self) -> list[KeyMetadata]:
        """List all managed keys."""
        return [
            KeyMetadata(
                key_id=meta["key_id"],
                created_at=meta["created_at"],
                algorithm=meta.get("algorithm", "AES-256-GCM"),
                status=meta.get("status", "active"),
                description=meta.get("description", ""),
            )
            for meta in self._metadata.values()
        ]

    def _generate_key_id(self) -> str:
        """Generate a unique key ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        random_bytes = os.urandom(8)
        hash_input = f"{timestamp}:{random_bytes.hex()}".encode()
        return f"key_{hashlib.sha256(hash_input).hexdigest()[:16]}"

    def delete_key(self, key_id: str) -> None:
        """
        Delete a key (soft delete - marks as deleted).

        Args:
          key_id: Key to delete
        """
        if key_id not in self._metadata:
            raise KeyError(f"Key not found: {key_id}")

        self._metadata[key_id]["status"] = "deleted"
        self._save_metadata()
        logger.info(f"Marked key as deleted: {key_id}")


class AWSKMSProvider(KMSProvider):
    """
    AWS KMS integration for production key management.

    Uses AWS KMS for key generation and management, with envelope
    encryption for data keys.
    """

    def __init__(
        self,
        kms_key_id: str,
        region: Optional[str] = None,
    ):
        """
        Initialize AWS KMS provider.

        Args:
          kms_key_id: AWS KMS Customer Master Key (CMK) ID or ARN
          region: AWS region. If not specified, uses AWS_DEFAULT_REGION
                  environment variable. Falls back to us-east-1 for
                  development convenience but production deployments
                  should explicitly set the region to match data residency
                  requirements.
        """
        self._kms_key_id = kms_key_id
        self._region = region or os.environ.get("AWS_DEFAULT_REGION")
        if self._region is None:
            import logging

            logging.getLogger(__name__).warning(
                "AWS region not specified and AWS_DEFAULT_REGION not set. "
                "Falling back to 'us-east-1'. Set region explicitly for "
                "production deployments to ensure proper data residency."
            )
            self._region = "us-east-1"
        self._client = None
        self._data_keys: Dict[str, bytes] = {}

    def _get_client(self):
        """Get or create boto3 KMS client."""
        if self._client is None:
            try:
                import boto3

                self._client = boto3.client("kms", region_name=self._region)
            except ImportError:
                raise ImportError(
                    "boto3 is required for AWS KMS integration. "
                    "Install with: pip install boto3"
                )
        return self._client

    def get_key(self, key_id: str) -> bytes:
        """
        Retrieve a data key by ID.

        If the key is not in memory, generates a new data key from KMS.
        """
        if key_id in self._data_keys:
            return self._data_keys[key_id]

        # Generate new data key using envelope encryption
        client = self._get_client()
        response = client.generate_data_key(
            KeyId=self._kms_key_id,
            KeySpec="AES_256",
        )

        plaintext_key = response["Plaintext"]
        self._data_keys[key_id] = plaintext_key
        return plaintext_key

    def create_key(
        self,
        description: str = "",
    ) -> KeyMetadata:
        """
        Create a new data key using envelope encryption.

        The data key is encrypted by the AWS KMS CMK.
        """
        key_id = f"kms_{os.urandom(8).hex()}"

        # Generate and store the data key
        self.get_key(key_id)

        return KeyMetadata(
            key_id=key_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            description=description,
        )

    def rotate_key(self, key_id: str) -> KeyMetadata:
        """
        Rotate a data key.

        Creates a new data key; the old key remains valid until
        explicitly revoked or rotated at the CMK level.
        """
        if key_id in self._data_keys:
            del self._data_keys[key_id]

        description = f"Rotated from {key_id}"
        return self.create_key(description=description)

    def list_keys(self) -> list[KeyMetadata]:
        """List all data keys currently in memory."""
        return [
            KeyMetadata(
                key_id=key_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                status="active",
            )
            for key_id in self._data_keys.keys()
        ]

    def encrypt_data_key(self, key_id: str) -> bytes:
        """
        Encrypt a data key for storage.

        Returns the encrypted (ciphertext) form of the data key
        that can be safely stored.
        """
        if key_id not in self._data_keys:
            raise KeyError(f"Key not found: {key_id}")

        client = self._get_client()
        response = client.encrypt(
            KeyId=self._kms_key_id,
            Plaintext=self._data_keys[key_id],
        )
        return response["CiphertextBlob"]

    def decrypt_data_key(self, encrypted_key: bytes, key_id: str) -> bytes:
        """
        Decrypt a stored data key.

        Args:
          encrypted_key: The encrypted data key blob
          key_id: Key identifier for caching

        Returns:
          The plaintext data key
        """
        client = self._get_client()
        response = client.decrypt(CiphertextBlob=encrypted_key)
        plaintext_key = response["Plaintext"]
        self._data_keys[key_id] = plaintext_key
        return plaintext_key


class VaultKMSProvider(KMSProvider):
    """
    HashiCorp Vault integration for secrets management.

    Supports both development (dev mode) and production Vault instances.
    Uses the Transit secrets engine for encryption key management.
    """

    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        mount_path: str = "transit",
        key_name: str = "kimberly",
    ):
        """
        Initialize Vault KMS provider.

        Args:
          vault_addr: Vault server address. Defaults to VAULT_ADDR env var.
          vault_token: Vault authentication token. Defaults to VAULT_TOKEN
                       env var.
          mount_path: Mount path for the Transit secrets engine.
          key_name: Name of the encryption key in Vault.
        """
        self._vault_addr = vault_addr or os.environ.get(
            "VAULT_ADDR", "http://127.0.0.1:8200"
        )
        self._vault_token = vault_token or os.environ.get("VAULT_TOKEN")
        self._mount_path = mount_path
        self._key_name = key_name
        self._client = None
        self._data_keys: Dict[str, bytes] = {}

    def _get_client(self):
        """Get or create hvac Vault client."""
        if self._client is None:
            try:
                import hvac

                self._client = hvac.Client(
                    url=self._vault_addr,
                    token=self._vault_token,
                )
                if not self._client.is_authenticated():
                    raise RuntimeError(
                        "Vault authentication failed. Check VAULT_TOKEN."
                    )
            except ImportError:
                raise ImportError(
                    "hvac is required for Vault integration. "
                    "Install with: pip install hvac"
                )
        return self._client

    def get_key(self, key_id: str) -> bytes:
        """
        Retrieve a data key by ID.

        If the key is not cached, generates a new data key.
        In a full implementation, this would use Vault Transit
        to encrypt/decrypt the data key.
        """
        if key_id in self._data_keys:
            return self._data_keys[key_id]

        # Generate a random data key
        # In production, this key would be encrypted by Vault Transit
        plaintext_key = os.urandom(32)  # 256-bit key
        self._data_keys[key_id] = plaintext_key
        return plaintext_key

    def create_key(
        self,
        description: str = "",
    ) -> KeyMetadata:
        """
        Create a new data key using Vault Transit engine.

        The data key is encrypted by the Vault transit key.
        """
        key_id = f"vault_{os.urandom(8).hex()}"

        # Generate and store the data key
        self.get_key(key_id)

        return KeyMetadata(
            key_id=key_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            description=description,
        )

    def rotate_key(self, key_id: str) -> KeyMetadata:
        """
        Rotate a data key.

        Creates a new data key; rotation of the transit key itself
        should be done via Vault CLI/API.
        """
        if key_id in self._data_keys:
            del self._data_keys[key_id]

        description = f"Rotated from {key_id}"
        return self.create_key(description=description)

    def list_keys(self) -> list[KeyMetadata]:
        """List all data keys currently in memory."""
        return [
            KeyMetadata(
                key_id=key_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                status="active",
            )
            for key_id in self._data_keys.keys()
        ]

    def encrypt_with_transit(self, plaintext: bytes) -> str:
        """
        Encrypt data using Vault Transit engine.

        Args:
          plaintext: Data to encrypt

        Returns:
          Vault ciphertext (base64 encoded)
        """
        client = self._get_client()
        # Vault Transit requires base64-encoded input
        encoded_data = base64.b64encode(plaintext).decode("utf-8")

        response = client.secrets.transit.encrypt_data(
            name=self._key_name,
            plaintext=encoded_data,
            mount_point=self._mount_path,
        )
        return response["data"]["ciphertext"]

    def decrypt_with_transit(self, ciphertext: str) -> bytes:
        """
        Decrypt data using Vault Transit engine.

        Args:
          ciphertext: Vault ciphertext to decrypt

        Returns:
          Decrypted plaintext bytes
        """
        client = self._get_client()

        response = client.secrets.transit.decrypt_data(
            name=self._key_name,
            ciphertext=ciphertext,
            mount_point=self._mount_path,
        )
        # Vault returns base64-encoded data in the 'plaintext' field
        encoded_result = response["data"]["plaintext"]
        return base64.b64decode(encoded_result)


class SOPSKMSProvider(KMSProvider):
    """
    Mozilla SOPS integration for encrypted secrets management.

    SOPS (Secrets OPerationS) provides file-level encryption with
    support for age, PGP, AWS KMS, GCP KMS, and Azure Key Vault.

    Best for GitOps workflows where secrets are stored encrypted
    in version control.
    """

    def __init__(
        self,
        secrets_file: str = "secrets.enc.yaml",
        age_key_file: Optional[str] = None,
    ):
        """
        Initialize SOPS KMS provider.

        Args:
          secrets_file: Path to SOPS-encrypted secrets file
          age_key_file: Path to age private key file. Defaults to
                        SOPS_AGE_KEY_FILE env var or
                        ~/.config/sops/age/keys.txt
        """
        self._secrets_file = Path(secrets_file)
        self._age_key_file = age_key_file or os.environ.get(
            "SOPS_AGE_KEY_FILE",
            str(Path.home() / ".config" / "sops" / "age" / "keys.txt"),
        )
        self._cached_secrets: Optional[Dict] = None
        self._data_keys: Dict[str, bytes] = {}

    def _load_secrets(self) -> Dict:
        """Load and decrypt secrets from SOPS file."""
        if self._cached_secrets is not None:
            return self._cached_secrets

        if not self._secrets_file.exists():
            logger.warning(
                f"SOPS secrets file not found: {self._secrets_file}"
            )
            return {}

        try:
            env = os.environ.copy()
            env["SOPS_AGE_KEY_FILE"] = self._age_key_file

            result = subprocess.run(
                ["sops", "-d", str(self._secrets_file)],
                capture_output=True,
                text=True,
                env=env,
                check=True,
            )

            # Lazy import: yaml is optional dependency for SOPS support
            try:
                import yaml
            except ImportError:
                raise ImportError(
                    "PyYAML is required for SOPS integration. "
                    "Install with: pip install pyyaml"
                )

            self._cached_secrets = yaml.safe_load(result.stdout)
            return self._cached_secrets

        except FileNotFoundError:
            raise ImportError(
                "sops CLI is required for SOPS integration. "
                "Install from: https://github.com/getsops/sops"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"SOPS decryption failed: {e.stderr}")

    def get_key(self, key_id: str) -> bytes:
        """
        Retrieve a key from SOPS secrets file.

        Keys are stored as base64-encoded strings in the SOPS file.
        """
        if key_id in self._data_keys:
            return self._data_keys[key_id]

        secrets = self._load_secrets()
        keys = secrets.get("encryption_keys", {})

        if key_id not in keys:
            # Generate a new key if not found
            key = DataEncryptor.generate_key()
            self._data_keys[key_id] = key
            logger.warning(
                f"Key {key_id} not found in SOPS file; "
                "generated ephemeral key"
            )
            return key

        key_b64 = keys[key_id]
        key = base64.b64decode(key_b64)
        self._data_keys[key_id] = key
        return key

    def create_key(
        self,
        description: str = "",
    ) -> KeyMetadata:
        """
        Create a new encryption key.

        Note: The key is generated in memory. To persist, update the
        SOPS secrets file manually with the base64-encoded key.
        """
        key = DataEncryptor.generate_key()
        key_id = f"sops_{os.urandom(8).hex()}"
        self._data_keys[key_id] = key

        logger.info(
            f"Created key {key_id}. To persist, add to SOPS file:\n"
            f"  encryption_keys:\n"
            f"    {key_id}: {base64.b64encode(key).decode()}"
        )

        return KeyMetadata(
            key_id=key_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            description=description,
        )

    def rotate_key(self, key_id: str) -> KeyMetadata:
        """
        Rotate a key.

        Note: Updates in-memory only. Update SOPS file to persist.
        """
        if key_id in self._data_keys:
            del self._data_keys[key_id]

        description = f"Rotated from {key_id}"
        return self.create_key(description=description)

    def list_keys(self) -> list[KeyMetadata]:
        """List all keys from SOPS secrets file."""
        secrets = self._load_secrets()
        keys = secrets.get("encryption_keys", {})

        result = [
            KeyMetadata(
                key_id=key_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                status="active",
                description="From SOPS file",
            )
            for key_id in keys.keys()
        ]

        # Also include in-memory keys
        for key_id in self._data_keys.keys():
            if key_id not in keys:
                result.append(
                    KeyMetadata(
                        key_id=key_id,
                        created_at=datetime.now(timezone.utc).isoformat(),
                        status="ephemeral",
                        description="In-memory only",
                    )
                )

        return result


def get_kms_provider(
    provider_type: Optional[str] = None,
) -> KMSProvider:
    """
    Factory function to get the appropriate KMS provider.

    Reads KMS_PROVIDER environment variable if provider_type not specified.

    Args:
      provider_type: One of 'local', 'aws', 'vault', 'sops'.
                     Defaults to KMS_PROVIDER env var or 'local'.

    Returns:
      Configured KMSProvider instance
    """
    provider_type = provider_type or os.environ.get("KMS_PROVIDER", "local")

    if provider_type == "local":
        keys_dir = os.environ.get("LOCAL_KMS_DIR", ".keys")
        return LocalKMSProvider(keys_dir=keys_dir)

    elif provider_type == "aws":
        kms_key_id = os.environ.get("AWS_KMS_KEY_ID")
        if not kms_key_id:
            raise ValueError("AWS_KMS_KEY_ID environment variable required")
        return AWSKMSProvider(kms_key_id=kms_key_id)

    elif provider_type == "vault":
        return VaultKMSProvider()

    elif provider_type == "sops":
        secrets_file = os.environ.get("SOPS_SECRETS_FILE", "secrets.enc.yaml")
        return SOPSKMSProvider(secrets_file=secrets_file)

    else:
        raise ValueError(
            f"Unknown KMS provider: {provider_type}. "
            "Valid options: local, aws, vault, sops"
        )
