"""Tests for run_pairs.py using fake runners (no model calls)."""
import importlib.util
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"

_V12_FIELDS = [
    "background", "objective", "sponsor", "people_involved",
    "costs", "budget", "benefits", "timelines", "risks",
    "strategic_contribution", "departments_involved", "complexity",
]


def _load_run_pairs():
    spec = importlib.util.spec_from_file_location(
        "run_pairs", _SCRIPTS / "run_pairs.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_run_pairs()


def _make_assessment(ratings: dict) -> dict:
    return {
        "template_version": "v12",
        "language": "nl",
        "fields": [
            {"id": fid, "rating": r, "quote": "...", "reason": "..."}
            for fid, r in ratings.items()
        ],
    }


def _all_sufficient() -> dict:
    return {fid: "sufficient" for fid in _V12_FIELDS}


def test_identical_ratings_no_mismatches():
    def fake_runner(_path):
        return _make_assessment(_all_sufficient()), {}

    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_pairs(
            [{"nl": "a.docx", "en": "b.docx"}],
            fake_runner,
            Path(tmpdir),
            fixture_dir=Path(tmpdir),
        )

    assert len(results) == 1
    assert results[0]["mismatches"] == []
    assert results[0]["error"] is None


def test_mismatch_detected():
    def fake_runner(path):
        if "en" in path.name:
            return _make_assessment({**_all_sufficient(), "background": "insufficient"}), {}
        return _make_assessment(_all_sufficient()), {}

    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_pairs(
            [{"nl": "sample.docx", "en": "sample-en.docx"}],
            fake_runner,
            Path(tmpdir),
            fixture_dir=Path(tmpdir),
        )

    assert len(results) == 1
    assert len(results[0]["mismatches"]) == 1
    mismatch = results[0]["mismatches"][0]
    assert mismatch["id"] == "background"
    assert mismatch["rating_a"] == "sufficient"
    assert mismatch["rating_b"] == "insufficient"


def test_multiple_mismatches():
    def fake_runner(path):
        if "en" in path.name:
            overrides = {"background": "insufficient", "objective": "point_of_attention"}
            return _make_assessment({**_all_sufficient(), **overrides}), {}
        return _make_assessment(_all_sufficient()), {}

    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_pairs(
            [{"nl": "a.docx", "en": "a-en.docx"}],
            fake_runner,
            Path(tmpdir),
            fixture_dir=Path(tmpdir),
        )

    assert len(results[0]["mismatches"]) == 2


def test_runner_error_recorded():
    def failing_runner(_path):
        raise RuntimeError("model unavailable")

    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_pairs(
            [{"nl": "a.docx", "en": "b.docx"}],
            failing_runner,
            Path(tmpdir),
            fixture_dir=Path(tmpdir),
        )

    assert len(results) == 1
    assert "model unavailable" in results[0]["error"]


def test_multiple_pairs_all_pass():
    def fake_runner(_path):
        return _make_assessment(_all_sufficient()), {}

    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_pairs(
            [
                {"nl": "a.docx", "en": "a-en.docx"},
                {"nl": "b.docx", "en": "b-en.docx"},
            ],
            fake_runner,
            Path(tmpdir),
            fixture_dir=Path(tmpdir),
        )

    assert len(results) == 2
    assert all(r["mismatches"] == [] for r in results)


def test_compare_ratings_unit():
    a = _make_assessment({"background": "sufficient", "objective": "insufficient"})
    b = _make_assessment({"background": "sufficient", "objective": "sufficient"})
    mismatches = _mod.compare_ratings(a, b)
    assert len(mismatches) == 1
    assert mismatches[0]["id"] == "objective"
    assert mismatches[0]["rating_a"] == "insufficient"
    assert mismatches[0]["rating_b"] == "sufficient"


def test_report_all_identical(capsys):
    results = [
        {"nl": "a.docx", "en": "b.docx", "mismatches": [], "error": None},
        {"nl": "c.docx", "en": "d.docx", "mismatches": [], "error": None},
    ]
    code = _mod.report_pairs(results)
    assert code == 0
    out = capsys.readouterr().out
    assert "V12 pairs: 2/2" in out


def test_report_mismatch_exits_nonzero(capsys):
    results = [
        {
            "nl": "a.docx",
            "en": "b.docx",
            "mismatches": [
                {"id": "background", "rating_a": "sufficient", "rating_b": "insufficient"}
            ],
            "error": None,
        }
    ]
    code = _mod.report_pairs(results)
    assert code == 1
    out = capsys.readouterr().out
    assert "MISMATCH" in out
    assert "V12 pairs: 0/1" in out
