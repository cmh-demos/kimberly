#!/usr/bin/env python3
"""
Database backup script for Kimberly.

Performs a logical backup of the PostgreSQL database with optional
compression and encryption.

Usage:
  python scripts/backup_db.py --output /path/to/backup
  python scripts/backup_db.py --output /path/to/backup --compress
"""

import argparse
import gzip
import hashlib
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
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
        "name": os.getenv("DB_NAME", "kimberly"),
        "user": os.getenv("DB_USER", "kimberly"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


def check_pg_dump():
    """Check if pg_dump is available."""
    if shutil.which("pg_dump") is None:
        logger.error("pg_dump not found. Please install PostgreSQL client.")
        return False
    return True


def create_backup(output_path, compress=False, dry_run=False):
    """
    Create a database backup.

    Args:
      output_path: Path to write the backup file.
      compress: Whether to gzip the backup.
      dry_run: If True, simulate backup without executing.

    Returns:
      dict with backup metadata or None on failure.
    """
    config = get_db_config()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"kimberly_backup_{timestamp}.sql"

    if compress:
        backup_filename += ".gz"

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    backup_file = output_dir / backup_filename

    logger.info(f"Starting backup to {backup_file}")

    if dry_run:
        logger.info("[DRY RUN] Would create backup with pg_dump")
        return {
            "file": str(backup_file),
            "timestamp": timestamp,
            "compressed": compress,
            "dry_run": True,
        }

    if not check_pg_dump():
        return None

    env = os.environ.copy()
    if config["password"]:
        env["PGPASSWORD"] = config["password"]

    pg_dump_cmd = [
        "pg_dump",
        "-h",
        config["host"],
        "-p",
        config["port"],
        "-U",
        config["user"],
        "-d",
        config["name"],
        "--format=plain",
        "--no-owner",
        "--no-acl",
    ]

    try:
        if compress:
            with gzip.open(backup_file, "wt", encoding="utf-8") as f:
                result = subprocess.run(
                    pg_dump_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=True,
                    text=True,
                )
        else:
            with open(backup_file, "w", encoding="utf-8") as f:
                result = subprocess.run(
                    pg_dump_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=True,
                    text=True,
                )

        file_size = backup_file.stat().st_size
        checksum = calculate_checksum(backup_file)

        logger.info(f"Backup completed: {backup_file}")
        logger.info(f"Size: {file_size} bytes, Checksum: {checksum}")

        return {
            "file": str(backup_file),
            "timestamp": timestamp,
            "compressed": compress,
            "size_bytes": file_size,
            "checksum_sha256": checksum,
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump failed: {e.stderr}")
        return None
    except OSError as e:
        logger.error(f"File operation failed: {e}")
        return None


def calculate_checksum(file_path):
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def cleanup_old_backups(backup_dir, retention_days=7):
    """
    Remove backups older than retention period.

    Args:
      backup_dir: Directory containing backups.
      retention_days: Number of days to retain backups.

    Returns:
      List of deleted files.
    """
    backup_path = Path(backup_dir)
    deleted = []

    if not backup_path.exists():
        return deleted

    cutoff = datetime.utcnow().timestamp() - (retention_days * 86400)

    for file in backup_path.glob("kimberly_backup_*.sql*"):
        if file.stat().st_mtime < cutoff:
            logger.info(f"Removing old backup: {file}")
            file.unlink()
            deleted.append(str(file))

    return deleted


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create PostgreSQL database backup for Kimberly"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="./backups",
        help="Output directory for backup file (default: ./backups)",
    )
    parser.add_argument(
        "--compress", "-c", action="store_true", help="Compress backup with gzip"
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Simulate backup without executing",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old backups after creating new one",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=7,
        help="Days to retain backups when cleanup is enabled (default: 7)",
    )

    args = parser.parse_args()

    result = create_backup(
        output_path=args.output, compress=args.compress, dry_run=args.dry_run
    )

    if result is None:
        logger.error("Backup failed")
        sys.exit(1)

    if args.cleanup and not args.dry_run:
        deleted = cleanup_old_backups(args.output, args.retention_days)
        if deleted:
            logger.info(f"Cleaned up {len(deleted)} old backups")

    logger.info("Backup completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
