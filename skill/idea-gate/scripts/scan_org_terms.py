"""Org-term scanner — blocks pushes that expose terms from the local denylist."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from local_config import denylist_path  # noqa: E402

_MAX_LINE_DISPLAY = 120


def load_denylist(path: Path) -> list[str]:
    """Parse denylist: one term per line, # comments and blank lines ignored."""
    terms = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                terms.append(stripped)
    return terms


def build_pattern(terms: list[str]) -> re.Pattern:
    """Compile whole-word case-insensitive pattern matching any term."""
    alternation = "|".join(re.escape(t) for t in terms)
    return re.compile(rf"\b(?:{alternation})\b", re.IGNORECASE)


def _git(args: list[str]) -> str:
    result = subprocess.run(["git"] + args, capture_output=True, text=True, check=False)
    return result.stdout


def parse_added_lines(git_range: str) -> list[tuple[str, int, str]]:
    """Parse git diff, returning (filename, new_line_num, content) for added lines."""
    result = []
    current_file = ""
    new_line = 0
    for raw in _git(["diff", git_range]).splitlines():
        if raw.startswith("+++ b/"):
            current_file = raw[6:]
        elif raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            new_line = int(m.group(1)) - 1 if m else 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            new_line += 1
            result.append((current_file, new_line, raw[1:]))
        elif raw.startswith(" "):
            new_line += 1
    return result


def get_changed_filenames(git_range: str) -> list[str]:
    return [f for f in _git(["diff", "--name-only", git_range]).splitlines() if f]


def scan_push(git_range: str, pattern: re.Pattern) -> list[str]:
    hits = []
    for fname, lineno, content in parse_added_lines(git_range):
        if pattern.search(content):
            hits.append(f"{fname}:{lineno}: {content.rstrip()[:_MAX_LINE_DISPLAY]}")
    for name in get_changed_filenames(git_range):
        if pattern.search(name):
            hits.append(f"[filename]: {name}")
    return hits


def scan_text_file(path: Path, pattern: re.Pattern) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    hits = []
    for i, line in enumerate(lines, 1):
        if pattern.search(line):
            hits.append(f"{path}:{i}: {line.rstrip()[:_MAX_LINE_DISPLAY]}")
    return hits


def scan_docx_file(path: Path, pattern: re.Pattern) -> list[str]:
    from docx import Document
    hits = []
    try:
        doc = Document(str(path))
    except Exception:
        return []
    for i, para in enumerate(doc.paragraphs, 1):
        if para.text and pattern.search(para.text):
            hits.append(f"{path}:paragraph {i}: {para.text[:_MAX_LINE_DISPLAY]}")
    return hits


def scan_file(path: Path, pattern: re.Pattern) -> list[str]:
    if path.suffix.lower() == ".docx":
        return scan_docx_file(path, pattern)
    return scan_text_file(path, pattern)


def get_tracked_files() -> list[Path]:
    return [Path(p) for p in _git(["ls-files"]).splitlines() if p]


def scan_all(pattern: re.Pattern) -> list[str]:
    hits = []
    for path in get_tracked_files():
        if path.exists():
            hits.extend(scan_file(path, pattern))
    return hits


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Scan for org terms from local denylist.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--push", metavar="RANGE", help="Scan added lines in git range")
    group.add_argument("--all", action="store_true", help="Scan all tracked files")
    args = parser.parse_args(argv)

    dl = denylist_path()
    if not dl.exists():
        print(f"Warning: no denylist at {dl} — scan skipped.", file=sys.stderr)
        return 0

    terms = load_denylist(dl)
    if not terms:
        return 0
    pattern = build_pattern(terms)

    hits = scan_push(args.push, pattern) if args.push else scan_all(pattern)
    for hit in hits:
        print(hit)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
