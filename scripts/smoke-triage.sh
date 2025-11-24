#!/usr/bin/env bash
set -euo pipefail
echo "Smoke run: executing triage_runner.py in dry-run mode"
export DRY_RUN=true
python3 scripts/triage_runner.py
echo "Smoke-run finished"
