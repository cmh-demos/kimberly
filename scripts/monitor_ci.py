#!/usr/bin/env python3
"""Monitor GitHub Actions runs for a given repo/branch/commit without using curl.

Usage examples:
  python scripts/monitor_ci.py --owner cmh-demos --repo kimberly --branch docs/project-definition
  python scripts/monitor_ci.py --owner cmh-demos --repo kimberly --sha 909cff36

This polls the GitHub Actions API and prints the run status until completion.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from typing import Optional

try:
    # prefer stdlib so no extra deps
    from urllib.request import Request, urlopen
except Exception:
    raise


def fetch_runs(owner: str, repo: str, branch: Optional[str], per_page: int = 10):
    base = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    if branch:
        url = f"{base}?branch={branch}&per_page={per_page}"
    else:
        url = f"{base}?per_page={per_page}"
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "monitor-ci-script",
        },
    )
    with urlopen(req) as resp:
        return json.load(resp)


def find_run(runs_payload, sha: Optional[str]):
    runs = runs_payload.get("workflow_runs", [])
    if sha:
        for r in runs:
            if r.get("head_sha") == sha:
                return r
        return None
    return runs[0] if runs else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--sha", default=None)
    parser.add_argument("--interval", type=int, default=5, help="poll interval seconds")
    parser.add_argument(
        "--timeout", type=int, default=300, help="overall timeout seconds"
    )
    args = parser.parse_args()

    deadline = time.time() + args.timeout

    print(
        f"Monitoring GitHub Actions runs for {args.owner}/{args.repo} branch={args.branch} sha={args.sha}"
    )

    run = None
    while time.time() < deadline:
        payload = fetch_runs(args.owner, args.repo, args.branch)
        run = find_run(payload, args.sha) if payload else None
        if not run:
            print("No run found yet — waiting...")
            time.sleep(args.interval)
            continue

        status = run.get("status")
        conclusion = run.get("conclusion")
        url = run.get("html_url")
        run_number = run.get("run_number")
        head_sha = run.get("head_sha")

        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(
            f"[{timestamp}] run #{run_number} sha={head_sha} status={status} conclusion={conclusion} url={url}"
        )

        if status == "completed":
            print("Run completed — final conclusion:", conclusion)
            break

        # if still in progress, sleep and retry
        time.sleep(args.interval)

    if not run:
        print("No run was found for the provided branch/sha within the timeout.")
        sys.exit(2)


if __name__ == "__main__":
    main()
