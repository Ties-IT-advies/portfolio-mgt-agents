"""Validate an assessment JSON against an answers JSON.

CLI: python validate_assessment.py <assessment.json> <answers.json>
Library: from validate_assessment import validate
"""
from collections import Counter
import json
import sys
from pathlib import Path

import yaml

_FIELDS_FILE = Path(__file__).parent.parent / "fields.yaml"
_VALID_RATINGS = frozenset({"sufficient", "point_of_attention", "insufficient"})
_VALID_LANGUAGES = frozenset({"en", "nl"})


def _load_body_fields(version: str) -> list[str]:
    """Return ordered body field ids for a template version from fields.yaml."""
    with _FIELDS_FILE.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    all_fields = data.get("fields", [])
    known = {v for entry in all_fields for v in entry.get("versions", [])}
    if version not in known:
        raise ValueError(
            f"template_version {version!r} not found in fields.yaml; "
            f"known: {sorted(known)}"
        )
    return [
        entry["id"]
        for entry in all_fields
        if entry.get("section") == "body" and version in entry.get("versions", [])
    ]


def _collapse_ws(s: str) -> str:
    return " ".join(s.split())


def _check_field_list(fields: list, expected_ids: list[str]) -> list[str]:
    """Rule 1: completeness, no unknowns, no duplicates, correct order."""
    violations = []
    expected_set = set(expected_ids)
    actual_ids = [f.get("id", "") for f in fields]
    counts = Counter(actual_ids)

    for fid, count in counts.items():
        if count > 1:
            violations.append(f"rule 1: field {fid!r} appears {count} times")
        if fid not in expected_set:
            violations.append(
                f"rule 1: field {fid!r} is not a body field of this version"
            )

    for fid in expected_ids:
        if fid not in counts:
            violations.append(f"rule 1: body field {fid!r} is missing")

    unique_actual = list(
        dict.fromkeys(fid for fid in actual_ids if fid in expected_set)
    )
    if unique_actual != expected_ids:
        violations.append(
            f"rule 1: field order is wrong; "
            f"expected {expected_ids}, got {unique_actual}"
        )

    return violations


def _check_field_entry(fid: str, entry: dict, answer: str) -> list[str]:
    """Rules 2-5 for one field entry."""
    violations = []
    rating = entry.get("rating", "")
    quote = entry.get("quote")
    reason = entry.get("reason", "")
    answer_trimmed = answer.strip()

    if rating not in _VALID_RATINGS:
        violations.append(f"rule 2: field {fid!r} has invalid rating {rating!r}")

    if answer_trimmed == "":
        if rating != "insufficient":
            violations.append(
                f"rule 4: field {fid!r} has empty answer; "
                f"rating must be 'insufficient', got {rating!r}"
            )
        if quote is not None:
            violations.append(
                f"rule 4: field {fid!r} has empty answer; quote must be null"
            )
    else:
        if not isinstance(quote, str) or not quote:
            violations.append(
                f"rule 4: field {fid!r} has non-empty answer; "
                f"quote must be a non-empty string"
            )
        elif _collapse_ws(quote) not in _collapse_ws(answer_trimmed):
            violations.append(
                f"rule 3: field {fid!r} quote not found in that field's answer"
            )

    if not isinstance(reason, str) or not reason.strip():
        violations.append(f"rule 5: field {fid!r} has empty reason")

    return violations


def validate(assessment: dict, answers: dict) -> list[str]:
    """Return a list of violation strings; empty list means valid."""
    violations = []
    version = assessment.get("template_version", "")
    language = assessment.get("language", "")

    if language not in _VALID_LANGUAGES:
        violations.append(f"language {language!r} must be 'en' or 'nl'")

    try:
        expected_ids = _load_body_fields(version)
    except ValueError as exc:
        violations.append(str(exc))
        return violations

    fields = assessment.get("fields", [])
    violations.extend(_check_field_list(fields, expected_ids))

    expected_set = set(expected_ids)
    answers_map = answers.get("fields", {})
    for entry in fields:
        fid = entry.get("id", "")
        if fid not in expected_set:
            continue
        answer = answers_map.get(fid, "")
        violations.extend(_check_field_entry(fid, entry, answer))

    return violations


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <assessment.json> <answers.json>",
            file=sys.stderr,
        )
        return 2

    with Path(sys.argv[1]).open(encoding="utf-8") as f:
        assessment = json.load(f)
    with Path(sys.argv[2]).open(encoding="utf-8") as f:
        answers = json.load(f)

    violations = validate(assessment, answers)
    if violations:
        for v in violations:
            print(v)
        return 1

    version = assessment.get("template_version", "?")
    n = len(assessment.get("fields", []))
    print(f"valid: {version} assessment with {n} fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
