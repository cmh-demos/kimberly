"""
Security module for Kimberly.

Provides encryption-at-rest (AES-256), cloud KMS integration, and audit
logging for sensitive operations.
"""

from scripts.security.encryption import (
    DataEncryptor,
    EncryptedData,
)
from scripts.security.kms import (
    KMSProvider,
    AWSKMSProvider,
    LocalKMSProvider,
)
from scripts.security.audit import (
    AuditLogger,
    AuditEvent,
    SensitiveOperation,
)

__all__ = [
    "DataEncryptor",
    "EncryptedData",
    "KMSProvider",
    "AWSKMSProvider",
    "LocalKMSProvider",
    "AuditLogger",
    "AuditEvent",
    "SensitiveOperation",
]
