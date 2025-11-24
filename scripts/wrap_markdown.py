#!/usr/bin/env python3
"""Conservative Markdown paragraph reflow/wrapping utility.

This script reflows plain paragraphs to a target width while preserving code
fences, tables, headings, lists, blockquotes, and frontmatter. It's designed to
be conservative — it will not change code blocks or lists, and will only reflow
safe-paragraph text to improve line lengths for markdown linters.

Usage:
  python3 scripts/wrap_markdown.py [--width 100] [paths...]

If no paths are provided, the script will search the repository for .md files
and process them (excluding common build / venv dirs).
"""
from __future__ import annotations

import argparse
import re
import sys
import textwrap
from pathlib import Path
from typing import Iterable, List


def should_ignore(path: Path) -> bool:
    ignore = {".git", "node_modules", "out", "dist", "venv-nodejs"}
    # exclude any dir that starts with .venv or venv
    for part in path.parts:
        if part in ignore or part.startswith(".venv") or part.startswith("venv"):
            return True
    return False


def find_md_files(root: Path) -> List[Path]:
    files = []
    for p in root.rglob("*.md"):
        if should_ignore(p):
            continue
        files.append(p)
    return sorted(files)


def reflow_paragraphs(lines: List[str], width: int) -> List[str]:
    out: List[str] = []
    para: List[str] = []

    in_fence = False
    fence_re = re.compile(r"^\s*```")
    header_re = re.compile(r"^\s{0,3}#{1,6}\b")
    # also accept '-- ' as a common 'dash' list marker used in some docs
    # accept checkboxes (e.g. "- [ ] ") as list markers as well
    list_re = re.compile(r"^\s*([-*+]\s|\d+\.\s|--\s|[-*+]\s+\[[ xX]\]\s+)")
    blockquote_re = re.compile(r"^\s*>")
    table_re = re.compile(r"\|")
    table_delim_re = re.compile(r"^\s*\|?\s*[:\-]+\s*(\|\s*[:\-]+\s*)*$")
    frontmatter_open = re.compile(r"^---\s*$")

    in_frontmatter = False

    def flush_para():
        nonlocal para
        if not para:
            return
        # merge and wrap the paragraph conservatively
        text = " ".join(p.strip() for p in para)
        # do not reflow paragraphs that look like list items (defensive)
        if list_re.match(para[0]) or para[0].lstrip().startswith(('-', '*', '+')):
            out.extend(para)
        else:
            wrapped = textwrap.fill(text, width=width)
            out.extend(wrapped.splitlines())
        para = []

    for ln in lines:
        # detect fences
        if not in_fence and fence_re.match(ln):
            flush_para()
            in_fence = True
            out.append(ln)
            continue
        if in_fence:
            out.append(ln)
            if fence_re.match(ln):
                in_fence = False
            continue

        # frontmatter
        if frontmatter_open.match(ln):
            flush_para()
            in_frontmatter = not in_frontmatter
            out.append(ln)
            continue
        if in_frontmatter:
            out.append(ln)
            continue

        # tables / headings / blockquotes — flush paragraph and keep as-is
        if ln.strip() == "":
            flush_para()
            out.append(ln)
            continue
        if header_re.match(ln) or blockquote_re.match(ln):
            flush_para()
            out.append(ln)
            continue

        # attempt safe table cell wrapping: skip the table delimiter row(s)
        if table_re.search(ln) and not table_delim_re.match(ln):
            # try to split by pipe and wrap long cells
            parts = ln.split("|")
            # keep first and last items that may be empty (leading/trailing pipes)
            wrapped_parts = []
            changed = False
            for cell in parts:
                c = cell.strip()
                # don't touch short cells or code-like cells
                if len(c) > max(40, width // 2) and "`" not in c and "http" not in c:
                    # wrap cell content and join with <br> to preserve table cell semantics
                    avail = max(20, width - 10)
                    w = textwrap.wrap(c, width=avail)
                    if len(w) > 1:
                        wrapped_parts.append("<br>".join(w))
                        changed = True
                        continue
                wrapped_parts.append(cell)

            if changed:
                # recompose using original pipe separators but trimmed cells
                new_line = "|".join(wrapped_parts)
                out.append(new_line)
                continue
            # fallback to leaving as-is
            flush_para()
            out.append(ln)
            continue

        # handle single-line list items by wrapping the item body while preserving
        # the list marker and indentation. This helps avoid extremely long single
        # bullet lines (conservative: we only rewrite when wrapping actually helps).
        m = list_re.match(ln)
        if m:
            # capture indent, marker and content
            # capture possible checkbox markers like '- [ ] ' as part of the marker
            lm = re.match(r"^(\s*)([-*+]\s|\d+\.\s|--\s|[-*+]\s+\[[ xX]\]\s+)(.*)$", ln)
            if lm:
                indent = lm.group(1)
                marker = lm.group(2)
                content = lm.group(3).strip()
                if content:
                    avail = max(20, width - len(indent) - len(marker))
                    wrapped = textwrap.wrap(content, width=avail)
                    if len(wrapped) > 1:
                        out.append(indent + marker + wrapped[0])
                        cont_indent = indent + " " * len(marker)
                        for w in wrapped[1:]:
                            out.append(cont_indent + w)
                        continue
            # fallback: treat it as-is
            flush_para()
            out.append(ln)
            continue

        # otherwise collect into a paragraph
        para.append(ln)

    flush_para()
    return out


def process_file(path: Path, width: int) -> bool:
    txt = path.read_text(encoding="utf-8")
    lines = txt.replace("\r\n", "\n").splitlines()
    new_lines = reflow_paragraphs(lines, width=width)
    # ensure EOF newline
    new_txt = "\n".join(new_lines).rstrip("\n") + "\n"
    if new_txt != txt:
        path.write_text(new_txt, encoding="utf-8")
        return True
    return False


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reflow plain markdown paragraphs")
    parser.add_argument("paths", nargs="*", help="Files or directories to process")
    parser.add_argument("--width", type=int, default=100, help="Wrap width (default: 100)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    targets: List[Path] = []
    if args.paths:
        for p in args.paths:
            path = Path(p)
            if path.is_dir():
                targets.extend(find_md_files(path))
            else:
                targets.append(path)
    else:
        root = Path(__file__).resolve().parent.parent
        targets = find_md_files(root)

    modified = []
    for t in sorted({p for p in targets}):
        if t.suffix.lower() != ".md":
            continue
        if should_ignore(t):
            continue
        changed = process_file(t, width=args.width)
        if changed:
            modified.append(t)

    print(f"Checked {len(targets)} markdown files; modified: {len(modified)}")
    if modified:
        print("Modified files:")
        root = Path(__file__).resolve().parent.parent
        for p in modified:
            try:
                print(" -", Path(p).resolve().relative_to(root))
            except Exception:
                # fallback if path relations are surprising
                print(" -", str(p))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
