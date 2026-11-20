"""Tests for the language detector."""
from __future__ import annotations

import importlib.util
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


def test_detect_empty_returns_unknown():
    assert mod.detect_language("") == "unknown"


def test_resolve_override_wins_over_dutch_detection():
    assert mod.resolve_language(DUTCH_TEXT, override="en") == "en"


def test_resolve_override_wins_over_english_detection():
    assert mod.resolve_language(ENGLISH_TEXT, override="nl") == "nl"


def test_resolve_no_override_detects_dutch():
    assert mod.resolve_language(DUTCH_TEXT) == "nl"


def test_resolve_no_override_detects_english():
    assert mod.resolve_language(ENGLISH_TEXT) == "en"


def test_resolve_invalid_override_raises():
    with pytest.raises(ValueError, match="Unsupported language override"):
        mod.resolve_language(ENGLISH_TEXT, override="fr")


def test_resolve_unknown_passthrough():
    assert mod.resolve_language("Dit is een kort stukje.") == "unknown"
