#!/usr/bin/env python3
"""Simple Markdown linter/fixer for this repo.

Performs safe, mechanical fixes:
- Trim trailing whitespace
- Ensure LF line endings
- Collapse consecutive blank lines to max 2
- Ensure a single newline at EOF
- Ensure there's an empty line after a heading

This is intentionally conservative — it will not reflow paragraphs or alter
semantic content.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List


def fix_text(text: str) -> str:
    # Normalize CRLF -> LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Trim trailing whitespace on each line
    lines = [re.sub(r"[ \t]+$", "", ln) for ln in text.split("\n")]

    # Ensure there's a blank line after any heading (e.g. '# Heading')
    out_lines: List[str] = []
    for i, ln in enumerate(lines):
        out_lines.append(ln)
        if re.match(r"^#{1,6}[^#].*", ln):
            # If next line exists and is not blank, insert one blank line
            if i + 1 < len(lines) and lines[i + 1] != "":
                out_lines.append("")

    # Collapse more than two blank lines into two
    collapsed: List[str] = []
    blank_count = 0
    for ln in out_lines:
        if ln == "":
            blank_count += 1
            if blank_count <= 2:
                collapsed.append(ln)
        else:
            blank_count = 0
            collapsed.append(ln)

    # Ensure EOF newline
    final = "\n".join(collapsed).rstrip("\n") + "\n"
    return final


def find_md_files(root: Path) -> List[Path]:
    ignore = {".git", "node_modules", "out", "dist", ".venv", "venv"}
    result: List[Path] = []
    for p in root.rglob("*.md"):
        if any(part in ignore for part in p.parts):
            continue
        result.append(p)
    return sorted(result)


def main():
    root = Path(__file__).resolve().parent.parent
    files = find_md_files(root)
    fixed = 0
    modified_files: List[Path] = []
    for f in files:
        txt = f.read_text(encoding="utf-8")
        new = fix_text(txt)
        if new != txt:
            f.write_text(new, encoding="utf-8")
            fixed += 1
            modified_files.append(f)

    print(f"Checked {len(files)} markdown files; fixed: {fixed}")
    if modified_files:
        print("Modified files:")
        for p in modified_files:
            print(" - ", p.relative_to(root))


if __name__ == "__main__":
    main()
