#!/usr/bin/env python3
"""Safe append helper for misc/copilot_tracking.json

Usage: python scripts/append_log.py --note "my note" --tokens-estimate 10 [--start START] [--end END]

The script will:
 - produce ISO-8601 timestamps with microsecond precision
 - compute processing_time_microseconds from start/end
 - validate the new entry against misc/copilot_tracking.schema.json (if jsonschema available)
 - verify the file hash before appending
 - append the new entry and write a stable formatted JSON array back
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "misc" / "copilot_tracking.json"
SCHEMA_PATH = ROOT / "misc" / "copilot_tracking.schema.json"


def now_iso():
    # include microseconds and timezone offset with colon
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def iso_to_dt(s: str) -> datetime:
    # Python's fromisoformat supports offsets like -08:00 and fractional seconds
    return datetime.fromisoformat(s)


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n")


def validate_entry(entry):
    try:
        import jsonschema
    except Exception:
        print(
            "jsonschema not installed; skipping schema validation (install with pip install jsonschema)"
        )
        return True

    schema = load_json(SCHEMA_PATH)
    # single-item schema validation - items schema applies
    item_schema = schema.get("items", {})
    jsonschema.validate(instance=entry, schema=item_schema)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--note", required=True, help="Short note describing the work")
    parser.add_argument("--tokens-estimate", type=int, required=True)
    parser.add_argument("--tokens-used", type=int, default=None)
    parser.add_argument("--tool-calls", type=int, default=0)
    parser.add_argument("--files-accessed", type=int, default=0)
    parser.add_argument("--terminal-commands", type=int, default=0)
    parser.add_argument(
        "--start", default=None, help="ISO timestamp for start (defaults to now)"
    )
    parser.add_argument(
        "--end", default=None, help="ISO timestamp for end (defaults to now)"
    )
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    start = args.start or now_iso()
    end = args.end or now_iso()

    try:
        dt_start = iso_to_dt(start)
        dt_end = iso_to_dt(end)
    except Exception as e:
        print(f"failed to parse timestamps: {e}")
        sys.exit(2)

    delta_us = int((dt_end - dt_start).total_seconds() * 1_000_000)
    if delta_us < 0:
        print("end < start — processing_time_microseconds would be negative")
        sys.exit(2)

    # full-file read & hash (pre-append)
    if not LOG_PATH.exists():
        print(f"log path not found: {LOG_PATH}")
        sys.exit(2)

    before_hash = file_hash(LOG_PATH)
    data = load_json(LOG_PATH)

    entry = {
        "request_start_time": dt_start.isoformat(timespec="microseconds"),
        "request_end_time": dt_end.isoformat(timespec="microseconds"),
        "processing_time_microseconds": delta_us,
        "tokens_used": args.tokens_used,
        "tokens_used_estimate": args.tokens_estimate,
        "tool_calls_count": args.tool_calls,
        "files_accessed_count": args.files_accessed,
        "terminal_commands_count": args.terminal_commands,
        "pre_append_file_sha256": before_hash,
        "note": args.note,
    }

    # At this point we already loaded the file and before_hash

    # validate entry
    try:
        validate_entry(entry)
    except Exception as e:
        print(f"Schema validation failed: {e}")
        sys.exit(3)

    # re-check file hash (verify_file_hash_before_append)
    after_read_hash = file_hash(LOG_PATH)
    if after_read_hash != before_hash:
        print("file changed while preparing to append; aborting")
        sys.exit(4)

    data.append(entry)

    if args.dry_run:
        print(json.dumps(entry, indent=2))
        print("DRY RUN - not writing to file")
        return

    write_json(LOG_PATH, data)
    print("appended new log entry — remember to commit the change")


if __name__ == "__main__":
    main()
