"""Tests for the locale loader."""
import importlib.util
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"


def _load_i18n():
    spec = importlib.util.spec_from_file_location(
        "idea_gate_i18n", _SCRIPTS / "i18n.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


i18n_mod = _load_i18n()


def test_ratings_point_of_attention_nl():
    assert i18n_mod.text("ratings.point_of_attention", "nl") == "Aandachtspunt"


def test_ratings_sufficient_en():
    assert i18n_mod.text("ratings.sufficient", "en") == "Sufficient"


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
        assert i18n_mod.text(key, "en") == val


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
        assert i18n_mod.text(key, "nl") == val


def test_field_label_en():
    assert i18n_mod.text("fields.date.label", "en") == "Date"


def test_field_label_nl():
    assert i18n_mod.text("fields.date.label", "nl") == "Datum"


def test_unknown_key_raises():
    with pytest.raises(KeyError, match="not found"):
        i18n_mod.text("ratings.nonexistent", "en")


def test_unsupported_language_raises():
    with pytest.raises(ValueError, match="Unsupported language"):
        i18n_mod.text("ratings.sufficient", "fr")


def test_non_string_key_raises():
    with pytest.raises(KeyError, match="non-string"):
        i18n_mod.text("fields.strategic_contribution.objectives", "en")
