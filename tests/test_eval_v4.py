"""Tests for eval_v4.py using fake runs (no model calls)."""
import importlib.util
from pathlib import Path

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"

_FIELD_IDS = ["background", "objective", "budget"]


def _load_eval_v4():
    spec = importlib.util.spec_from_file_location("eval_v4", _SCRIPTS / "eval_v4.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_eval_v4()


def _make_assessment(ratings: dict, classification: str | None = None) -> dict:
    """Build a minimal assessment with the given per-field ratings."""
    fields = [{"id": fid, "rating": ratings.get(fid, "sufficient")} for fid in _FIELD_IDS]
    result = {"fields": fields}
    if classification is not None:
        result["classification"] = classification
    return result


def _make_result(fixture: str, run: int, assessment: dict | None, error: str | None = None) -> dict:
    r = {"fixture": fixture, "run": run, "passed": True, "violations": [], "expectations": None}
    if assessment is not None:
        r["assessment"] = assessment
    if error:
        r["error"] = error
        r["passed"] = False
    return r


def test_identical_runs_zero_differences():
    """Three runs with identical ratings → 0 differences."""
    assessment = _make_assessment({"budget": "sufficient"})
    runs = [_make_result("a.docx", i, assessment) for i in range(1, 4)]
    comparison = _mod.compare_runs(runs)
    assert comparison["field_diffs"] == {}
    assert comparison["classification_diff"] is None


def test_one_differing_rating_reported():
    """One field differs across runs → that field appears in field_diffs."""
    runs = [
        _make_result("a.docx", 1, _make_assessment({"budget": "sufficient"})),
        _make_result("a.docx", 2, _make_assessment({"budget": "point_of_attention"})),
        _make_result("a.docx", 3, _make_assessment({"budget": "sufficient"})),
    ]
    comparison = _mod.compare_runs(runs)
    assert "budget" in comparison["field_diffs"]
    assert comparison["field_diffs"]["budget"] == [
        "sufficient", "point_of_attention", "sufficient"
    ]


def test_classification_compared_when_present():
    """Classification difference is reported when field is present."""
    runs = [
        _make_result("a.docx", 1, _make_assessment({}, classification="go")),
        _make_result("a.docx", 2, _make_assessment({}, classification="no-go")),
    ]
    comparison = _mod.compare_runs(runs)
    assert comparison["classification_diff"] == ["go", "no-go"]


def test_classification_skipped_when_absent():
    """No classification field in any run → classification_diff is None."""
    assessment = _make_assessment({})
    runs = [_make_result("a.docx", i, assessment) for i in range(1, 3)]
    comparison = _mod.compare_runs(runs)
    assert comparison["classification_diff"] is None


def test_failed_run_counts_as_difference():
    """An errored run (no assessment) is treated as [error] and counts as a difference."""
    runs = [
        _make_result("a.docx", 1, _make_assessment({"budget": "sufficient"})),
        _make_result("a.docx", 2, None, error="model unavailable"),
    ]
    comparison = _mod.compare_runs(runs)
    assert "budget" in comparison["field_diffs"]
    assert comparison["field_diffs"]["budget"] == ["sufficient", "[error]"]


def test_single_run_no_v4_line():
    """check_v4 returns None when every fixture has only one run."""
    results = [
        _make_result("a.docx", 1, _make_assessment({})),
        _make_result("b.docx", 1, _make_assessment({})),
    ]
    assert _mod.check_v4(results) is None


def test_check_v4_groups_by_fixture():
    """check_v4 returns one comparison per fixture when runs >= 2."""
    results = [
        _make_result("a.docx", 1, _make_assessment({"budget": "sufficient"})),
        _make_result("a.docx", 2, _make_assessment({"budget": "sufficient"})),
        _make_result("b.docx", 1, _make_assessment({"budget": "point_of_attention"})),
        _make_result("b.docx", 2, _make_assessment({"budget": "insufficient"})),
    ]
    comparisons = _mod.check_v4(results)
    assert comparisons is not None
    assert len(comparisons) == 2
    names = [c["fixture"] for c in comparisons]
    assert "a.docx" in names
    assert "b.docx" in names


def test_summarize_v4_all_identical():
    """summarize_v4 returns ok=True and 0 differences when all runs match."""
    comparisons = [
        {"fixture": "a.docx", "field_diffs": {}, "classification_diff": None},
        {"fixture": "b.docx", "field_diffs": {}, "classification_diff": None},
    ]
    line, ok = _mod.summarize_v4(comparisons)
    assert line == "V4: 2 fixtures, 0 differences"
    assert ok is True


def test_summarize_v4_with_differences():
    """summarize_v4 returns ok=False and correct count when differences exist."""
    comparisons = [
        {"fixture": "a.docx", "field_diffs": {"budget": ["s", "p"]}, "classification_diff": None},
        {"fixture": "b.docx", "field_diffs": {}, "classification_diff": None},
    ]
    line, ok = _mod.summarize_v4(comparisons)
    assert line == "V4: 2 fixtures, 1 differences"
    assert ok is False


def test_format_v4_no_differences():
    """format_v4 returns empty string when there are no differences."""
    comparison = {"fixture": "a.docx", "field_diffs": {}, "classification_diff": None}
    assert _mod.format_v4(comparison) == ""


def test_format_v4_with_field_diff():
    """format_v4 includes field name and slash-separated ratings."""
    comparison = {
        "fixture": "a.docx",
        "field_diffs": {"budget": ["sufficient", "point_of_attention", "insufficient"]},
        "classification_diff": None,
    }
    result = _mod.format_v4(comparison)
    assert "budget: sufficient / point_of_attention / insufficient" in result
