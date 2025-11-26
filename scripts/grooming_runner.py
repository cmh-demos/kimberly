#!/usr/bin/env python3
"""Grooming runner for Copilot triage system.

This script automates post-triage grooming of GitHub issues:
- Assigns 'needs-info' issues to copilot-bot and removes 'Triaged' label.
- Moves 'Triaged' + 'Backlog' issues to the Backlog column on GitHub
  Projects.
- Handles stale issues (e.g., closes old 'needs-info' issues).

Configuration is loaded from copilot_grooming_rules.yml and
copilot_triage_rules.yml.

Security: Validates GitHub tokens and sanitizes audit logs for PII.
Resilience: Retries API calls with exponential backoff and rate limit
monitoring.
Activation: Can be run manually, scheduled, or via webhooks
(configurable).

Usage:
    python scripts/grooming_runner.py

Environment Variables:
    GITHUB_REPOSITORY: Required (e.g., 'owner/repo')
    GITHUB_TOKEN: Optional; enables live changes (else dry-run)
    DRY_RUN: Force dry-run mode
    GROOMING_RULES_PATH: Path to grooming rules YAML
        (default: copilot_grooming_rules.yml)
    TRIAGE_RULES_PATH: Path to triage rules YAML
        (default: copilot_triage_rules.yml)

This is a manual stage, activated on demand or via automation.

Note about assignments in GitHub Actions:
    The default Actions-provided GITHUB_TOKEN is a runtime token and
    often cannot be used to assign Copilot coding agents (they require a
    user token PAT or a user-to-server token with GraphQL access). When
    running in Actions you should provide a PAT in secrets and use that
    instead of the default GITHUB_TOKEN in order to assign Copilot.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests
import yaml

from scripts.utils import retry_on_failure

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Log rotation configuration
MAX_LOG_ENTRIES = 1000  # Maximum entries before rotation
LOG_ARCHIVE_DIR = "logs/archive"

# Per-run Copilot assignment counter (enforced across stages)
copilot_assigns_this_run: int = 0
# Configurable defaults (can be overridden from rules loaded in main)
MAX_COPILOT_ASSIGN_PER_RUN = 1
GROOMABLE_STATUS_LABELS = ["Backlog", "In progress"]


def validate_github_token(token: str | None) -> bool:
    """Validate GitHub token format (supports multiple token types)."""
    if not token:
        return False
    # Support classic, fine-grained PATs, and other formats
    valid_prefixes = (
        "ghp_",
        "ghs_",
        "ghu_",
        "gho_",
        "github_pat_",
        "gh_",
        "github_",
    )
    return (
        any(token.startswith(prefix) for prefix in valid_prefixes)
        or len(token) == 40
    )  # Classic token length


def handle_rate_limit(resp: requests.Response) -> None:
    """Handle GitHub API rate limiting by sleeping if necessary."""
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
    reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
    if remaining < 5:
        sleep_time = max(reset_time - int(time.time()), 60)  # At least 60s
        logger.warning(
            f"Rate limit low ({remaining} remaining). "
            f"Sleeping {sleep_time}s."
        )
        time.sleep(sleep_time)


def sanitize_log_entry(entry: dict) -> dict:
    """Remove or redact sensitive information from log entries."""
    sanitized = entry.copy()
    # Redact any potential PII in notes or titles (basic check)
    if "notes" in sanitized and any(
        word in sanitized["notes"].lower()
        for word in ["email", "password", "token"]
    ):
        sanitized["notes"] = "[REDACTED: Potential PII]"
    return sanitized


@retry_on_failure(logger=logger)
def close_issue(owner: str, repo: str, issue_number: int, token: str) -> None:
    base = f"https://api.github.com/repos/{owner}/{repo}"
    url = f"{base}/issues/{issue_number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    data = {"state": "closed"}
    resp = requests.patch(url, headers=headers, json=data)
    resp.raise_for_status()

    # Handle rate limit
    handle_rate_limit(resp)


@retry_on_failure(logger=logger)
def post_comment(
    owner: str, repo: str, issue_number: int, comment: str, token: str
) -> None:
    url = (
        "https://api.github.com/repos/"
        f"{owner}/{repo}/issues/{issue_number}/comments"
    )
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


@retry_on_failure(logger=logger)
def github_search_issues(
    owner: str,
    repo: str,
    token: str | None,
    per_page: int = 100,
    max_pages: int = 10,
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
        if (
            len(all_items) >= total_count
            or len(items) < per_page
            or page >= max_pages
        ):
            break
        page += 1

    return all_items


@retry_on_failure(logger=logger)
def github_get_issue(
    owner: str, repo: str, issue_number: int, token: str | None
) -> dict | None:
    base = f"https://api.github.com/repos/{owner}/{repo}"
    url = f"{base}/issues/{issue_number}"
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
            f"Warning: Low rate limit remaining ({remaining}). "
            f"Consider pausing.",
            file=sys.stderr,
        )

    return resp.json()


@retry_on_failure(logger=logger)
def assign_issue(
    owner: str, repo: str, issue_number: int, assignee: str, token: str
) -> None:
    # For Copilot coding agents we MUST use the grooming PAT set in
    # the GROOMING_ACCESS_KEY secret. Do not fall back to the runtime
    # GITHUB_TOKEN or any other token for assigning Copilot agents.
    is_copilot_agent = "copilot" in (assignee or "").lower()
    if is_copilot_agent:
        used_token = os.environ.get("GROOMING_ACCESS_KEY")
        if not used_token:
            # No PAT available — skip Copilot assignment to avoid
            # attempting with an unsuitable token.
            logger.warning(
                "No GROOMING_ACCESS_KEY present — cannot assign Copilot "
                "agent for issue %s; skipping assign",
                issue_number,
            )
            return
    else:
        # Non-Copilot assignees may use the provided token.
        used_token = token

    base = f"https://api.github.com/repos/{owner}/{repo}"
    url = f"{base}/issues/{issue_number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {used_token}",
    }
    resp = requests.patch(url, headers=headers, json={"assignees": [assignee]})
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        # Common case: 422 Unprocessable Entity when the requested assignee
        # cannot be added via the REST API (e.g., Copilot coding agent).
        if resp.status_code == 422 and used_token:
            # If we are running inside GitHub Actions with the default
            # GITHUB_TOKEN, this token is a runtime token with limited
            # permissions and can't be used to assign Copilot agents via
            # GraphQL. Avoid retry storms and fail loudly but gracefully
            # by logging and skipping assignment instead of raising.
            # If we're running in Actions and the token actually being
            # used is the runtime GITHUB_TOKEN then we know agent
            # assignments will not work — skip instead of retrying
            # graphQL. If GROOMING_ACCESS_KEY is present we will use it
            # and attempt the GraphQL fallback.
            if (
                os.environ.get("GITHUB_ACTIONS") == "true"
                and os.environ.get("GITHUB_TOKEN")
                and used_token == os.environ.get("GITHUB_TOKEN")
                and not os.environ.get("GROOMING_ACCESS_KEY")
            ):
                logger.warning(
                    "Running in GitHub Actions with GITHUB_TOKEN: cannot "
                    "assign Copilot agents; skipping assign for issue %s",
                    issue_number,
                )
                return
            logger.warning(
                "REST assignment failed with 422 - attempting GraphQL "
                "assign fallback for assignee '%s'",
                assignee,
            )
            # Try GraphQL fallback to assign agents like Copilot. If that
            # fails, re-raise the original exception so callers know.
            try:
                # Use the same token used for the REST call for the
                # GraphQL fallback path. For Copilot assignments this
                # will be the grooming PAT.
                _assign_issue_via_graphql(
                    owner, repo, issue_number, assignee, used_token
                )
                return
            except Exception:
                logger.exception("GraphQL assign fallback failed")
                raise
        raise

    # Check rate limit
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
    if remaining < 5:
        print(
            f"Warning: Low rate limit remaining ({remaining}). "
            f"Consider pausing.",
            file=sys.stderr,
        )


@retry_on_failure(logger=logger)
def github_graphql_request(
    token: str, query: str, variables: dict | None = None
) -> dict:
    """Send a GraphQL query to the GitHub API and return the parsed json.

    Raises HTTPError on non-OK responses or GraphQL errors.
    """
    url = "https://api.github.com/graphql"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    body = resp.json()
    if body.get("errors"):
        raise requests.HTTPError(
            "GraphQL API returned errors: %s" % body.get("errors")
        )
    return body.get("data", {})


@retry_on_failure(logger=logger)
def _find_actor_id_for_assignable(
    owner: str, repo: str, token: str, candidate: str
) -> str | None:
    """Return a GraphQL node id for a suggested actor able to be assigned.

    The query uses suggestedActors(capabilities: [CAN_BE_ASSIGNED]) and
    attempts to find a matching login for the candidate. If none match,
    will try reasonable fallbacks (substring / first copilot-like actor).
    """
    # Use inline fragments for concrete actor types when requesting id.
    # Some GraphQL schemas do not expose `id` directly on the Actor
    # interface; requesting `id` inside the concrete fragments avoids
    # "Field 'id' doesn't exist on type 'Actor'" errors from the
    # GraphQL API.
    query = (
        "query($owner:String!, $repo:String!) {"
        " repository(owner: $owner, name: $repo) {"
        " suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 100) {"
        " nodes { login __typename"
        " ... on User { id }"
        " ... on Bot { id }"
        " ... on Mannequin { id }"
        " ... on Organization { id }"
        " } } } }"
    )
    variables = {"owner": owner, "repo": repo}
    data = github_graphql_request(token, query, variables)
    nodes = (
        data.get("repository", {}).get("suggestedActors", {}).get("nodes") or []
    )

    # Try exact login match
    for n in nodes:
        if n.get("login") == candidate:
            return n.get("id")

    # Try lowercased substring match
    candidate_low = candidate.lower()
    for n in nodes:
        login = n.get("login", "")
        if candidate_low in login.lower():
            return n.get("id")

    # Final fallback: find a copilot-like actor
    for n in nodes:
        login = n.get("login", "")
        if "copilot" in login.lower():
            return n.get("id")

    return None


@retry_on_failure(logger=logger)
def _get_issue_node_id(
    owner: str, repo: str, issue_number: int, token: str
) -> str:
    query = (
        "query($owner:String!, $repo:String!, $num:Int!) {"
        " repository(owner: $owner, name: $repo) {"
        " issue(number: $num) { id } } }"
    )
    variables = {"owner": owner, "repo": repo, "num": issue_number}
    data = github_graphql_request(token, query, variables)
    issue_id = data.get("repository", {}).get("issue", {}).get("id")
    if not issue_id:
        raise RuntimeError("Unable to fetch issue node id via GraphQL")
    return issue_id


@retry_on_failure(logger=logger)
def _assign_issue_via_graphql(
    owner: str, repo: str, issue_number: int, assignee: str, token: str
) -> None:
    """Assign an existing issue to an actor (eg. Copilot) via GraphQL.

    This implements the flow described in GitHub docs:
    1) Find the assignable actor ID using suggestedActors
    2) Fetch the issue node ID
    3) Call replaceActorsForAssignable to assign by actor id
    """
    actor_id = _find_actor_id_for_assignable(owner, repo, token, assignee)
    if not actor_id:
        raise RuntimeError("No assignable actor found for '%s'" % assignee)

    issue_id = _get_issue_node_id(owner, repo, issue_number, token)

    # The GraphQL API expects a non-null list of non-null IDs for
    # actorIds — declare $actorIds as [ID!]! to match the API and avoid
    # nullability mismatch errors.
    mutation = (
        "mutation($assignableId: ID!, $actorIds: [ID!]!) {"
        " replaceActorsForAssignable(input: {assignableId: $assignableId, "
        "actorIds: $actorIds}) { assignable { ... on Issue { id } } } }"
    )
    variables = {"assignableId": issue_id, "actorIds": [actor_id]}
    github_graphql_request(token, mutation, variables)


@retry_on_failure(logger=logger)
def get_most_recent_copilot_event(
    owner: str, repo: str, issue_number: int, token: str
) -> dict | None:
    """Return the most recent Copilot-related timeline event for an issue.

    Looks for timeline entries that reference "copilot" (case-insensitive)
    in textual fields and classifies the most recent matching entry as
    'start', 'error', 'finished', or 'other'. Also returns the timestamp of
    the most recent Copilot error if present.
    """
    url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/issues/{issue_number}/timeline"
    )
    headers = {
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    nodes: list = []
    page = 1
    while True:
        params = {"per_page": 100, "page": page}
        resp = requests.get(url, headers=headers, params=params)
        # If timeline not available (403/404), return None gracefully
        if resp.status_code in (403, 404):
            return None
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            nodes.extend(data)
        else:
            # Some endpoints may return dict wrapper
            items = data.get("items") or []
            nodes.extend(items)

        if len(nodes) < 1 or len(nodes) < (page * 100):
            break
        page += 1

    copilot_nodes = []
    last_error_time = None
    for n in nodes:
        # Collect textual fields that may contain Copilot traces
        text_fields = []
        for f in ("body", "event", "message", "title"):
            v = n.get(f)
            if isinstance(v, str):
                text_fields.append(v)
        actor = n.get("actor") or {}
        if isinstance(actor, dict):
            login = actor.get("login")
            if isinstance(login, str):
                text_fields.append(login)

        joined = " ".join(x for x in text_fields if x).lower()
        if "copilot" in joined:
            # classify
            created = n.get("created_at") or n.get("updated_at")
            try:
                created_dt = (
                    datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if created
                    else None
                )
            except Exception:
                created_dt = None

            node_type = "other"
            if "error" in joined:
                node_type = "error"
                if created_dt and (
                    not last_error_time or created_dt > last_error_time
                ):
                    last_error_time = created_dt
            elif (
                "finish" in joined
                or "finished" in joined
                or "completed" in joined
            ):
                node_type = "finished"
            elif "start" in joined or "started" in joined:
                node_type = "start"

            copilot_nodes.append(
                {
                    "type": node_type,
                    "text": joined,
                    "created_at": created_dt,
                    "raw": n,
                }
            )

    if not copilot_nodes:
        return None

    # sort by created_at if available else leave order
    copilot_nodes_sorted = sorted(
        copilot_nodes, key=lambda x: x.get("created_at") or datetime.min
    )
    last = copilot_nodes_sorted[-1]
    return {
        "type": last.get("type"),
        "text": last.get("text"),
        "created_at": last.get("created_at"),
        "last_error_time": last_error_time,
    }


@retry_on_failure(logger=logger)
def add_label(
    owner: str, repo: str, issue_number: int, label: str, token: str
) -> None:
    url = (
        "https://api.github.com/repos/"
        f"{owner}/{repo}/issues/{issue_number}/labels"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    data = [label]
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()

    # Handle rate limit
    handle_rate_limit(resp)


@retry_on_failure(logger=logger)
def remove_label(
    owner: str, repo: str, issue_number: int, label: str, token: str
) -> None:
    url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues/"
        f"{issue_number}/labels/{label}"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.delete(url, headers=headers)
    resp.raise_for_status()

    # Handle rate limit
    handle_rate_limit(resp)


@retry_on_failure(logger=logger)
def get_project_columns(
    owner: str, repo: str, project_id: int, token: str
) -> List[dict]:
    url = (
        "https://api.github.com/repos/"
        f"{owner}/{repo}/projects/{project_id}/columns"
    )
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
            f"Warning: Low rate limit remaining ({remaining}). "
            f"Consider pausing.",
            file=sys.stderr,
        )

    return resp.json()


@retry_on_failure(logger=logger)
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
            f"Warning: Low rate limit remaining ({remaining}). "
            f"Consider pausing.",
            file=sys.stderr,
        )

    return resp.json()


def find_card_for_issue(cards: List[dict], issue_url: str) -> dict | None:
    for card in cards:
        if card.get("content_url") == issue_url:
            return card
    return None


@retry_on_failure(logger=logger)
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
    assignee_for_needs_work: str,
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
    *args,
    **kwargs,
) -> Dict[str, Any]:
    global copilot_assigns_this_run
    number = issue.get("number")
    title = issue.get("title")
    labels = [
        lbl.get("name")
        for lbl in issue.get("labels", [])
        if isinstance(lbl, dict)
    ]
    issue_url = issue.get("url")

    print(f"---\nIssue #{number}: {title}")
    print(f"Labels: {labels}")

    actions: List[str] = []
    changed_fields: List[str] = []

    now_utc = datetime.now(timezone.utc)
    audit_entry: Dict[str, Any] = {
        "issue_number": number,
        "timestamp": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_type": audit_event_type,
        "dry_run": dry_run,
        "execution_branch": os.environ.get("GITHUB_REF", "unknown"),
        "changed_fields": [],
        "notes": "",
    }

    # Skip if issue is closed
    if issue.get("state") == "closed":
        print("Issue is closed, skipping.")
        return audit_entry

    # Status gate: only process issues in configured groomable statuses
    labels_lower = [lbl.lower() for lbl in labels if isinstance(lbl, str)]
    groomable_lower = [s.lower() for s in GROOMABLE_STATUS_LABELS]
    status_allowed = any(lbl in groomable_lower for lbl in labels_lower)
    # Project-card fallback when labels not present or ambiguous
    if not status_allowed and project_enabled and project_id:
        try:
            cols = get_project_columns(owner, repo, project_id, gh_token)
            # build mapping id->name
            for c in cols:
                col_cards = get_column_cards(c.get("id"), gh_token)
                card = find_card_for_issue(col_cards, issue_url)
                if card:
                    # compare to configured backlog/in_progress ids
                    in_backlog = bool(
                        backlog_column_id and c.get("id") == backlog_column_id
                    )
                    in_inprogress = bool(
                        project_columns.get("in_progress")
                        and c.get("id") == project_columns.get("in_progress")
                    )
                    status_allowed = in_backlog or in_inprogress
                    break
        except Exception as e:
            logger.debug(
                f"Project-card fallback failed for issue #{number}: {e}"
            )

    if not status_allowed:
        audit_entry["notes"] += "skipped — not in Backlog/In progress"
        return audit_entry

    # Check for stale issues
    if stale_enabled:
        updated_at_str = issue.get("updated_at")
        if updated_at_str:
            updated_at = datetime.fromisoformat(
                updated_at_str.replace("Z", "+00:00")
            )
            now = datetime.now(timezone.utc)
            days_since_update = (now - updated_at).days
            if days_since_update > stale_days and any(
                label in labels for label in stale_labels
            ):
                actions.append(f"{stale_action} stale issue")
                audit_entry[
                    "notes"
                ] += f"stale detected ({days_since_update} days); "
                if not dry_run:
                    try:
                        if stale_action == "close":
                            post_comment(
                                owner, repo, number, stale_comment, gh_token
                            )
                            close_issue(owner, repo, number, gh_token)
                            changed_fields.append("closed as stale")
                        elif stale_action == "comment":
                            post_comment(
                                owner, repo, number, stale_comment, gh_token
                            )
                            changed_fields.append("commented as stale")
                        elif stale_action == "label":
                            # Add a label, e.g., "stale"
                            add_label(owner, repo, number, "stale", gh_token)
                            changed_fields.append("labeled as stale")
                    except Exception as e:
                        logger.error(
                            f"Failed to handle stale issue #{number}: {e}"
                        )
                else:
                    changed_fields.append(f"would {stale_action} as stale")

    # Check for needs-info variants
    if any(variant in labels for variant in needs_info_variants):
        actions.append("assign to copilot-bot and remove Triaged")
        audit_entry["notes"] += "needs-info detected; "
        if not dry_run:
            try:
                # Timeline-aware decision: consult most recent Copilot event
                evt = get_most_recent_copilot_event(
                    owner, repo, number, gh_token
                )
                if evt:
                    etype = (evt.get("type") or "").lower()
                    last_err = evt.get("last_error_time")
                    if etype == "finished":
                        # Move to In Review; do not consume slot
                        in_review_id = project_columns.get("in_review")
                        if in_review_id and project_enabled and project_id:
                            move_issue_to_column(
                                owner,
                                repo,
                                number,
                                issue_url,
                                project_id,
                                in_review_id,
                                gh_token,
                            )
                            changed_fields.append(
                                "moved to In Review (copilot finished work)"
                            )
                            audit_entry[
                                "notes"
                            ] += "moved to In Review (copilot finished); "
                        else:
                            audit_entry[
                                "notes"
                            ] += (
                                "would move to In Review "
                                "(no column configured); "
                            )
                    elif etype == "error":
                        audit_entry[
                            "notes"
                        ] += "skipped assign — recent copilot error; "
                    elif (
                        etype == "start"
                        and evt.get("created_at")
                        and last_err
                        and evt.get("created_at") > last_err
                    ):
                        audit_entry["notes"] += (
                            "skipped assign — copilot restarted after error; "
                        )
                    else:
                        # No blocking Copilot event; attempt to assign
                        if (
                            copilot_assigns_this_run
                            >= MAX_COPILOT_ASSIGN_PER_RUN
                        ):
                            audit_entry[
                                "notes"
                            ] += "skipped assign — per-run cap reached; "
                        else:
                            copilot_assigns_this_run += 1
                            assign_issue(
                                owner,
                                repo,
                                number,
                                assignee_for_needs_info,
                                gh_token,
                            )
                            if (
                                remove_triaged_on_needs_info
                                and "Triaged" in labels
                            ):
                                remove_label(
                                    owner, repo, number, "Triaged", gh_token
                                )
                                changed_fields.append("removed Triaged")
                            changed_fields.append(
                                f"assigned to {assignee_for_needs_info}"
                            )
                else:
                    # No Copilot timeline; assign if slot available
                    if copilot_assigns_this_run >= MAX_COPILOT_ASSIGN_PER_RUN:
                        audit_entry[
                            "notes"
                        ] += "skipped assign — per-run cap reached; "
                    else:
                        copilot_assigns_this_run += 1
                        assign_issue(
                            owner,
                            repo,
                            number,
                            assignee_for_needs_info,
                            gh_token,
                        )
                        if remove_triaged_on_needs_info and "Triaged" in labels:
                            remove_label(
                                owner, repo, number, "Triaged", gh_token
                            )
                            changed_fields.append("removed Triaged")
                        changed_fields.append(
                            f"assigned to {assignee_for_needs_info}"
                        )
            except Exception as e:
                logger.error(f"Failed to update issue #{number}: {e}")
        else:
            changed_fields.append(
                f"would assign to {assignee_for_needs_info} "
                f"and remove Triaged"
            )

    # Check for needs_work label (assign to copilot for fixes)
    if "needs_work" in labels:
        actions.append("assign to copilot for fixes")
        audit_entry["notes"] += "needs_work detected; "
        if not dry_run:
            try:
                evt = get_most_recent_copilot_event(
                    owner, repo, number, gh_token
                )
                if evt:
                    etype = (evt.get("type") or "").lower()
                    last_err = evt.get("last_error_time")
                    if etype == "finished":
                        in_review_id = project_columns.get("in_review")
                        if in_review_id and project_enabled and project_id:
                            move_issue_to_column(
                                owner,
                                repo,
                                number,
                                issue_url,
                                project_id,
                                in_review_id,
                                gh_token,
                            )
                            changed_fields.append(
                                "moved to In Review (copilot finished work)"
                            )
                            audit_entry[
                                "notes"
                            ] += "moved to In Review (copilot finished); "
                        else:
                            audit_entry["notes"] += (
                                "would move to In Review "
                                "(no column configured); "
                            )
                    elif etype == "error":
                        audit_entry[
                            "notes"
                        ] += "skipped assign — recent copilot error; "
                    elif (
                        etype == "start"
                        and evt.get("created_at")
                        and last_err
                        and evt.get("created_at") > last_err
                    ):
                        audit_entry[
                            "notes"
                        ] += "skipped assign — copilot restarted after error; "
                    else:
                        if (
                            copilot_assigns_this_run
                            >= MAX_COPILOT_ASSIGN_PER_RUN
                        ):
                            audit_entry[
                                "notes"
                            ] += "skipped assign — per-run cap reached; "
                        else:
                            copilot_assigns_this_run += 1
                            assign_issue(
                                owner,
                                repo,
                                number,
                                assignee_for_needs_work,
                                gh_token,
                            )
                            # Keep label in place until fixes are done
                            changed_fields.append(
                                f"assigned to {assignee_for_needs_work}"
                            )
                            # Optionally add guidance comment for the author
                            post_comment(
                                owner,
                                repo,
                                number,
                                (
                                    "Marked as needs_work — moving back "
                                    "to In progress and assigning to "
                                    "@copilot to help move it forward. "
                                    "Please update when ready for re-review."
                                ),
                                gh_token,
                            )
                            changed_fields.append(
                                "commented needs_work guidance"
                            )
                else:
                    if copilot_assigns_this_run >= MAX_COPILOT_ASSIGN_PER_RUN:
                        audit_entry[
                            "notes"
                        ] += "skipped assign — per-run cap reached; "
                    else:
                        copilot_assigns_this_run += 1
                        assign_issue(
                            owner,
                            repo,
                            number,
                            assignee_for_needs_work,
                            gh_token,
                        )
                        changed_fields.append(
                            f"assigned to {assignee_for_needs_work}"
                        )
                        post_comment(
                            owner,
                            repo,
                            number,
                            (
                                "Marked as needs_work — moving back "
                                "to In progress and assigning to "
                                "@copilot to help move it forward. "
                                "Please update when ready for re-review."
                            ),
                            gh_token,
                        )
                        changed_fields.append("commented needs_work guidance")
            except Exception as e:
                logger.error(f"Failed to assign needs_work for #{number}: {e}")
        else:
            changed_fields.append(
                f"would assign to {assignee_for_needs_work} and comment"
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

            # Check if all required labels are present
            has_required_labels = all(
                label in labels for label in required_labels
            )
            # Check if assignee matches
            has_assignee = (
                required_assignee is None
                or required_assignee in assignee_logins
            )
            # Check if none of the not_labels are present
            has_no_not_labels = not any(label in labels for label in not_labels)

            if has_required_labels and has_assignee and has_no_not_labels:
                target_column_id = project_columns.get(
                    to_column.lower().replace(" ", "_")
                )
                if target_column_id:
                    actions.append(f"move to {to_column} column")
                    audit_entry[
                        "notes"
                    ] += f"workflow transition to {to_column}; "
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
                            changed_fields.append(
                                f"moved to {to_column} column"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to move issue #{number} to "
                                f"{to_column}: {e}"
                            )
                    else:
                        changed_fields.append(
                            f"would move to {to_column} column"
                        )
                break  # Only apply the first matching transition

    audit_entry["event_type"] = audit_event_type
    audit_entry["changed_fields"] = changed_fields

    if dry_run:
        print("[dry-run] " + ", ".join(actions))
    else:
        print("[live] " + ", ".join(actions))

    return audit_entry


def run_grooming_stages(
    owner: str,
    repo: str,
    gh_token: str,
    items: List[dict],
    dry_run: bool,
    needs_info_variants: list,
    assignee_for_needs_info: str,
    remove_triaged_on_needs_info: bool,
    assignee_for_needs_work: str,
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
) -> List[dict]:
    """Run grooming in stages and return audit entries.

    Stage 1: collect triaged open issues
    Stage 2: process Backlog issues (with at most one Copilot assign)
    Stage 3: process In progress issues (restart stalled Copilot)
    Stage 4: final non-Copilot cleanup
    """
    audit_entries: List[dict] = []

    # Stage 1: filter triaged open issues
    triaged = []
    for it in items:
        if it.get("state") == "closed":
            continue
        labels = [
            lbl.get("name", "")
            for lbl in it.get("labels", [])
            if isinstance(lbl, dict)
        ]
        if any(lbl.lower() == "triaged" for lbl in labels):
            triaged.append(it)

    # Stage 2: Backlog
    processed_ids = set()
    for issue in triaged:
        labels = [
            lbl.get("name", "")
            for lbl in issue.get("labels", [])
            if isinstance(lbl, dict)
        ]
        if any(lbl.lower() == "backlog" for lbl in labels):
            audit = process_issue(
                issue,
                owner,
                repo,
                gh_token,
                dry_run,
                needs_info_variants,
                assignee_for_needs_info,
                remove_triaged_on_needs_info,
                assignee_for_needs_work,
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
            audit_entries.append(audit)
            processed_ids.add(issue.get("number"))

    # Stage 3: In progress (exclude ones already processed)
    for issue in triaged:
        if issue.get("number") in processed_ids:
            continue
        labels = [
            lbl.get("name", "")
            for lbl in issue.get("labels", [])
            if isinstance(lbl, dict)
        ]
        if any(lbl.lower() == "in progress" for lbl in labels) or any(
            lbl.lower() == "in-progress" for lbl in labels
        ):
            audit = process_issue(
                issue,
                owner,
                repo,
                gh_token,
                dry_run,
                needs_info_variants,
                assignee_for_needs_info,
                remove_triaged_on_needs_info,
                assignee_for_needs_work,
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
            audit_entries.append(audit)
            processed_ids.add(issue.get("number"))

    # Stage 4: final cleanup for remaining triaged issues
    for issue in triaged:
        if issue.get("number") in processed_ids:
            continue
        audit = process_issue(
            issue,
            owner,
            repo,
            gh_token,
            dry_run,
            needs_info_variants,
            assignee_for_needs_info,
            remove_triaged_on_needs_info,
            assignee_for_needs_work,
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
        audit_entries.append(audit)

    return audit_entries


def main() -> int:
    triage_rules_path = os.environ.get(
        "TRIAGE_RULES_PATH", "copilot_triage_rules.yml"
    )
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
    # Apply grooming config overrides for Copilot assignment behavior
    try:
        global MAX_COPILOT_ASSIGN_PER_RUN, GROOMABLE_STATUS_LABELS
        MAX_COPILOT_ASSIGN_PER_RUN = int(
            grooming_settings.get(
                "max_copilot_assigns_per_run", MAX_COPILOT_ASSIGN_PER_RUN
            )
        )
        GROOMABLE_STATUS_LABELS = grooming_settings.get(
            "groomable_status_labels", GROOMABLE_STATUS_LABELS
        )
    except Exception:
        logger.debug(
            "Failed to parse grooming config overrides; using defaults"
        )
    needs_info_variants = grooming_settings.get(
        "needs_info_variants", ["needs-info"]
    )
    assignee_for_needs_info = grooming_settings.get(
        "assignee_for_needs_info", "copilot-bot"
    )
    remove_triaged_on_needs_info = grooming_settings.get(
        "remove_triaged_on_needs_info", True
    )
    assignee_for_needs_work = grooming_settings.get(
        "assignee_for_needs_work", "copilot"
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

    dry_run_env = os.environ.get("DRY_RUN", "").lower()
    dry_run = dry_run_env in ("1", "true", "yes")

    gh_repo = os.environ.get("GITHUB_REPOSITORY")
    gh_token = os.environ.get("GITHUB_TOKEN")

    # Validate token for security
    if gh_token and not validate_github_token(gh_token):
        logger.error(
            "Invalid GitHub token format. " "Ensure it's a valid GitHub token."
        )
        return 1

    # Warn if running in Actions with the default GITHUB_TOKEN — this
    # token cannot be used to assign Copilot agents via GraphQL. Users
    # should supply a PAT with the required scopes in repository secrets
    # if they want the groomer to assign Copilot agents.
    if (
        os.environ.get("GITHUB_ACTIONS") == "true"
        and gh_token
        and gh_token == os.environ.get("GITHUB_TOKEN")
    ):
        logger.warning(
            "Using the Actions-provided GITHUB_TOKEN. Copilot agent "
            "assignments require a user token (PAT) — assignment may "
            "fail or be skipped. Consider supplying a PAT via secrets."
        )

    if not gh_repo:
        print(
            "No GITHUB_REPOSITORY environment — running in local "
            "simulation mode"
        )
        return 0

    owner, repo = gh_repo.split("/")

    # Validate project and column IDs if token provided
    if gh_token and project_enabled and project_id:
        try:
            columns = get_project_columns(owner, repo, project_id, gh_token)
            valid_column_ids = {col["id"] for col in columns}
            for col_name, col_id in project_columns.items():
                if col_id and col_id not in valid_column_ids:
                    logger.warning(
                        f"Invalid column ID for {col_name}: {col_id}"
                    )
        except Exception as e:
            logger.error(f"Failed to validate project columns: {e}")

    if not gh_token:
        print(
            "No GITHUB_TOKEN present — will operate in dry-run only",
            file=sys.stderr,
        )
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
            assignee_for_needs_work,
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
        sanitized_entries = [
            sanitize_log_entry(entry) for entry in audit_entries
        ]
        logs.extend(sanitized_entries)

        # Log rotation: archive old entries if exceeding max
        if len(logs) > MAX_LOG_ENTRIES:
            os.makedirs(LOG_ARCHIVE_DIR, exist_ok=True)
            archive_timestamp = datetime.now(timezone.utc).strftime(
                "%Y%m%d_%H%M%S"
            )
            archive_file = os.path.join(
                LOG_ARCHIVE_DIR, f"triage_log_{archive_timestamp}.json"
            )
            # Archive older entries (keep only most recent)
            entries_to_archive = logs[:-MAX_LOG_ENTRIES]
            logs = logs[-MAX_LOG_ENTRIES:]
            with open(archive_file, "w", encoding="utf-8") as af:
                json.dump(entries_to_archive, af, indent=2)
            logger.info(
                f"Archived {len(entries_to_archive)} entries to "
                f"{archive_file}"
            )

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".json"
        ) as tmp:
            json.dump(logs, tmp, indent=2)
            tmp.flush()
            os.replace(tmp.name, log_file)
        print(f"Appended {len(audit_entries)} grooming audits to {log_file}")
    except Exception as e:
        logger.error(f"Failed to append to grooming log: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
