#!/usr/bin/env bash
set -euo pipefail
# Lightweight wrapper for running markdownlint-cli2 locally.
# Behavior:
#  - If npx is available and works, use it (local Node)
#  - Otherwise fallback to a Node 20 Docker image (node:20)
#  - Default target when no args: **/*.md

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$#" -eq 0 ]; then
  set -- "**/*.md"
fi

echo "Running markdownlint-cli2 on: $*"

if command -v npx >/dev/null 2>&1; then
  echo "Attempting local npx markdownlint-cli2..."
  if npx --yes markdownlint-cli2 "$@"; then
    exit 0
  else
    echo "Local npx ran but failed — check output above for details" >&2
    exit 1
  fi
fi

echo "ERROR: markdownlint-cli2 (via npx) is not available on this machine."
echo "Please install Node >=20 (recommended) and re-run the command."
echo "Examples:"
echo "  # using nvm"
echo "  nvm install 20 && nvm use 20"
echo "  # or using Volta"
echo "  volta install node@20"
echo "Once Node >=20 is available, run: npx markdownlint-cli2 '**/*.md'"
exit 2
exit 2
