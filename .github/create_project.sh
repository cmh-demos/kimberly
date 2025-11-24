#!/usr/bin/env bash
set -euo pipefail

# Repository helper: create a GitHub Project board and default columns using the GitHub CLI (gh).
# This script is a helper to run locally where 'gh' is installed and authenticated.
# It intentionally prints the commands it would run for review and then executes them if --yes is passed.

NAME="Kimberly — Work"
REPO=""
DRY_RUN=true

usage(){
  cat <<EOF
Usage: $0 --repo owner/repo [--name "Project Name"] [--yes]
Examples:
  $0 --repo cmh-demos/kimberly
  $0 --repo cmh-demos/kimberly --name "Kimberly — Work" --yes
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; shift 2;;
    --repo) REPO="$2"; shift 2;;
    --yes) DRY_RUN=false; shift 1;;
    --help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

if [[ -z "$REPO" ]]; then
  echo "ERROR: --repo owner/repo is required" >&2
  usage
  exit 2
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI not found. Install: https://cli.github.com/ and authenticate (gh auth login)" >&2
  exit 3
fi

echo "Preparing to create GitHub Project: $NAME (repo: $REPO)"

commands=(
  "# Create a repo-level project (classic projects API)"
  "gh api -X POST /repos/$REPO/projects -f name=\"$NAME\" -f body=\"Primary project board for work tracking\" -H 'Accept: application/vnd.github.inertia-preview+json'"
  "# Create columns (Backlog, Selected for Development, In progress, Review / QA, Done)"
  "# Use the returned project id from the previous command and substitute into the following commands"
  "gh api -H 'Accept: application/vnd.github.inertia-preview+json' -X POST /repos/$REPO/projects/<PROJECT_ID>/columns -f name='Backlog'"
  "gh api -H 'Accept: application/vnd.github.inertia-preview+json' -X POST /repos/$REPO/projects/<PROJECT_ID>/columns -f name='Selected for Development'"
  "gh api -H 'Accept: application/vnd.github.inertia-preview+json' -X POST /repos/$REPO/projects/<PROJECT_ID>/columns -f name='In progress'"
  "gh api -H 'Accept: application/vnd.github.inertia-preview+json' -X POST /repos/$REPO/projects/<PROJECT_ID>/columns -f name='Review / QA'"
  "gh api -H 'Accept: application/vnd.github.inertia-preview+json' -X POST /repos/$REPO/projects/<PROJECT_ID>/columns -f name='Done'"
  "# Alternative: use gh project create (projects v2) if available: gh project create \"$NAME\" --repo $REPO --body 'Primary project board'"
)

echo "The script will print the commands it would run:\n"
for c in "${commands[@]}"; do
  echo "$c"
done

if [[ "$DRY_RUN" = true ]]; then
  echo "\nDRY-RUN: nothing was executed. Re-run with --yes to actually make changes." >&2
  exit 0
fi

echo "Executing creation commands..."

# Execute: create project
project_json=$(gh api -X POST /repos/$REPO/projects -f name="$NAME" -f body="Primary project board for work tracking" -H 'Accept: application/vnd.github.inertia-preview+json')
project_id=$(echo "$project_json" | sed -n 's/.*"id":\s*\([0-9]*\).*/\1/p' || true)
if [[ -z "$project_id" ]]; then
  echo "Failed to create project or couldn't detect project id; output follows:"
  echo "$project_json"
  exit 4
fi

for col in "Backlog" "Selected for Development" "In progress" "Review / QA" "Done"; do
  echo "Creating column: $col"
  gh api -H 'Accept: application/vnd.github.inertia-preview+json' -X POST /repos/$REPO/projects/$project_id/columns -f name="$col"
done

echo "Project created with id: $project_id; remember to add automation rules, labels, and populate the board from issues/PRs." 
