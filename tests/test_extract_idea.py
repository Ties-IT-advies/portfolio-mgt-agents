"""Tests for extract_idea.py."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml
from docx import Document

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"
_FIXTURES = Path(__file__).parent / "fixtures"
_SAMPLES_DIR = _FIXTURES / "samples"

_V12_FIELD_IDS = [
    "prepared_by", "date", "status",
    "background", "objective", "sponsor", "people_involved",
    "costs", "budget", "benefits", "timelines", "risks",
    "strategic_contribution", "departments_involved", "complexity",
]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "extract_idea", _SCRIPTS / "extract_idea.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


extract_mod = _load_module()


def _make_docx_with_unicode_answer(tmp_path: Path) -> Path:
    """Return a .docx with a recognized field containing the ✓ character."""
    doc = Document()
    p = doc.add_paragraph()
    p.add_run("Project IDEE: Unicode Test")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Achtergrond"
    table.cell(0, 1).text = "Testachtergrond ✓"
    path = tmp_path / "unicode_test.docx"
    doc.save(str(path))
    return path


def test_sample_project_name():
    result = extract_mod.extract(_FIXTURES / "idea-v12-sample.docx")
    assert result["project_name"] == "Digitaal Klantportaal"


def test_sample_header_fields():
    result = extract_mod.extract(_FIXTURES / "idea-v12-sample.docx")
    assert result["fields"]["prepared_by"] == "J. de Vries, Projectleider"
    assert result["fields"]["date"] == "2024-01-15"
    assert result["fields"]["status"] == "Concept"


def test_sample_all_12_body_answers():
    with (_SAMPLES_DIR / "sample.yaml").open(encoding="utf-8") as f:
        expected = yaml.safe_load(f)

    result = extract_mod.extract(_FIXTURES / "idea-v12-sample.docx")

    for fid, value in expected.get("header", {}).items():
        assert result["fields"].get(fid) == value, (
            f"Header field {fid!r}: expected {value!r}, got {result['fields'].get(fid)!r}"
        )
    for fid, value in expected.get("body", {}).items():
        assert result["fields"].get(fid) == value, (
            f"Body field {fid!r}: expected {value!r}, got {result['fields'].get(fid)!r}"
        )


def test_blank_all_answers_empty():
    result = extract_mod.extract(_FIXTURES / "idea-v12-blank.docx")
    for fid in _V12_FIELD_IDS:
        assert fid in result["fields"], f"Field {fid!r} missing from blank extraction"
    for fid in _V12_FIELD_IDS:
        assert result["fields"][fid] == "", f"Expected empty for {fid!r}, got {result['fields'][fid]!r}"


def test_blank_project_name_empty():
    result = extract_mod.extract(_FIXTURES / "idea-v12-blank.docx")
    assert result["project_name"] == ""


def test_unknown_label_in_unmatched(tmp_path):
    doc = Document()
    p = doc.add_paragraph()
    p.add_run("Project IDEE: TestProject")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Onbekend Veld"
    table.cell(0, 1).text = "Antwoord"
    path = tmp_path / "test.docx"
    doc.save(str(path))

    result = extract_mod.extract(path)
    assert "Onbekend Veld" in result["unmatched_labels"]
    assert "Onbekend Veld" not in str(result["fields"])


def test_known_labels_not_in_unmatched():
    result = extract_mod.extract(_FIXTURES / "idea-v12-sample.docx")
    assert result["unmatched_labels"] == []


def test_stdout_utf8_in_cp1252_env(tmp_path):
    """Script must not crash when terminal reports cp1252 encoding."""
    docx_path = _make_docx_with_unicode_answer(tmp_path)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    env["PYTHONUTF8"] = "0"

    result = subprocess.run(
        [sys.executable, str(_SCRIPTS / "extract_idea.py"), str(docx_path)],
        capture_output=True,
        env=env,
    )

    assert result.returncode == 0, f"Script failed:\n{result.stderr.decode('utf-8', errors='replace')}"
    output = result.stdout.decode("utf-8")
    assert "✓" in output


def test_out_flag_writes_utf8_json(tmp_path):
    """--out writes valid UTF-8 JSON to path and nothing to stdout."""
    docx_path = _make_docx_with_unicode_answer(tmp_path)
    out_path = tmp_path / "output.answers.json"

    result = subprocess.run(
        [
            sys.executable, str(_SCRIPTS / "extract_idea.py"),
            str(docx_path), "--out", str(out_path),
        ],
        capture_output=True,
    )

    assert result.returncode == 0, f"Script failed:\n{result.stderr.decode('utf-8', errors='replace')}"
    assert result.stdout == b""
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "✓" in data["fields"].get("background", "")
