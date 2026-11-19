"""Tests for the locale key-parity checker."""
import importlib.util
from pathlib import Path

import pytest
import yaml

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"


def _load_check_locales():
    spec = importlib.util.spec_from_file_location(
        "idea_gate_check_locales", _SCRIPTS / "check_locales.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


check_locales_mod = _load_check_locales()


def test_parity_passes_on_current_locales():
    assert check_locales_mod.check() is True


def test_parity_fails_when_nl_missing_key(tmp_path, monkeypatch):
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()

    en_data = {"ratings": {"sufficient": "Sufficient", "insufficient": "Insufficient"}}
    nl_data = {"ratings": {"sufficient": "Voldoende"}}

    (locales_dir / "en.yaml").write_text(yaml.dump(en_data), encoding="utf-8")
    (locales_dir / "nl.yaml").write_text(yaml.dump(nl_data), encoding="utf-8")

    monkeypatch.setattr(check_locales_mod, "_LOCALES_DIR", locales_dir)

    assert check_locales_mod.check() is False


def test_parity_fails_when_en_missing_key(tmp_path, monkeypatch):
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()

    en_data = {"ratings": {"sufficient": "Sufficient"}}
    nl_data = {"ratings": {"sufficient": "Voldoende", "extra": "Extra"}}

    (locales_dir / "en.yaml").write_text(yaml.dump(en_data), encoding="utf-8")
    (locales_dir / "nl.yaml").write_text(yaml.dump(nl_data), encoding="utf-8")

    monkeypatch.setattr(check_locales_mod, "_LOCALES_DIR", locales_dir)

    assert check_locales_mod.check() is False


def test_flatten_keys_nested():
    data = {"a": {"b": "val", "c": {"d": "deep"}}}
    keys = check_locales_mod._flatten_keys(data)
    assert keys == {"a.b", "a.c.d"}
