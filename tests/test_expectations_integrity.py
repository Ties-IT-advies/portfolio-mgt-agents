"""No-model check: every expectations file is consistent with fixtures and field registry."""
import pathlib

import pytest
import yaml

_FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"
_EXPECTATIONS_DIR = _FIXTURES_DIR / "expectations"
_FIELDS_PATH = pathlib.Path(__file__).parent.parent / "skill" / "idea-gate" / "fields.yaml"

_VALID_RATINGS = {"sufficient", "point_of_attention", "insufficient"}


def _load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _v12_body_field_ids():
    registry = _load_yaml(_FIELDS_PATH)["fields"]
    return {f["id"] for f in registry if f["section"] == "body" and "v12" in f["versions"]}


def _expectations_files():
    if not _EXPECTATIONS_DIR.exists():
        return []
    return list(_EXPECTATIONS_DIR.glob("*.yaml"))


@pytest.mark.parametrize("exp_path", _expectations_files(), ids=lambda p: p.name)
def test_expectations_fixture_exists(exp_path):
    stem = exp_path.stem
    docx_path = _FIXTURES_DIR / f"{stem}.docx"
    assert docx_path.exists(), (
        f"{exp_path.name} references fixture '{stem}.docx' which does not exist in {_FIXTURES_DIR}"
    )


@pytest.mark.parametrize("exp_path", _expectations_files(), ids=lambda p: p.name)
def test_expectations_uses_valid_field_ids(exp_path):
    data = _load_yaml(exp_path)
    valid_ids = _v12_body_field_ids()
    fields = data.get("fields", {})
    unknown = set(fields) - valid_ids
    assert not unknown, (
        f"{exp_path.name} contains unknown field id(s): {sorted(unknown)}. "
        f"Valid v12 body fields: {sorted(valid_ids)}"
    )


@pytest.mark.parametrize("exp_path", _expectations_files(), ids=lambda p: p.name)
def test_expectations_uses_valid_rating_keys(exp_path):
    data = _load_yaml(exp_path)
    fields = data.get("fields", {})
    invalid = {fid: rating for fid, rating in fields.items() if rating not in _VALID_RATINGS}
    assert not invalid, (
        f"{exp_path.name} contains invalid rating(s): {invalid}. "
        f"Valid ratings: {sorted(_VALID_RATINGS)}"
    )
