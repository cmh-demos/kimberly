#!/usr/bin/env python3
"""Grooming runner for Copilot triage system.

This script automates post-triage grooming of GitHub issues:
- Assigns 'needs-info' issues to copilot-bot and removes 'Triaged' label.
- Moves 'Triaged' + 'Backlog' issues to the Backlog column on GitHub Projects.
- Handles stale issues (e.g., closes old 'needs-info' issues).

Configuration is loaded from copilot_grooming_rules.yml and copilot_triage_rules.yml.

Security: Validates GitHub tokens and sanitizes audit logs for PII.
Resilience: Retries API calls with exponential backoff and rate limit monitoring.
Activation: Can be run manually, scheduled, or via webhooks (configurable).

Usage:
    python scripts/grooming_runner.py

Environment Variables:
    GITHUB_REPOSITORY: Required (e.g., 'owner/repo')
    GITHUB_TOKEN: Optional; enables live changes (else dry-run)
    DRY_RUN: Force dry-run mode
    GROOMING_RULES_PATH: Path to grooming rules YAML (default: copilot_grooming_rules.yml)
    TRIAGE_RULES_PATH: Path to triage rules YAML (default: copilot_triage_rules.yml)

This is a manual stage, activated on demand or via automation.
"""

from __future__ import annotations
import os
import sys
import json
import yaml
import requests
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_github_token(token: str | None) -> bool:
    """Validate GitHub token format (supports multiple token types)."""
    if not token:
        return False
    # Support classic, fine-grained PATs, and other formats
    valid_prefixes = ("ghp_", "ghs_", "ghu_", "gho_", "github_pat_", "gh_", "github_")
    return (
        any(token.startswith(prefix) for prefix in valid_prefixes) or len(token) == 40
    )  # Classic token length


def handle_rate_limit(resp: requests.Response) -> None:
    """Handle GitHub API rate limiting by sleeping if necessary."""
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
    reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
    if remaining < 5:
        sleep_time = max(reset_time - int(time.time()), 60)  # At least 60s
        logger.warning(f"Rate limit low ({remaining} remaining). Sleeping {sleep_time}s.")
        time.sleep(sleep_time)


def sanitize_log_entry(entry: dict) -> dict:
    """Remove or redact sensitive information from log entries."""
    sanitized = entry.copy()
    # Redact any potential PII in notes or titles (basic check)
    if "notes" in sanitized and any(
        word in sanitized["notes"].lower() for word in ["email", "password", "token"]
    ):
        sanitized["notes"] = "[REDACTED: Potential PII]"
    return sanitized


def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator to retry a function on failure with exponential backoff."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (
                    requests.ConnectionError,
                    requests.Timeout,
                    requests.HTTPError,
                ) as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_factor**attempt
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed.")
                        raise last_exception
            raise last_exception

        return wrapper

    return decorator


@retry_on_failure()
def close_issue(owner: str, repo: str, issue_number: int, token: str) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    data = {"state": "closed"}
    resp = requests.patch(url, headers=headers, json=data)
    resp.raise_for_status()

    # Handle rate limit
    handle_rate_limit(resp)


@retry_on_failure()
def post_comment(
    owner: str, repo: str, issue_number: int, comment: str, token: str
) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    data = {"body": comment}
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()

    # Handle rate limit
    handle_rate_limit(resp)


def load_rules(path: str) -> dict | None:
    """Load YAML rules from file path. Returns None if file not found."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
            return data
    except FileNotFoundError:
        return None


@retry_on_failure()
def github_search_issues(
    owner: str, repo: str, token: str | None, per_page: int = 100, max_pages: int = 10
) -> List[dict]:
    """Search for open issues in the repo, with pagination support."""
    query = f"repo:{owner}/{repo} is:issue is:open"
    url = "https://api.github.com/search/issues"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    all_items = []
    page = 1
    while True:
        params = {
            "q": query,
            "per_page": per_page,
            "page": page,
        }

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()

        # Handle rate limit
        handle_rate_limit(resp)

        data = resp.json()
        items = data.get("items", [])
        all_items.extend(items)

        total_count = data.get("total_count", 0)
        if len(all_items) >= total_count or len(items) < per_page or page >= max_pages:
            break
        page += 1

    return all_items


@retry_on_failure()
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

    # Check rate limit
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
    if remaining < 5:
        print(
            f"Warning: Low rate limit remaining ({remaining}). Consider pausing.",
            file=sys.stderr,
        )

    return resp.json()


@retry_on_failure()
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

    # Check rate limit
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
    if remaining < 5:
        print(
            f"Warning: Low rate limit remaining ({remaining}). Consider pausing.",
            file=sys.stderr,
        )


@retry_on_failure()
@retry_on_failure()
def add_label(
    owner: str, repo: str, issue_number: int, label: str, token: str
) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    data = [label]
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()

@retry_on_failure()
def add_label(
    owner: str, repo: str, issue_number: int, label: str, token: str
) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    data = [label]
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()

    # Handle rate limit
    handle_rate_limit(resp)


@retry_on_failure()
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

    # Handle rate limit
    handle_rate_limit(resp)


@retry_on_failure()
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

    # Check rate limit
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
    if remaining < 5:
        print(
            f"Warning: Low rate limit remaining ({remaining}). Consider pausing.",
            file=sys.stderr,
        )

    return resp.json()


@retry_on_failure()
def get_column_cards(column_id: int, token: str) -> List[dict]:
    url = f"https://api.github.com/projects/columns/{column_id}/cards"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    # Check rate limit
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
    if remaining < 5:
        print(
            f"Warning: Low rate limit remaining ({remaining}). Consider pausing.",
            file=sys.stderr,
        )

    return resp.json()


def find_card_for_issue(cards: List[dict], issue_url: str) -> dict | None:
    for card in cards:
        if card.get("content_url") == issue_url:
            return card
    return None


@retry_on_failure()
def move_card(card_id: int, to_column_id: int, token: str) -> None:
    url = f"https://api.github.com/projects/columns/{to_column_id}/moves"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    data = {"card_id": card_id, "position": "top"}
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()

    # Handle rate limit
    handle_rate_limit(resp)


def move_issue_to_column(
    owner: str,
    repo: str,
    issue_number: int,
    issue_url: str,
    project_id: int,
    target_column_id: int,
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
        # Move existing card to target column
        move_card(card["id"], target_column_id, token)


def process_issue(
    issue: dict,
    owner: str,
    repo: str,
    gh_token: str,
    dry_run: bool,
    needs_info_variants: list,
    assignee_for_needs_info: str,
    remove_triaged_on_needs_info: bool,
    project_enabled: bool,
    project_id: int,
    backlog_column_id: int,
    move_to_backlog_if_triaged_and_backlog: bool,
    stale_enabled: bool,
    stale_labels: list,
    stale_days: int,
    stale_action: str,
    stale_comment: str,
    audit_event_type: str,
    workflow_enabled: bool,
    transitions: list,
    project_columns: dict,
) -> Dict[str, Any]:
    number = issue.get("number")
    title = issue.get("title")
    labels = [
        lbl.get("name") for lbl in issue.get("labels", []) if isinstance(lbl, dict)
    ]
    issue_url = issue.get("url")

    print(f"---\nIssue #{number}: {title}")
    print(f"Labels: {labels}")

    # Skip if issue is closed
    if issue.get("state") == "closed":
        print("Issue is closed, skipping.")
        return audit_entry

    actions: List[str] = []
    changed_fields: List[str] = []

    audit_entry: Dict[str, Any] = {
        "issue_number": number,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_type": audit_event_type,
        "dry_run": dry_run,
        "execution_branch": os.environ.get("GITHUB_REF", "unknown"),
        "changed_fields": [],
        "notes": "",
    }

    # Check for stale issues
    if stale_enabled:
        updated_at_str = issue.get("updated_at")
        if updated_at_str:
            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if (now - updated_at).days > stale_days and any(
                label in labels for label in stale_labels
            ):
                actions.append(f"{stale_action} stale issue")
                audit_entry[
                    "notes"
                ] += f"stale detected ({(now - updated_at).days} days); "
                if not dry_run:
                    try:
                        if stale_action == "close":
                            post_comment(owner, repo, number, stale_comment, gh_token)
                            close_issue(owner, repo, number, gh_token)
                            changed_fields.append("closed as stale")
                        elif stale_action == "comment":
                            post_comment(owner, repo, number, stale_comment, gh_token)
                            changed_fields.append("commented as stale")
                        elif stale_action == "label":
                            # Add a label, e.g., "stale"
                            add_label(owner, repo, number, "stale", gh_token)
                            changed_fields.append("labeled as stale")
                    except Exception as e:
                        logger.error(f"Failed to handle stale issue #{number}: {e}")
                else:
                    changed_fields.append(f"would {stale_action} as stale")

    # Check for needs-info variants
    if any(variant in labels for variant in needs_info_variants):
        actions.append("assign to copilot-bot and remove Triaged")
        audit_entry["notes"] += "needs-info detected; "
        if not dry_run:
            try:
                assign_issue(owner, repo, number, assignee_for_needs_info, gh_token)
                if remove_triaged_on_needs_info and "Triaged" in labels:
                    remove_label(owner, repo, number, "Triaged", gh_token)
                    changed_fields.append("removed Triaged")
                changed_fields.append(f"assigned to {assignee_for_needs_info}")
            except Exception as e:
                logger.error(f"Failed to update issue #{number}: {e}")
        else:
            changed_fields.append(
                f"would assign to {assignee_for_needs_info} and remove Triaged"
            )

    # Check for Triaged and Backlog
    if (
        "Triaged" in labels
        and "Backlog" in labels
        and project_enabled
        and backlog_column_id
        and move_to_backlog_if_triaged_and_backlog
    ):
        actions.append("move to Backlog column on board")
        audit_entry["notes"] += "Triaged+Backlog detected; "
        if not dry_run:
            try:
                move_issue_to_column(
                    owner,
                    repo,
                    number,
                    issue_url,
                    project_id,
                    backlog_column_id,
                    gh_token,
                )
                changed_fields.append("moved to Backlog column")
            except Exception as e:
                logger.error(f"Failed to move issue #{number} on board: {e}")
        else:
            changed_fields.append("would move to Backlog column")

    # Check for workflow transitions
    if workflow_enabled and project_enabled and project_id:
        assignees = issue.get("assignees", [])
        assignee_logins = [a.get("login") for a in assignees if a]
        for transition in transitions:
            condition = transition.get("condition", {})
            required_labels = condition.get("labels", [])
            required_assignee = condition.get("assignee")
            not_labels = condition.get("not_labels", [])
            to_column = transition.get("to_column")
            from_column = transition.get("from_column")

            # Check if all required labels are present
            has_required_labels = all(label in labels for label in required_labels)
            # Check if assignee matches
            has_assignee = required_assignee is None or required_assignee in assignee_logins
            # Check if none of the not_labels are present
            has_no_not_labels = not any(label in labels for label in not_labels)

            if has_required_labels and has_assignee and has_no_not_labels:
                target_column_id = project_columns.get(
                    to_column.lower().replace(" ", "_")
                )
                if target_column_id:
                    actions.append(f"move to {to_column} column")
                    audit_entry["notes"] += f"workflow transition to {to_column}; "
                    if not dry_run:
                        try:
                            move_issue_to_column(
                                owner,
                                repo,
                                number,
                                issue_url,
                                project_id,
                                target_column_id,
                                gh_token,
                            )
                            changed_fields.append(f"moved to {to_column} column")
                        except Exception as e:
                            logger.error(
                                f"Failed to move issue #{number} to {to_column}: {e}"
                            )
                    else:
                        changed_fields.append(f"would move to {to_column} column")
                break  # Only apply the first matching transition

    audit_entry["event_type"] = audit_event_type
    audit_entry["changed_fields"] = changed_fields

    if dry_run:
        print("[dry-run] " + ", ".join(actions))
    else:
        print("[live] " + ", ".join(actions))

    return audit_entry


def main() -> int:
    triage_rules_path = os.environ.get("TRIAGE_RULES_PATH", "copilot_triage_rules.yml")
    grooming_rules_path = os.environ.get(
        "GROOMING_RULES_PATH", "copilot_grooming_rules.yml"
    )
    triage_rules = load_rules(triage_rules_path)
    grooming_rules = load_rules(grooming_rules_path)
    if triage_rules is None:
        print(
            f"ERROR: triage rules file not found at {triage_rules_path}",
            file=sys.stderr,
        )
        return 1
    if grooming_rules is None:
        print(
            f"ERROR: grooming rules file not found at {grooming_rules_path}",
            file=sys.stderr,
        )
        return 1

    # Get project management config from triage rules
    project_management = triage_rules.get("project_management", {})
    project_enabled = project_management.get("enabled", False)
    project_id = project_management.get("project_id")
    backlog_column_id = project_management.get("columns", {}).get("Backlog")

    # Get grooming settings
    grooming_settings = grooming_rules.get("grooming_bot_settings", {})
    needs_info_variants = grooming_settings.get("needs_info_variants", ["needs-info"])
    assignee_for_needs_info = grooming_settings.get(
        "assignee_for_needs_info", "copilot-bot"
    )
    remove_triaged_on_needs_info = grooming_settings.get(
        "remove_triaged_on_needs_info", True
    )
    move_to_backlog_if_triaged_and_backlog = grooming_settings.get(
        "move_to_backlog_if_triaged_and_backlog", True
    )
    audit_event_type = grooming_settings.get("audit_event_type", "grooming")
    stale_handling = grooming_settings.get("stale_issue_handling", {})
    stale_enabled = stale_handling.get("enabled", False)
    stale_labels = stale_handling.get("labels_to_check", [])
    stale_days = stale_handling.get("days_threshold", 14)
    stale_action = stale_handling.get("action", "close")
    stale_comment = stale_handling.get("close_comment", "Closing stale issue.")

    # Get workflow automation settings
    workflow_automation = grooming_settings.get("workflow_automation", {})
    workflow_enabled = workflow_automation.get("enabled", False)
    transitions = workflow_automation.get("transitions", [])

    # Get project columns
    project_columns = grooming_settings.get("project_columns", {})
    ready_column_id = project_columns.get("ready")
    in_progress_column_id = project_columns.get("in_progress")
    in_review_column_id = project_columns.get("in_review")
    done_column_id = project_columns.get("done")

    gh_token = os.environ.get("GITHUB_TOKEN")

    # Validate project and column IDs if token provided
    if gh_token and project_enabled and project_id:
        try:
            columns = get_project_columns(owner, repo, project_id, gh_token)
            valid_column_ids = {col["id"] for col in columns}
            for col_name, col_id in project_columns.items():
                if col_id and col_id not in valid_column_ids:
                    logger.warning(f"Invalid column ID for {col_name}: {col_id}")
        except Exception as e:
            logger.error(f"Failed to validate project columns: {e}")

    dry_run_env = os.environ.get("DRY_RUN", "").lower()
    dry_run = dry_run_env in ("1", "true", "yes")

    gh_repo = os.environ.get("GITHUB_REPOSITORY")
    gh_token = os.environ.get("GITHUB_TOKEN")

    # Validate token for security
    if gh_token and not validate_github_token(gh_token):
        logger.error("Invalid GitHub token format. Ensure it's a valid GitHub token.")
        return 1

    if not gh_repo:
        print("No GITHUB_REPOSITORY environment — running in local simulation mode")
        return 0

    owner, repo = gh_repo.split("/")

    # Validate project and column IDs if token provided
    if gh_token and project_enabled and project_id:
        try:
            columns = get_project_columns(owner, repo, project_id, gh_token)
            valid_column_ids = {col["id"] for col in columns}
            for col_name, col_id in project_columns.items():
                if col_id and col_id not in valid_column_ids:
                    logger.warning(f"Invalid column ID for {col_name}: {col_id}")
        except Exception as e:
            logger.error(f"Failed to validate project columns: {e}")

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
        print("No open issues found.")
        return 0

    print(f"Found {len(items)} open issues")

    audit_entries = []
    for issue in items:
        audit_entry = process_issue(
            issue,
            owner,
            repo,
            gh_token,
            dry_run,
            needs_info_variants,
            assignee_for_needs_info,
            remove_triaged_on_needs_info,
            project_enabled,
            project_id,
            backlog_column_id,
            move_to_backlog_if_triaged_and_backlog,
            stale_enabled,
            stale_labels,
            stale_days,
            stale_action,
            stale_comment,
            audit_event_type,
            workflow_enabled,
            transitions,
            project_columns,
        )
        audit_entries.append(audit_entry)

    # Record audits in triage_log.json
    log_file = "triage_log.json"
    try:
        import tempfile
        logs = []
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as fh:
                try:
                    logs = json.load(fh)
                except Exception:
                    logs = []
        # Sanitize entries for compliance
        sanitized_entries = [sanitize_log_entry(entry) for entry in audit_entries]
        logs.extend(sanitized_entries)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json") as tmp:
            json.dump(logs, tmp, indent=2)
            tmp.flush()
            os.replace(tmp.name, log_file)
        print(f"Appended {len(audit_entries)} grooming audits to {log_file}")
    except Exception as e:
        logger.error(f"Failed to append to grooming log: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
