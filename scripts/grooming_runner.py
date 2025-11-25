#!/usr/bin/env python3
"""Grooming runner for Copilot triage system.

Behavior:
- Reads `copilot_triage_rules.yml` for configuration
- Queries GitHub for open issues
- For issues with 'needs-info': assigns to copilot-bot and removes 'Triaged'
- For issues with 'Triaged' and 'Backlog': moves to Backlog column on project board
- Logs actions to triage_log.json

This is a manual stage, activated on demand.
"""

from __future__ import annotations
import os
import sys
import json
import yaml
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Load rules
def load_rules(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
            return data
    except FileNotFoundError:
        return None

def github_search_issues(
    owner: str, repo: str, token: str | None, per_page: int = 100
) -> List[dict]:
    query = f'repo:{owner}/{repo} is:issue is:open'
    url = "https://api.github.com/search/issues"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "q": query,
        "per_page": per_page,
    }

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", [])

def github_get_issue(
    owner: str, repo: str, issue_number: int, token: str | None
) -> dict | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(url, headers=headers)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()

def assign_issue(
    owner: str, repo: str, issue_number: int, assignee: str, token: str
) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.patch(url, headers=headers, json={"assignees": [assignee]})
    resp.raise_for_status()

def remove_label(
    owner: str, repo: str, issue_number: int, label: str, token: str
) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels/{label}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.delete(url, headers=headers)
    resp.raise_for_status()

def get_project_columns(
    owner: str, repo: str, project_id: int, token: str
) -> List[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/projects/{project_id}/columns"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_column_cards(column_id: int, token: str) -> List[dict]:
    url = f"https://api.github.com/projects/columns/{column_id}/cards"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def find_card_for_issue(cards: List[dict], issue_url: str) -> dict | None:
    for card in cards:
        if card.get("content_url") == issue_url:
            return card
    return None

def move_card(card_id: int, to_column_id: int, token: str) -> None:
    url = f"https://api.github.com/projects/columns/{to_column_id}/moves"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    data = {"card_id": card_id, "position": "top"}
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()

def move_issue_to_backlog_column(
    owner: str,
    repo: str,
    issue_number: int,
    issue_url: str,
    project_id: int,
    backlog_column_id: int,
    token: str,
) -> None:
    # Get all columns for the project
    columns = get_project_columns(owner, repo, project_id, token)

    # Find the card for this issue across all columns
    card = None
    for col in columns:
        cards = get_column_cards(col["id"], token)
        card = find_card_for_issue(cards, issue_url)
        if card:
            break

    if card:
        # Move existing card to Backlog column
        move_card(card["id"], backlog_column_id, token)

def main() -> int:
    rules_path = os.environ.get("RULES_PATH", "copilot_triage_rules.yml")
    rules = load_rules(rules_path)
    if rules is None:
        print(f"ERROR: rules file not found at {rules_path}", file=sys.stderr)
        return 1

    # Get project management config
    project_management = rules.get("project_management", {})
    project_enabled = project_management.get("enabled", False)
    project_id = project_management.get("project_id")
    backlog_column_id = project_management.get("columns", {}).get("Backlog")

    dry_run_env = os.environ.get("DRY_RUN", "").lower()
    dry_run = dry_run_env in ("1", "true", "yes")

    gh_repo = os.environ.get("GITHUB_REPOSITORY")
    gh_token = os.environ.get("GITHUB_TOKEN")

    if not gh_repo:
        print("No GITHUB_REPOSITORY environment — running in local simulation mode")
        return 0

    owner, repo = gh_repo.split("/")
    if not gh_token:
        print("No GITHUB_TOKEN present — will operate in dry-run only", file=sys.stderr)
        dry_run = True

    print(f"Dry-run: {dry_run}")

    items = []
    try:
        items = github_search_issues(owner, repo, gh_token)
    except Exception as e:
        print("Failed to query GitHub issues:", e, file=sys.stderr)
        return 1

    if not items:
        print('No open issues found.')
        return 0

    print(f"Found {len(items)} open issues")

    for issue in items:
        number = issue.get("number")
        title = issue.get("title")
        labels = [lbl.get("name") for lbl in issue.get("labels", []) if isinstance(lbl, dict)]
        issue_url = issue.get("url")

        print(f"---\nIssue #{number}: {title}")
        print(f"Labels: {labels}")

        actions: List[str] = []
        changed_fields: List[str] = []

        audit_entry: Dict[str, Any] = {
            "issue_number": number,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_type": "grooming",
            "dry_run": dry_run,
            "execution_branch": os.environ.get("GITHUB_REF", "unknown"),
            "changed_fields": [],
            "notes": "",
        }

        # Check for needs-info variants (assume "needs-info" for now)
        needs_info_variants = ["needs-info"]  # Can expand if needed
        if any(variant in labels for variant in needs_info_variants):
            actions.append("assign to copilot-bot and remove Triaged")
            audit_entry["notes"] += "needs-info detected; "
            if not dry_run:
                try:
                    assign_issue(owner, repo, number, "copilot-bot", gh_token)
                    if "Triaged" in labels:
                        remove_label(owner, repo, number, "Triaged", gh_token)
                        changed_fields.append("removed Triaged")
                    changed_fields.append("assigned to copilot-bot")
                except Exception as e:
                    print(f"Failed to update issue #{number}: {e}", file=sys.stderr)
            else:
                changed_fields.append("would assign to copilot-bot and remove Triaged")

        # Check for Triaged and Backlog
        if "Triaged" in labels and "Backlog" in labels and project_enabled and backlog_column_id:
            actions.append("move to Backlog column on board")
            audit_entry["notes"] += "Triaged+Backlog detected; "
            if not dry_run:
                try:
                    move_issue_to_backlog_column(owner, repo, number, issue_url, project_id, backlog_column_id, gh_token)
                    changed_fields.append("moved to Backlog column")
                except Exception as e:
                    print(f"Failed to move issue #{number} on board: {e}", file=sys.stderr)
            else:
                changed_fields.append("would move to Backlog column")

        audit_entry["changed_fields"] = changed_fields

        if dry_run:
            print("[dry-run] " + ", ".join(actions))
        else:
            print("[live] " + ", ".join(actions))

        # Record audit in triage_log.json
        log_entry = audit_entry
        log_file = "triage_log.json"
        try:
            logs = []
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as fh:
                    try:
                        logs = json.load(fh)
                    except Exception:
                        logs = []
            logs.append(log_entry)
            with open(log_file, "w", encoding="utf-8") as fh:
                json.dump(logs, fh, indent=2)
            print(f"Appended grooming audit to {log_file}")
        except Exception as e:
            print("Failed to append to grooming log:", e, file=sys.stderr)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())