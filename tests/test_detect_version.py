"""Tests for detect_version.py and v9 fixture extraction."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"
_FIXTURES = Path(__file__).parent / "fixtures"
_FIELDS_PATH = Path(__file__).parent.parent / "skill" / "idea-gate" / "fields.yaml"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


detect_version_mod = _load_module("detect_version", _SCRIPTS / "detect_version.py")
extract_mod = _load_module("extract_idea", _SCRIPTS / "extract_idea.py")

_V12_ONLY_IDS = detect_version_mod._load_v12_only_ids(_FIELDS_PATH)


def _get_v9_field_ids():
    with _FIELDS_PATH.open(encoding="utf-8") as f:
        registry = yaml.safe_load(f)["fields"]
    return [field["id"] for field in registry if "v9" in field["versions"]]


# --- Extraction tests ---

def test_v9_fixture_nl_all_v9_fields_extracted():
    answers = extract_mod.extract(_FIXTURES / "idea-v9-sample.docx")
    for fid in _get_v9_field_ids():
        assert fid in answers["fields"], f"v9 field {fid!r} missing from NL extraction"


def test_v9_fixture_nl_missing_fields_are_v12_only():
    answers = extract_mod.extract(_FIXTURES / "idea-v9-sample.docx")
    assert sorted(answers["missing_fields"]) == sorted(_V12_ONLY_IDS)


def test_v9_fixture_en_all_v9_fields_extracted():
    answers = extract_mod.extract(_FIXTURES / "idea-v9-sample-en.docx")
    for fid in _get_v9_field_ids():
        assert fid in answers["fields"], f"v9 field {fid!r} missing from EN extraction"


def test_v9_fixture_en_missing_fields_are_v12_only():
    answers = extract_mod.extract(_FIXTURES / "idea-v9-sample-en.docx")
    assert sorted(answers["missing_fields"]) == sorted(_V12_ONLY_IDS)


# --- Version detection tests ---

def test_v9_fixture_nl_detected_as_v9():
    answers = extract_mod.extract(_FIXTURES / "idea-v9-sample.docx")
    assert detect_version_mod.detect_version(answers, _V12_ONLY_IDS) == "v9"


def test_v9_fixture_en_detected_as_v9():
    answers = extract_mod.extract(_FIXTURES / "idea-v9-sample-en.docx")
    assert detect_version_mod.detect_version(answers, _V12_ONLY_IDS) == "v9"


@pytest.mark.parametrize("fixture_name", [
    "idea-v12-sample.docx",
    "idea-v12-sample-en.docx",
    "idea-v12-blank.docx",
    "idea-v12-mixed.docx",
    "idea-v12-weak.docx",
    "idea-v12-uncertainty.docx",
    "idea-v12-uncertainty-en.docx",
])
def test_v12_fixture_detected_as_v12(fixture_name):
    answers = extract_mod.extract(_FIXTURES / fixture_name)
    assert detect_version_mod.detect_version(answers, _V12_ONLY_IDS) == "v12"


def test_partial_v12_detected_as_v12():
    """A v12 doc with only one v12-only field present is still classified as v12."""
    answers = {
        "project_name": "Test",
        "fields": {"background": "some text", "strategic_contribution": "some text"},
        "unmatched_labels": [],
        "missing_fields": [],
    }
    assert detect_version_mod.detect_version(answers, _V12_ONLY_IDS) == "v12"


def test_no_v12_only_fields_detected_as_v9():
    answers = {
        "project_name": "Test",
        "fields": {"background": "text", "objective": "text", "risks": "text"},
        "unmatched_labels": [],
        "missing_fields": [],
    }
    assert detect_version_mod.detect_version(answers, _V12_ONLY_IDS) == "v9"


def test_v12_only_ids_matches_fields_yaml():
    assert set(_V12_ONLY_IDS) == {"strategic_contribution", "departments_involved", "complexity"}


def test_cli_v9_outputs_v9(tmp_path):
    answers = extract_mod.extract(_FIXTURES / "idea-v9-sample.docx")
    answers_path = tmp_path / "v9.answers.json"
    answers_path.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_SCRIPTS / "detect_version.py"), str(answers_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "v9"
