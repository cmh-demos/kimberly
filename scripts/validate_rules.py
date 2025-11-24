#!/usr/bin/env python3
"""
Validate the copilot_triage_rules.yml file against its embedded JSON schema.
"""
import argparse
import json
import sys

import jsonschema
import yaml


def main():
    parser = argparse.ArgumentParser(
        description="Validate YAML file against embedded JSON schema"
    )
    parser.add_argument("rules_file", help="Path to the YAML rules file")
    args = parser.parse_args()

    # Load the rules file
    try:
        with open(args.rules_file, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        sys.exit(1)

    # Extract the embedded schema
    schema = data.get("json_schema")
    if not schema:
        print("No 'json_schema' found in rules file")
        sys.exit(1)

    # Validate using jsonschema
    try:
        jsonschema.validate(instance=data, schema=schema)
        print("Schema validation passed")
    except jsonschema.ValidationError as e:
        print(f"Schema validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
