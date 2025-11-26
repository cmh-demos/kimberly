#!/usr/bin/env python3
"""JSON data export script for Kimberly.

This script exports application data to JSON format for backup, migration,
or data portability purposes. It supports exporting memory items, triage
logs, and configuration files.

Usage:
    python scripts/export_data.py [--output FILE] [--type TYPE] [--pretty]

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (optional, for DB exports)
    EXPORT_DIR: Default export directory (default: exports/)

Example:
    # Export all data types
    python scripts/export_data.py --output backup.json

    # Export only triage logs
    python scripts/export_data.py --type triage --output triage_export.json

    # Export memory items with pretty printing
    python scripts/export_data.py --type memory --pretty
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Data types available for export
EXPORT_TYPES = ["all", "memory", "triage", "config"]


def sanitize_for_export(data: Any) -> Any:
    """Sanitize data for safe export by removing sensitive fields.

    Args:
        data: Data to sanitize

    Returns:
        Sanitized data safe for export
    """
    if isinstance(data, dict):
        sanitized = {}
        # Fields that should be redacted
        sensitive_keys = {
            "password",
            "secret",
            "token",
            "api_key",
            "apikey",
            "credential",
            "private_key",
        }
        for key, value in data.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_for_export(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_for_export(item) for item in data]
    else:
        return data


def export_triage_logs(log_path: Path) -> List[Dict[str, Any]]:
    """Export triage log entries.

    Args:
        log_path: Path to the triage log JSON file

    Returns:
        List of triage log entries
    """
    if not log_path.exists():
        logger.warning(f"Triage log not found: {log_path}")
        return []

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            logs = json.load(f)
            if not isinstance(logs, list):
                logs = [logs]
            return sanitize_for_export(logs)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse triage log: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to read triage log: {e}")
        return []


def export_config_files(config_paths: List[Path]) -> Dict[str, Any]:
    """Export configuration files.

    Args:
        config_paths: List of paths to configuration files

    Returns:
        Dictionary of config file contents keyed by filename
    """
    import yaml

    configs = {}

    for path in config_paths:
        if not path.exists():
            logger.warning(f"Config file not found: {path}")
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                if path.suffix in (".yml", ".yaml"):
                    content = yaml.safe_load(f)
                elif path.suffix == ".json":
                    content = json.load(f)
                else:
                    content = f.read()

                configs[path.name] = sanitize_for_export(content)
        except Exception as e:
            logger.error(f"Failed to read config {path}: {e}")

    return configs


def export_memory_items_from_db() -> List[Dict[str, Any]]:
    """Export memory items from PostgreSQL database.

    Returns:
        List of memory item dictionaries
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.warning(
            "DATABASE_URL not set - skipping database memory export"
        )
        return []

    try:
        # Try to import psycopg2 for PostgreSQL
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query memory items table if it exists
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'memory_items'
        """)

        if not cursor.fetchone():
            logger.info("memory_items table not found - skipping")
            cursor.close()
            conn.close()
            return []

        cursor.execute("""
            SELECT id, user_id, type, content, metadata, score,
                   created_at, last_seen_at
            FROM memory_items
            ORDER BY created_at DESC
        """)

        items = []
        for row in cursor.fetchall():
            item = dict(row)
            # Convert datetime objects to ISO format strings
            for key in ["created_at", "last_seen_at"]:
                if item.get(key):
                    item[key] = item[key].isoformat()
            items.append(sanitize_for_export(item))

        cursor.close()
        conn.close()
        logger.info(f"Exported {len(items)} memory items from database")
        return items

    except ImportError:
        logger.warning("psycopg2 not installed - skipping database export")
        return []
    except Exception as e:
        logger.error(f"Failed to export from database: {e}")
        return []


def export_memory_items_from_sqlite(db_path: Path) -> List[Dict[str, Any]]:
    """Export memory items from SQLite database.

    Args:
        db_path: Path to SQLite database file

    Returns:
        List of memory item dictionaries
    """
    if not db_path.exists():
        logger.warning(f"SQLite database not found: {db_path}")
        return []

    try:
        import sqlite3

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if memory_items table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='memory_items'
        """)

        if not cursor.fetchone():
            logger.info("memory_items table not found in SQLite - skipping")
            conn.close()
            return []

        cursor.execute("""
            SELECT * FROM memory_items
            ORDER BY created_at DESC
        """)

        items = [sanitize_for_export(dict(row)) for row in cursor.fetchall()]
        conn.close()
        logger.info(f"Exported {len(items)} memory items from SQLite")
        return items

    except Exception as e:
        logger.error(f"Failed to export from SQLite: {e}")
        return []


def create_export_package(
    export_types: List[str],
    triage_log_path: Path,
    config_paths: List[Path],
    sqlite_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Create a complete export package.

    Args:
        export_types: List of data types to export
        triage_log_path: Path to triage log file
        config_paths: List of config file paths
        sqlite_path: Optional path to SQLite database

    Returns:
        Dictionary containing all exported data
    """
    export_all = "all" in export_types

    package = {
        "export_metadata": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "types_included": export_types,
        }
    }

    if export_all or "triage" in export_types:
        package["triage_logs"] = export_triage_logs(triage_log_path)

    if export_all or "config" in export_types:
        package["configurations"] = export_config_files(config_paths)

    if export_all or "memory" in export_types:
        if sqlite_path:
            package["memory_items"] = export_memory_items_from_sqlite(
                sqlite_path
            )
        else:
            package["memory_items"] = export_memory_items_from_db()

    return package


def main() -> int:
    """Main entry point for the export script."""
    parser = argparse.ArgumentParser(
        description="Export Kimberly data to JSON format"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (default: exports/export_TIMESTAMP.json)",
    )
    parser.add_argument(
        "--type",
        "-t",
        type=str,
        choices=EXPORT_TYPES,
        default="all",
        help="Type of data to export",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Format JSON output with indentation",
    )
    parser.add_argument(
        "--sqlite",
        type=str,
        help="Path to SQLite database (for free-mode deployments)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without writing",
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        export_dir = Path(os.environ.get("EXPORT_DIR", "exports"))
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = export_dir / f"export_{timestamp}.json"

    # Paths to standard files
    repo_root = Path(__file__).parent.parent
    triage_log_path = repo_root / "triage_log.json"
    config_paths = [
        repo_root / "copilot_triage_rules.yml",
        repo_root / "copilot_grooming_rules.yml",
    ]

    sqlite_path = Path(args.sqlite) if args.sqlite else None

    # Create export package
    export_types = [args.type] if args.type != "all" else ["all"]
    package = create_export_package(
        export_types, triage_log_path, config_paths, sqlite_path
    )

    # Calculate stats
    stats = {
        "triage_logs": len(package.get("triage_logs", [])),
        "configurations": len(package.get("configurations", {})),
        "memory_items": len(package.get("memory_items", [])),
    }

    if args.dry_run:
        logger.info(f"[dry-run] Would export to: {output_path}")
        logger.info(f"[dry-run] Export stats: {stats}")
        return 0

    # Write export file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            indent = 2 if args.pretty else None
            json.dump(package, f, indent=indent, ensure_ascii=False)

        file_size = output_path.stat().st_size
        logger.info(f"Export saved to: {output_path} ({file_size} bytes)")
        logger.info(f"Export stats: {stats}")
        return 0

    except Exception as e:
        logger.error(f"Failed to write export: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
