#!/usr/bin/env python3
"""JSON data import script for Kimberly.

This script imports application data from JSON format exports created by
export_data.py. It supports importing memory items, triage logs, and
validates data before import.

Usage:
    python scripts/import_data.py IMPORT_FILE [--type TYPE] [--dry-run]

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (optional, for DB imports)

Example:
    # Import all data from export file
    python scripts/import_data.py exports/export_20250101_120000.json

    # Import only triage logs
    python scripts/import_data.py backup.json --type triage

    # Dry run to validate without importing
    python scripts/import_data.py backup.json --dry-run

Security:
    - Validates JSON structure before import
    - Sanitizes data to prevent injection
    - Logs all import operations for audit trail
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Data types available for import
IMPORT_TYPES = ["all", "memory", "triage", "config"]

# Maximum allowed file size (50 MB)
MAX_IMPORT_SIZE = 50 * 1024 * 1024


def validate_import_file(import_path: Path) -> bool:
    """Validate import file exists and is within size limits.

    Args:
        import_path: Path to the import file

    Returns:
        True if valid, False otherwise
    """
    if not import_path.exists():
        logger.error(f"Import file not found: {import_path}")
        return False

    if import_path.suffix != ".json":
        logger.error(f"Invalid file type. Expected .json: {import_path}")
        return False

    file_size = import_path.stat().st_size
    if file_size > MAX_IMPORT_SIZE:
        logger.error(
            f"Import file too large: {file_size} bytes "
            f"(max: {MAX_IMPORT_SIZE})"
        )
        return False

    return True


def validate_export_structure(data: Dict[str, Any]) -> bool:
    """Validate the structure of an export package.

    Args:
        data: Parsed JSON data

    Returns:
        True if structure is valid, False otherwise
    """
    if not isinstance(data, dict):
        logger.error("Import file must contain a JSON object")
        return False

    if "export_metadata" not in data:
        logger.warning("Missing export_metadata - may be legacy format")

    return True


def sanitize_string(value: str, max_length: int = 10000) -> str:
    """Sanitize a string value for safe database insertion.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)

    # Truncate to max length
    if len(value) > max_length:
        value = value[:max_length]

    # Remove null bytes
    value = value.replace("\x00", "")

    return value


def sanitize_import_data(data: Any) -> Any:
    """Sanitize data for safe import.

    Args:
        data: Data to sanitize

    Returns:
        Sanitized data
    """
    if isinstance(data, dict):
        return {
            sanitize_string(str(k), 255): sanitize_import_data(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_import_data(item) for item in data]
    elif isinstance(data, str):
        return sanitize_string(data)
    else:
        return data


def import_triage_logs(
    logs: List[Dict[str, Any]], target_path: Path, merge: bool = True
) -> int:
    """Import triage log entries.

    Args:
        logs: List of triage log entries to import
        target_path: Path to the triage log JSON file
        merge: Whether to merge with existing logs

    Returns:
        Number of entries imported
    """
    existing_logs = []

    if merge and target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                existing_logs = json.load(f)
                if not isinstance(existing_logs, list):
                    existing_logs = [existing_logs]
        except Exception as e:
            logger.warning(f"Could not read existing logs: {e}")
            existing_logs = []

    # Sanitize incoming logs
    sanitized_logs = sanitize_import_data(logs)

    # Merge logs (avoid duplicates based on issue_number + timestamp)
    existing_keys = set()
    for log in existing_logs:
        key = (log.get("issue_number"), log.get("timestamp"))
        existing_keys.add(key)

    new_count = 0
    for log in sanitized_logs:
        key = (log.get("issue_number"), log.get("timestamp"))
        if key not in existing_keys:
            existing_logs.append(log)
            existing_keys.add(key)
            new_count += 1

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(existing_logs, f, indent=2)
        logger.info(f"Imported {new_count} new triage log entries")
        return new_count
    except Exception as e:
        logger.error(f"Failed to write triage logs: {e}")
        return 0


def import_memory_items_to_db(items: List[Dict[str, Any]]) -> int:
    """Import memory items to PostgreSQL database.

    Args:
        items: List of memory item dictionaries

    Returns:
        Number of items imported
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not set - cannot import to database")
        return 0

    try:
        import psycopg2

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_items (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                type TEXT,
                content TEXT,
                metadata JSONB,
                score REAL DEFAULT 0.0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_seen_at TIMESTAMPTZ
            )
        """)

        imported = 0
        for item in items:
            sanitized = sanitize_import_data(item)
            try:
                cursor.execute("""
                    INSERT INTO memory_items
                        (id, user_id, type, content, metadata, score,
                         created_at, last_seen_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        score = EXCLUDED.score,
                        last_seen_at = EXCLUDED.last_seen_at
                """, (
                    sanitized.get("id"),
                    sanitized.get("user_id"),
                    sanitized.get("type"),
                    sanitized.get("content"),
                    json.dumps(sanitized.get("metadata", {})),
                    sanitized.get("score", 0.0),
                    sanitized.get("created_at"),
                    sanitized.get("last_seen_at"),
                ))
                imported += 1
            except Exception as e:
                logger.warning(f"Failed to import item {sanitized.get('id')}: {e}")

        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Imported {imported} memory items to database")
        return imported

    except ImportError:
        logger.error("psycopg2 not installed - cannot import to database")
        return 0
    except Exception as e:
        logger.error(f"Database import failed: {e}")
        return 0


def import_memory_items_to_sqlite(
    items: List[Dict[str, Any]], db_path: Path
) -> int:
    """Import memory items to SQLite database.

    Args:
        items: List of memory item dictionaries
        db_path: Path to SQLite database file

    Returns:
        Number of items imported
    """
    try:
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_items (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                type TEXT,
                content TEXT,
                metadata TEXT,
                score REAL DEFAULT 0.0,
                created_at TEXT,
                last_seen_at TEXT
            )
        """)

        imported = 0
        for item in items:
            sanitized = sanitize_import_data(item)
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO memory_items
                        (id, user_id, type, content, metadata, score,
                         created_at, last_seen_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sanitized.get("id"),
                    sanitized.get("user_id"),
                    sanitized.get("type"),
                    sanitized.get("content"),
                    json.dumps(sanitized.get("metadata", {})),
                    sanitized.get("score", 0.0),
                    sanitized.get("created_at"),
                    sanitized.get("last_seen_at"),
                ))
                imported += 1
            except Exception as e:
                logger.warning(f"Failed to import item {sanitized.get('id')}: {e}")

        conn.commit()
        conn.close()
        logger.info(f"Imported {imported} memory items to SQLite")
        return imported

    except Exception as e:
        logger.error(f"SQLite import failed: {e}")
        return 0


def import_config_files(
    configs: Dict[str, Any], target_dir: Path, overwrite: bool = False
) -> int:
    """Import configuration files.

    Args:
        configs: Dictionary of config contents keyed by filename
        target_dir: Directory to write config files
        overwrite: Whether to overwrite existing files

    Returns:
        Number of files imported
    """
    import yaml

    imported = 0

    for filename, content in configs.items():
        target_path = target_dir / filename

        if target_path.exists() and not overwrite:
            logger.warning(f"Skipping existing config: {filename}")
            continue

        try:
            sanitized = sanitize_import_data(content)
            with open(target_path, "w", encoding="utf-8") as f:
                if filename.endswith((".yml", ".yaml")):
                    yaml.dump(sanitized, f, default_flow_style=False)
                elif filename.endswith(".json"):
                    json.dump(sanitized, f, indent=2)
                else:
                    f.write(str(sanitized))

            logger.info(f"Imported config: {filename}")
            imported += 1
        except Exception as e:
            logger.error(f"Failed to import config {filename}: {e}")

    return imported


def main() -> int:
    """Main entry point for the import script."""
    parser = argparse.ArgumentParser(
        description="Import Kimberly data from JSON export"
    )
    parser.add_argument("import_file", type=str, help="Path to import file")
    parser.add_argument(
        "--type",
        "-t",
        type=str,
        choices=IMPORT_TYPES,
        default="all",
        help="Type of data to import",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and show what would be imported",
    )
    parser.add_argument(
        "--sqlite",
        type=str,
        help="Path to SQLite database for memory import",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        default=True,
        help="Merge with existing data (default: true)",
    )
    parser.add_argument(
        "--overwrite-configs",
        action="store_true",
        help="Overwrite existing configuration files",
    )

    args = parser.parse_args()

    import_path = Path(args.import_file)

    # Validate import file
    if not validate_import_file(import_path):
        return 1

    # Parse import file
    try:
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in import file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Failed to read import file: {e}")
        return 1

    # Validate structure
    if not validate_export_structure(data):
        return 1

    import_all = args.type == "all"

    # Calculate stats
    stats = {
        "triage_logs": len(data.get("triage_logs", [])),
        "configurations": len(data.get("configurations", {})),
        "memory_items": len(data.get("memory_items", [])),
    }

    logger.info(f"Import file contains: {stats}")

    if args.dry_run:
        logger.info("[dry-run] Validation passed - no changes made")
        return 0

    # Perform imports
    repo_root = Path(__file__).parent.parent
    imported_counts = {}

    if import_all or args.type == "triage":
        triage_logs = data.get("triage_logs", [])
        if triage_logs:
            target = repo_root / "triage_log.json"
            imported_counts["triage"] = import_triage_logs(
                triage_logs, target, args.merge
            )

    if import_all or args.type == "memory":
        memory_items = data.get("memory_items", [])
        if memory_items:
            if args.sqlite:
                imported_counts["memory"] = import_memory_items_to_sqlite(
                    memory_items, Path(args.sqlite)
                )
            else:
                imported_counts["memory"] = import_memory_items_to_db(
                    memory_items
                )

    if import_all or args.type == "config":
        configs = data.get("configurations", {})
        if configs:
            imported_counts["config"] = import_config_files(
                configs, repo_root, args.overwrite_configs
            )

    logger.info(f"Import completed: {imported_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
