"""Compare eval run ratings against expectations and check questions."""
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_EXPECTATIONS_DIR = _REPO_ROOT / "tests" / "fixtures" / "expectations"


def load_expectations(fixture_path: Path) -> dict | None:
    """Return field → rating dict from expectations file, or None if absent."""
    exp_file = _EXPECTATIONS_DIR / f"{fixture_path.stem}.yaml"
    if not exp_file.exists():
        return None
    with exp_file.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("fields", {}) if data else {}


def check_run(assessment: dict, expectations: dict) -> dict:
    """
    Compare assessment ratings against expectations and check questions.

    Returns counts for ratings and questions, plus mismatch details.
    """
    fields_map = {f["id"]: f for f in assessment.get("fields", [])}
    ratings_matched = 0
    mismatches = []

    for field_id, expected_rating in expectations.items():
        field = fields_map.get(field_id)
        if field is None:
            mismatches.append(f"{field_id}: missing from assessment")
            continue
        actual_rating = field.get("rating", "")
        if actual_rating == expected_rating:
            ratings_matched += 1
        else:
            mismatches.append(
                f"{field_id}: expected {expected_rating!r}, got {actual_rating!r}"
            )

    insufficient_fields = [
        f for f in assessment.get("fields", [])
        if f.get("rating") == "insufficient"
    ]
    questions_ok = sum(
        1 for f in insufficient_fields
        if isinstance(f.get("question"), str) and f["question"].strip()
    )
    for f in insufficient_fields:
        if not (isinstance(f.get("question"), str) and f["question"].strip()):
            mismatches.append(f"{f['id']}: insufficient without question")

    return {
        "ratings_matched": ratings_matched,
        "ratings_total": len(expectations),
        "questions_ok": questions_ok,
        "questions_total": len(insufficient_fields),
        "mismatches": mismatches,
    }


def format_run_v7(exp: dict) -> str:
    """Return a formatted V7 detail block for one run's expectations result."""
    lines = [
        f"  V7 {exp['ratings_matched']}/{exp['ratings_total']} ratings, "
        f"{exp['questions_ok']}/{exp['questions_total']} questioned"
    ]
    lines.extend(f"    {m}" for m in exp["mismatches"])
    return "\n".join(lines)


def summarize(results: list[dict]) -> tuple[str | None, bool]:
    """Aggregate V7 metrics across results; return (summary_line_or_None, ok)."""
    v7_runs = [r for r in results if r.get("expectations") is not None]
    if not v7_runs:
        return None, True
    rm = sum(r["expectations"]["ratings_matched"] for r in v7_runs)
    rt = sum(r["expectations"]["ratings_total"] for r in v7_runs)
    qo = sum(r["expectations"]["questions_ok"] for r in v7_runs)
    qt = sum(r["expectations"]["questions_total"] for r in v7_runs)
    return f"V7: {rm}/{rt} ratings matched, {qo}/{qt} questioned", rm == rt and qo == qt
