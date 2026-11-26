"""Tests for the language detector."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"


def _load_detect_language():
    spec = importlib.util.spec_from_file_location(
        "detect_language", _SCRIPTS / "detect_language.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_detect_language()

DUTCH_TEXT = (
    "Het project wil de samenwerking tussen de afdelingen verbeteren door "
    "een nieuw systeem te bouwen. Dit is een van de belangrijkste doelen "
    "van het management en moet worden afgerond voor het einde van het jaar."
)

ENGLISH_TEXT = (
    "The project aims to improve collaboration between departments by "
    "building a new system. This is one of the key goals of management "
    "and must be completed before the end of the year."
)


def test_detect_clear_dutch():
    assert mod.detect_language(DUTCH_TEXT) == "nl"


def test_detect_clear_english():
    assert mod.detect_language(ENGLISH_TEXT) == "en"


def test_detect_too_short_returns_unknown():
    assert mod.detect_language("Dit is een kort stukje.") == "unknown"


def test_detect_mixed_returns_unknown():
    # Roughly equal Dutch and English stop-word density — neither dominates.
    mixed = (
        "the de van it that het a for een to be but met als zou ze "
        "this or and they can which their"
    )
    assert mod.detect_language(mixed) == "unknown"


def test_detect_empty_returns_en():
    # Empty document has no language; English is canonical per DEC-008.
    assert mod.detect_language("") == "en"


def test_detect_whitespace_only_returns_en():
    # Whitespace-only text tokenizes to zero words — same rule as empty.
    assert mod.detect_language("   \t\n  ") == "en"


def test_detect_short_nonzero_text_returns_unknown():
    # Fewer than MIN_WORD_COUNT words but not zero: still unknown.
    assert mod.detect_language("Short text here.") == "unknown"


def test_diacritic_word_not_split_into_stop_word():
    # With [a-z]+ tokenizer "Creër" splits into ["cre", "er"]; "er" is a
    # Dutch stop-word, producing a false Dutch detection. With [^\W\d_]+
    # the whole word is kept as one token and no stop-word is hit.
    text = " ".join(["Creër"] * 15)
    assert mod.detect_language(text) == "unknown"


def test_resolve_override_wins_over_dutch_detection():
    assert mod.resolve_language(DUTCH_TEXT, override="en") == "en"


def test_resolve_override_wins_over_english_detection():
    assert mod.resolve_language(ENGLISH_TEXT, override="nl") == "nl"


def test_resolve_override_wins_over_empty_text():
    # Override must beat the empty-document default too.
    assert mod.resolve_language("", override="nl") == "nl"


def test_resolve_no_override_detects_dutch():
    assert mod.resolve_language(DUTCH_TEXT) == "nl"


def test_resolve_no_override_detects_english():
    assert mod.resolve_language(ENGLISH_TEXT) == "en"


def test_resolve_invalid_override_raises():
    with pytest.raises(ValueError, match="Unsupported language override"):
        mod.resolve_language(ENGLISH_TEXT, override="fr")


def test_resolve_unknown_passthrough():
    assert mod.resolve_language("Dit is een kort stukje.") == "unknown"


def test_cli_detects_dutch(tmp_path):
    answers = {"fields": {"field1": DUTCH_TEXT}}
    p = tmp_path / "test.answers.json"
    p.write_text(json.dumps(answers), encoding="utf-8")
    result = subprocess.run(
        ["python", str(_SCRIPTS / "detect_language.py"), str(p)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "nl"


def test_cli_override_en(tmp_path):
    answers = {"fields": {"field1": DUTCH_TEXT}}
    p = tmp_path / "test.answers.json"
    p.write_text(json.dumps(answers), encoding="utf-8")
    result = subprocess.run(
        ["python", str(_SCRIPTS / "detect_language.py"), str(p), "--override", "en"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "en"


def test_cli_all_empty_answers_returns_en(tmp_path):
    # Blank fixture: every field is empty or whitespace — must return en.
    answers = {"fields": {"field1": "", "field2": "   ", "field3": ""}}
    p = tmp_path / "test.answers.json"
    p.write_text(json.dumps(answers), encoding="utf-8")
    result = subprocess.run(
        ["python", str(_SCRIPTS / "detect_language.py"), str(p)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "en"
