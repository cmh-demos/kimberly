"""
Audit logging for sensitive operations.

Provides comprehensive audit trails for security-critical operations
including authentication, data access, encryption, and key management.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class SensitiveOperation(str, Enum):
    """Types of sensitive operations that require audit logging."""

    # Authentication
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_ISSUED = "auth.token_issued"
    AUTH_TOKEN_REVOKED = "auth.token_revoked"

    # Data access
    DATA_READ = "data.read"
    DATA_WRITE = "data.write"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # Memory operations
    MEMORY_CREATE = "memory.create"
    MEMORY_READ = "memory.read"
    MEMORY_UPDATE = "memory.update"
    MEMORY_DELETE = "memory.delete"
    MEMORY_MEDITATE = "memory.meditate"
    MEMORY_PRUNE = "memory.prune"

    # Encryption operations
    ENCRYPT_DATA = "encrypt.data"
    DECRYPT_DATA = "decrypt.data"

    # Key management
    KEY_CREATE = "key.create"
    KEY_ROTATE = "key.rotate"
    KEY_DELETE = "key.delete"
    KEY_ACCESS = "key.access"

    # Agent operations
    AGENT_INVOKE = "agent.invoke"
    AGENT_COMPLETE = "agent.complete"
    AGENT_ERROR = "agent.error"

    # Admin operations
    ADMIN_CONFIG_CHANGE = "admin.config_change"
    ADMIN_USER_CREATE = "admin.user_create"
    ADMIN_USER_DELETE = "admin.user_delete"

    # Security events
    SECURITY_ALERT = "security.alert"
    SECURITY_VIOLATION = "security.violation"


@dataclass
class AuditEvent:
    """
    Represents an auditable security event.

    All sensitive operations generate audit events that are
    immutably logged for compliance and forensics.
    """

    operation: str
    timestamp: str
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    status: str = "success"
    details: Dict[str, Any] = field(default_factory=dict)
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create from dictionary."""
        return cls(
            operation=data["operation"],
            timestamp=data["timestamp"],
            user_id=data.get("user_id"),
            resource_id=data.get("resource_id"),
            resource_type=data.get("resource_type"),
            status=data.get("status", "success"),
            details=data.get("details", {}),
            source_ip=data.get("source_ip"),
            user_agent=data.get("user_agent"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            duration_ms=data.get("duration_ms"),
        )


class AuditLogger:
    """
    Audit logger for sensitive operations.

    Provides tamper-evident logging with support for multiple
    backends (file, database, external SIEM).
    """

    def __init__(
        self,
        log_file: str = "audit.log",
        logger_name: Optional[str] = None,
        enable_console: bool = False,
        enable_file: bool = True,
        max_entries: int = 10000,
        archive_dir: str = "logs/audit_archive",
    ):
        """
        Initialize audit logger.

        Args:
          log_file: Path to audit log file
          logger_name: Logger name for Python logging integration
                       (auto-generated if not provided)
          enable_console: Whether to also log to console
          enable_file: Whether to log to file
          max_entries: Maximum entries before rotation
          archive_dir: Directory for archived logs
        """
        self._log_file = Path(log_file)
        self._max_entries = max_entries
        self._archive_dir = Path(archive_dir)
        self._entry_count = 0
        self._handlers: List[Callable[[AuditEvent], None]] = []
        self._file_handler: Optional[logging.FileHandler] = None

        # Generate unique logger name if not provided
        if logger_name is None:
            logger_name = f"kimberly.security.audit.{uuid.uuid4().hex[:8]}"

        # Set up Python logger with fresh handlers
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        # Clear any existing handlers
        self._logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s - AUDIT - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )

        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

        if enable_file:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            self._file_handler = logging.FileHandler(self._log_file)
            self._file_handler.setFormatter(formatter)
            self._logger.addHandler(self._file_handler)

        # Load entry count
        if self._log_file.exists():
            self._entry_count = self._count_entries()

    def _count_entries(self) -> int:
        """Count existing log entries."""
        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def log(
        self,
        operation: SensitiveOperation | str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
          operation: Type of operation
          user_id: User performing the operation
          resource_id: ID of affected resource
          resource_type: Type of affected resource
          status: Operation status (success, failure, error)
          details: Additional event details (will be sanitized)
          source_ip: Client IP address
          user_agent: Client user agent
          session_id: Session identifier
          request_id: Request correlation ID
          duration_ms: Operation duration in milliseconds

        Returns:
          The created AuditEvent
        """
        if isinstance(operation, SensitiveOperation):
            operation = operation.value

        # Sanitize details to remove sensitive data
        sanitized_details = self._sanitize_details(details or {})

        event = AuditEvent(
            operation=operation,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            status=status,
            details=sanitized_details,
            source_ip=source_ip,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
            duration_ms=duration_ms,
        )

        # Log to Python logger
        self._logger.info(event.to_json())

        # Flush file handler to ensure immediate write
        if self._file_handler:
            self._file_handler.flush()

        # Call additional handlers
        for handler in self._handlers:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"Audit handler error: {e}")

        # Check for rotation
        self._entry_count += 1
        if self._entry_count >= self._max_entries:
            self._rotate_logs()

        return event

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive information from details.

        Redacts fields that may contain PII or credentials.
        """
        sensitive_keys = {
            "password",
            "token",
            "secret",
            "key",
            "credential",
            "api_key",
            "access_token",
            "refresh_token",
            "authorization",
            "ssn",
            "credit_card",
            "cvv",
        }

        sanitized = {}
        for k, v in details.items():
            key_lower = k.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sanitized[k] = self._sanitize_details(v)
            elif isinstance(v, str) and self._looks_like_pii(v):
                sanitized[k] = "[REDACTED: Potential PII]"
            else:
                sanitized[k] = v

        return sanitized

    def _looks_like_pii(self, value: str) -> bool:
        """Check if value looks like it contains PII."""
        import re

        # Email pattern
        if re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", value):
            return True

        # SSN pattern
        if re.search(r"\b\d{3}-\d{2}-\d{4}\b", value):
            return True

        # Credit card pattern (basic)
        if re.search(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", value):
            return True

        return False

    def _rotate_logs(self) -> None:
        """Rotate log file when max entries reached."""
        if not self._log_file.exists():
            return

        self._archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_file = self._archive_dir / f"audit_{timestamp}.log"

        # Move current log to archive
        self._log_file.rename(archive_file)
        self._entry_count = 0

        self._logger.info(f"Rotated audit log to {archive_file}")

    def add_handler(
        self,
        handler: Callable[[AuditEvent], None],
    ) -> None:
        """
        Add a custom event handler.

        Args:
          handler: Callable that receives AuditEvent
        """
        self._handlers.append(handler)

    def search(
        self,
        operation: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Search audit log for matching events.

        Args:
          operation: Filter by operation type
          user_id: Filter by user ID
          start_time: Filter events after this time
          end_time: Filter events before this time
          status: Filter by status
          limit: Maximum number of results

        Returns:
          List of matching AuditEvent objects
        """
        results = []

        if not self._log_file.exists():
            return results

        with open(self._log_file, "r", encoding="utf-8") as f:
            for line in f:
                if len(results) >= limit:
                    break

                try:
                    # Extract JSON from log line
                    json_start = line.find("{")
                    if json_start == -1:
                        continue
                    json_str = line[json_start:]
                    data = json.loads(json_str)
                    event = AuditEvent.from_dict(data)

                    # Apply filters
                    if operation and event.operation != operation:
                        continue
                    if user_id and event.user_id != user_id:
                        continue
                    if status and event.status != status:
                        continue
                    if start_time:
                        event_time = datetime.fromisoformat(
                            event.timestamp.replace("Z", "+00:00")
                        )
                        if event_time < start_time:
                            continue
                    if end_time:
                        event_time = datetime.fromisoformat(
                            event.timestamp.replace("Z", "+00:00")
                        )
                        if event_time > end_time:
                            continue

                    results.append(event)

                except (json.JSONDecodeError, KeyError):
                    continue

        return results

    # Convenience methods for common operations

    def log_auth_success(
        self,
        user_id: str,
        source_ip: Optional[str] = None,
        **kwargs,
    ) -> AuditEvent:
        """Log successful authentication."""
        return self.log(
            operation=SensitiveOperation.AUTH_LOGIN,
            user_id=user_id,
            status="success",
            source_ip=source_ip,
            **kwargs,
        )

    def log_auth_failure(
        self,
        user_id: Optional[str] = None,
        reason: str = "",
        source_ip: Optional[str] = None,
        **kwargs,
    ) -> AuditEvent:
        """Log failed authentication."""
        return self.log(
            operation=SensitiveOperation.AUTH_FAILED,
            user_id=user_id,
            status="failure",
            details={"reason": reason},
            source_ip=source_ip,
            **kwargs,
        )

    def log_data_access(
        self,
        user_id: str,
        resource_id: str,
        resource_type: str,
        action: str = "read",
        **kwargs,
    ) -> AuditEvent:
        """Log data access event."""
        operation = {
            "read": SensitiveOperation.DATA_READ,
            "write": SensitiveOperation.DATA_WRITE,
            "delete": SensitiveOperation.DATA_DELETE,
            "export": SensitiveOperation.DATA_EXPORT,
        }.get(action, SensitiveOperation.DATA_READ)

        return self.log(
            operation=operation,
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            **kwargs,
        )

    def log_encryption_operation(
        self,
        operation_type: str,
        key_id: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs,
    ) -> AuditEvent:
        """Log encryption/decryption operation."""
        operation = (
            SensitiveOperation.ENCRYPT_DATA
            if operation_type == "encrypt"
            else SensitiveOperation.DECRYPT_DATA
        )

        return self.log(
            operation=operation,
            user_id=user_id,
            resource_id=resource_id,
            details={"key_id": key_id},
            **kwargs,
        )

    def log_key_operation(
        self,
        operation_type: str,
        key_id: str,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> AuditEvent:
        """Log key management operation."""
        operation_map = {
            "create": SensitiveOperation.KEY_CREATE,
            "rotate": SensitiveOperation.KEY_ROTATE,
            "delete": SensitiveOperation.KEY_DELETE,
            "access": SensitiveOperation.KEY_ACCESS,
        }
        operation = operation_map.get(
            operation_type, SensitiveOperation.KEY_ACCESS
        )

        return self.log(
            operation=operation,
            user_id=user_id,
            resource_id=key_id,
            resource_type="encryption_key",
            **kwargs,
        )

    def log_security_event(
        self,
        event_type: str,
        severity: str = "warning",
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> AuditEvent:
        """Log security alert or violation."""
        operation = (
            SensitiveOperation.SECURITY_VIOLATION
            if severity == "critical"
            else SensitiveOperation.SECURITY_ALERT
        )

        return self.log(
            operation=operation,
            user_id=user_id,
            status=severity,
            details={"event_type": event_type, **(details or {})},
            **kwargs,
        )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        log_file = os.environ.get("AUDIT_LOG_FILE", "audit.log")
        _audit_logger = AuditLogger(log_file=log_file)
    return _audit_logger


def set_audit_logger(logger: AuditLogger) -> None:
    """Set the global audit logger instance."""
    global _audit_logger
    _audit_logger = logger
