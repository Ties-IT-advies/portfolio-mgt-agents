"""Build the claude command and parse usage from its JSON output."""
from pathlib import Path

DEFAULT_MODEL = "sonnet"
_ALLOWED_TOOLS = "Read,Write,Bash(python skill/idea-gate/scripts/*)"


def build_claude_command(fixture_path: Path, model: str) -> list[str]:
    """Return the claude subprocess argv for a given fixture and model."""
    return [
        "claude", "-p", f"Assess {fixture_path}",
        "--output-format", "json",
        "--allowedTools", _ALLOWED_TOOLS,
        "--model", model,
        "--strict-mcp-config",
        "--setting-sources", "project,local",
    ]


def parse_usage(data: dict) -> dict | None:
    """Extract usage fields from claude's JSON output dict; return None if absent."""
    usage_data = data.get("usage") or {}
    num_turns = data.get("num_turns")
    input_tokens = usage_data.get("input_tokens")
    output_tokens = usage_data.get("output_tokens")
    if all(v is None for v in [num_turns, input_tokens, output_tokens]):
        return None
    result: dict = {}
    if num_turns is not None:
        result["num_turns"] = num_turns
    if input_tokens is not None:
        result["input_tokens"] = input_tokens
    if output_tokens is not None:
        result["output_tokens"] = output_tokens
    cache_read = usage_data.get("cache_read_input_tokens")
    if cache_read is not None:
        result["cache_read_tokens"] = cache_read
    cache_create = usage_data.get("cache_creation_input_tokens")
    if cache_create is not None:
        result["cache_creation_tokens"] = cache_create
    cost = data.get("total_cost_usd")
    if cost is not None:
        result["total_cost_usd"] = cost
    return result


def format_usage(usage: dict | None) -> str:
    """Format usage dict as a compact string; return empty string if None or empty."""
    if not usage:
        return ""
    parts = []
    if usage.get("num_turns") is not None:
        parts.append(f"turns={usage['num_turns']}")
    if usage.get("input_tokens") is not None:
        parts.append(f"in={usage['input_tokens']}")
    if usage.get("output_tokens") is not None:
        parts.append(f"out={usage['output_tokens']}")
    if usage.get("cache_read_tokens") is not None:
        parts.append(f"cache_read={usage['cache_read_tokens']}")
    if usage.get("cache_creation_tokens") is not None:
        parts.append(f"cache_create={usage['cache_creation_tokens']}")
    if usage.get("total_cost_usd") is not None:
        parts.append(f"cost=${usage['total_cost_usd']:.4f}")
    return "  ".join(parts)


def total_usage(usages: list) -> dict | None:
    """Sum a list of usage dicts; return None if all are None or empty."""
    result: dict = {}
    for u in usages:
        if not u:
            continue
        for key, val in u.items():
            if val is None:
                continue
            if key == "total_cost_usd":
                result[key] = round(result.get(key, 0.0) + val, 6)
            else:
                result[key] = result.get(key, 0) + val
    return result if result else None
