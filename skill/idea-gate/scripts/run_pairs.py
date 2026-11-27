"""Pair comparison for the idea-gate eval harness.

Loads pairs from pairs.yaml, runs both fixtures through the runner,
and compares field ratings. Quotes and reasons are not compared.
Library: from run_pairs import run_pairs, report_pairs
"""
import json
from pathlib import Path
from typing import Callable

import yaml

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_DEFAULT_PAIRS_PATH = _REPO_ROOT / "tests" / "fixtures" / "pairs.yaml"
_DEFAULT_FIXTURE_DIR = _REPO_ROOT / "tests" / "fixtures"


def load_pairs(pairs_path: Path = None) -> list[dict]:
    path = pairs_path or _DEFAULT_PAIRS_PATH
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)["pairs"]


def compare_ratings(assessment_a: dict, assessment_b: dict) -> list[dict]:
    """Return list of field rating mismatches between two assessments."""
    ratings_a = {f["id"]: f["rating"] for f in assessment_a.get("fields", [])}
    ratings_b = {f["id"]: f["rating"] for f in assessment_b.get("fields", [])}
    all_ids = sorted(set(ratings_a) | set(ratings_b))
    return [
        {"id": fid, "rating_a": ratings_a.get(fid), "rating_b": ratings_b.get(fid)}
        for fid in all_ids
        if ratings_a.get(fid) != ratings_b.get(fid)
    ]


def _write_pair_outputs(pair: dict, nl_assessment: dict, en_assessment: dict, out_dir: Path):
    nl_stem = Path(pair["nl"]).stem
    en_stem = Path(pair["en"]).stem
    tag = f"{nl_stem}_vs_{en_stem}"
    (out_dir / f"{tag}.nl.assessment.json").write_text(
        json.dumps(nl_assessment, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / f"{tag}.en.assessment.json").write_text(
        json.dumps(en_assessment, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _run_pair(pair: dict, fixture_dir: Path, out_dir: Path, runner: Callable) -> dict:
    result = {"nl": pair["nl"], "en": pair["en"], "mismatches": [], "error": None}
    try:
        raw_nl = runner(fixture_dir / pair["nl"])
        raw_en = runner(fixture_dir / pair["en"])
        assessment_nl, assessment_en = raw_nl[0], raw_en[0]
        result["mismatches"] = compare_ratings(assessment_nl, assessment_en)
        _write_pair_outputs(pair, assessment_nl, assessment_en, out_dir)
    except Exception as exc:
        result["error"] = str(exc)
    return result


def run_pairs(
    pairs: list[dict],
    runner: Callable,
    out_dir: Path,
    fixture_dir: Path = None,
) -> list[dict]:
    """Run all language pairs through runner; return list of comparison results."""
    fdir = fixture_dir or _DEFAULT_FIXTURE_DIR
    return [_run_pair(p, fdir, out_dir, runner) for p in pairs]


def report_pairs(results: list[dict]) -> int:
    """Print per-pair mismatches and summary line; return exit code."""
    identical = 0
    for r in results:
        if r.get("error"):
            print(f"ERROR ({r['nl']} vs {r['en']}): {r['error']}")
            continue
        for m in r["mismatches"]:
            print(
                f"MISMATCH {r['nl']} vs {r['en']}: "
                f"{m['id']} — {m['rating_a']} != {m['rating_b']}"
            )
        if not r["mismatches"]:
            identical += 1
            print(f"OK {r['nl']} vs {r['en']}: all ratings identical")
    total = len(results)
    print(f"\nV12 pairs: {identical}/{total}")
    return 0 if identical == total else 1
