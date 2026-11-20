"""Extract field answers from a Project Idea .docx into answers per field id."""
import argparse
import json
import re
from pathlib import Path

import yaml
from docx import Document

_SCRIPTS_DIR = Path(__file__).parent
_LOCALES_DIR = _SCRIPTS_DIR.parent / "locales"
_FIELDS_PATH = _SCRIPTS_DIR.parent / "fields.yaml"
_SUPPORTED_LANGS = ("en", "nl")

_TITLE_PATTERNS = [
    re.compile(r"(?i)^project\s+idee\s*:\s*(.*)$"),
    re.compile(r"(?i)^project\s+idea\s*:\s*(.*)$"),
]


def _normalize_label(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text.rstrip(":")


def _load_locale(lang: str) -> dict:
    path = _LOCALES_DIR / f"{lang}.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_label_map(registry: list[dict]) -> dict[str, str]:
    """Return normalized-label -> field_id from all supported locales."""
    label_map: dict[str, str] = {}
    for lang in _SUPPORTED_LANGS:
        locale_fields = _load_locale(lang).get("fields", {})
        for field in registry:
            fid = field["id"]
            if fid in locale_fields:
                label = locale_fields[fid].get("label")
                if label:
                    label_map[_normalize_label(label)] = fid
    return label_map


def _build_guidance_set(registry: list[dict]) -> dict[str, set[str]]:
    """Return field_id -> set of guidance strings from all supported locales."""
    guidance_set: dict[str, set[str]] = {}
    for lang in _SUPPORTED_LANGS:
        locale_fields = _load_locale(lang).get("fields", {})
        for field in registry:
            fid = field["id"]
            if fid in locale_fields:
                guidance = locale_fields[fid].get("guidance")
                if guidance:
                    guidance_set.setdefault(fid, set()).add(guidance.strip())
    return guidance_set


def _cell_text(cell) -> str:
    return "\n".join(p.text for p in cell.paragraphs).strip()


def _extract_project_name(doc: Document) -> str:
    for para in doc.paragraphs:
        for pattern in _TITLE_PATTERNS:
            m = pattern.match(para.text.strip())
            if m:
                return m.group(1).strip()
    return ""


def _process_tables(
    doc: Document,
    label_map: dict[str, str],
    guidance_set: dict[str, set[str]],
) -> tuple[dict[str, str], list[str]]:
    fields: dict[str, str] = {}
    unmatched: list[str] = []

    for table in doc.tables:
        for row in table.rows:
            if len(row.cells) < 2:
                continue
            raw_label = row.cells[0].text.strip()
            raw_answer = _cell_text(row.cells[1])
            norm = _normalize_label(raw_label)
            field_id = label_map.get(norm)

            if field_id is None:
                if raw_label:
                    unmatched.append(raw_label)
                continue

            guidances = guidance_set.get(field_id, set())
            fields[field_id] = "" if raw_answer in guidances else raw_answer

    return fields, unmatched


def extract(path) -> dict:
    """Extract answers from a Project Idea .docx.

    Returns {"project_name": str, "fields": {id: answer},
             "unmatched_labels": [str], "missing_fields": [id]}.
    """
    with _FIELDS_PATH.open(encoding="utf-8") as f:
        registry = yaml.safe_load(f)["fields"]

    label_map = _build_label_map(registry)
    guidance_set = _build_guidance_set(registry)

    doc = Document(str(path))
    project_name = _extract_project_name(doc)
    fields, unmatched = _process_tables(doc, label_map, guidance_set)

    all_ids = [f["id"] for f in registry]
    missing_fields = [fid for fid in all_ids if fid not in fields]

    return {
        "project_name": project_name,
        "fields": fields,
        "unmatched_labels": unmatched,
        "missing_fields": missing_fields,
    }


def main() -> None:
    from cli_utils import configure_utf8_streams
    configure_utf8_streams()

    parser = argparse.ArgumentParser(
        description="Extract answers from a Project Idea .docx."
    )
    parser.add_argument("docx", help="Path to the .docx file")
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="Write JSON to PATH as UTF-8; nothing is printed to stdout",
    )
    args = parser.parse_args()

    result = extract(Path(args.docx))
    json_str = json.dumps(result, ensure_ascii=False, indent=2)

    if args.out:
        Path(args.out).write_text(json_str, encoding="utf-8")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
