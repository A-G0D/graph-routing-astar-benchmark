"""Lints tracked markdown/Python files for common AI-writing tells and leaked
tool-call artifacts. Stdlib only, no dependencies.

Usage: python scripts/check_prose.py [path ...]

With no arguments it scans every tracked .md and .py file under the repo root
(via ``git ls-files``, falling back to a plain directory walk if git isn't
available). Exits 1 and prints ``file:line: reason`` for each hit, 0 if clean.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXTENSIONS = {".md", ".py"}

# (label, compiled pattern)
PATTERNS = [
    ("em-dash", re.compile("—")),
    ("leaked tool-call artifact", re.compile(
        r"</invoke>|<function>|</function>|<parameter>|</parameter>|"
        r"tool_use|</content>|<invoke\b"
    )),
    ("employer/internal-tool reference", re.compile(
        r"\bGSS\b|Global Shop|gssmail|fact.graph|brain.vault|livefire",
        re.IGNORECASE,
    )),
]


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        paths = [ROOT / line for line in out.stdout.splitlines() if line.strip()]
        return [
            p for p in paths
            if p.suffix in EXTENSIONS and p.is_file() and p != Path(__file__).resolve()
        ]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [
            p for p in ROOT.rglob("*")
            if p.suffix in EXTENSIONS and p.is_file() and p != Path(__file__).resolve()
        ]


def scan(paths: list[Path]) -> list[str]:
    hits: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for label, pattern in PATTERNS:
                if pattern.search(line):
                    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
                    hits.append(f"{rel}:{lineno}: {label}: {line.strip()}")
    return hits


def main() -> int:
    args = sys.argv[1:]
    paths = [Path(a) for a in args] if args else tracked_files()
    hits = scan(paths)
    if hits:
        for hit in hits:
            print(hit)
        print(f"\n{len(hits)} issue(s) found.")
        return 1
    print("clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
