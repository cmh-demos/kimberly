#!/usr/bin/env python3
"""Doc review cycle script: Scan for gaps like TBD, placeholder, TODO in docs.

Usage: python scripts/doc_review.py [--fix] [--verbose]

Scans all .md files in docs/ and root for common placeholders.
Prints findings. With --fix, attempts to replace simple ones.
"""

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

PLACEHOLDERS = [
    r"\bTBD\b",
    r"placeholder",
    r"TODO",
    r"\(placeholder\)",
    r"@owner TBD",
    r"@.* TBD",
]


def scan_docs(
    root_dir: str = ".", extensions: List[str] = [".md"]
) -> Dict[str, List[Tuple[int, str, str]]]:
    findings: Dict[str, List[Tuple[int, str, str]]] = {}
    for ext in extensions:
        for file_path in Path(root_dir).rglob(f"*{ext}"):
            if "node_modules" in str(file_path) or ".git" in str(file_path):
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    file_findings: List[Tuple[int, str, str]] = []
                    for i, line in enumerate(lines, 1):
                        for pattern in PLACEHOLDERS:
                            if re.search(pattern, line, re.IGNORECASE):
                                file_findings.append((i, line.strip(), pattern))
                    if file_findings:
                        findings[str(file_path)] = file_findings
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    return findings


def print_findings(
    findings: Dict[str, List[Tuple[int, str, str]]], verbose: bool = False
) -> None:
    if not findings:
        print("No placeholders found! Docs are clean.")
        return
    print(
        f"Found {sum(len(v) for v in findings.values())} placeholder instances in {len(findings)} files:"
    )
    for file, issues in findings.items():
        print(f"\n{file}:")
        for line_num, line, pattern in issues:
            print(f"  Line {line_num}: {line} (matched: {pattern})")
            if verbose:
                print(f"    Context: {line}")


def fix_simple(findings: Dict[str, List[Tuple[int, str, str]]]) -> None:
    # Simple fixes: e.g., replace @owner TBD with @backend-dev
    fixes = {
        "@owner TBD": "@backend-dev",
        "@sec TBD": "@security-eng",
        "@ops TBD": "@sre",
        "@data_privacy TBD": "@privacy-eng",
        "@api TBD": "@api-eng",
        "@ml TBD": "@ml-eng",
        "@dev TBD": "@backend-dev",
    }
    fixed_count = 0
    for file, issues in findings.items():
        content = Path(file).read_text(encoding="utf-8")
        original = content
        for _, _, pattern in issues:
            if pattern in fixes:
                content = re.sub(
                    re.escape(pattern), fixes[pattern], content, flags=re.IGNORECASE
                )
        if content != original:
            Path(file).write_text(content, encoding="utf-8")
            fixed_count += 1
    print(f"Applied {fixed_count} simple fixes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Doc review cycle: Scan for placeholders."
    )
    parser.add_argument("--fix", action="store_true", help="Attempt simple fixes.")
    parser.add_argument("--verbose", action="store_true", help="Show more context.")
    args = parser.parse_args()

    findings = scan_docs()
    print_findings(findings, args.verbose)
    if args.fix:
        fix_simple(findings)
        print("Re-run without --fix to verify.")
