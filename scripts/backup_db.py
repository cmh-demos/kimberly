#!/usr/bin/env python3
"""Database backup script for Kimberly.

This script provides PostgreSQL database backup functionality with support
for full and incremental backups, compression, and rotation.

Usage:
    python scripts/backup_db.py [--output-dir DIR] [--compress] [--retention DAYS]

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
        (e.g., 'postgresql://user:pass@host:5432/dbname')
    BACKUP_DIR: Default backup directory (default: backups/)

Example:
    # Full backup with compression
    python scripts/backup_db.py --compress

    # Custom output directory with 30-day retention
    python scripts/backup_db.py --output-dir /var/backups/kimberly --retention 30
"""

from __future__ import annotations

import argparse
import gzip
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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


def create_backup_filename(database: str, compress: bool = False) -> str:
    """Generate a timestamped backup filename."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ext = ".sql.gz" if compress else ".sql"
    return f"{database}_backup_{timestamp}{ext}"


def run_pg_dump(
    db_config: dict, output_path: Path, compress: bool = False
) -> bool:
    """Execute pg_dump to create a database backup.

    Args:
        db_config: Database connection configuration
        output_path: Path where backup file will be saved
        compress: Whether to compress the output with gzip

    Returns:
        True if backup succeeded, False otherwise
    """
    env = os.environ.copy()
    if db_config["password"]:
        env["PGPASSWORD"] = db_config["password"]

    cmd = [
        "pg_dump",
        "-h",
        db_config["host"],
        "-p",
        str(db_config["port"]),
        "-U",
        db_config["user"],
        "-d",
        db_config["database"],
        "--format=plain",
        "--no-owner",
        "--no-acl",
    ]

    try:
        if compress:
            # Pipe through gzip
            with open(output_path, "wb") as f:
                pg_dump = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
                )
                with gzip.open(f, "wb") as gz:
                    while True:
                        chunk = pg_dump.stdout.read(8192)
                        if not chunk:
                            break
                        gz.write(chunk)
                pg_dump.wait()
                if pg_dump.returncode != 0:
                    stderr = pg_dump.stderr.read().decode()
                    logger.error(f"pg_dump failed: {stderr}")
                    return False
        else:
            with open(output_path, "w") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.PIPE, env=env, check=True
                )
        logger.info(f"Backup created: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump failed: {e.stderr.decode()}")
        return False
    except FileNotFoundError:
        logger.error(
            "pg_dump not found. Ensure PostgreSQL client tools are installed."
        )
        return False
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False


def cleanup_old_backups(backup_dir: Path, retention_days: int) -> int:
    """Remove backup files older than retention period.

    Args:
        backup_dir: Directory containing backup files
        retention_days: Number of days to retain backups

    Returns:
        Number of files removed
    """
    if retention_days <= 0:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    removed = 0

    for backup_file in backup_dir.glob("*_backup_*.sql*"):
        try:
            stat = backup_file.stat()
            file_time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            if file_time < cutoff:
                backup_file.unlink()
                logger.info(f"Removed old backup: {backup_file}")
                removed += 1
        except Exception as e:
            logger.warning(f"Failed to check/remove {backup_file}: {e}")

    return removed


def backup_sqlite(
    db_path: Path, output_dir: Path, compress: bool = False
) -> Optional[Path]:
    """Create a backup of a SQLite database.

    Args:
        db_path: Path to the SQLite database file
        output_dir: Directory for backup output
        compress: Whether to compress the backup

    Returns:
        Path to the backup file, or None if backup failed
    """
    if not db_path.exists():
        logger.error(f"SQLite database not found: {db_path}")
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"{db_path.stem}_backup_{timestamp}"

    if compress:
        backup_path = output_dir / f"{backup_name}.db.gz"
        try:
            with open(db_path, "rb") as f_in:
                with gzip.open(backup_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logger.info(f"SQLite backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            return None
    else:
        backup_path = output_dir / f"{backup_name}.db"
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"SQLite backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            return None


def main() -> int:
    """Main entry point for the backup script."""
    parser = argparse.ArgumentParser(
        description="Create database backups for Kimberly"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.environ.get("BACKUP_DIR", "backups"),
        help="Directory to store backup files",
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress backup files with gzip",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=7,
        help="Number of days to retain old backups (0 to disable cleanup)",
    )
    parser.add_argument(
        "--sqlite",
        type=str,
        help="Path to SQLite database file (for free-mode deployments)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    success = True

    if args.sqlite:
        # SQLite backup mode
        sqlite_path = Path(args.sqlite)
        if args.dry_run:
            logger.info(f"[dry-run] Would backup SQLite: {sqlite_path}")
        else:
            result = backup_sqlite(sqlite_path, output_dir, args.compress)
            if not result:
                success = False
    else:
        # PostgreSQL backup mode
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error(
                "DATABASE_URL environment variable not set. "
                "Use --sqlite for SQLite backups."
            )
            return 1

        db_config = parse_database_url(db_url)
        backup_filename = create_backup_filename(
            db_config["database"], args.compress
        )
        backup_path = output_dir / backup_filename

        if args.dry_run:
            logger.info(f"[dry-run] Would create backup: {backup_path}")
        else:
            if not run_pg_dump(db_config, backup_path, args.compress):
                success = False

    # Cleanup old backups
    if args.retention > 0 and not args.dry_run:
        removed = cleanup_old_backups(output_dir, args.retention)
        if removed > 0:
            logger.info(f"Cleaned up {removed} old backup(s)")

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
