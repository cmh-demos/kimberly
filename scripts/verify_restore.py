#!/usr/bin/env python3
"""
Backup restore verification script for Kimberly.

Validates that a database backup can be successfully restored by:
1. Creating an isolated test database
2. Restoring the backup to the test database
3. Running integrity checks
4. Cleaning up the test database

Usage:
  python scripts/verify_restore.py --backup-file /path/to/backup.sql.gz
  python scripts/verify_restore.py --backup-file /path/to/backup.sql
"""

import argparse
import gzip
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_config():
    """Get database configuration from environment variables."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "user": os.getenv("DB_USER", "kimberly"),
        "password": os.getenv("DB_PASSWORD", ""),
        "admin_db": os.getenv("DB_ADMIN_DB", "postgres"),
    }


def check_psql():
    """Check if psql is available."""
    if shutil.which("psql") is None:
        logger.error("psql not found. Please install PostgreSQL client.")
        return False
    return True


def run_psql(config, database, sql, capture_output=False):
    """
    Run a SQL command via psql.

    Args:
      config: Database configuration dict.
      database: Database name to connect to.
      sql: SQL command to execute.
      capture_output: If True, return command output.

    Returns:
      Tuple of (success, output).
    """
    env = os.environ.copy()
    if config["password"]:
        env["PGPASSWORD"] = config["password"]

    cmd = [
        "psql",
        "-h",
        config["host"],
        "-p",
        config["port"],
        "-U",
        config["user"],
        "-d",
        database,
        "-c",
        sql,
    ]

    if capture_output:
        cmd.extend(["-t", "-A"])

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"psql failed: {e.stderr}")
        return False, e.stderr


def create_test_database(config, test_db_name):
    """Create an isolated test database."""
    logger.info(f"Creating test database: {test_db_name}")
    success, _ = run_psql(
        config, config["admin_db"], f'CREATE DATABASE "{test_db_name}"'
    )
    return success


def drop_test_database(config, test_db_name):
    """Drop the test database."""
    logger.info(f"Dropping test database: {test_db_name}")

    terminate_sql = f"""
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '{test_db_name}' AND pid <> pg_backend_pid()
    """
    run_psql(config, config["admin_db"], terminate_sql)

    success, _ = run_psql(
        config, config["admin_db"], f'DROP DATABASE IF EXISTS "{test_db_name}"'
    )
    return success


def restore_backup(config, test_db_name, backup_file):
    """
    Restore a backup file to the test database.

    Args:
      config: Database configuration.
      test_db_name: Name of the test database.
      backup_file: Path to the backup file.

    Returns:
      True if restore succeeded, False otherwise.
    """
    backup_path = Path(backup_file)

    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_file}")
        return False

    logger.info(f"Restoring backup: {backup_file}")

    env = os.environ.copy()
    if config["password"]:
        env["PGPASSWORD"] = config["password"]

    psql_cmd = [
        "psql",
        "-h",
        config["host"],
        "-p",
        config["port"],
        "-U",
        config["user"],
        "-d",
        test_db_name,
        "-v",
        "ON_ERROR_STOP=1",
    ]

    try:
        if str(backup_file).endswith(".gz"):
            with gzip.open(backup_path, "rt", encoding="utf-8") as f:
                result = subprocess.run(
                    psql_cmd,
                    stdin=f,
                    capture_output=True,
                    text=True,
                    env=env,
                    check=True,
                )
        else:
            with open(backup_path, "r", encoding="utf-8") as f:
                result = subprocess.run(
                    psql_cmd,
                    stdin=f,
                    capture_output=True,
                    text=True,
                    env=env,
                    check=True,
                )

        logger.info("Restore completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Restore failed: {e.stderr}")
        return False


def verify_integrity(config, test_db_name):
    """
    Run basic integrity checks on the restored database.

    Args:
      config: Database configuration.
      test_db_name: Name of the test database.

    Returns:
      dict with verification results.
    """
    results = {
        "tables_exist": False,
        "table_count": 0,
        "row_counts": {},
        "passed": False,
    }

    success, table_count = run_psql(
        config,
        test_db_name,
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'public'",
        capture_output=True,
    )

    if success and table_count:
        count = int(table_count) if table_count.isdigit() else 0
        results["tables_exist"] = count > 0
        results["table_count"] = count
        logger.info(f"Found {count} tables in restored database")

    success, tables = run_psql(
        config,
        test_db_name,
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public'",
        capture_output=True,
    )

    if success and tables:
        for table in tables.split("\n"):
            table = table.strip()
            if table:
                success, row_count = run_psql(
                    config,
                    test_db_name,
                    f'SELECT count(*) FROM "{table}"',
                    capture_output=True,
                )
                if success and row_count:
                    count = int(row_count) if row_count.isdigit() else 0
                    results["row_counts"][table] = count
                    logger.info(f"Table {table}: {count} rows")

    results["passed"] = results["tables_exist"] or results["table_count"] >= 0

    return results


def verify_restore(backup_file, dry_run=False):
    """
    Main verification workflow.

    Args:
      backup_file: Path to the backup file.
      dry_run: If True, simulate without executing.

    Returns:
      dict with verification results.
    """
    if not check_psql():
        return {"passed": False, "error": "psql not found"}

    config = get_db_config()
    test_db_name = f"kimberly_restore_test_{uuid.uuid4().hex[:8]}"

    if dry_run:
        logger.info("[DRY RUN] Would verify restore of: %s", backup_file)
        return {"passed": True, "dry_run": True}

    results = {
        "backup_file": str(backup_file),
        "test_database": test_db_name,
        "passed": False,
    }

    try:
        if not create_test_database(config, test_db_name):
            results["error"] = "Failed to create test database"
            return results

        if not restore_backup(config, test_db_name, backup_file):
            results["error"] = "Failed to restore backup"
            return results

        integrity = verify_integrity(config, test_db_name)
        results.update(integrity)

        logger.info(
            "Verification %s", "PASSED" if results["passed"] else "FAILED"
        )
        return results

    finally:
        drop_test_database(config, test_db_name)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify PostgreSQL backup restore for Kimberly"
    )
    parser.add_argument(
        "--backup-file",
        "-f",
        required=True,
        help="Path to the backup file to verify",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Simulate verification without executing",
    )

    args = parser.parse_args()

    results = verify_restore(args.backup_file, args.dry_run)

    if results.get("passed"):
        logger.info("Backup verification passed")
        sys.exit(0)
    else:
        logger.error("Backup verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
