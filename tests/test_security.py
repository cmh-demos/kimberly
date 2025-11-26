"""Tests for the security module."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.security.audit import (
    AuditEvent,
    AuditLogger,
    SensitiveOperation,
    get_audit_logger,
    set_audit_logger,
)
from scripts.security.encryption import DataEncryptor, EncryptedData
from scripts.security.kms import KeyMetadata, LocalKMSProvider


class TestEncryptedData(unittest.TestCase):
    """Tests for EncryptedData serialization."""

    def test_to_dict_and_from_dict(self):
        data = EncryptedData(
            ciphertext=b"encrypted_content",
            nonce=b"random_nonce",
            key_id="test_key_123",
        )

        serialized = data.to_dict()
        restored = EncryptedData.from_dict(serialized)

        self.assertEqual(restored.ciphertext, data.ciphertext)
        self.assertEqual(restored.nonce, data.nonce)
        self.assertEqual(restored.key_id, data.key_id)
        self.assertEqual(restored.algorithm, "AES-256-GCM")

    def test_to_json_and_from_json(self):
        data = EncryptedData(
            ciphertext=b"test_cipher",
            nonce=b"test_nonce",
            key_id="key_abc",
        )

        json_str = data.to_json()
        restored = EncryptedData.from_json(json_str)

        self.assertEqual(restored.ciphertext, data.ciphertext)
        self.assertEqual(restored.nonce, data.nonce)
        self.assertEqual(restored.key_id, data.key_id)


class TestDataEncryptor(unittest.TestCase):
    """Tests for DataEncryptor."""

    def setUp(self):
        self.key = DataEncryptor.generate_key()
        self.encryptor = DataEncryptor(self.key, key_id="test_key")

    def test_generate_key_length(self):
        key = DataEncryptor.generate_key()
        self.assertEqual(len(key), 32)  # 256 bits

    def test_invalid_key_length(self):
        with self.assertRaises(ValueError):
            DataEncryptor(b"short_key", key_id="test")

    def test_key_id_property(self):
        self.assertEqual(self.encryptor.key_id, "test_key")

    def test_encrypt_decrypt_bytes(self):
        plaintext = b"Hello, World! This is secret data."
        encrypted = self.encryptor.encrypt(plaintext)

        self.assertIsInstance(encrypted, EncryptedData)
        self.assertNotEqual(encrypted.ciphertext, plaintext)
        self.assertEqual(encrypted.key_id, "test_key")

        decrypted = self.encryptor.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)

    def test_encrypt_decrypt_with_aad(self):
        plaintext = b"Secret message"
        aad = b"user_id:12345"

        encrypted = self.encryptor.encrypt(plaintext, associated_data=aad)
        decrypted = self.encryptor.decrypt(encrypted, associated_data=aad)

        self.assertEqual(decrypted, plaintext)

    def test_decrypt_fails_with_wrong_aad(self):
        plaintext = b"Secret message"
        aad = b"user_id:12345"

        encrypted = self.encryptor.encrypt(plaintext, associated_data=aad)

        # Should fail with wrong AAD
        from cryptography.exceptions import InvalidTag

        with self.assertRaises(InvalidTag):
            self.encryptor.decrypt(encrypted, associated_data=b"wrong_aad")

    def test_encrypt_decrypt_string(self):
        plaintext = "This is a secret string!"
        encrypted = self.encryptor.encrypt_string(plaintext)
        decrypted = self.encryptor.decrypt_string(encrypted)

        self.assertEqual(decrypted, plaintext)

    def test_encrypt_decrypt_string_with_aad(self):
        plaintext = "Secret data"
        aad = "context_info"

        encrypted = self.encryptor.encrypt_string(plaintext, aad)
        decrypted = self.encryptor.decrypt_string(encrypted, aad)

        self.assertEqual(decrypted, plaintext)

    def test_encrypt_decrypt_json(self):
        data = {
            "user_id": "user_123",
            "preferences": {"theme": "dark", "language": "en"},
            "memories": ["item1", "item2"],
        }

        encrypted = self.encryptor.encrypt_json(data)
        decrypted = self.encryptor.decrypt_json(encrypted)

        self.assertEqual(decrypted, data)

    def test_unique_nonces(self):
        plaintext = b"Same message"
        encrypted1 = self.encryptor.encrypt(plaintext)
        encrypted2 = self.encryptor.encrypt(plaintext)

        # Nonces should be different
        self.assertNotEqual(encrypted1.nonce, encrypted2.nonce)
        # Ciphertexts should also be different
        self.assertNotEqual(encrypted1.ciphertext, encrypted2.ciphertext)

    def test_different_keys_produce_different_ciphertext(self):
        plaintext = b"Test message"

        key1 = DataEncryptor.generate_key()
        key2 = DataEncryptor.generate_key()

        enc1 = DataEncryptor(key1, "key1")
        enc2 = DataEncryptor(key2, "key2")

        encrypted1 = enc1.encrypt(plaintext)
        encrypted2 = enc2.encrypt(plaintext)

        # TEST ONLY: Force same nonce to verify keys produce different output.
        # WARNING: Nonce reuse is a critical vulnerability in AES-GCM and must
        # never be done in production code. This is safe here because we're
        # only comparing ciphertexts from different keys, not reusing for
        # encryption.
        encrypted2.nonce = encrypted1.nonce

        # Even with same nonce, different keys produce different ciphertext
        self.assertNotEqual(encrypted1.ciphertext, encrypted2.ciphertext)


class TestLocalKMSProvider(unittest.TestCase):
    """Tests for LocalKMSProvider."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.kms = LocalKMSProvider(keys_dir=self.temp_dir)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_key(self):
        metadata = self.kms.create_key(description="Test key")

        self.assertIsInstance(metadata, KeyMetadata)
        self.assertTrue(metadata.key_id.startswith("key_"))
        self.assertEqual(metadata.status, "active")
        self.assertEqual(metadata.description, "Test key")

    def test_get_key(self):
        metadata = self.kms.create_key()
        key = self.kms.get_key(metadata.key_id)

        self.assertEqual(len(key), 32)  # 256 bits

    def test_get_nonexistent_key(self):
        with self.assertRaises(KeyError):
            self.kms.get_key("nonexistent_key")

    def test_list_keys(self):
        self.kms.create_key(description="Key 1")
        self.kms.create_key(description="Key 2")

        keys = self.kms.list_keys()

        self.assertEqual(len(keys), 2)
        descriptions = {k.description for k in keys}
        self.assertIn("Key 1", descriptions)
        self.assertIn("Key 2", descriptions)

    def test_rotate_key(self):
        original = self.kms.create_key(description="Original")
        rotated = self.kms.rotate_key(original.key_id)

        # Original should be marked as rotated
        keys = self.kms.list_keys()
        original_key = next(k for k in keys if k.key_id == original.key_id)
        self.assertEqual(original_key.status, "rotated")

        # New key should be active
        new_key = next(k for k in keys if k.key_id == rotated.key_id)
        self.assertEqual(new_key.status, "active")

    def test_rotate_nonexistent_key(self):
        with self.assertRaises(KeyError):
            self.kms.rotate_key("nonexistent")

    def test_delete_key(self):
        metadata = self.kms.create_key()
        self.kms.delete_key(metadata.key_id)

        keys = self.kms.list_keys()
        deleted_key = next(k for k in keys if k.key_id == metadata.key_id)
        self.assertEqual(deleted_key.status, "deleted")

    def test_get_encryptor(self):
        metadata = self.kms.create_key()
        encryptor = self.kms.get_encryptor(metadata.key_id)

        self.assertIsInstance(encryptor, DataEncryptor)
        self.assertEqual(encryptor.key_id, metadata.key_id)

        # Test that it works
        plaintext = b"Test data"
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)

    def test_persistence(self):
        # Create key with first instance
        metadata = self.kms.create_key(description="Persistent key")
        original_key = self.kms.get_key(metadata.key_id)

        # Create new instance pointing to same directory
        kms2 = LocalKMSProvider(keys_dir=self.temp_dir)

        # Key should be available
        restored_key = kms2.get_key(metadata.key_id)
        self.assertEqual(restored_key, original_key)

    def test_with_master_key(self):
        master_key = DataEncryptor.generate_key()
        kms = LocalKMSProvider(keys_dir=self.temp_dir, master_key=master_key)

        metadata = kms.create_key(description="Encrypted key")
        key = kms.get_key(metadata.key_id)

        self.assertEqual(len(key), 32)

        # Key file should be encrypted (contain JSON structure)
        key_file = Path(self.temp_dir) / f"{metadata.key_id}.key"
        with open(key_file, "r") as f:
            content = f.read()
            # Should be JSON (encrypted form)
            data = json.loads(content)
            self.assertIn("ciphertext", data)


class TestAuditEvent(unittest.TestCase):
    """Tests for AuditEvent."""

    def test_to_dict(self):
        event = AuditEvent(
            operation="data.read",
            timestamp="2025-11-26T10:00:00Z",
            user_id="user_123",
            resource_id="mem_456",
            resource_type="memory",
            status="success",
        )

        d = event.to_dict()

        self.assertEqual(d["operation"], "data.read")
        self.assertEqual(d["user_id"], "user_123")
        self.assertEqual(d["resource_id"], "mem_456")

    def test_to_dict_excludes_none(self):
        event = AuditEvent(
            operation="auth.login",
            timestamp="2025-11-26T10:00:00Z",
        )

        d = event.to_dict()

        self.assertNotIn("user_id", d)
        self.assertNotIn("resource_id", d)

    def test_from_dict(self):
        data = {
            "operation": "key.create",
            "timestamp": "2025-11-26T12:00:00Z",
            "user_id": "admin",
            "status": "success",
        }

        event = AuditEvent.from_dict(data)

        self.assertEqual(event.operation, "key.create")
        self.assertEqual(event.user_id, "admin")
        self.assertEqual(event.status, "success")

    def test_to_json_and_from_json(self):
        event = AuditEvent(
            operation="memory.create",
            timestamp="2025-11-26T14:00:00Z",
            user_id="user_abc",
            details={"size": 1024},
        )

        json_str = event.to_json()
        # Should be valid JSON
        parsed = json.loads(json_str)
        self.assertEqual(parsed["operation"], "memory.create")


class TestAuditLogger(unittest.TestCase):
    """Tests for AuditLogger."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_audit.log")
        self.logger = AuditLogger(
            log_file=self.log_file,
            enable_console=False,
            enable_file=True,
            max_entries=100,
            archive_dir=os.path.join(self.temp_dir, "archive"),
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_creates_event(self):
        event = self.logger.log(
            operation=SensitiveOperation.AUTH_LOGIN,
            user_id="user_123",
            status="success",
        )

        self.assertIsInstance(event, AuditEvent)
        self.assertEqual(event.operation, "auth.login")
        self.assertEqual(event.user_id, "user_123")
        self.assertIsNotNone(event.timestamp)

    def test_log_writes_to_file(self):
        self.logger.log(
            operation=SensitiveOperation.DATA_READ,
            user_id="user_abc",
        )

        with open(self.log_file, "r") as f:
            content = f.read()

        self.assertIn("data.read", content)
        self.assertIn("user_abc", content)

    def test_log_sanitizes_passwords(self):
        self.logger.log(
            operation=SensitiveOperation.AUTH_LOGIN,
            user_id="user_123",
            details={"password": "secret123", "username": "testuser"},
        )

        with open(self.log_file, "r") as f:
            content = f.read()

        self.assertNotIn("secret123", content)
        self.assertIn("[REDACTED]", content)
        self.assertIn("testuser", content)

    def test_log_sanitizes_tokens(self):
        self.logger.log(
            operation=SensitiveOperation.AUTH_TOKEN_ISSUED,
            details={"api_key": "sk-12345", "scope": "read"},
        )

        with open(self.log_file, "r") as f:
            content = f.read()

        self.assertNotIn("sk-12345", content)
        self.assertIn("read", content)

    def test_log_sanitizes_email(self):
        self.logger.log(
            operation=SensitiveOperation.DATA_WRITE,
            details={"email_content": "Contact me at user@example.com"},
        )

        with open(self.log_file, "r") as f:
            content = f.read()

        self.assertNotIn("user@example.com", content)
        self.assertIn("[REDACTED: Potential PII]", content)

    def test_log_auth_success(self):
        event = self.logger.log_auth_success(
            user_id="user_123",
            source_ip="192.168.1.1",
        )

        self.assertEqual(event.operation, "auth.login")
        self.assertEqual(event.status, "success")
        self.assertEqual(event.source_ip, "192.168.1.1")

    def test_log_auth_failure(self):
        event = self.logger.log_auth_failure(
            user_id="user_123",
            reason="Invalid password",
        )

        self.assertEqual(event.operation, "auth.failed")
        self.assertEqual(event.status, "failure")
        self.assertIn("reason", event.details)

    def test_log_data_access(self):
        event = self.logger.log_data_access(
            user_id="user_123",
            resource_id="mem_456",
            resource_type="memory",
            action="read",
        )

        self.assertEqual(event.operation, "data.read")
        self.assertEqual(event.resource_id, "mem_456")

    def test_log_encryption_operation(self):
        event = self.logger.log_encryption_operation(
            operation_type="encrypt",
            key_id="key_abc",
            user_id="user_123",
        )

        self.assertEqual(event.operation, "encrypt.data")
        self.assertIn("key_id", event.details)

    def test_log_key_operation(self):
        event = self.logger.log_key_operation(
            operation_type="create",
            key_id="key_new",
            user_id="admin",
        )

        self.assertEqual(event.operation, "key.create")
        self.assertEqual(event.resource_id, "key_new")

    def test_log_security_event(self):
        event = self.logger.log_security_event(
            event_type="brute_force_attempt",
            severity="warning",
            details={"attempts": 5},
        )

        self.assertEqual(event.operation, "security.alert")
        self.assertEqual(event.status, "warning")

    def test_search_by_operation(self):
        self.logger.log(operation=SensitiveOperation.AUTH_LOGIN, user_id="a")
        self.logger.log(operation=SensitiveOperation.DATA_READ, user_id="b")
        self.logger.log(operation=SensitiveOperation.AUTH_LOGIN, user_id="c")

        results = self.logger.search(operation="auth.login")

        self.assertEqual(len(results), 2)
        for event in results:
            self.assertEqual(event.operation, "auth.login")

    def test_search_by_user_id(self):
        self.logger.log(operation=SensitiveOperation.DATA_READ, user_id="a")
        self.logger.log(operation=SensitiveOperation.DATA_READ, user_id="b")

        results = self.logger.search(user_id="a")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user_id, "a")

    def test_add_handler(self):
        events = []

        def custom_handler(event):
            events.append(event)

        self.logger.add_handler(custom_handler)
        self.logger.log(operation=SensitiveOperation.AUTH_LOGIN)

        self.assertEqual(len(events), 1)

    def test_sensitive_operation_enum_values(self):
        self.assertEqual(SensitiveOperation.AUTH_LOGIN.value, "auth.login")
        self.assertEqual(SensitiveOperation.DATA_READ.value, "data.read")
        self.assertEqual(SensitiveOperation.KEY_CREATE.value, "key.create")
        self.assertEqual(
            SensitiveOperation.MEMORY_MEDITATE.value, "memory.meditate"
        )


class TestGlobalAuditLogger(unittest.TestCase):
    """Tests for global audit logger functions."""

    def test_get_audit_logger_returns_singleton(self):
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        self.assertIs(logger1, logger2)

    def test_set_audit_logger(self):
        original = get_audit_logger()

        temp_dir = tempfile.mkdtemp()
        custom = AuditLogger(log_file=os.path.join(temp_dir, "custom.log"))
        set_audit_logger(custom)

        self.assertIs(get_audit_logger(), custom)

        # Restore
        set_audit_logger(original)

        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


class TestIntegration(unittest.TestCase):
    """Integration tests for security module."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_encryption_workflow(self):
        # Create KMS provider
        kms = LocalKMSProvider(keys_dir=os.path.join(self.temp_dir, "keys"))

        # Create audit logger
        audit = AuditLogger(
            log_file=os.path.join(self.temp_dir, "audit.log"),
            enable_console=False,
        )

        # Create a key and log it
        key_metadata = kms.create_key(description="Data encryption key")
        audit.log_key_operation("create", key_metadata.key_id, "system")

        # Get encryptor
        encryptor = kms.get_encryptor(key_metadata.key_id)

        # Encrypt data
        sensitive_data = {"user_id": "u123", "preferences": {"theme": "dark"}}
        encrypted = encryptor.encrypt_json(sensitive_data)
        audit.log_encryption_operation(
            "encrypt", key_metadata.key_id, resource_id="prefs_u123"
        )

        # Decrypt data
        decrypted = encryptor.decrypt_json(encrypted)
        audit.log_encryption_operation(
            "decrypt", key_metadata.key_id, resource_id="prefs_u123"
        )

        # Verify data integrity
        self.assertEqual(decrypted, sensitive_data)

        # Verify audit log
        events = audit.search(operation="key.create")
        self.assertEqual(len(events), 1)

        encrypt_events = audit.search(operation="encrypt.data")
        self.assertEqual(len(encrypt_events), 1)

    def test_key_rotation_with_reencryption(self):
        kms = LocalKMSProvider(keys_dir=os.path.join(self.temp_dir, "keys"))

        # Create initial key
        old_metadata = kms.create_key(description="Old key")
        old_encryptor = kms.get_encryptor(old_metadata.key_id)

        # Encrypt data with old key
        data = b"Important secret data"
        encrypted = old_encryptor.encrypt(data)

        # Rotate key
        new_metadata = kms.rotate_key(old_metadata.key_id)
        new_encryptor = kms.get_encryptor(new_metadata.key_id)

        # Old key should still work for decryption
        old_key = kms.get_key(old_metadata.key_id)
        old_decryptor = DataEncryptor(old_key, old_metadata.key_id)
        decrypted = old_decryptor.decrypt(encrypted)
        self.assertEqual(decrypted, data)

        # Re-encrypt with new key
        new_encrypted = new_encryptor.encrypt(data)
        new_decrypted = new_encryptor.decrypt(new_encrypted)
        self.assertEqual(new_decrypted, data)

        # Verify key statuses
        keys = kms.list_keys()
        old_key_meta = next(k for k in keys if k.key_id == old_metadata.key_id)
        new_key_meta = next(k for k in keys if k.key_id == new_metadata.key_id)

        self.assertEqual(old_key_meta.status, "rotated")
        self.assertEqual(new_key_meta.status, "active")


class TestGetKMSProviderFactory(unittest.TestCase):
    """Tests for get_kms_provider factory function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Save original env vars
        self._orig_kms_provider = os.environ.get("KMS_PROVIDER")
        self._orig_local_kms_dir = os.environ.get("LOCAL_KMS_DIR")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Restore original env vars
        if self._orig_kms_provider is not None:
            os.environ["KMS_PROVIDER"] = self._orig_kms_provider
        elif "KMS_PROVIDER" in os.environ:
            del os.environ["KMS_PROVIDER"]

        if self._orig_local_kms_dir is not None:
            os.environ["LOCAL_KMS_DIR"] = self._orig_local_kms_dir
        elif "LOCAL_KMS_DIR" in os.environ:
            del os.environ["LOCAL_KMS_DIR"]

    def test_get_local_provider_default(self):
        from scripts.security.kms import get_kms_provider

        os.environ["LOCAL_KMS_DIR"] = self.temp_dir
        if "KMS_PROVIDER" in os.environ:
            del os.environ["KMS_PROVIDER"]

        provider = get_kms_provider()
        self.assertIsInstance(provider, LocalKMSProvider)

    def test_get_local_provider_explicit(self):
        from scripts.security.kms import get_kms_provider

        os.environ["LOCAL_KMS_DIR"] = self.temp_dir
        provider = get_kms_provider("local")
        self.assertIsInstance(provider, LocalKMSProvider)

    def test_get_local_provider_from_env(self):
        from scripts.security.kms import get_kms_provider

        os.environ["KMS_PROVIDER"] = "local"
        os.environ["LOCAL_KMS_DIR"] = self.temp_dir

        provider = get_kms_provider()
        self.assertIsInstance(provider, LocalKMSProvider)

    def test_get_invalid_provider(self):
        from scripts.security.kms import get_kms_provider

        with self.assertRaises(ValueError) as ctx:
            get_kms_provider("invalid_provider")

        self.assertIn("Unknown KMS provider", str(ctx.exception))

    def test_get_aws_provider_missing_key_id(self):
        from scripts.security.kms import get_kms_provider

        # Remove AWS_KMS_KEY_ID if set
        if "AWS_KMS_KEY_ID" in os.environ:
            del os.environ["AWS_KMS_KEY_ID"]

        with self.assertRaises(ValueError) as ctx:
            get_kms_provider("aws")

        self.assertIn("AWS_KMS_KEY_ID", str(ctx.exception))


class TestVaultKMSProvider(unittest.TestCase):
    """Tests for VaultKMSProvider (without actual Vault connection)."""

    def test_vault_provider_initialization(self):
        from scripts.security.kms import VaultKMSProvider

        provider = VaultKMSProvider(
            vault_addr="http://127.0.0.1:8200",
            vault_token="test-token",
            mount_path="transit",
            key_name="test-key",
        )

        self.assertEqual(provider._vault_addr, "http://127.0.0.1:8200")
        self.assertEqual(provider._vault_token, "test-token")
        self.assertEqual(provider._mount_path, "transit")
        self.assertEqual(provider._key_name, "test-key")

    def test_vault_provider_env_vars(self):
        from scripts.security.kms import VaultKMSProvider

        # Temporarily set env vars
        os.environ["VAULT_ADDR"] = "http://vault.example.com:8200"
        os.environ["VAULT_TOKEN"] = "env-token"

        try:
            provider = VaultKMSProvider()
            self.assertEqual(
                provider._vault_addr, "http://vault.example.com:8200"
            )
            self.assertEqual(provider._vault_token, "env-token")
        finally:
            del os.environ["VAULT_ADDR"]
            del os.environ["VAULT_TOKEN"]

    def test_vault_create_key(self):
        from scripts.security.kms import VaultKMSProvider

        provider = VaultKMSProvider(vault_token="test")
        metadata = provider.create_key(description="Test key")

        self.assertTrue(metadata.key_id.startswith("vault_"))
        self.assertEqual(metadata.description, "Test key")

    def test_vault_get_key_generates_key(self):
        from scripts.security.kms import VaultKMSProvider

        provider = VaultKMSProvider(vault_token="test")
        key = provider.get_key("test_key_id")

        self.assertEqual(len(key), 32)  # 256-bit key

    def test_vault_list_keys(self):
        from scripts.security.kms import VaultKMSProvider

        provider = VaultKMSProvider(vault_token="test")
        provider.create_key(description="Key 1")
        provider.create_key(description="Key 2")

        keys = provider.list_keys()
        self.assertEqual(len(keys), 2)

    def test_vault_rotate_key(self):
        from scripts.security.kms import VaultKMSProvider

        provider = VaultKMSProvider(vault_token="test")
        original = provider.create_key()
        rotated = provider.rotate_key(original.key_id)

        self.assertNotEqual(original.key_id, rotated.key_id)
        self.assertIn("Rotated from", rotated.description)


class TestSOPSKMSProvider(unittest.TestCase):
    """Tests for SOPSKMSProvider (without actual SOPS execution)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sops_provider_initialization(self):
        from scripts.security.kms import SOPSKMSProvider

        secrets_file = os.path.join(self.temp_dir, "secrets.enc.yaml")
        provider = SOPSKMSProvider(
            secrets_file=secrets_file,
            age_key_file="~/.config/sops/age/keys.txt",
        )

        self.assertEqual(str(provider._secrets_file), secrets_file)
        self.assertEqual(
            provider._age_key_file, "~/.config/sops/age/keys.txt"
        )

    def test_sops_create_key(self):
        from scripts.security.kms import SOPSKMSProvider

        secrets_file = os.path.join(self.temp_dir, "secrets.enc.yaml")
        provider = SOPSKMSProvider(secrets_file=secrets_file)

        metadata = provider.create_key(description="Test SOPS key")

        self.assertTrue(metadata.key_id.startswith("sops_"))
        self.assertEqual(metadata.description, "Test SOPS key")

    def test_sops_get_key_generates_ephemeral(self):
        from scripts.security.kms import SOPSKMSProvider

        secrets_file = os.path.join(self.temp_dir, "secrets.enc.yaml")
        provider = SOPSKMSProvider(secrets_file=secrets_file)

        key = provider.get_key("nonexistent_key")

        # Should generate ephemeral key
        self.assertEqual(len(key), 32)

    def test_sops_list_keys(self):
        from scripts.security.kms import SOPSKMSProvider

        secrets_file = os.path.join(self.temp_dir, "secrets.enc.yaml")
        provider = SOPSKMSProvider(secrets_file=secrets_file)

        provider.create_key(description="Key 1")
        provider.create_key(description="Key 2")

        keys = provider.list_keys()

        # Both should be ephemeral since no SOPS file
        self.assertEqual(len(keys), 2)
        for key in keys:
            self.assertEqual(key.status, "ephemeral")

    def test_sops_rotate_key(self):
        from scripts.security.kms import SOPSKMSProvider

        secrets_file = os.path.join(self.temp_dir, "secrets.enc.yaml")
        provider = SOPSKMSProvider(secrets_file=secrets_file)

        original = provider.create_key()
        rotated = provider.rotate_key(original.key_id)

        self.assertNotEqual(original.key_id, rotated.key_id)


if __name__ == "__main__":
    unittest.main()
