"""Tests for the assessment validator."""
import importlib.util
from pathlib import Path

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_assessment", _SCRIPTS / "validate_assessment.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


validate = _load_validator().validate

_V12_BODY_FIELDS = [
    "background", "objective", "sponsor", "people_involved",
    "costs", "budget", "benefits", "timelines", "risks",
    "strategic_contribution", "departments_involved", "complexity",
]


def _answers(overrides=None):
    fields = {fid: f"Answer text for {fid}." for fid in _V12_BODY_FIELDS}
    if overrides:
        fields.update(overrides)
    return {"fields": fields}


def _assessment(field_overrides=None, **top):
    fields = [
        {
            "id": fid,
            "rating": "sufficient",
            "quote": f"Answer text for {fid}.",
            "reason": f"The field {fid} is adequately addressed.",
        }
        for fid in _V12_BODY_FIELDS
    ]
    base = {
        "template_version": "v12",
        "language": "en",
        "fields": field_overrides if field_overrides is not None else fields,
    }
    base.update(top)
    return base


def test_valid_v12_passes():
    assert validate(_assessment(), _answers()) == []


def test_rule1_missing_field():
    fields = [
        {"id": fid, "rating": "sufficient", "quote": f"Answer text for {fid}.", "reason": "ok"}
        for fid in _V12_BODY_FIELDS if fid != "complexity"
    ]
    violations = validate(_assessment(field_overrides=fields), _answers())
    assert any("complexity" in v and "missing" in v for v in violations)


def test_rule1_duplicate_field():
    fields = [
        {"id": fid, "rating": "sufficient", "quote": f"Answer text for {fid}.", "reason": "ok"}
        for fid in _V12_BODY_FIELDS
    ]
    fields.append(
        {"id": "background", "rating": "sufficient",
         "quote": "Answer text for background.", "reason": "ok"}
    )
    violations = validate(_assessment(field_overrides=fields), _answers())
    assert any("background" in v and ("2 times" in v or "duplicat" in v) for v in violations)


def test_rule1_unknown_field():
    fields = [
        {"id": fid, "rating": "sufficient", "quote": f"Answer text for {fid}.", "reason": "ok"}
        for fid in _V12_BODY_FIELDS
    ]
    fields.append({"id": "ghost_field", "rating": "sufficient", "quote": "text", "reason": "ok"})
    violations = validate(_assessment(field_overrides=fields), _answers())
    assert any("ghost_field" in v for v in violations)


def test_rule1_wrong_order():
    reordered = _V12_BODY_FIELDS.copy()
    reordered[0], reordered[1] = reordered[1], reordered[0]
    fields = [
        {"id": fid, "rating": "sufficient", "quote": f"Answer text for {fid}.", "reason": "ok"}
        for fid in reordered
    ]
    violations = validate(_assessment(field_overrides=fields), _answers())
    assert any("rule 1" in v and "order" in v for v in violations)


def test_rule2_invalid_rating():
    a = _assessment()
    a["fields"][0]["rating"] = "great"
    violations = validate(a, _answers())
    assert any("rule 2" in v and "background" in v for v in violations)


def test_rule3_quote_not_in_answer():
    a = _assessment()
    a["fields"][0]["quote"] = "This text does not appear anywhere in the answer."
    violations = validate(a, _answers())
    assert any("rule 3" in v and "background" in v for v in violations)


def test_rule3_neighbouring_field_quote_fails():
    """A quote verbatim from a neighbour's answer must fail rule 3."""
    a = _assessment()
    a["fields"][0]["quote"] = "Answer text for objective."
    violations = validate(a, _answers())
    assert any("rule 3" in v and "background" in v for v in violations)


def test_rule4_empty_answer_wrong_rating():
    a = _assessment()
    a["fields"][0]["rating"] = "sufficient"
    a["fields"][0]["quote"] = None
    violations = validate(a, _answers(overrides={"background": "   "}))
    assert any("rule 4" in v and "background" in v and "insufficient" in v for v in violations)


def test_rule4_empty_answer_non_null_quote():
    a = _assessment()
    a["fields"][0]["rating"] = "insufficient"
    a["fields"][0]["quote"] = "some text"
    violations = validate(a, _answers(overrides={"background": ""}))
    assert any("rule 4" in v and "background" in v and "null" in v for v in violations)


def test_rule4_nonempty_answer_null_quote():
    a = _assessment()
    a["fields"][0]["quote"] = None
    violations = validate(a, _answers())
    assert any("rule 4" in v and "background" in v for v in violations)


def test_rule5_empty_reason():
    a = _assessment()
    a["fields"][0]["reason"] = ""
    violations = validate(a, _answers())
    assert any("rule 5" in v and "background" in v for v in violations)


def test_rule5_whitespace_only_reason():
    a = _assessment()
    a["fields"][0]["reason"] = "   "
    violations = validate(a, _answers())
    assert any("rule 5" in v and "background" in v for v in violations)
