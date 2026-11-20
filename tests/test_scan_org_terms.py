"""Tests for scan_org_terms.py."""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"

TERM = "acme"


def _load_scan():
    spec = importlib.util.spec_from_file_location(
        "idea_gate_scan_org_terms", _SCRIPTS / "scan_org_terms.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scan = _load_scan()
PATTERN = scan.build_pattern([TERM])


def _docx_with_table_cell(text: str) -> bytes:
    from docx import Document
    doc = Document()
    table = doc.add_table(rows=1, cols=1)
    table.cell(0, 0).text = text
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


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


# --- --locations-only: text file ---

def test_locations_only_text_has_location(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text(f"line with {TERM} in it\n")
    hits = scan.scan_text_file(f, PATTERN, locations_only=True)
    assert len(hits) == 1
    assert ":1" in hits[0]


def test_locations_only_text_no_term(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text(f"line with {TERM} in it\n")
    hits = scan.scan_text_file(f, PATTERN, locations_only=True)
    assert TERM.lower() not in hits[0].lower()


def test_locations_off_text_includes_term(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text(f"line with {TERM} in it\n")
    hits = scan.scan_text_file(f, PATTERN, locations_only=False)
    assert TERM.lower() in hits[0].lower()


# --- --locations-only: .docx table cell ---

def test_locations_only_docx_table_has_location():
    blob = _docx_with_table_cell(f"cell containing {TERM}")
    hits = scan.scan_docx_blob(blob, "report.docx", PATTERN, locations_only=True)
    assert len(hits) == 1
    assert "table" in hits[0]
    assert "row" in hits[0]


def test_locations_only_docx_table_no_term():
    blob = _docx_with_table_cell(f"cell containing {TERM}")
    hits = scan.scan_docx_blob(blob, "report.docx", PATTERN, locations_only=True)
    assert TERM.lower() not in hits[0].lower()


# --- --denylist-env reads from env var ---

def test_denylist_env_reads_terms(monkeypatch):
    monkeypatch.setenv("TEST_DENYLIST", f"{TERM}\n# comment\nsecondterm\n")
    result = scan.load_denylist_env("TEST_DENYLIST")
    assert result == [TERM, "secondterm"]


def test_denylist_env_ignores_comments_and_blanks(monkeypatch):
    monkeypatch.setenv("MY_VAR", "  \n# skip\n  term1  \n\n")
    result = scan.load_denylist_env("MY_VAR")
    assert result == ["term1"]


# --- unset variable warns and exits 0 ---

def test_unset_denylist_env_exits_zero(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    assert scan.main(["--all", "--denylist-env", "MISSING_VAR"]) == 0


def test_unset_denylist_env_warns(monkeypatch, capsys):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    scan.main(["--all", "--denylist-env", "MISSING_VAR"])
    err = capsys.readouterr().err
    assert "MISSING_VAR" in err
    assert "unset or empty" in err


def test_empty_denylist_env_exits_zero(monkeypatch):
    monkeypatch.setenv("EMPTY_VAR", "")
    assert scan.main(["--all", "--denylist-env", "EMPTY_VAR"]) == 0


# --- path containing the term ---

def test_scan_all_path_match_locations_only_no_term(tmp_path, monkeypatch):
    p = tmp_path / f"{TERM}-doc.txt"
    p.write_text("clean content\n")
    monkeypatch.setattr(scan, "get_tracked_files", lambda: [p])
    hits = scan.scan_all(PATTERN, locations_only=True)
    assert len(hits) == 1
    assert TERM.lower() not in hits[0].lower()


def test_scan_all_path_match_reported(tmp_path, monkeypatch):
    p = tmp_path / f"{TERM}-doc.txt"
    p.write_text("clean content\n")
    monkeypatch.setattr(scan, "get_tracked_files", lambda: [p])
    hits = scan.scan_all(PATTERN, locations_only=False)
    assert len(hits) == 1
    assert "[filename]:" in hits[0]


def test_scan_push_filename_match_locations_only_no_term(monkeypatch):
    monkeypatch.setattr(scan, "parse_added_lines", lambda _: [])
    monkeypatch.setattr(scan, "get_changed_filenames", lambda _: [f"docs/{TERM}-report.txt"])
    hits = scan.scan_push("abc..def", PATTERN, locations_only=True)
    assert len(hits) == 1
    assert TERM.lower() not in hits[0].lower()


def test_scan_push_filename_match_reported(monkeypatch):
    monkeypatch.setattr(scan, "parse_added_lines", lambda _: [])
    monkeypatch.setattr(scan, "get_changed_filenames", lambda _: [f"docs/{TERM}-report.txt"])
    hits = scan.scan_push("abc..def", PATTERN, locations_only=False)
    assert len(hits) == 1
    assert "[filename]:" in hits[0]
