"""Tests for eval_expectations.py using fake assessments (no model calls)."""
import importlib.util
from pathlib import Path

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"

_V12_FIELDS = [
    "background", "objective", "sponsor", "people_involved",
    "costs", "budget", "benefits", "timelines", "risks",
    "strategic_contribution", "departments_involved", "complexity",
]


def _load_eval_expectations():
    spec = importlib.util.spec_from_file_location(
        "eval_expectations", _SCRIPTS / "eval_expectations.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_eval_expectations()


def _make_assessment(overrides: dict | None = None) -> dict:
    """Build a base assessment with all fields rated sufficient."""
    fields = [
        {
            "id": fid,
            "rating": "sufficient",
            "quote": f"Quote for {fid}.",
            "reason": f"Reason for {fid}.",
            "question": None,
        }
        for fid in _V12_FIELDS
    ]
    if overrides:
        for field in fields:
            if field["id"] in overrides:
                field.update(overrides[field["id"]])
    return {"template_version": "v12", "language": "nl", "fields": fields}


def test_full_match_passes():
    """All expected ratings match → both metrics 100%."""
    expectations = {"budget": "sufficient", "costs": "sufficient"}
    result = _mod.check_run(_make_assessment(), expectations)
    assert result["ratings_matched"] == 2
    assert result["ratings_total"] == 2
    assert result["questions_ok"] == 0
    assert result["questions_total"] == 0
    assert result["mismatches"] == []


def test_wrong_rating_fails():
    """One wrong rating → ratings_matched < ratings_total."""
    expectations = {"budget": "insufficient", "costs": "sufficient"}
    result = _mod.check_run(_make_assessment(), expectations)
    assert result["ratings_matched"] == 1
    assert result["ratings_total"] == 2
    assert any("budget" in m for m in result["mismatches"])


def test_missing_question_fails():
    """Insufficient field with no question → questions_ok < questions_total."""
    expectations = {"budget": "insufficient"}
    overrides = {"budget": {"rating": "insufficient", "quote": None, "question": None}}
    result = _mod.check_run(_make_assessment(overrides), expectations)
    assert result["ratings_matched"] == 1
    assert result["questions_total"] == 1
    assert result["questions_ok"] == 0
    assert any("budget" in m for m in result["mismatches"])


def test_no_expectations_file_means_no_v7_check():
    """Fixture with no expectations file → load_expectations returns None."""
    result = _mod.load_expectations(Path("nonexistent-fixture.docx"))
    assert result is None


def test_load_expectations_reads_yaml(tmp_path, monkeypatch):
    """When an expectations file exists, load_expectations returns its fields."""
    exp_dir = tmp_path / "expectations"
    exp_dir.mkdir()
    (exp_dir / "my-fixture.yaml").write_text(
        "fields:\n  budget: insufficient\n  costs: sufficient\n", encoding="utf-8"
    )
    monkeypatch.setattr(_mod, "_EXPECTATIONS_DIR", exp_dir)
    result = _mod.load_expectations(Path("my-fixture.docx"))
    assert result == {"budget": "insufficient", "costs": "sufficient"}


def test_question_present_passes():
    """Insufficient field with non-empty question → questions_ok == questions_total."""
    expectations = {"budget": "insufficient"}
    overrides = {
        "budget": {"rating": "insufficient", "quote": None, "question": "What is the budget?"}
    }
    result = _mod.check_run(_make_assessment(overrides), expectations)
    assert result["ratings_matched"] == 1
    assert result["questions_ok"] == 1
    assert result["questions_total"] == 1
    assert result["mismatches"] == []


def test_summarize_no_v7_runs():
    """No runs with expectations → no V7 line and ok=True."""
    results = [{"fixture": "a.docx", "run": 1, "passed": True, "violations": [], "expectations": None}]
    line, ok = _mod.summarize(results)
    assert line is None
    assert ok is True


def test_summarize_two_runs_aggregate():
    """Two runs with expectations aggregate correctly."""
    run1_exp = {
        "ratings_matched": 2, "ratings_total": 2,
        "questions_ok": 1, "questions_total": 1, "mismatches": [],
    }
    run2_exp = {
        "ratings_matched": 1, "ratings_total": 2,
        "questions_ok": 0, "questions_total": 1, "mismatches": ["foo"],
    }
    results = [
        {"fixture": "a.docx", "run": 1, "passed": True, "violations": [], "expectations": run1_exp},
        {"fixture": "a.docx", "run": 2, "passed": True, "violations": [], "expectations": run2_exp},
    ]
    line, ok = _mod.summarize(results)
    assert line == "V7: 3/4 ratings matched, 1/2 questioned"
    assert ok is False
