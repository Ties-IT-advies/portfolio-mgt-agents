"""Determine the template version (v9 or v12) from an answers JSON file."""

import argparse
import json
from pathlib import Path

import yaml

_FIELDS_PATH = Path(__file__).parent.parent / "fields.yaml"


def _load_v12_only_ids(fields_path: Path) -> list[str]:
    """Return field ids present in v12 but absent from v9."""
    with fields_path.open(encoding="utf-8") as f:
        registry = yaml.safe_load(f)["fields"]
    return [
        field["id"]
        for field in registry
        if "v12" in field["versions"] and "v9" not in field["versions"]
    ]


def detect_version(answers: dict, v12_only_ids: list[str]) -> str:
    """Return 'v12' if any v12-only field id is present in answers, else 'v9'.

    A v12 document with deleted rows (some v12-only fields missing) is still v12
    — the missing fields are rated as empty.
    """
    field_keys = set(answers.get("fields", {}).keys())
    if any(fid in field_keys for fid in v12_only_ids):
        return "v12"
    return "v9"


if __name__ == "__main__":
    from cli_utils import configure_utf8_streams
    configure_utf8_streams()

    parser = argparse.ArgumentParser(
        description="Detect template version from an answers JSON file."
    )
    parser.add_argument("answers_json", help="Path to <stem>.answers.json")
    args = parser.parse_args()

    v12_only_ids = _load_v12_only_ids(_FIELDS_PATH)
    with open(args.answers_json, encoding="utf-8") as fh:
        answers = json.load(fh)

    print(detect_version(answers, v12_only_ids))
