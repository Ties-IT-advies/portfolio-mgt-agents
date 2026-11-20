"""Denylist I/O and hit-location formatting for the org-term scanner."""
from __future__ import annotations

import os
from pathlib import Path

_MAX_LINE_DISPLAY = 120


def load_denylist(path: Path) -> list[str]:
    """Parse denylist file: one term per line, # comments and blank lines ignored."""
    terms = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                terms.append(stripped)
    return terms


def load_denylist_env(var_name: str) -> list[str] | None:
    """Read denylist from env var; returns None if unset or empty."""
    raw = os.environ.get(var_name, "")
    if not raw.strip():
        return None
    terms = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            terms.append(stripped)
    return terms


def text_hit(label: str, lineno: int, content: str, locations_only: bool) -> str:
    if locations_only:
        return f"{label}:{lineno}"
    return f"{label}:{lineno}: {content.rstrip()[:_MAX_LINE_DISPLAY]}"


def docx_para_hit(label: str, para_idx: int, content: str, locations_only: bool) -> str:
    if locations_only:
        return f"{label}:paragraph {para_idx}"
    return f"{label}:paragraph {para_idx}: {content[:_MAX_LINE_DISPLAY]}"


def docx_table_hit(label: str, t_idx: int, r_idx: int, content: str, locations_only: bool) -> str:
    if locations_only:
        return f"{label}:table {t_idx} row {r_idx}"
    return f"{label}:table {t_idx} row {r_idx}: {content[:_MAX_LINE_DISPLAY]}"
