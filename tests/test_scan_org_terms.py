"""Tests for scan_org_terms.py."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"


def _load_scan():
    spec = importlib.util.spec_from_file_location(
        "idea_gate_scan_org_terms", _SCRIPTS / "scan_org_terms.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scan = _load_scan()


def _make_denylist(directory: Path, terms: list) -> Path:
    dl = directory / "denylist.txt"
    dl.write_text("\n".join(terms), encoding="utf-8")
    return dl


def test_hit_in_text_file(tmp_path):
    dl = _make_denylist(tmp_path, ["ACME", "Contoso"])
    target = tmp_path / "proposal.txt"
    target.write_text("This project is funded by ACME Corp.\n", encoding="utf-8")

    terms = scan.load_denylist(dl)
    pattern = scan.build_pattern(terms)
    hits = scan.scan_text_file(target, pattern)

    assert len(hits) == 1
    assert "proposal.txt" in hits[0]


def test_hit_in_docx(tmp_path):
    from docx import Document

    dl = _make_denylist(tmp_path, ["SecretCorp"])
    docx_path = tmp_path / "brief.docx"
    doc = Document()
    doc.add_paragraph("This is a normal paragraph.")
    doc.add_paragraph("SecretCorp is funding this initiative.")
    doc.save(str(docx_path))

    terms = scan.load_denylist(dl)
    pattern = scan.build_pattern(terms)
    hits = scan.scan_docx_file(docx_path, pattern)

    assert len(hits) == 1
    assert "paragraph 2" in hits[0]


def test_whole_word_no_false_positive(tmp_path):
    dl = _make_denylist(tmp_path, ["corp"])
    target = tmp_path / "text.txt"
    target.write_text("incorporate and corporation are not matches\n", encoding="utf-8")

    terms = scan.load_denylist(dl)
    pattern = scan.build_pattern(terms)
    hits = scan.scan_text_file(target, pattern)

    assert hits == []


def test_whole_word_matches_exact(tmp_path):
    dl = _make_denylist(tmp_path, ["corp"])
    target = tmp_path / "text.txt"
    target.write_text("The corp is here\n", encoding="utf-8")

    terms = scan.load_denylist(dl)
    pattern = scan.build_pattern(terms)
    hits = scan.scan_text_file(target, pattern)

    assert len(hits) == 1


def test_no_denylist_warning(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "denylist.txt"
    monkeypatch.setattr(scan, "denylist_path", lambda: missing)

    exit_code = scan.main(["--all"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Warning" in captured.err
    assert "denylist" in captured.err.lower()
