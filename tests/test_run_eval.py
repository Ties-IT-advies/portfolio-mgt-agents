"""Tests for run_eval.py using a fake runner (no model calls)."""
import importlib.util
import json
import re
import tempfile
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"

_V12_FIELDS = [
    "background", "objective", "sponsor", "people_involved",
    "costs", "budget", "benefits", "timelines", "risks",
    "strategic_contribution", "departments_involved", "complexity",
]


def _load_run_eval():
    spec = importlib.util.spec_from_file_location(
        "run_eval", _SCRIPTS / "run_eval.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_run_eval()


def _valid_pair():
    answers = {"fields": {fid: f"Answer for {fid}." for fid in _V12_FIELDS}}
    assessment = {
        "template_version": "v12",
        "language": "en",
        "fields": [
            {
                "id": fid,
                "rating": "sufficient",
                "quote": f"Answer for {fid}.",
                "reason": f"Field {fid} is adequately addressed.",
            }
            for fid in _V12_FIELDS
        ],
    }
    return assessment, answers


def _invalid_pair():
    assessment, answers = _valid_pair()
    assessment["fields"][0] = {**assessment["fields"][0], "rating": "great"}
    return assessment, answers


def test_pass_with_valid_runner():
    def fake_runner(_path):
        return _valid_pair()

    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_eval(
            [Path("dummy.docx")], 1, runner=fake_runner, out_dir=Path(tmpdir)
        )

    assert len(results) == 1
    assert results[0]["passed"] is True
    assert results[0]["violations"] == []


def test_fail_with_invalid_runner():
    def fake_runner(_path):
        return _invalid_pair()

    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_eval(
            [Path("dummy.docx")], 1, runner=fake_runner, out_dir=Path(tmpdir)
        )

    assert len(results) == 1
    assert results[0]["passed"] is False
    assert len(results[0]["violations"]) > 0


def test_multiple_runs_repeats_fixture():
    calls = []

    def fake_runner(path):
        calls.append(path)
        return _valid_pair()

    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_eval(
            [Path("a.docx")], 3, runner=fake_runner, out_dir=Path(tmpdir)
        )

    assert len(calls) == 3
    assert len(results) == 3
    assert [r["run"] for r in results] == [1, 2, 3]


def test_multiple_fixtures_all_run():
    calls = []

    def fake_runner(path):
        calls.append(path.name)
        return _valid_pair()

    fixtures = [Path("a.docx"), Path("b.docx"), Path("c.docx")]
    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_eval(
            fixtures, 2, runner=fake_runner, out_dir=Path(tmpdir)
        )

    assert len(calls) == 6
    assert len(results) == 6


def test_runner_error_recorded_not_raised():
    def failing_runner(_path):
        raise RuntimeError("model unavailable")

    with tempfile.TemporaryDirectory() as tmpdir:
        results = _mod.run_eval(
            [Path("dummy.docx")], 1, runner=failing_runner, out_dir=Path(tmpdir)
        )

    assert len(results) == 1
    assert results[0]["passed"] is False
    assert "error" in results[0]
    assert "model unavailable" in results[0]["error"]


def test_output_files_written(tmp_path):
    def fake_runner(_path):
        return _valid_pair()

    _mod.run_eval(
        [Path("idea-v12-sample.docx")], 1, runner=fake_runner, out_dir=tmp_path
    )

    assert (tmp_path / "idea-v12-sample_run1.assessment.json").exists()
    assert (tmp_path / "idea-v12-sample_run1.answers.json").exists()


def test_report_all_pass(capsys):
    results = [
        {"fixture": "a.docx", "run": 1, "passed": True, "violations": []},
        {"fixture": "b.docx", "run": 1, "passed": True, "violations": []},
    ]
    code = _mod._report(results)
    assert code == 0
    out = capsys.readouterr().out
    assert "V1: 2/2 runs valid" in out


def test_report_partial_fail(capsys):
    results = [
        {"fixture": "a.docx", "run": 1, "passed": True, "violations": []},
        {"fixture": "b.docx", "run": 1, "passed": False, "violations": ["rule 2: ..."]},
    ]
    code = _mod._report(results)
    assert code == 1
    out = capsys.readouterr().out
    assert "V1: 1/2 runs valid" in out
    assert "FAIL" in out


def test_default_runner_stale_file_rejected(tmp_path, monkeypatch):
    fixture = tmp_path / "idea-v12-sample.docx"
    fixture.touch()
    stale_assessment = tmp_path / "idea-v12-sample.assessment.json"
    stale_assessment.write_text('{"stale": true}', encoding="utf-8")

    captured = []

    class _FakeResult:
        returncode = 0
        stderr = ""
        stdout = ""

    def _fake_run(cmd, **kwargs):
        captured.append({"cmd": list(cmd), "kwargs": kwargs})
        return _FakeResult()

    monkeypatch.setattr(_mod.subprocess, "run", _fake_run)

    with pytest.raises(RuntimeError, match="not written"):
        _mod.default_runner(fixture)

    assert len(captured) == 1
    assert "--allowedTools" in captured[0]["cmd"]
    assert "cwd" in captured[0]["kwargs"]
    assert captured[0]["kwargs"].get("stdin") is _mod.subprocess.DEVNULL


def test_skill_md_no_bare_output_paths():
    """Every bash command block in SKILL.md uses full paths (no bare stem placeholders)."""
    skill_md = Path(__file__).parent.parent / "skill" / "idea-gate" / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    bash_blocks = re.findall(r"```bash\n(.*?)```", content, re.DOTALL)
    violations = []
    for block in bash_blocks:
        for line in block.splitlines():
            # Any .json token that has no '/' separator before it is a bare path
            for token in line.split():
                if token.endswith(".json") and "/" not in token:
                    violations.append(line.strip())
    assert not violations, f"Bare output paths in SKILL.md bash blocks: {violations}"


def test_default_runner_missing_files_includes_result_and_denials(tmp_path, monkeypatch):
    """When files are not written, error message includes Claude result and denied commands."""
    fixture = tmp_path / "idea-v12-sample.docx"
    fixture.touch()

    stdout_data = json.dumps({
        "result": "I tried to write the file but could not.",
        "permission_denials": [
            {
                "tool_name": "Bash",
                "tool_use_id": "x",
                "tool_input": {"command": "python skill/idea-gate/scripts/extract_idea.py foo.docx --out foo.answers.json"},
            }
        ],
    })

    class _FakeResult:
        returncode = 0
        stderr = ""
        stdout = stdout_data

    monkeypatch.setattr(_mod.subprocess, "run", lambda *a, **kw: _FakeResult())

    with pytest.raises(RuntimeError) as exc_info:
        _mod.default_runner(fixture)

    msg = str(exc_info.value)
    assert "I tried to write the file but could not." in msg
    assert "extract_idea.py foo.docx --out foo.answers.json" in msg
