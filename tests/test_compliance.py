"""Tests for GDPR compliance API module."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from src.api.compliance import (
    AuditAction,
    AuditLogger,
    CheckStatus,
    ComplianceChecker,
    ComplianceStatus,
    DataDeletionService,
    DataExportService,
    DataType,
    DeleteRequest,
    DeletionStatus,
    ExportRequest,
    ExportStatus,
    RetentionPolicyService,
    RetentionPolicyUpdate,
    get_audit_logger,
    get_compliance_checker,
    get_deletion_service,
    get_export_service,
    get_retention_service,
)


class TestAuditLogger(unittest.TestCase):
    """Tests for AuditLogger."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json"
        )
        self.temp_file.close()
        self.logger = AuditLogger(storage_path=self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_log_creates_entry(self):
        entry = self.logger.log(
            user_id="user_123",
            action=AuditAction.DATA_EXPORT_REQUESTED,
            resource_type="user_data",
            resource_id="exp_001",
        )

        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.user_id, "user_123")
        self.assertEqual(entry.action, AuditAction.DATA_EXPORT_REQUESTED)
        self.assertEqual(entry.resource_type, "user_data")
        self.assertEqual(entry.resource_id, "exp_001")

    def test_log_with_details(self):
        entry = self.logger.log(
            user_id="user_123",
            action=AuditAction.SETTINGS_CHANGED,
            details={"setting": "retention_days", "value": 30},
        )

        self.assertEqual(entry.details["setting"], "retention_days")
        self.assertEqual(entry.details["value"], 30)

    def test_log_with_ip_and_user_agent(self):
        entry = self.logger.log(
            user_id="user_123",
            action=AuditAction.LOGIN,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        self.assertEqual(entry.ip_address, "192.168.1.1")
        self.assertEqual(entry.user_agent, "Mozilla/5.0")

    def test_query_returns_user_logs(self):
        self.logger.log(user_id="user_123", action=AuditAction.LOGIN)
        self.logger.log(user_id="user_123", action=AuditAction.LOGOUT)
        self.logger.log(user_id="user_456", action=AuditAction.LOGIN)

        result = self.logger.query(user_id="user_123")

        self.assertEqual(result.total, 2)
        self.assertEqual(len(result.items), 2)
        for item in result.items:
            self.assertEqual(item.user_id, "user_123")

    def test_query_filters_by_action(self):
        self.logger.log(user_id="user_123", action=AuditAction.LOGIN)
        self.logger.log(user_id="user_123", action=AuditAction.LOGOUT)
        self.logger.log(user_id="user_123", action=AuditAction.LOGIN)

        result = self.logger.query(user_id="user_123", action=AuditAction.LOGIN)

        self.assertEqual(result.total, 2)
        for item in result.items:
            self.assertEqual(item.action, AuditAction.LOGIN)

    def test_query_filters_by_date_range(self):
        now = datetime.now(timezone.utc)
        self.logger.log(user_id="user_123", action=AuditAction.LOGIN)

        result = self.logger.query(
            user_id="user_123",
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
        )

        self.assertEqual(result.total, 1)

    def test_query_pagination(self):
        for i in range(15):
            self.logger.log(
                user_id="user_123", action=AuditAction.DATA_ACCESSED
            )

        result_page1 = self.logger.query(
            user_id="user_123", page=1, per_page=10
        )
        result_page2 = self.logger.query(
            user_id="user_123", page=2, per_page=10
        )

        self.assertEqual(len(result_page1.items), 10)
        self.assertEqual(len(result_page2.items), 5)
        self.assertEqual(result_page1.total, 15)


class TestDataExportService(unittest.TestCase):
    """Tests for DataExportService."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json"
        )
        self.temp_file.close()
        self.audit_logger = AuditLogger(storage_path=self.temp_file.name)
        self.service = DataExportService(self.audit_logger)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_request_export_creates_pending_export(self):
        request = ExportRequest(format="json", include_metadata=True)
        response = self.service.request_export(
            user_id="user_123", request=request
        )

        self.assertIsNotNone(response.export_id)
        self.assertEqual(response.status, ExportStatus.PENDING)
        self.assertIsNotNone(response.created_at)
        self.assertIsNotNone(response.expires_at)

    def test_request_export_logs_audit_event(self):
        request = ExportRequest()
        self.service.request_export(user_id="user_123", request=request)

        logs = self.audit_logger.query(user_id="user_123")
        self.assertEqual(logs.total, 1)
        self.assertEqual(
            logs.items[0].action, AuditAction.DATA_EXPORT_REQUESTED
        )

    def test_get_export_status_returns_status(self):
        request = ExportRequest()
        response = self.service.request_export(
            user_id="user_123", request=request
        )

        status = self.service.get_export_status(
            export_id=response.export_id, user_id="user_123"
        )

        self.assertIsNotNone(status)
        self.assertEqual(status.export_id, response.export_id)
        self.assertEqual(status.status, ExportStatus.PENDING)

    def test_get_export_status_returns_none_for_unknown_id(self):
        status = self.service.get_export_status(
            export_id="unknown_id", user_id="user_123"
        )
        self.assertIsNone(status)

    def test_complete_export_updates_status(self):
        request = ExportRequest()
        response = self.service.request_export(
            user_id="user_123", request=request
        )

        self.service.complete_export(
            export_id=response.export_id,
            user_id="user_123",
            download_url="https://example.com/download",
        )

        status = self.service.get_export_status(
            export_id=response.export_id, user_id="user_123"
        )

        self.assertEqual(status.status, ExportStatus.COMPLETED)
        self.assertEqual(status.progress_percent, 100)
        self.assertEqual(status.download_url, "https://example.com/download")
        self.assertIsNotNone(status.completed_at)


class TestDataDeletionService(unittest.TestCase):
    """Tests for DataDeletionService."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json"
        )
        self.temp_file.close()
        self.audit_logger = AuditLogger(storage_path=self.temp_file.name)
        self.service = DataDeletionService(self.audit_logger)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_request_deletion_creates_pending_deletion(self):
        request = DeleteRequest(confirm=True)
        response = self.service.request_deletion(
            user_id="user_123", request=request
        )

        self.assertIsNotNone(response.deletion_id)
        self.assertEqual(response.status, DeletionStatus.PENDING)
        self.assertIsNotNone(response.created_at)

    def test_request_deletion_logs_audit_event(self):
        request = DeleteRequest(confirm=True, reason="No longer needed")
        self.service.request_deletion(user_id="user_123", request=request)

        logs = self.audit_logger.query(user_id="user_123")
        self.assertEqual(logs.total, 1)
        self.assertEqual(
            logs.items[0].action, AuditAction.DATA_DELETION_REQUESTED
        )
        self.assertEqual(logs.items[0].details["reason"], "No longer needed")

    def test_get_deletion_status_returns_status(self):
        request = DeleteRequest(confirm=True)
        response = self.service.request_deletion(
            user_id="user_123", request=request
        )

        status = self.service.get_deletion_status(
            deletion_id=response.deletion_id, user_id="user_123"
        )

        self.assertIsNotNone(status)
        self.assertEqual(status.deletion_id, response.deletion_id)
        self.assertEqual(status.status, DeletionStatus.PENDING)

    def test_complete_deletion_updates_status(self):
        request = DeleteRequest(confirm=True)
        response = self.service.request_deletion(
            user_id="user_123", request=request
        )

        data_types = ["profile", "memories", "chat_history"]
        self.service.complete_deletion(
            deletion_id=response.deletion_id,
            user_id="user_123",
            data_types=data_types,
        )

        status = self.service.get_deletion_status(
            deletion_id=response.deletion_id, user_id="user_123"
        )

        self.assertEqual(status.status, DeletionStatus.COMPLETED)
        self.assertEqual(status.progress_percent, 100)
        self.assertEqual(status.data_types_deleted, data_types)
        self.assertIsNotNone(status.completed_at)


class TestRetentionPolicyService(unittest.TestCase):
    """Tests for RetentionPolicyService."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json"
        )
        self.temp_file.close()
        self.audit_logger = AuditLogger(storage_path=self.temp_file.name)
        self.service = RetentionPolicyService(self.audit_logger)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_get_policies_initializes_defaults(self):
        policies = self.service.get_policies(user_id="user_123")

        self.assertEqual(len(policies.policies), len(DataType))
        policy_types = {p.data_type for p in policies.policies}
        for data_type in DataType:
            self.assertIn(data_type, policy_types)

    def test_default_policies_have_expected_values(self):
        policies = self.service.get_policies(user_id="user_123")

        policy_map = {p.data_type: p for p in policies.policies}

        self.assertEqual(
            policy_map[DataType.MEMORY_SHORT_TERM].retention_days, 7
        )
        self.assertEqual(policy_map[DataType.CHAT_HISTORY].retention_days, 365)
        self.assertEqual(
            policy_map[DataType.MEMORY_PERMANENT].retention_days, 0
        )

    def test_update_policies_modifies_retention_days(self):
        updates = [
            RetentionPolicyUpdate(
                data_type=DataType.CHAT_HISTORY,
                retention_days=180,
                auto_delete=True,
            )
        ]

        result = self.service.update_policies(
            user_id="user_123", updates=updates
        )

        policy_map = {p.data_type: p for p in result.policies}
        self.assertEqual(policy_map[DataType.CHAT_HISTORY].retention_days, 180)

    def test_update_policies_logs_audit_event(self):
        updates = [
            RetentionPolicyUpdate(
                data_type=DataType.TELEMETRY,
                retention_days=30,
                auto_delete=True,
            )
        ]

        self.service.update_policies(user_id="user_123", updates=updates)

        logs = self.audit_logger.query(user_id="user_123")
        self.assertEqual(logs.total, 1)
        self.assertEqual(logs.items[0].action, AuditAction.SETTINGS_CHANGED)


class TestComplianceChecker(unittest.TestCase):
    """Tests for ComplianceChecker."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json"
        )
        self.temp_file.close()
        self.audit_logger = AuditLogger(storage_path=self.temp_file.name)
        self.retention_service = RetentionPolicyService(self.audit_logger)
        self.checker = ComplianceChecker(
            self.audit_logger, self.retention_service
        )

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_run_checks_returns_result(self):
        result = self.checker.run_checks(user_id="user_123")

        self.assertIsNotNone(result.check_id)
        self.assertIsNotNone(result.timestamp)
        self.assertIn(
            result.overall_status,
            [
                ComplianceStatus.COMPLIANT,
                ComplianceStatus.WARNING,
                ComplianceStatus.NON_COMPLIANT,
            ],
        )

    def test_run_checks_includes_required_checks(self):
        result = self.checker.run_checks(user_id="user_123")

        check_names = {c.name for c in result.checks}
        required_checks = {
            "Data Encryption",
            "Retention Policies",
            "Audit Logging",
            "Data Export",
            "Data Deletion",
            "Consent Management",
        }

        for required in required_checks:
            self.assertIn(required, check_names)

    def test_run_checks_all_pass_for_compliant_user(self):
        # Initialize policies for user first
        self.retention_service.get_policies(user_id="user_123")

        result = self.checker.run_checks(user_id="user_123")

        for check in result.checks:
            self.assertIn(
                check.status, [CheckStatus.PASSED, CheckStatus.WARNING]
            )


class TestServiceSingletons(unittest.TestCase):
    """Tests for service singleton functions."""

    def test_get_audit_logger_returns_same_instance(self):
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        self.assertIs(logger1, logger2)

    def test_get_export_service_returns_same_instance(self):
        service1 = get_export_service()
        service2 = get_export_service()
        self.assertIs(service1, service2)

    def test_get_deletion_service_returns_same_instance(self):
        service1 = get_deletion_service()
        service2 = get_deletion_service()
        self.assertIs(service1, service2)

    def test_get_retention_service_returns_same_instance(self):
        service1 = get_retention_service()
        service2 = get_retention_service()
        self.assertIs(service1, service2)

    def test_get_compliance_checker_returns_same_instance(self):
        checker1 = get_compliance_checker()
        checker2 = get_compliance_checker()
        self.assertIs(checker1, checker2)


if __name__ == "__main__":
    unittest.main()
