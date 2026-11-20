"""Tests for scan_org_terms.py."""
from __future__ import annotations

import importlib.util
import io
import subprocess
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


@pytest.fixture
def git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)
    return repo


def _commit(repo: Path, files: dict, msg: str = "change") -> str:
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=repo, check=True, capture_output=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()


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


def test_hit_in_docx_table(tmp_path):
    from docx import Document

    dl = _make_denylist(tmp_path, ["SecretCorp"])
    docx_path = tmp_path / "brief.docx"
    doc = Document()
    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Normal cell"
    table.rows[1].cells[1].text = "SecretCorp in table"
    doc.save(str(docx_path))

    terms = scan.load_denylist(dl)
    pattern = scan.build_pattern(terms)
    hits = scan.scan_docx_file(docx_path, pattern)

    assert len(hits) == 1
    assert "table 1 row 2" in hits[0]


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


def test_push_hits_added_text_line(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    base = _commit(git_repo, {"base.txt": "nothing here"}, "base")
    head = _commit(git_repo, {"added.txt": "ACME funded this project"}, "add")

    pattern = scan.build_pattern(["ACME"])
    hits = scan.scan_push(f"{base}..{head}", pattern)

    assert len(hits) == 1
    assert "added.txt" in hits[0]
    assert "ACME" in hits[0]


def test_push_hits_docx_table_cell(git_repo, monkeypatch):
    from docx import Document

    monkeypatch.chdir(git_repo)
    base = _commit(git_repo, {"base.txt": "nothing"}, "base")

    doc = Document()
    table = doc.add_table(rows=1, cols=1)
    table.rows[0].cells[0].text = "SecretCorp in table"
    bio = io.BytesIO()
    doc.save(bio)
    head = _commit(git_repo, {"report.docx": bio.getvalue()}, "add docx")

    pattern = scan.build_pattern(["SecretCorp"])
    hits = scan.scan_push(f"{base}..{head}", pattern)

    assert any("table" in h for h in hits)


def test_push_clean_no_hits(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    base = _commit(git_repo, {"base.txt": "nothing"}, "base")
    head = _commit(git_repo, {"added.txt": "clean content here"}, "add")

    pattern = scan.build_pattern(["ACME"])
    hits = scan.scan_push(f"{base}..{head}", pattern)

    assert hits == []


def test_push_invalid_range_exits_2(git_repo, monkeypatch, capsys):
    monkeypatch.chdir(git_repo)
    _commit(git_repo, {"base.txt": "nothing"}, "base")

    dl = git_repo / "denylist.txt"
    dl.write_text("ACME", encoding="utf-8")
    monkeypatch.setattr(scan, "denylist_path", lambda: dl)

    exit_code = scan.main(["--push", "deadbeef..cafebabe"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Error" in captured.err
