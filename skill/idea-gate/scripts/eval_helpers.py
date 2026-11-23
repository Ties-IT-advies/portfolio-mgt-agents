"""Shared utilities for the idea-gate eval harness."""
import importlib.util
import json
from pathlib import Path

_SCRIPTS = Path(__file__).parent
_TRUNCATE_LEN = 500


def load_run_pairs():
    """Dynamically load run_pairs module from the scripts directory."""
    spec = importlib.util.spec_from_file_location(
        "run_pairs", _SCRIPTS / "run_pairs.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def format_missing_file_error(stdout: str) -> str:
    """Extract result text and permission denial commands from claude's JSON stdout."""
    try:
        data = json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return f"stdout: {stdout[:_TRUNCATE_LEN]!r}"
    parts = []
    result_text = data.get("result", "")
    if result_text:
        parts.append(f"result: {result_text[:_TRUNCATE_LEN]!r}")
    denials = data.get("permission_denials", [])
    if denials:
        commands = [d["command"] for d in denials if isinstance(d, dict) and "command" in d]
        if commands:
            parts.append(f"denied: {', '.join(commands)}")
    return "; ".join(parts) if parts else "(no result in output)"
