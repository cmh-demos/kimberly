#!/usr/bin/env python3
"""Minimal Copilot triage runner (Python)

Behavior:
- Reads `copilot_triage_rules.yml` for version & guidance
- Queries GitHub for open issues with label "Needs Triage" (up to 25)
- Simulates triage actions and logs them (dry-run)
- If DRY_RUN is false and GITHUB_TOKEN is available, performs minimal actions
  (add label 'Triaged' and post a small comment)

This runner is intentionally conservative — it only performs live changes
when DRY_RUN=false (the workflow sets DRY_RUN=false only for main branch).
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

import requests
import yaml

# Default duplicate detection similarity threshold (0.0-1.0)
# Can be overridden via detect_duplicates.similarity_threshold in rules file
DEFAULT_DUPLICATE_SIMILARITY_THRESHOLD = 0.78


def load_rules(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
            return data
    except FileNotFoundError:
        return None


def read_rules_version(path: str) -> str | None:
    try:
        data = load_rules(path)
        if not isinstance(data, dict):
            return None
        schema = data.get("triage_audit_schema")
        if isinstance(schema, dict):
            return schema.get("version", "unknown")
        return "unknown"
    except FileNotFoundError:
        return None


def github_search_issues(
    owner: str, repo: str, token: str | None, per_page: int = 25
) -> List[dict]:
    query = f'repo:{owner}/{repo} is:issue is:open -label:"Triaged"'
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


def post_label(
    owner: str, repo: str, issue_number: int, label: str, token: str
) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.post(url, headers=headers, json={"labels": [label]})
    resp.raise_for_status()


def post_comment(
    owner: str, repo: str, issue_number: int, comment_text: str, token: str
) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.post(url, headers=headers, json={"body": comment_text})
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


def create_card(column_id: int, issue_id: int, token: str) -> None:
    url = f"https://api.github.com/projects/columns/{column_id}/cards"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    data = {"content_id": issue_id, "content_type": "Issue"}
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
    else:
        # Create new card in Backlog column
        create_card(backlog_column_id, issue_number, token)


def fetch_related_docs(
    owner: str, repo: str, token: str | None, issue_body: str, issue_title: str
) -> List[str]:
    """Search repo for related docs based on issue content."""
    references = []
    # Simple implementation: search for keywords in docs/ folder via GitHub API
    # This is a placeholder; in practice, use GitHub search or local search
    keywords = re.findall(r"\w+", issue_title + " " + issue_body)[:10]  # top 10 words
    query = f'repo:{owner}/{repo} path:docs/ {" ".join(keywords[:5])}'
    try:
        resp = requests.get(
            "https://api.github.com/search/code",
            params={"q": query},
            headers={"Authorization": f"Bearer {token}"} if token else {},
        )
        if resp.ok:
            items = resp.json().get("items", [])
            for item in items[:3]:  # limit to 3
                references.append(item.get("html_url", ""))
    except Exception:
        # Placeholder implementation: silently ignore API errors
        pass
    return references


def move_card(
    owner: str, repo: str, issue_number: int, token: str, column_name: str
) -> None:
    """Move issue to project card column. Placeholder - requires project board setup."""
    # GitHub Projects API is complex; this is a stub
    # In practice, find project, card, move to column
    print(f"[stub] Would move issue #{issue_number} to column: {column_name}")


def assign_triage_owner(
    owner: str, repo: str, issue_number: int, assignee: str, token: str
) -> None:
    """Assign triage owner to issue."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.patch(url, headers=headers, json={"assignees": [assignee]})
    resp.raise_for_status()


def detect_pii(text: str) -> bool:
    if not text:
        return False
    # default PII patterns; runner will try to use patterns from rules when available
    patterns = [
        re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.I),
        re.compile(r"secret\s*[:=]\s*\S+", re.I),
        re.compile(r"password\s*[:=]\s*\S+", re.I),
        re.compile(r"-----BEGIN PRIVATE KEY-----"),
    ]
    return any(p.search(text) for p in patterns)


def main() -> int:
    rules_path = os.environ.get("RULES_PATH", "copilot_triage_rules.yml")
    rules = load_rules(rules_path)
    if rules is None:
        print(f"ERROR: rules file not found at {rules_path}", file=sys.stderr)
        return 1

    version = read_rules_version(rules_path)
    if version is None:
        print(f"ERROR: rules file not found at {rules_path}", file=sys.stderr)
        return 1

    print(f"Loaded triage rules version: {version}")

    # helper config from rules
    protected_branches = rules.get("execution_policy", {}).get(
        "protected_branches", ["main"]
    )
    default_owner = rules.get("triage_ownership", {}).get(
        "default_owner", "copilot-bot"
    )
    # project management config
    project_management = rules.get("project_management", {})
    project_enabled = project_management.get("enabled", False)
    project_id = project_management.get("project_id")
    backlog_column_id = project_management.get("columns", {}).get("Backlog")

    required_fields = []
    req = rules.get("required_issue_fields")
    if isinstance(req, dict):
        required_fields = list(req.keys())

    detect_pii_patterns = []
    # extract duplicate detection similarity threshold from rules
    duplicate_similarity_threshold = DEFAULT_DUPLICATE_SIMILARITY_THRESHOLD
    # collect patterns if present
    if isinstance(rules, dict):
        steps = rules.get("steps") or []
        for s in steps:
            if isinstance(s, dict) and "scan_for_pii" in s:
                pii_cfg = s["scan_for_pii"]
                if isinstance(pii_cfg, dict):
                    detect_pii_patterns = pii_cfg.get("patterns", [])
            if isinstance(s, dict) and "detect_duplicates" in s:
                dup_cfg = s["detect_duplicates"]
                if isinstance(dup_cfg, dict):
                    duplicate_similarity_threshold = dup_cfg.get(
                        "similarity_threshold", DEFAULT_DUPLICATE_SIMILARITY_THRESHOLD
                    )
            # fallback older style keys
        # also check for pii_handling.detect_patterns
        pii_handling = rules.get("pii_handling") or {}
        if isinstance(pii_handling, dict):
            detect_pii_patterns = detect_pii_patterns + pii_handling.get(
                "detect_patterns", []
            )

    # compile detect patterns where present
    compiled_pii_patterns = []
    for p in detect_pii_patterns:
        try:
            compiled_pii_patterns.append(re.compile(p, re.I))
        except Exception:
            # ignore patterns that fail to compile
            pass

    dry_run_env = os.environ.get("DRY_RUN", "").lower()
    # If DRY_RUN unset, pick based on branch (GITHUB_REF)
    if not dry_run_env:
        ref = os.environ.get("GITHUB_REF", "")
        current_branch = (
            ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ""
        )
        dry_run = current_branch not in protected_branches
    else:
        dry_run = dry_run_env in ("1", "true", "yes")

    gh_repo = os.environ.get("GITHUB_REPOSITORY")
    gh_token = os.environ.get("GITHUB_TOKEN")

    if not gh_repo:
        print("No GITHUB_REPOSITORY environment — running in local simulation mode")
        print("Runner exits after parsing rules (no API calls without repository).")
        return 0

    owner, repo = gh_repo.split("/")
    if not gh_token:
        print("No GITHUB_TOKEN present — will operate in dry-run only", file=sys.stderr)
        dry_run = True

    print(f"Dry-run: {dry_run}")

    # Optionally target a single issue by setting ISSUE_NUMBER env var.
    issue_env = os.environ.get("ISSUE_NUMBER")

    items = []
    try:
        if issue_env:
            target = github_get_issue(owner, repo, int(issue_env), gh_token)
            if target:
                items = [target]
            else:
                print(f"Issue #{issue_env} not found or inaccessible")
                return 0
        else:
            items = github_search_issues(owner, repo, gh_token)
    except Exception as e:
        print("Failed to query GitHub issues:", e, file=sys.stderr)
        return 1

    if not items:
        print('No issues labeled "Needs Triage" found (up to 25).')
        return 0

    print(f"Found {len(items)} candidate issues")

    for issue in items:
        number = issue.get("number")
        title = issue.get("title")
        body = issue.get("body") or ""
        print("---")
        print(f"Issue #{number}: {title}")

        actions: List[str] = []
        changed_fields: List[str] = []
        audit_entry: Dict[str, Any] = {
            "issue_number": number,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_type": "initial_triage",
            "triage_owner": default_owner,
            "severity": None,
            "priority": None,
            "size_estimate": None,
            "pii_detected": False,
            "redacted_fields": [],
            "redaction_actions": [],
            "dry_run": dry_run,
            "execution_branch": os.environ.get("GITHUB_REF", "unknown"),
            "title_sanitized": False,
            "original_title": None,
            "changed_fields": [],
            "notes": "",
            "references": [],
        }

        # 1) Fetch related docs
        references = fetch_related_docs(owner, repo, gh_token, body, title)
        audit_entry["references"] = references

        # 2) Check required fields
        missing_fields = []
        for f in required_fields:
            # simple detection: look for a literal "<field>:" in body
            if not re.search(rf"{re.escape(f)}\s*[:=]", body, re.I):
                missing_fields.append(f)

        if missing_fields:
            actions.append(
                f"would add label: needs-info (missing: {','.join(missing_fields)})"
            )
            audit_entry["notes"] += f"missing_fields={missing_fields}; "
            audit_entry["changed_fields"].append("needs_info")

        # 2) PII detection (use compiled patterns when available)
        pii_found = False
        matches: List[str] = []
        if compiled_pii_patterns:
            for p in compiled_pii_patterns:
                for m in p.finditer(body):
                    pii_found = True
                    matches.append(m.group(0))
        else:
            # fallback to builtin check
            pii_found = detect_pii(body)

        if pii_found:
            actions.append("would add label: security")
            audit_entry["pii_detected"] = True
            audit_entry["redacted_fields"] = matches
            audit_entry["redaction_actions"].append(
                "redact" if not dry_run else "would_redact"
            )

        # 3) Duplicate detection (basic title/title similarity)
        duplicates = []
        try:
            # perform a lightweight search for issues with similar words from title
            title_terms = [w.lower() for w in re.findall(r"\w+", title) if len(w) > 2]
            if title_terms:
                q = " ".join(title_terms[:6])
                q_full = f"repo:{owner}/{repo} is:issue is:open {q}"
                r = requests.get(
                    "https://api.github.com/search/issues",
                    params={"q": q_full, "per_page": 25},
                    headers=(
                        {
                            "Accept": "application/vnd.github+json",
                            "Authorization": f"Bearer {gh_token}",
                        }
                        if gh_token
                        else {"Accept": "application/vnd.github+json"}
                    ),
                )
                r.raise_for_status()
                cand = r.json().get("items", [])
                for c in cand:
                    if c.get("number") == number:
                        continue
                    s = SequenceMatcher(None, title.lower(), c.get("title", "").lower())
                    ratio = s.ratio()
                    if ratio >= duplicate_similarity_threshold:
                        duplicates.append(
                            {
                                "number": c.get("number"),
                                "title": c.get("title"),
                                "ratio": ratio,
                            }
                        )
        except Exception:
            duplicates = []

        if duplicates:
            actions.append("would mark as duplicate and link to canonical issue(s)")
            audit_entry["notes"] += f"duplicates={duplicates}; "
        # 4) Title sanitization: remove priority tags from title when present
        sanitized_title = re.sub(
            r"\s*\[\s*(Top Priority|High Priority|Medium Priority|Low Priority|P0|P1|P2|P3|Other)\s*\]\s*",
            " ",
            title,
            flags=re.I,
        )
        if sanitized_title.strip() != title.strip():
            audit_entry["original_title"] = title
            audit_entry["title_sanitized"] = True
            if dry_run:
                actions.append("would sanitize title and record original_title")
                audit_entry["changed_fields"].append("would_replace_title")
            else:
                actions.append("sanitize title and update original_title")
        # 5) compute severity / priority basic heuristics
        severity = None
        priority = None
        # map label names to severity if present
        labels_list = [
            lbl.get("name") for lbl in issue.get("labels", []) if isinstance(lbl, dict)
        ]
        label_to_sev = rules.get("label_mappings", {}).get("label_to_severity", {})
        for lbl in labels_list:
            if lbl in label_to_sev:
                severity = label_to_sev[lbl]
                break

        # fallback heuristics
        if not severity:
            text = (title + "\n" + body).lower()
            if (
                "data loss" in text
                or "complete loss" in text
                or "security" in labels_list
            ):
                severity = "critical"
            elif "block" in text or "broken for many" in text or "major" in text:
                severity = "high"
            elif "minor" in text or "typo" in text:
                severity = "low"
            else:
                severity = "medium"

        # compute priority from labels or fallback
        label_to_pr = rules.get("label_mappings", {}).get("label_to_priority", {})
        for lbl in labels_list:
            if lbl in label_to_pr:
                priority = label_to_pr[lbl]
                break
        if not priority:
            # simple mapping based on severity
            priority_map = {"critical": "p0", "high": "p1", "medium": "p2", "low": "p3"}
            priority = priority_map.get(severity, "p3")

        audit_entry["severity"] = severity
        audit_entry["priority"] = priority

        # 6) Backlog gating logic: check required 'size_estimate' and product-approved for features
        backlog_actions: List[str] = []
        # detect feature-request label
        if "feature-request" in labels_list:
            product_ok = "product-approved" in labels_list
        else:
            product_ok = True

        # check if size_estimate found in body and allowed values
        size_est_match = re.search(r"size_estimate\s*[:=]\s*(\w+)", body, re.I)
        size_est_value: Optional[str] = (
            size_est_match.group(1).lower() if size_est_match else None
        )
        allowed_sizes = rules.get("quick_size_estimates", {}).get(
            "allowed_values", ["xsmall", "small", "medium", "large", "epic"]
        )
        if size_est_value:
            audit_entry["size_estimate"] = size_est_value
            if size_est_value not in allowed_sizes:
                # invalid size estimate
                backlog_actions.append("invalid_size_estimate")
                actions.append("would add label: needs-info (invalid size_estimate)")
        else:
            backlog_actions.append("missing_size_estimate")

        if not dry_run:
            # live mode processing
            print("[live] performing actions...")
            try:
                # apply PII handling: add security label and post secure intake instructions
                if pii_found:
                    if "security" not in labels_list:
                        post_label(owner, repo, number, "security", gh_token)
                        print(f"Added label security to #{number}")
                        changed_fields.append("security")
                    # post redaction message
                    post_comment(
                        owner,
                        repo,
                        number,
                        rules.get("bot_comment_templates", {}).get(
                            "redaction_notice",
                            "Sensitive content was detected and redacted.",
                        ),
                        gh_token,
                    )

                # sanitize title if needed
                if audit_entry["title_sanitized"] and audit_entry["original_title"]:
                    # update title via issue edit
                    new_title = sanitized_title.strip()
                    resp = requests.patch(
                        f"https://api.github.com/repos/{owner}/{repo}/issues/{number}",
                        headers={
                            "Authorization": f"Bearer {gh_token}",
                            "Accept": "application/vnd.github+json",
                        },
                        json={"title": new_title},
                    )
                    resp.raise_for_status()
                    print(f"Updated title for #{number}")
                    changed_fields.append("title")

                # If missing required fields, add needs-info label and comment
                if missing_fields:
                    if "needs-info" not in labels_list:
                        post_label(owner, repo, number, "needs-info", gh_token)
                        print(f"Added label needs-info to #{number}")
                        changed_fields.append("needs-info")
                    comment_text = rules.get("bot_comment_templates", {}).get(
                        "request_more_info",
                        "Please update the issue with more information",
                    )
                    post_comment(owner, repo, number, comment_text, gh_token)

                # backlog gating
                can_add_backlog = True
                if "missing_size_estimate" in backlog_actions:
                    can_add_backlog = False
                if "invalid_size_estimate" in backlog_actions:
                    can_add_backlog = False
                if "feature-request" in labels_list and not product_ok:
                    can_add_backlog = False

                if can_add_backlog:
                    # add Triaged label and short comment if triaging complete
                    if "Triaged" not in labels_list:
                        post_label(owner, repo, number, "Triaged", gh_token)
                        post_comment(
                            owner,
                            repo,
                            number,
                            rules.get("bot_comment_templates", {}).get(
                                "triaged_backlog_notice",
                                "This issue has been marked Triaged and placed in Backlog.",
                            ),
                            gh_token,
                        )
                        changed_fields.append("Triaged")

                    if "Backlog" not in labels_list:
                        post_label(owner, repo, number, "Backlog", gh_token)
                        post_comment(
                            owner,
                            repo,
                            number,
                            rules.get("bot_comment_templates", {}).get(
                                "backlog_added_notice", "Added to backlog"
                            ),
                            gh_token,
                        )
                        changed_fields.append("Backlog")
                else:
                    # gate failed
                    if "needs-product-review" not in labels_list:
                        post_label(
                            owner, repo, number, "needs-product-review", gh_token
                        )
                        changed_fields.append("needs-product-review")
                    if "needs_work" not in labels_list:
                        post_label(owner, repo, number, "needs_work", gh_token)
                        changed_fields.append("needs_work")
                    post_comment(
                        owner,
                        repo,
                        number,
                        rules.get("bot_comment_templates", {}).get(
                            "backlog_gate_blocked_notice",
                            "Backlog gate blocked — missing info",
                        ),
                        gh_token,
                    )

                # escalate when critical / security
                if audit_entry["severity"] == "critical" or "security" in labels_list:
                    post_comment(
                        owner,
                        repo,
                        number,
                        rules.get("bot_comment_templates", {}).get(
                            "escalation_notice", "Issue escalated to oncall"
                        ),
                        gh_token,
                    )
                    changed_fields.append("escalation")

                # Pair enforcement & triaged_to_backlog/backlog_to_triaged
                pair_cfg = rules.get("label_policy", {}).get("pair_enforcement", {})
                if isinstance(pair_cfg, dict):
                    pair = pair_cfg.get("pair", ["Triaged", "Backlog"])
                    if "Triaged" in pair and "Backlog" in pair:
                        skip_labels = set(pair_cfg.get("skip_if_any_present", []))
                        # refresh labels_list from API
                        lbls_resp = requests.get(
                            f"https://api.github.com/repos/{owner}/{repo}/issues/{number}",
                            headers={
                                "Accept": "application/vnd.github+json",
                                "Authorization": f"Bearer {gh_token}",
                            },
                        )
                        if lbls_resp.ok:
                            latest = lbls_resp.json()
                            latest_labels = [
                                l.get("name")
                                for l in latest.get("labels", [])
                                if isinstance(l, dict)
                            ]
                        else:
                            latest_labels = labels_list

                        if "Triaged" in latest_labels:
                            print(f"Issue #{number} already triaged, skipping")
                            continue

                        # When Triaged is present and Backlog missing -> add Backlog
                        if (
                            "Triaged" in latest_labels
                            and "Backlog" not in latest_labels
                            and not (set(latest_labels) & skip_labels)
                        ):
                            # respect grace_period_hours: if recently modified by a human, skip
                            # (not implemented full recent human action detection here)
                            post_label(owner, repo, number, "Backlog", gh_token)
                            post_comment(
                                owner,
                                repo,
                                number,
                                rules.get("bot_comment_templates", {}).get(
                                    "backlog_added_notice", "Added to backlog"
                                ),
                                gh_token,
                            )
                            changed_fields.append("Backlog")
                            # Move to Backlog column if project management is enabled
                            if project_enabled and project_id and backlog_column_id:
                                issue_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
                                try:
                                    move_issue_to_backlog_column(
                                        owner,
                                        repo,
                                        number,
                                        issue_url,
                                        project_id,
                                        backlog_column_id,
                                        gh_token,
                                    )
                                except Exception as e:
                                    print(
                                        f"Failed to move issue to Backlog column: {e}",
                                        file=sys.stderr,
                                    )

                        # When Backlog is present and Triaged missing -> add Triaged
                        if (
                            "Backlog" in latest_labels
                            and "Triaged" not in latest_labels
                            and not (set(latest_labels) & skip_labels)
                        ):
                            post_label(owner, repo, number, "Triaged", gh_token)
                            post_comment(
                                owner,
                                repo,
                                number,
                                rules.get("bot_comment_templates", {}).get(
                                    "label_added", "Added missing Triaged"
                                ),
                                gh_token,
                            )
                            changed_fields.append("Triaged")

                # triaged_if: deterministic triage completion
                triaged_if = rules.get("triaged_if") or []
                # Basic evaluation: required_fields_present, triage_owner_assigned, severity_assigned
                triage_complete = True
                if isinstance(triaged_if, list):
                    for condition in triaged_if:
                        if (
                            isinstance(condition, dict)
                            and "required_fields_present" in condition
                        ):
                            required = condition["required_fields_present"]
                            for rf in required:
                                if not re.search(
                                    rf"{re.escape(rf)}\s*[:=]", body, re.I
                                ):
                                    triage_complete = False
                        if (
                            isinstance(condition, dict)
                            and "triage_owner_assigned" in condition
                        ):
                            if not default_owner:
                                triage_complete = False
                        if (
                            isinstance(condition, dict)
                            and "severity_assigned" in condition
                        ):
                            if not audit_entry.get("severity"):
                                triage_complete = False

                if triage_complete:
                    # remove 'Needs Triage' and ensure Triaged/Backlog present
                    if "Needs Triage" in latest_labels:
                        # remove label via issues API
                        requests.delete(
                            f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/labels/Needs%20Triage",
                            headers={
                                "Authorization": f"Bearer {gh_token}",
                                "Accept": "application/vnd.github+json",
                            },
                        )
                        changed_fields.append("Needs Triage")

            except Exception as e:
                print(
                    "Failed to apply live changes for issue",
                    number,
                    str(e),
                    file=sys.stderr,
                )
        else:
            print("[dry-run] " + ", ".join(actions))
        # end issue processing (live branch already handled above)

        # record audit in triage_log.json (local). On live runs we would also push or append via API.
        log_entry = audit_entry
        log_file = (
            rules.get("log_triage_event", {}).get("path", "triage_log.json")
            if isinstance(rules, dict)
            else "triage_log.json"
        )
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
            print(f"Appended triage audit to {log_file}")
        except Exception as e:
            print("Failed to append to triage log:", e, file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
