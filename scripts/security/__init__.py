"""
Security module for Kimberly.

Provides encryption-at-rest (AES-256), cloud KMS integration, and audit
logging for sensitive operations.
"""

from scripts.security.audit import (
    AuditEvent,
    AuditLogger,
    SensitiveOperation,
)
from scripts.security.encryption import (
    DataEncryptor,
    EncryptedData,
)
from scripts.security.kms import (
    AWSKMSProvider,
    KMSProvider,
    LocalKMSProvider,
    SOPSKMSProvider,
    VaultKMSProvider,
    get_kms_provider,
)

__all__ = [
    "DataEncryptor",
    "EncryptedData",
    "KMSProvider",
    "AWSKMSProvider",
    "LocalKMSProvider",
    "VaultKMSProvider",
    "SOPSKMSProvider",
    "get_kms_provider",
    "AuditLogger",
    "AuditEvent",
    "SensitiveOperation",
]
