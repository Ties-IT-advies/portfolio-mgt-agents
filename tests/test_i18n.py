"""Tests for the locale loader."""
import importlib.util
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"


def _load_locale():
    spec = importlib.util.spec_from_file_location(
        "idea_gate_locale", _SCRIPTS / "locale.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


locale_mod = _load_locale()


def test_ratings_point_of_attention_nl():
    assert locale_mod.text("ratings.point_of_attention", "nl") == "Aandachtspunt"


def test_ratings_sufficient_en():
    assert locale_mod.text("ratings.sufficient", "en") == "Sufficient"


def test_all_core_vocab_en():
    expected = {
        "ratings.sufficient": "Sufficient",
        "ratings.point_of_attention": "Point of Attention",
        "ratings.insufficient": "Insufficient",
        "classification.not_a_project": "Not a project",
        "classification.normal_project": "Normal project",
        "classification.portfolio_project": "Portfolio project",
        "board_advice.title": "Advice to the Portfolio Board",
    }
    for key, val in expected.items():
        assert locale_mod.text(key, "en") == val


def test_all_core_vocab_nl():
    expected = {
        "ratings.sufficient": "Voldoende",
        "ratings.point_of_attention": "Aandachtspunt",
        "ratings.insufficient": "Onvoldoende",
        "classification.not_a_project": "Geen project",
        "classification.normal_project": "Normaal project",
        "classification.portfolio_project": "Portfolioproject",
        "board_advice.title": "Advies aan de Portfolio Board",
    }
    for key, val in expected.items():
        assert locale_mod.text(key, "nl") == val


def test_field_label_en():
    assert locale_mod.text("fields.date.label", "en") == "Date"


def test_field_label_nl():
    assert locale_mod.text("fields.date.label", "nl") == "Datum"


def test_unknown_key_raises():
    with pytest.raises(KeyError, match="not found"):
        locale_mod.text("ratings.nonexistent", "en")


def test_unsupported_language_raises():
    with pytest.raises(ValueError, match="Unsupported language"):
        locale_mod.text("ratings.sufficient", "fr")


def test_non_string_key_raises():
    with pytest.raises(KeyError, match="non-string"):
        locale_mod.text("fields.strategic_contribution.objectives", "en")
