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

    return {
        "ratings_matched": ratings_matched,
        "ratings_total": len(expectations),
        "questions_ok": questions_ok,
        "questions_total": len(insufficient_fields),
        "mismatches": mismatches,
    }
