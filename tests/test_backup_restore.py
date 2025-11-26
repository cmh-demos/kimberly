import gzip
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from scripts import backup_db as backup
from scripts import export_data as export
from scripts import import_data as import_data
from scripts import restore_db as restore


class TestBackupDb(unittest.TestCase):
    def test_parse_database_url(self):
        url = "postgresql://user:pass@localhost:5432/testdb"
        result = backup.parse_database_url(url)
        self.assertEqual(result["host"], "localhost")
        self.assertEqual(result["port"], 5432)
        self.assertEqual(result["user"], "user")
        self.assertEqual(result["password"], "pass")
        self.assertEqual(result["database"], "testdb")

    def test_parse_database_url_defaults(self):
        url = "postgresql:///mydb"
        result = backup.parse_database_url(url)
        self.assertEqual(result["host"], "localhost")
        self.assertEqual(result["port"], 5432)
        self.assertEqual(result["user"], "postgres")
        self.assertEqual(result["database"], "mydb")

    def test_create_backup_filename(self):
        filename = backup.create_backup_filename("testdb", compress=False)
        self.assertTrue(filename.startswith("testdb_backup_"))
        self.assertTrue(filename.endswith(".sql"))

    def test_create_backup_filename_compressed(self):
        filename = backup.create_backup_filename("testdb", compress=True)
        self.assertTrue(filename.endswith(".sql.gz"))

    def test_cleanup_old_backups(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create a test backup file
            old_file = tmppath / "test_backup_20200101_000000.sql"
            old_file.touch()

            # Set file modification time to old
            old_time = datetime(2020, 1, 1).timestamp()
            os.utime(old_file, (old_time, old_time))

            removed = backup.cleanup_old_backups(tmppath, retention_days=1)
            self.assertEqual(removed, 1)
            self.assertFalse(old_file.exists())

    def test_cleanup_old_backups_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            removed = backup.cleanup_old_backups(Path(tmpdir), retention_days=0)
            self.assertEqual(removed, 0)

    def test_backup_sqlite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create a test SQLite file
            db_file = tmppath / "test.db"
            db_file.write_bytes(b"SQLite test content")

            result = backup.backup_sqlite(db_file, tmppath, compress=False)
            self.assertIsNotNone(result)
            self.assertTrue(result.exists())
            self.assertTrue("backup" in result.name)

    def test_backup_sqlite_compressed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            db_file = tmppath / "test.db"
            db_file.write_bytes(b"SQLite test content")

            result = backup.backup_sqlite(db_file, tmppath, compress=True)
            self.assertIsNotNone(result)
            self.assertTrue(result.name.endswith(".db.gz"))

    def test_backup_sqlite_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = backup.backup_sqlite(
                Path("/nonexistent/db.db"), Path(tmpdir), compress=False
            )
            self.assertIsNone(result)

    @patch.dict(os.environ, {}, clear=True)
    def test_main_no_database_url_no_sqlite(self):
        with patch("sys.argv", ["backup_db.py"]):
            result = backup.main()
            self.assertEqual(result, 1)

    @patch.dict(os.environ, {}, clear=True)
    def test_main_sqlite_mode_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_file = Path(tmpdir) / "test.db"
            db_file.write_bytes(b"test")
            with patch(
                "sys.argv",
                ["backup_db.py", "--sqlite", str(db_file), "--dry-run"],
            ):
                result = backup.main()
                self.assertEqual(result, 0)


class TestRestoreDb(unittest.TestCase):
    def test_parse_database_url(self):
        url = "postgresql://user:pass@host:5432/db"
        result = restore.parse_database_url(url)
        self.assertEqual(result["database"], "db")

    def test_validate_backup_file_not_found(self):
        result = restore.validate_backup_file(Path("/nonexistent/file.sql"))
        self.assertFalse(result)

    def test_validate_backup_file_invalid_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            result = restore.validate_backup_file(Path(f.name))
            self.assertFalse(result)

    def test_validate_backup_file_valid(self):
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
            f.write(b"SQL content")
            f.flush()
            result = restore.validate_backup_file(Path(f.name))
            self.assertTrue(result)
            os.unlink(f.name)

    def test_validate_backup_file_gzip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gz_file = Path(tmpdir) / "test.sql.gz"
            with gzip.open(gz_file, "wb") as f:
                f.write(b"SQL content")
            result = restore.validate_backup_file(gz_file)
            self.assertTrue(result)

    def test_restore_sqlite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            backup_file = tmppath / "backup.db"
            backup_file.write_bytes(b"SQLite data")
            target_file = tmppath / "restored.db"

            result = restore.restore_sqlite(backup_file, target_file)
            self.assertTrue(result)
            self.assertTrue(target_file.exists())

    def test_restore_sqlite_compressed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            backup_file = tmppath / "backup.db.gz"
            with gzip.open(backup_file, "wb") as f:
                f.write(b"SQLite data")
            target_file = tmppath / "restored.db"

            result = restore.restore_sqlite(backup_file, target_file)
            self.assertTrue(result)
            self.assertTrue(target_file.exists())

    def test_decompress_backup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gz_file = Path(tmpdir) / "test.sql.gz"
            original_content = b"SELECT * FROM test;"
            with gzip.open(gz_file, "wb") as f:
                f.write(original_content)

            temp_path = restore.decompress_backup(gz_file)
            try:
                self.assertTrue(temp_path.exists())
                self.assertEqual(temp_path.read_bytes(), original_content)
            finally:
                temp_path.unlink()

    @patch.dict(os.environ, {}, clear=True)
    def test_main_dry_run(self):
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
            f.write(b"SQL content")
            f.flush()
            try:
                with patch(
                    "sys.argv", ["restore_db.py", f.name, "--dry-run"]
                ):
                    result = restore.main()
                    self.assertEqual(result, 0)
            finally:
                os.unlink(f.name)

    @patch.dict(os.environ, {}, clear=True)
    def test_main_sqlite_no_target(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(b"SQLite")
            f.flush()
            try:
                with patch("sys.argv", ["restore_db.py", f.name]):
                    result = restore.main()
                    self.assertEqual(result, 1)
            finally:
                os.unlink(f.name)


class TestExportData(unittest.TestCase):
    def test_sanitize_for_export_dict(self):
        data = {"name": "test", "password": "secret123", "api_key": "key123"}
        result = export.sanitize_for_export(data)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["password"], "[REDACTED]")
        self.assertEqual(result["api_key"], "[REDACTED]")

    def test_sanitize_for_export_list(self):
        data = [{"password": "secret"}, {"name": "test"}]
        result = export.sanitize_for_export(data)
        self.assertEqual(result[0]["password"], "[REDACTED]")
        self.assertEqual(result[1]["name"], "test")

    def test_sanitize_for_export_nested(self):
        data = {"config": {"secret_token": "abc123"}}
        result = export.sanitize_for_export(data)
        self.assertEqual(result["config"]["secret_token"], "[REDACTED]")

    def test_export_triage_logs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "triage_log.json"
            logs = [{"issue_number": 1, "timestamp": "2025-01-01T00:00:00Z"}]
            log_file.write_text(json.dumps(logs))

            result = export.export_triage_logs(log_file)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["issue_number"], 1)

    def test_export_triage_logs_not_found(self):
        result = export.export_triage_logs(Path("/nonexistent/log.json"))
        self.assertEqual(result, [])

    def test_export_triage_logs_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "triage_log.json"
            log_file.write_text("invalid json {")

            result = export.export_triage_logs(log_file)
            self.assertEqual(result, [])

    def test_export_config_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yml"
            config_file.write_text("key: value\n")

            result = export.export_config_files([config_file])
            self.assertIn("config.yml", result)
            self.assertEqual(result["config.yml"]["key"], "value")

    def test_export_config_files_not_found(self):
        result = export.export_config_files([Path("/nonexistent/config.yml")])
        self.assertEqual(result, {})

    def test_create_export_package(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "triage.json"
            log_file.write_text("[]")

            result = export.create_export_package(
                ["all"], log_file, [], None
            )
            self.assertIn("export_metadata", result)
            self.assertIn("exported_at", result["export_metadata"])

    @patch.dict(os.environ, {}, clear=True)
    def test_main_dry_run(self):
        with patch(
            "sys.argv",
            ["export_data.py", "--dry-run", "--output", "/tmp/test.json"],
        ):
            result = export.main()
            self.assertEqual(result, 0)


class TestImportData(unittest.TestCase):
    def test_validate_import_file_not_found(self):
        result = import_data.validate_import_file(Path("/nonexistent.json"))
        self.assertFalse(result)

    def test_validate_import_file_wrong_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            result = import_data.validate_import_file(Path(f.name))
            self.assertFalse(result)

    def test_validate_import_file_valid(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            f.write(b"{}")
            f.flush()
            result = import_data.validate_import_file(Path(f.name))
            self.assertTrue(result)
            os.unlink(f.name)

    def test_validate_export_structure_valid(self):
        data = {"export_metadata": {"version": "1.0.0"}}
        result = import_data.validate_export_structure(data)
        self.assertTrue(result)

    def test_validate_export_structure_invalid(self):
        result = import_data.validate_export_structure([])
        self.assertFalse(result)

    def test_sanitize_string(self):
        result = import_data.sanitize_string("hello\x00world")
        self.assertEqual(result, "helloworld")

    def test_sanitize_string_truncate(self):
        long_string = "a" * 20000
        result = import_data.sanitize_string(long_string, max_length=100)
        self.assertEqual(len(result), 100)

    def test_sanitize_import_data_dict(self):
        data = {"key\x00": "value\x00"}
        result = import_data.sanitize_import_data(data)
        self.assertIn("key", result)
        self.assertEqual(result["key"], "value")

    def test_sanitize_import_data_list(self):
        data = ["item1\x00", "item2"]
        result = import_data.sanitize_import_data(data)
        self.assertEqual(result, ["item1", "item2"])

    def test_import_triage_logs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "triage_log.json"
            logs = [{"issue_number": 1, "timestamp": "2025-01-01T00:00:00Z"}]

            count = import_data.import_triage_logs(logs, target, merge=False)
            self.assertEqual(count, 1)
            self.assertTrue(target.exists())

    def test_import_triage_logs_merge(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "triage_log.json"
            existing = [{"issue_number": 1, "timestamp": "2025-01-01T00:00:00Z"}]
            target.write_text(json.dumps(existing))

            new_logs = [
                {"issue_number": 2, "timestamp": "2025-01-02T00:00:00Z"}
            ]
            count = import_data.import_triage_logs(new_logs, target, merge=True)
            self.assertEqual(count, 1)

            with open(target) as f:
                result = json.load(f)
                self.assertEqual(len(result), 2)

    def test_import_triage_logs_dedup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "triage_log.json"
            existing = [{"issue_number": 1, "timestamp": "2025-01-01T00:00:00Z"}]
            target.write_text(json.dumps(existing))

            # Import same log entry
            count = import_data.import_triage_logs(existing, target, merge=True)
            self.assertEqual(count, 0)

    def test_import_memory_items_to_sqlite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            items = [
                {
                    "id": "mem_123",
                    "user_id": "user_1",
                    "type": "long-term",
                    "content": "Test content",
                    "metadata": {"tags": ["test"]},
                    "score": 0.5,
                }
            ]

            count = import_data.import_memory_items_to_sqlite(items, db_path)
            self.assertEqual(count, 1)
            self.assertTrue(db_path.exists())

    def test_import_config_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            configs = {"test.yml": {"key": "value"}}
            count = import_data.import_config_files(
                configs, Path(tmpdir), overwrite=False
            )
            self.assertEqual(count, 1)
            self.assertTrue((Path(tmpdir) / "test.yml").exists())

    def test_import_config_files_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir) / "test.yml"
            existing.write_text("existing: true\n")

            configs = {"test.yml": {"key": "value"}}
            count = import_data.import_config_files(
                configs, Path(tmpdir), overwrite=False
            )
            self.assertEqual(count, 0)

    @patch.dict(os.environ, {}, clear=True)
    def test_main_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            import_file = Path(tmpdir) / "import.json"
            data = {"export_metadata": {"version": "1.0.0"}, "triage_logs": []}
            import_file.write_text(json.dumps(data))

            with patch(
                "sys.argv",
                ["import_data.py", str(import_file), "--dry-run"],
            ):
                result = import_data.main()
                self.assertEqual(result, 0)

    @patch.dict(os.environ, {}, clear=True)
    def test_main_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            import_file = Path(tmpdir) / "import.json"
            import_file.write_text("invalid json {")

            with patch("sys.argv", ["import_data.py", str(import_file)]):
                result = import_data.main()
                self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
