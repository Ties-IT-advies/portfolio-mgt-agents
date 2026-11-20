"""Org-term scanner — blocks pushes that expose terms from the local denylist."""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from local_config import denylist_path  # noqa: E402
from org_terms_io import (  # noqa: E402
    docx_para_hit,
    docx_table_hit,
    load_denylist,
    load_denylist_env,
    text_hit,
)


def build_pattern(terms: list[str]) -> re.Pattern:
    """Compile whole-word case-insensitive pattern matching any term."""
    alternation = "|".join(re.escape(t) for t in terms)
    return re.compile(rf"\b(?:{alternation})\b", re.IGNORECASE)


def _git(args: list[str]) -> str:
    result = subprocess.run(["git"] + args, capture_output=True, text=True, check=True)
    return result.stdout


def _git_bytes(args: list[str]) -> bytes:
    result = subprocess.run(["git"] + args, capture_output=True, check=True)
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


def _scan_docx_content(doc, label: str, pattern: re.Pattern, locations_only: bool = False) -> list[str]:
    hits = []
    for i, para in enumerate(doc.paragraphs, 1):
        if para.text and pattern.search(para.text):
            hits.append(docx_para_hit(label, i, para.text, locations_only))
    for t_idx, table in enumerate(doc.tables, 1):
        for r_idx, row in enumerate(table.rows, 1):
            for cell in row.cells:
                for para in cell.paragraphs:
                    if para.text and pattern.search(para.text):
                        hits.append(docx_table_hit(label, t_idx, r_idx, para.text, locations_only))
    return hits


def scan_docx_file(path: Path, pattern: re.Pattern, locations_only: bool = False, label: str | None = None) -> list[str]:
    from docx import Document
    try:
        doc = Document(str(path))
    except Exception:
        return []
    return _scan_docx_content(doc, label or str(path), pattern, locations_only)


def scan_docx_blob(blob: bytes, label: str, pattern: re.Pattern, locations_only: bool = False) -> list[str]:
    from docx import Document
    try:
        doc = Document(io.BytesIO(blob))
    except Exception:
        return []
    return _scan_docx_content(doc, label, pattern, locations_only)


def scan_text_file(path: Path, pattern: re.Pattern, locations_only: bool = False, label: str | None = None) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    hits = []
    for i, line in enumerate(lines, 1):
        if pattern.search(line):
            hits.append(text_hit(label or str(path), i, line, locations_only))
    return hits


def scan_file(path: Path, pattern: re.Pattern, locations_only: bool = False, label: str | None = None) -> list[str]:
    if path.suffix.lower() == ".docx":
        return scan_docx_file(path, pattern, locations_only, label)
    return scan_text_file(path, pattern, locations_only, label)


def get_tracked_files() -> list[Path]:
    return [Path(p) for p in _git(["ls-files"]).splitlines() if p]


def scan_all(pattern: re.Pattern, locations_only: bool = False) -> list[str]:
    hits = []
    for idx, path in enumerate(get_tracked_files(), 1):
        if not path.exists():
            continue
        path_str = str(path)
        path_hits = bool(pattern.search(path_str))
        label = f"[redacted path: tracked file #{idx}]" if (locations_only and path_hits) else path_str
        if path_hits:
            hits.append(label if locations_only else f"[filename]: {path_str}")
        hits.extend(scan_file(path, pattern, locations_only, label=label))
    return hits


def scan_push(git_range: str, pattern: re.Pattern, locations_only: bool = False) -> list[str]:
    hits = []
    head_sha = git_range.split("..")[-1]
    names = get_changed_filenames(git_range)
    labels = {}
    for idx, name in enumerate(names, 1):
        name_hits = bool(pattern.search(name))
        labels[name] = f"[redacted path: changed file #{idx}]" if (locations_only and name_hits) else name
    for fname, lineno, content in parse_added_lines(git_range):
        if pattern.search(content):
            label = labels.get(fname, fname)
            hits.append(text_hit(label, lineno, content, locations_only))
    for name in names:
        name_hits = bool(pattern.search(name))
        label = labels[name]
        if name_hits:
            hits.append(label if locations_only else f"[filename]: {name}")
        if name.lower().endswith(".docx"):
            try:
                blob = _git_bytes(["show", f"{head_sha}:{name}"])
            except subprocess.CalledProcessError:
                continue
            hits.extend(scan_docx_blob(blob, label, pattern, locations_only))
    return hits


def _load_terms(args: argparse.Namespace) -> list[str] | None:
    """Load terms from env var or file. Returns None to signal warn-and-skip."""
    if args.denylist_env:
        terms = load_denylist_env(args.denylist_env)
        if terms is None:
            print(f"Warning: {args.denylist_env} is unset or empty — scan skipped.", file=sys.stderr)
        return terms
    dl = denylist_path()
    if not dl.exists():
        print(f"Warning: no denylist at {dl} — scan skipped.", file=sys.stderr)
        return None
    return load_denylist(dl)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Scan for org terms.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--push", metavar="RANGE", help="Scan added lines in git range")
    group.add_argument("--all", action="store_true", help="Scan all tracked files")
    parser.add_argument(
        "--locations-only",
        action="store_true",
        help="Output file:line locations only — no matched text",
    )
    parser.add_argument(
        "--denylist-env",
        metavar="VAR",
        help="Read denylist from environment variable VAR instead of local file",
    )
    args = parser.parse_args(argv)

    terms = _load_terms(args)
    if terms is None:
        return 0
    if not terms:
        return 0
    pattern = build_pattern(terms)

    try:
        hits = (
            scan_push(args.push, pattern, args.locations_only)
            if args.push
            else scan_all(pattern, args.locations_only)
        )
    except subprocess.CalledProcessError as exc:
        print(f"Error: git command failed ({exc.returncode}) — push blocked for safety.", file=sys.stderr)
        return 2

    for hit in hits:
        print(hit)
    if hits and args.locations_only:
        print(f"{len(hits)} hit(s).", file=sys.stderr)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
