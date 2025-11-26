#!/usr/bin/env python3
"""
Check for paid API usage in the codebase.

This script scans Python files for references to paid API providers
(e.g., OpenAI, Anthropic, Cohere, Pinecone) to enforce free-mode operation
and prevent accidental cost overruns.

Usage:
  python scripts/check_paid_apis.py [--path PATH] [--exclude PATTERN]

Exit codes:
  0 - No paid API usage detected
  1 - Paid API usage detected
  2 - Script error
"""

import argparse
import fnmatch
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Patterns that indicate paid API usage
# Each pattern is a tuple of (regex_pattern, description)
PAID_API_PATTERNS = [
    # OpenAI
    (r"\bopenai\b", "OpenAI API"),
    (r"\bOpenAI\b", "OpenAI API"),
    (r"\bgpt-4\b", "OpenAI GPT-4 model"),
    (r"\bgpt-3\.5\b", "OpenAI GPT-3.5 model"),
    (r"\bchatgpt\b", "ChatGPT reference"),
    # Anthropic / Claude
    (r"\banthropic\b", "Anthropic API"),
    (r"\bAnthropic\b", "Anthropic API"),
    (r"\bclaude\b", "Claude model"),
    (r"\bClaude\b", "Claude model"),
    # Cohere
    (r"\bcohere\b", "Cohere API"),
    (r"\bCohere\b", "Cohere API"),
    # Pinecone (paid vector DB)
    (r"\bpinecone\b", "Pinecone vector database"),
    (r"\bPinecone\b", "Pinecone vector database"),
    # Replicate
    (r"\breplicate\b", "Replicate API"),
    (r"\bReplicate\b", "Replicate API"),
    # Google AI / Vertex AI (paid tiers)
    (r"\bvertex_ai\b", "Google Vertex AI"),
    (r"\bvertexai\b", "Google Vertex AI"),
    (r"\bgoogle\.generativeai\b", "Google Generative AI"),
    # AWS Bedrock
    (r"\bbedrock\b", "AWS Bedrock"),
    (r"\bBedrock\b", "AWS Bedrock"),
    # Azure OpenAI
    (r"\bazure\.ai\.openai\b", "Azure OpenAI"),
    (r"\bAzureOpenAI\b", "Azure OpenAI"),
]

# Files/directories to always exclude from scanning
DEFAULT_EXCLUDES = [
    "*.pyc",
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "*.egg-info",
    ".tox",
    ".pytest_cache",
    "dist",
    "build",
    # Exclude this script itself and its tests
    "check_paid_apis.py",
    "test_check_paid_apis.py",
]

# Files that are allowed to reference paid APIs (for documentation purposes)
ALLOWED_FILES = [
    "FREE_RUNBOOK.md",
    "FREE_HOSTING.md",
    "ARCHITECTURE.md",
    "README.md",
    "SECURITY_AND_RISKS.md",
    "threat-model.md",
    "requirements*.txt",
    "pyproject.toml",
    "*.yml",
    "*.yaml",
]


@dataclass
class Violation:
    """Represents a paid API usage violation."""

    file_path: str
    line_number: int
    line_content: str
    pattern_matched: str
    description: str


def should_exclude(path: Path, excludes: list[str]) -> bool:
    """Check if a path should be excluded from scanning."""
    path_str = str(path)
    name = path.name

    for pattern in excludes:
        if fnmatch.fnmatch(name, pattern):
            return True
        if fnmatch.fnmatch(path_str, pattern):
            return True

    return False


def is_allowed_file(path: Path, allowed: list[str]) -> bool:
    """Check if a file is in the allowed list."""
    name = path.name

    for pattern in allowed:
        if fnmatch.fnmatch(name, pattern):
            return True

    return False


def scan_file(
    file_path: Path, patterns: list[tuple[str, str]]
) -> list[Violation]:
    """Scan a single file for paid API patterns."""
    violations = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, start=1):
                # Skip comment lines for less noise
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue

                for pattern, description in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_number=line_num,
                                line_content=line.rstrip(),
                                pattern_matched=pattern,
                                description=description,
                            )
                        )
                        # Only report first pattern match per line
                        break
    except (OSError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return violations


def scan_directory(
    root_path: Path,
    patterns: list[tuple[str, str]],
    excludes: list[str],
    allowed: list[str],
    file_extensions: Optional[list[str]] = None,
) -> list[Violation]:
    """Scan a directory recursively for paid API patterns."""
    if file_extensions is None:
        file_extensions = [".py"]

    violations = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        current_dir = Path(dirpath)

        # Remove excluded directories from traversal
        dirnames[:] = [
            d for d in dirnames if not should_exclude(current_dir / d, excludes)
        ]

        for filename in filenames:
            file_path = current_dir / filename

            # Skip if excluded
            if should_exclude(file_path, excludes):
                continue

            # Skip if in allowed list
            if is_allowed_file(file_path, allowed):
                continue

            # Check file extension
            if not any(filename.endswith(ext) for ext in file_extensions):
                continue

            file_violations = scan_file(file_path, patterns)
            violations.extend(file_violations)

    return violations


def format_violations(violations: list[Violation]) -> str:
    """Format violations for output."""
    if not violations:
        return "No paid API usage detected. Free-mode enforcement passed!"

    lines = [
        "=" * 60,
        "PAID API USAGE DETECTED - FREE-MODE VIOLATION",
        "=" * 60,
        "",
    ]

    # Group by file
    by_file: dict[str, list[Violation]] = {}
    for v in violations:
        if v.file_path not in by_file:
            by_file[v.file_path] = []
        by_file[v.file_path].append(v)

    for file_path, file_violations in sorted(by_file.items()):
        lines.append(f"File: {file_path}")
        for v in file_violations:
            lines.append(f"  Line {v.line_number}: {v.description}")
            lines.append(f"    {v.line_content[:80]}...")
        lines.append("")

    lines.append("=" * 60)
    lines.append(f"Total violations: {len(violations)}")
    lines.append("")
    lines.append("To fix: Remove or replace paid API references with")
    lines.append("free/self-hosted alternatives. See docs/FREE_RUNBOOK.md")
    lines.append("=" * 60)

    return "\n".join(lines)


def main(args: Optional[list[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check for paid API usage in the codebase"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to scan (default: current directory)",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        action="append",
        default=[],
        help="Additional patterns to exclude",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default=".py",
        help="Comma-separated file extensions to scan (default: .py)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only output if violations found",
    )

    parsed = parser.parse_args(args)

    root_path = Path(parsed.path).resolve()
    if not root_path.exists():
        print(f"Error: Path does not exist: {root_path}", file=sys.stderr)
        return 2

    excludes = DEFAULT_EXCLUDES + parsed.exclude
    extensions = [ext.strip() for ext in parsed.extensions.split(",")]

    violations = scan_directory(
        root_path,
        PAID_API_PATTERNS,
        excludes,
        ALLOWED_FILES,
        extensions,
    )

    if violations or not parsed.quiet:
        print(format_violations(violations))

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
