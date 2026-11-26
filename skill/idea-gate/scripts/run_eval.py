"""Evaluate the idea-gate skill on fixture .docx files.

CLI: python run_eval.py [--fixture GLOB] [--runs N] [--pairs]
Library: from run_eval import run_eval
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_DEFAULT_FIXTURE_GLOB = "tests/fixtures/*.docx"
_EVAL_OUT_DIR = _REPO_ROOT / ".eval-out"
_RUN_TIMEOUT_S = 600
_ALLOWED_TOOLS = "Read,Write,Bash(python skill/idea-gate/scripts/*)"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent / filename
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_validate = _load_module("validate_assessment", "validate_assessment.py").validate
_eval_helpers = _load_module("eval_helpers", "eval_helpers.py")
_eval_expectations = _load_module("eval_expectations", "eval_expectations.py")


def default_runner(fixture_path: Path) -> tuple[dict, dict]:
    """Call claude headless on fixture_path; return (assessment, answers)."""
    stem = fixture_path.stem
    assessment_path = fixture_path.parent / f"{stem}.assessment.json"
    answers_path = fixture_path.parent / f"{stem}.answers.json"
    assessment_path.unlink(missing_ok=True)
    answers_path.unlink(missing_ok=True)
    try:
        result = subprocess.run(
            [
                "claude", "-p", f"Assess {fixture_path}",
                "--output-format", "json",
                "--allowedTools", _ALLOWED_TOOLS,
            ],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            cwd=_REPO_ROOT,
            timeout=_RUN_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"claude timed out after {_RUN_TIMEOUT_S}s")
    if result.returncode != 0:
        raise RuntimeError(
            f"claude exited {result.returncode}: {result.stderr.strip()}"
        )
    if not assessment_path.exists() or not answers_path.exists():
        missing = ", ".join(p.name for p in (assessment_path, answers_path) if not p.exists())
        detail = _eval_helpers.format_missing_file_error(result.stdout)
        raise RuntimeError(f"file(s) not written: {missing} — {detail}")
    with assessment_path.open(encoding="utf-8") as f:
        assessment = json.load(f)
    with answers_path.open(encoding="utf-8") as f:
        answers = json.load(f)
    return assessment, answers


def _run_one(fixture_path: Path, run_index: int, out_dir: Path, runner) -> dict:
    """Run the model once on fixture_path; return a result record."""
    result = {
        "fixture": fixture_path.name,
        "run": run_index,
        "passed": False,
        "violations": [],
        "expectations": None,
    }
    try:
        assessment, answers = runner(fixture_path)
        violations = _validate(assessment, answers)
        result["passed"] = len(violations) == 0
        result["violations"] = violations
        exp = _eval_expectations.load_expectations(fixture_path)
        if exp is not None:
            result["expectations"] = _eval_expectations.check_run(assessment, exp)
        tag = f"{fixture_path.stem}_run{run_index}"
        (out_dir / f"{tag}.assessment.json").write_text(
            json.dumps(assessment, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (out_dir / f"{tag}.answers.json").write_text(
            json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as exc:
        result["error"] = str(exc)
    return result


def run_eval(
    fixture_paths: list[Path],
    runs: int,
    runner=None,
    out_dir: Path = None,
) -> list[dict]:
    """Run evaluation on fixture_paths; return list of result records."""
    if runner is None:
        runner = default_runner
    if out_dir is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = _EVAL_OUT_DIR / timestamp
        out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for fixture_path in fixture_paths:
        for run_index in range(1, runs + 1):
            results.append(_run_one(fixture_path, run_index, out_dir, runner))
    return results


def _report(results: list[dict]) -> int:
    """Print per-run result lines and V1/V7 summaries; return exit code."""
    passed = 0
    for r in results:
        if r.get("error"):
            line = f"ERROR: {r['error']}"
        elif r["passed"]:
            line = "PASS"
            passed += 1
        else:
            n = len(r["violations"])
            line = f"FAIL {n} violation{'s' if n != 1 else ''}"
        print(f"{r['fixture']} (run {r['run']}): {line}")
        if r.get("expectations") is not None:
            print(_eval_expectations.format_run_v7(r["expectations"]))
    print(f"\nV1: {passed}/{len(results)} runs valid")
    v7_line, v7_ok = _eval_expectations.summarize(results)
    if v7_line:
        print(v7_line)
    return 0 if passed == len(results) and v7_ok else 1


def main() -> int:
    from cli_utils import configure_utf8_streams
    configure_utf8_streams()

    parser = argparse.ArgumentParser(
        description="Run idea-gate skill on fixtures and validate results."
    )
    parser.add_argument(
        "--fixture",
        default=_DEFAULT_FIXTURE_GLOB,
        metavar="GLOB",
        help="Glob relative to repo root (default: %(default)s)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        metavar="N",
        help="Runs per fixture (default: %(default)s)",
    )
    parser.add_argument(
        "--pairs",
        action="store_true",
        help="Compare language pairs from tests/fixtures/pairs.yaml",
    )
    args = parser.parse_args()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = _EVAL_OUT_DIR / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.pairs:
        rp = _eval_helpers.load_run_pairs()
        pairs_path = _REPO_ROOT / "tests" / "fixtures" / "pairs.yaml"
        pairs = rp.load_pairs(pairs_path)
        results = rp.run_pairs(pairs, default_runner, out_dir)
        (out_dir / "pairs-report.json").write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return rp.report_pairs(results)

    fixture_paths = sorted(_REPO_ROOT.glob(args.fixture))
    if not fixture_paths:
        print(f"No fixtures found for: {args.fixture}", file=sys.stderr)
        return 1

    results = run_eval(fixture_paths, args.runs, out_dir=out_dir)

    (out_dir / "report.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return _report(results)


if __name__ == "__main__":
    sys.exit(main())
