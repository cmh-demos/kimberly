#!/usr/bin/env python
"""Validate copilot_tracking.json against its JSON schema."""
import json
import sys

from jsonschema import ValidationError, validate


def main():
    """Validate copilot_tracking.json against its JSON schema."""
    # Load schema
    with open("misc/copilot_tracking.schema.json", encoding="utf-8") as f:
        schema = json.load(f)

    # Load data (handle empty file)
    with open("misc/copilot_tracking.json", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            data = []
        else:
            data = json.loads(content)

    # Validate
    try:
        validate(instance=data, schema=schema)
        print("copilot_tracking.json is valid")
        return 0
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
