"""Tests for eval_runner.py (no model calls)."""
import importlib.util
from pathlib import Path

_SCRIPTS = Path(__file__).parent.parent / "skill" / "idea-gate" / "scripts"


def _load_eval_runner():
    spec = importlib.util.spec_from_file_location(
        "eval_runner", _SCRIPTS / "eval_runner.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_eval_runner()


def test_default_model_is_sonnet():
    assert _mod.DEFAULT_MODEL == "sonnet"


def test_command_includes_model_sonnet_by_default():
    cmd = _mod.build_claude_command(Path("test.docx"), _mod.DEFAULT_MODEL)
    assert "--model" in cmd
    idx = cmd.index("--model")
    assert cmd[idx + 1] == "sonnet"


def test_command_includes_strict_mcp_config():
    cmd = _mod.build_claude_command(Path("test.docx"), _mod.DEFAULT_MODEL)
    assert "--strict-mcp-config" in cmd


def test_command_includes_setting_sources_project_local():
    cmd = _mod.build_claude_command(Path("test.docx"), _mod.DEFAULT_MODEL)
    assert "--setting-sources" in cmd
    idx = cmd.index("--setting-sources")
    assert cmd[idx + 1] == "project,local"


def test_model_override():
    cmd = _mod.build_claude_command(Path("test.docx"), "opus")
    idx = cmd.index("--model")
    assert cmd[idx + 1] == "opus"


def test_command_includes_allowed_tools():
    cmd = _mod.build_claude_command(Path("test.docx"), _mod.DEFAULT_MODEL)
    assert "--allowedTools" in cmd


def test_parse_usage_full():
    data = {
        "num_turns": 5,
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 500,
            "cache_read_input_tokens": 200,
            "cache_creation_input_tokens": 300,
        },
        "total_cost_usd": 0.0025,
    }
    usage = _mod.parse_usage(data)
    assert usage is not None
    assert usage["num_turns"] == 5
    assert usage["input_tokens"] == 1000
    assert usage["output_tokens"] == 500
    assert usage["cache_read_tokens"] == 200
    assert usage["cache_creation_tokens"] == 300
    assert usage["total_cost_usd"] == 0.0025


def test_parse_usage_missing_fields_returns_none():
    assert _mod.parse_usage({}) is None


def test_parse_usage_partial_fields_no_crash():
    data = {"num_turns": 3, "usage": {"input_tokens": 500}}
    usage = _mod.parse_usage(data)
    assert usage is not None
    assert usage["num_turns"] == 3
    assert usage["input_tokens"] == 500
    assert "output_tokens" not in usage


def test_parse_usage_missing_usage_key():
    data = {"num_turns": 2}
    usage = _mod.parse_usage(data)
    assert usage is not None
    assert usage["num_turns"] == 2


def test_format_usage_full():
    usage = {
        "num_turns": 5,
        "input_tokens": 1000,
        "output_tokens": 500,
        "cache_read_tokens": 200,
        "cache_creation_tokens": 300,
        "total_cost_usd": 0.0025,
    }
    line = _mod.format_usage(usage)
    assert "turns=5" in line
    assert "in=1000" in line
    assert "out=500" in line
    assert "cache_read=200" in line
    assert "cache_create=300" in line
    assert "cost=$0.0025" in line


def test_format_usage_none_returns_empty():
    assert _mod.format_usage(None) == ""


def test_format_usage_empty_dict_returns_empty():
    assert _mod.format_usage({}) == ""


def test_total_usage_sums_correctly():
    usages = [
        {"num_turns": 3, "input_tokens": 500, "output_tokens": 200},
        {"num_turns": 2, "input_tokens": 300, "output_tokens": 100},
    ]
    total = _mod.total_usage(usages)
    assert total["num_turns"] == 5
    assert total["input_tokens"] == 800
    assert total["output_tokens"] == 300


def test_total_usage_all_none_returns_none():
    assert _mod.total_usage([None, None]) is None


def test_total_usage_mixed_none():
    usages = [None, {"num_turns": 4, "input_tokens": 600}]
    total = _mod.total_usage(usages)
    assert total["num_turns"] == 4


def test_total_usage_sums_cost():
    usages = [
        {"total_cost_usd": 0.001},
        {"total_cost_usd": 0.002},
    ]
    total = _mod.total_usage(usages)
    assert abs(total["total_cost_usd"] - 0.003) < 1e-9
