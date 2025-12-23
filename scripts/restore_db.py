#!/usr/bin/env python3
"""Database restore script for Kimberly.

This script provides PostgreSQL database restore functionality from
backup files created by backup_db.py.

Usage:
    python scripts/restore_db.py BACKUP_FILE [--dry-run]

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
        (e.g., 'postgresql://user:pass@host:5432/dbname')

Example:
    # Restore from a backup file
    python scripts/restore_db.py backups/kimberly_backup_20250101_120000.sql

    # Restore from compressed backup
    python scripts/restore_db.py backups/kimberly_backup_20250101_120000.sql.gz

Security:
    - Validates backup file extension before processing
    - Uses parameterized environment variables for credentials
    - Logs all restore operations for audit trail
"""

from __future__ import annotations

import argparse
import gzip
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Allowed backup file extensions for security
ALLOWED_EXTENSIONS = {".sql", ".sql.gz", ".db", ".db.gz"}


def parse_database_url(url: str) -> dict:
    """Parse a PostgreSQL connection URL into components."""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "database": parsed.path.lstrip("/") or "kimberly",
    }


def validate_backup_file(backup_path: Path) -> bool:
    """Validate backup file exists and has allowed extension.

    Args:
        backup_path: Path to the backup file

    Returns:
        True if valid, False otherwise
    """
    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_path}")
        return False

    # Check for allowed extensions
    suffix = backup_path.suffix
    if suffix == ".gz":
        # Check double extension like .sql.gz
        full_suffix = "".join(backup_path.suffixes[-2:])
        if full_suffix not in ALLOWED_EXTENSIONS:
            logger.error(f"Invalid backup file extension: {full_suffix}")
            return False
    elif suffix not in ALLOWED_EXTENSIONS:
        logger.error(f"Invalid backup file extension: {suffix}")
        return False

    return True


def run_psql_restore(db_config: dict, backup_path: Path) -> bool:
    """Execute psql to restore a database from backup.

    Args:
        db_config: Database connection configuration
        backup_path: Path to the backup SQL file

    Returns:
        True if restore succeeded, False otherwise
    """
    env = os.environ.copy()
    if db_config["password"]:
        env["PGPASSWORD"] = db_config["password"]

    cmd = [
        "psql",
        "-h",
        db_config["host"],
        "-p",
        str(db_config["port"]),
        "-U",
        db_config["user"],
        "-d",
        db_config["database"],
        "-f",
        str(backup_path),
        "--quiet",
    ]

    try:
        result = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=env,
            check=True,
        )
        logger.info(f"Database restored from: {backup_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"psql restore failed: {e.stderr.decode()}")
        return False
    except FileNotFoundError:
        logger.error(
            "psql not found. Ensure PostgreSQL client tools are installed."
        )
        return False
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


def decompress_backup(backup_path: Path) -> Path:
    """Decompress a gzipped backup file to a temporary location.

    Args:
        backup_path: Path to the compressed backup file

    Returns:
        Path to the decompressed file (caller must clean up)
    """
    # Create temp file with appropriate suffix
    suffix = backup_path.stem.split("_")[-1]
    if backup_path.name.endswith(".sql.gz"):
        temp_suffix = ".sql"
    elif backup_path.name.endswith(".db.gz"):
        temp_suffix = ".db"
    else:
        temp_suffix = ""

    fd, temp_path = tempfile.mkstemp(suffix=temp_suffix)
    try:
        with gzip.open(backup_path, "rb") as f_in:
            with os.fdopen(fd, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return Path(temp_path)
    except Exception as e:
        os.close(fd)
        os.unlink(temp_path)
        raise e


def restore_sqlite(backup_path: Path, target_path: Path) -> bool:
    """Restore a SQLite database from backup.

    Args:
        backup_path: Path to the backup file
        target_path: Path where database should be restored

    Returns:
        True if restore succeeded, False otherwise
    """
    try:
        is_compressed = backup_path.name.endswith(".gz")

        if is_compressed:
            with gzip.open(backup_path, "rb") as f_in:
                with open(target_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(backup_path, target_path)

        logger.info(f"SQLite database restored to: {target_path}")
        return True
    except Exception as e:
        logger.error(f"SQLite restore failed: {e}")
        return False


def main() -> int:
    """Main entry point for the restore script."""
    parser = argparse.ArgumentParser(
        description="Restore Kimberly database from backup"
    )
    parser.add_argument("backup_file", type=str, help="Path to backup file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    parser.add_argument(
        "--sqlite-target",
        type=str,
        help="Target path for SQLite restore (for .db backups)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing database without confirmation",
    )

    args = parser.parse_args()

    backup_path = Path(args.backup_file)

    # Validate backup file
    if not validate_backup_file(backup_path):
        return 1

    is_sqlite = backup_path.name.endswith((".db", ".db.gz"))
    is_compressed = backup_path.name.endswith(".gz")

    if args.dry_run:
        db_type = "SQLite" if is_sqlite else "PostgreSQL"
        logger.info(f"[dry-run] Would restore {db_type} from: {backup_path}")
        return 0

    if is_sqlite:
        # SQLite restore
        if not args.sqlite_target:
            logger.error("--sqlite-target required for SQLite restore")
            return 1

        target_path = Path(args.sqlite_target)
        if target_path.exists() and not args.force:
            logger.error(
                f"Target exists: {target_path}. Use --force to overwrite."
            )
            return 1

        if not restore_sqlite(backup_path, target_path):
            return 1
    else:
        # PostgreSQL restore
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not set.")
            return 1

        db_config = parse_database_url(db_url)

        # Handle compressed backups
        restore_path = backup_path
        temp_file = None

        if is_compressed:
            logger.info("Decompressing backup file...")
            try:
                restore_path = decompress_backup(backup_path)
                temp_file = restore_path
            except Exception as e:
                logger.error(f"Failed to decompress backup: {e}")
                return 1

        try:
            if not run_psql_restore(db_config, restore_path):
                return 1
        finally:
            # Clean up temporary file
            if temp_file and temp_file.exists():
                temp_file.unlink()

    logger.info("Restore completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
