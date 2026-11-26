"""Compare repeated eval runs field-by-field (V4 consistency check)."""
from collections import defaultdict


def _run_ratings(run: dict) -> dict[str, str] | None:
    """Return {field_id: rating} from a result record, or None if errored."""
    assessment = run.get("assessment")
    if assessment is None:
        return None
    return {f["id"]: f.get("rating", "") for f in assessment.get("fields", [])}


def _compare_classification(fixture_runs: list[dict]) -> list[str] | None:
    """Return list of classification values across runs if they differ, else None."""
    assessments = [r.get("assessment") for r in fixture_runs]
    has_classification = any(
        a is not None and "classification" in a for a in assessments
    )
    if not has_classification:
        return None
    values = []
    for a in assessments:
        if a is None:
            values.append("[error]")
        elif "classification" in a:
            values.append(str(a["classification"]))
        else:
            values.append("[absent]")
    return values if len(set(values)) > 1 else None


def compare_runs(fixture_runs: list[dict]) -> dict:
    """Compare all runs for one fixture; return a comparison record."""
    run_ratings = [_run_ratings(r) for r in fixture_runs]
    all_field_ids = {
        fid
        for ratings in run_ratings
        if ratings is not None
        for fid in ratings
    }
    field_diffs = {}
    for field_id in sorted(all_field_ids):
        ratings = [
            ratings_map.get(field_id, "[absent]") if ratings_map is not None else "[error]"
            for ratings_map in run_ratings
        ]
        if len(set(ratings)) > 1:
            field_diffs[field_id] = ratings
    if not all_field_ids and any(r is None for r in run_ratings):
        field_diffs["[run errors]"] = [
            "[error]" if r is None else "ok" for r in run_ratings
        ]
    return {
        "fixture": fixture_runs[0]["fixture"],
        "field_diffs": field_diffs,
        "classification_diff": _compare_classification(fixture_runs),
    }


def check_v4(results: list[dict]) -> list[dict] | None:
    """Group results by fixture and compare; return comparisons or None for single-run."""
    by_fixture: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_fixture[r["fixture"]].append(r)
    if max(len(runs) for runs in by_fixture.values()) < 2:
        return None
    return [compare_runs(by_fixture[name]) for name in sorted(by_fixture)]


def format_v4(comparison: dict) -> str:
    """Return formatted per-fixture V4 differences; empty string if none."""
    lines = []
    for field_id, ratings in comparison["field_diffs"].items():
        lines.append(f"  {field_id}: {' / '.join(ratings)}")
    if comparison["classification_diff"]:
        lines.append(f"  classification: {' / '.join(comparison['classification_diff'])}")
    return "\n".join(lines)


def summarize_v4(comparisons: list[dict]) -> tuple[str, bool]:
    """Return (V4 summary line, ok) given comparisons from check_v4."""
    total = len(comparisons)
    diffs = sum(
        1 for c in comparisons
        if c["field_diffs"] or c["classification_diff"]
    )
    return f"V4: {total} fixtures, {diffs} differences", diffs == 0
