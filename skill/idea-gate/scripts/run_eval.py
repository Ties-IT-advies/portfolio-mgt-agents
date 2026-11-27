"""Evaluate the idea-gate skill on fixture .docx files.
CLI: python run_eval.py [--fixture GLOB] [--runs N] [--pairs] [--model NAME]
Library: from run_eval import run_eval
"""
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
_cli_utils = _load_module("cli_utils", "cli_utils.py")
_eval_v4 = _load_module("eval_v4", "eval_v4.py")
_eval_runner = _load_module("eval_runner", "eval_runner.py")


def _run_claude(fixture_path: Path, model: str) -> tuple:
    """Call claude headless on fixture_path; return (assessment, answers, usage)."""
    stem = fixture_path.stem
    assessment_path = fixture_path.parent / f"{stem}.assessment.json"
    answers_path = fixture_path.parent / f"{stem}.answers.json"
    assessment_path.unlink(missing_ok=True)
    answers_path.unlink(missing_ok=True)
    try:
        result = subprocess.run(
            _eval_runner.build_claude_command(fixture_path, model),
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
    try:
        usage = _eval_runner.parse_usage(json.loads(result.stdout))
    except (json.JSONDecodeError, ValueError):
        usage = None
    return assessment, answers, usage


def default_runner(fixture_path: Path) -> tuple:
    return _run_claude(fixture_path, _eval_runner.DEFAULT_MODEL)


def _run_one(fixture_path: Path, run_index: int, out_dir: Path, runner) -> dict:
    result = {
        "fixture": fixture_path.name,
        "run": run_index,
        "passed": False,
        "violations": [],
        "expectations": None,
    }
    try:
        assessment, answers, *rest = runner(fixture_path)
        result["usage"] = rest[0] if rest else None
        violations = _validate(assessment, answers)
        result["passed"] = len(violations) == 0
        result["violations"] = violations
        result["assessment"] = assessment
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
    """Print per-run result lines and V1/V7/V4 summaries; return exit code."""
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
        if not r.get("error"):
            print(f"  {_eval_runner.format_usage(r.get('usage')) or 'usage unavailable'}")
        if r.get("expectations") is not None:
            print(_eval_expectations.format_run_v7(r["expectations"]))
    print(f"\nV1: {passed}/{len(results)} runs valid")
    v7_line, v7_ok = _eval_expectations.summarize(results)
    if v7_line:
        print(v7_line)
    comparisons = _eval_v4.check_v4(results)
    if comparisons is not None:
        for c in comparisons:
            diff_text = _eval_v4.format_v4(c)
            if diff_text:
                print(f"{c['fixture']} V4 differences:")
                print(diff_text)
        v4_line, v4_ok = _eval_v4.summarize_v4(comparisons)
        print(v4_line)
    else:
        v4_ok = True
    print(f"\nUsage: {_eval_runner.format_usage(_eval_runner.total_usage([r.get('usage') for r in results])) or 'unavailable'}")
    return 0 if passed == len(results) and v7_ok and v4_ok else 1


def main() -> int:
    _cli_utils.configure_utf8_streams()
    args = _cli_utils.build_eval_parser(_DEFAULT_FIXTURE_GLOB, _eval_runner.DEFAULT_MODEL).parse_args()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = _EVAL_OUT_DIR / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    runner = lambda path: _run_claude(path, args.model)
    print(f"Model: {args.model}")

    if args.pairs:
        rp = _eval_helpers.load_run_pairs()
        pairs_path = _REPO_ROOT / "tests" / "fixtures" / "pairs.yaml"
        pairs = rp.load_pairs(pairs_path)
        results = rp.run_pairs(pairs, runner, out_dir)
        (out_dir / "pairs-report.json").write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return rp.report_pairs(results)

    fixture_paths = sorted(_REPO_ROOT.glob(args.fixture))
    if not fixture_paths:
        print(f"No fixtures found for: {args.fixture}", file=sys.stderr)
        return 1
    results = run_eval(
        fixture_paths, args.runs,
        runner=runner,
        out_dir=out_dir,
    )
    (out_dir / "report.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return _report(results)


if __name__ == "__main__":
    sys.exit(main())
