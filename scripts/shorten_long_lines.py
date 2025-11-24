#!/usr/bin/env python3
"""A focused tool to wrap stubborn long single-lines in Markdown files.

This will re-wrap individual lines that exceed the target length but are not
table rows, do not contain URLs or inline code, and are not inside fenced code
blocks. It is conservative by design — only edits clearly-wrapped plain text.

Usage: python3 scripts/shorten_long_lines.py --width 100 [paths...]
"""
from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path
from typing import Iterable, List


def find_md_files(root: Path):
    ignore = {".git", "node_modules", "out", "dist", "venv-nodejs"}
    for p in root.rglob("*.md"):
        if any(part in ignore or part.startswith(".venv") or part.startswith("venv") for part in p.parts):
            continue
        yield p


def should_wrap_line(line: str, width: int) -> bool:
    if len(line) <= width:
        return False
    if "|" in line:
        return False
    # avoid touching links or other likely-breakage cases
    if "http" in line or "<code>" in line:
        return False
    # allow short inline-code tokens (e.g. `slug`) but avoid wrapping code with spaces
    if "`" in line:
        for m in re.finditer(r"`([^`]+)`", line):
            tok = m.group(1)
            if len(tok) > 60 or " " in tok:
                return False
    if re.search(r"\S+@\S+", line):
        return False
    return True


def wrap_line(line: str, width: int) -> List[str]:
    # preserve leading indentation and common list markers
    m = re.match(r"^(\s*)([-*+]\s+\[[ xX]\]\s+|[-*+]\s+|\d+\.\s+|--\s+)?(.*)$", line)
    if not m:
        return [line]
    indent, marker, rest = m.groups()
    marker = marker or ""
    # wrap the rest of the text
    avail = max(20, width - len(indent) - len(marker))
    wrapped = textwrap.wrap(rest.strip(), width=avail)
    if not wrapped:
        return [line]
    out = [indent + marker + wrapped[0]]
    cont_indent = indent + (" " * len(marker))
    for w in wrapped[1:]:
        out.append(cont_indent + w)
    return out


def process_file(path: Path, width: int) -> bool:
    txt = path.read_text(encoding="utf-8")
    lines = txt.replace("\r\n", "\n").splitlines()
    out_lines: List[str] = []
    in_fence = False
    fence_re = re.compile(r"^\s*```")
    changed = False

    for ln in lines:
        if fence_re.match(ln):
            in_fence = not in_fence
            out_lines.append(ln)
            continue
        if in_fence or not should_wrap_line(ln, width):
            out_lines.append(ln)
            continue
        wrapped = wrap_line(ln, width)
        if len(wrapped) > 1 or wrapped[0] != ln:
            changed = True
        out_lines.extend(wrapped)

    if changed:
        new_txt = "\n".join(out_lines).rstrip("\n") + "\n"
        path.write_text(new_txt, encoding="utf-8")
    return changed


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="Files or directories to process")
    parser.add_argument("--width", type=int, default=100)
    args = parser.parse_args(list(argv) if argv else None)

    targets: List[Path] = []
    if args.paths:
        for p in args.paths:
            path = Path(p)
            if path.is_dir():
                targets.extend(find_md_files(path))
            else:
                targets.append(path)
    else:
        targets = list(find_md_files(Path(__file__).resolve().parent.parent))

    modified: List[Path] = []
    for t in sorted(set(targets)):
        if t.suffix.lower() != ".md":
            continue
        if process_file(t, args.width):
            modified.append(t)

    print(f"Checked {len(targets)} files; modified: {len(modified)}")
    if modified:
        print("Modified files:")
        root = Path(__file__).resolve().parent.parent
        for p in modified:
            try:
                print(" -", Path(p).resolve().relative_to(root))
            except Exception:
                print(" -", str(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
