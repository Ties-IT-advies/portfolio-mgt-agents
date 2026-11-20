"""Tests for --locations-only and --denylist-env in scan_org_terms."""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from org_terms_io import load_denylist_env  # noqa: E402
from scan_org_terms import build_pattern, main, scan_docx_blob, scan_text_file  # noqa: E402

TERM = "acme"
PATTERN = build_pattern([TERM])


# --- --locations-only: text file ---

def test_locations_only_text_has_location(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text(f"line with {TERM} in it\n")
    hits = scan_text_file(f, PATTERN, locations_only=True)
    assert len(hits) == 1
    assert ":1" in hits[0]


def test_locations_only_text_no_term(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text(f"line with {TERM} in it\n")
    hits = scan_text_file(f, PATTERN, locations_only=True)
    assert TERM.lower() not in hits[0].lower()


def test_locations_off_text_includes_term(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text(f"line with {TERM} in it\n")
    hits = scan_text_file(f, PATTERN, locations_only=False)
    assert TERM.lower() in hits[0].lower()


# --- --locations-only: .docx table cell ---

def _docx_with_table_cell(text: str) -> bytes:
    from docx import Document
    doc = Document()
    table = doc.add_table(rows=1, cols=1)
    table.cell(0, 0).text = text
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_locations_only_docx_table_has_location():
    blob = _docx_with_table_cell(f"cell containing {TERM}")
    hits = scan_docx_blob(blob, "report.docx", PATTERN, locations_only=True)
    assert len(hits) == 1
    assert "table" in hits[0]
    assert "row" in hits[0]


def test_locations_only_docx_table_no_term():
    blob = _docx_with_table_cell(f"cell containing {TERM}")
    hits = scan_docx_blob(blob, "report.docx", PATTERN, locations_only=True)
    assert TERM.lower() not in hits[0].lower()


# --- --denylist-env reads from monkeypatched env var ---

def test_denylist_env_reads_terms(monkeypatch):
    monkeypatch.setenv("TEST_DENYLIST", f"{TERM}\n# comment\nsecondterm\n")
    result = load_denylist_env("TEST_DENYLIST")
    assert result == [TERM, "secondterm"]


def test_denylist_env_ignores_comments_and_blanks(monkeypatch):
    monkeypatch.setenv("MY_VAR", "  \n# skip\n  term1  \n\n")
    result = load_denylist_env("MY_VAR")
    assert result == ["term1"]


# --- unset variable warns and exits 0 ---

def test_unset_denylist_env_exits_zero(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    assert main(["--all", "--denylist-env", "MISSING_VAR"]) == 0


def test_unset_denylist_env_warns(monkeypatch, capsys):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    main(["--all", "--denylist-env", "MISSING_VAR"])
    err = capsys.readouterr().err
    assert "MISSING_VAR" in err
    assert "unset or empty" in err


def test_empty_denylist_env_exits_zero(monkeypatch):
    monkeypatch.setenv("EMPTY_VAR", "")
    assert main(["--all", "--denylist-env", "EMPTY_VAR"]) == 0
