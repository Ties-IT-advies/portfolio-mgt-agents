"""Generate v12 Project Idea .docx fixtures from the field registry and Dutch locale."""

import datetime
import io
import pathlib
import zipfile

import yaml
from docx import Document
from docx.shared import Pt

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
FIELDS_PATH = REPO_ROOT / "skill" / "idea-gate" / "fields.yaml"
LOCALE_PATH = REPO_ROOT / "skill" / "idea-gate" / "locales" / "nl.yaml"
OUT_DIR = pathlib.Path(__file__).parent
SAMPLES_DIR = pathlib.Path(__file__).parent / "samples"

FIXED_AUTHOR = "hall-of-automata"
FIXED_DATE = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
FIXED_ZIP_TIME = (2024, 1, 1, 0, 0, 0)


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_v12_fields(registry, section):
    return [f for f in registry if f["section"] == section and "v12" in f["versions"]]


def set_core_properties(doc):
    props = doc.core_properties
    props.author = FIXED_AUTHOR
    props.last_modified_by = FIXED_AUTHOR
    props.created = FIXED_DATE
    props.modified = FIXED_DATE


def add_title(doc, project_name):
    p = doc.add_paragraph()
    run = p.add_run(f"Project IDEE: {project_name}")
    run.bold = True
    run.font.size = Pt(16)


def add_table(doc, rows):
    table = doc.add_table(rows=len(rows), cols=2)
    table.style = "Table Grid"
    for i, (label, value) in enumerate(rows):
        table.cell(i, 0).text = label
        table.cell(i, 1).text = value


def build_strategic_contribution(locale_fields, picks):
    obj = locale_fields["strategic_contribution"]["objectives"]
    lines = []
    for key, idx, explanation in picks:
        label = obj[key]["label"]
        item = obj[key]["items"][idx]
        line = f"[✓] {label}: {item}"
        if explanation:
            line += f" — {explanation}"
        lines.append(line)
    return "\n".join(lines)


def build_document(registry, locale, project_name, header_values, body_values):
    header_fields = get_v12_fields(registry, "header")
    body_fields = get_v12_fields(registry, "body")
    doc = Document()
    set_core_properties(doc)
    add_title(doc, project_name)
    header_rows = [(locale[f["id"]]["label"], header_values.get(f["id"], "")) for f in header_fields]
    add_table(doc, header_rows)
    doc.add_paragraph()
    body_rows = [
        (locale[f["id"]]["label"], body_values.get(f["id"], locale[f["id"]].get("guidance", "")))
        for f in body_fields
    ]
    add_table(doc, body_rows)
    return doc


def normalize_zip_timestamps(path):
    """Rewrite the ZIP at path with all entry metadata fixed for cross-platform determinism."""
    buf = io.BytesIO()
    with zipfile.ZipFile(path, "r") as src:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dst:
            for info in src.infolist():
                info.date_time = FIXED_ZIP_TIME
                info.create_system = 3  # Unix — fixed regardless of host OS
                info.external_attr = 0o644 << 16
                dst.writestr(info, src.read(info.filename))
    path.write_bytes(buf.getvalue())


def save_deterministic(doc, path):
    doc.save(path)
    normalize_zip_timestamps(path)


def build_sample_document(registry, locale, sample):
    picks = [
        (p["objective"], p["index"], p.get("explanation", ""))
        for p in sample.get("strategic_picks", [])
    ]
    strategic_text = build_strategic_contribution(locale, picks) if picks else ""
    body = dict(sample.get("body", {}))
    if strategic_text:
        body["strategic_contribution"] = strategic_text
    return build_document(
        registry, locale,
        sample.get("project_name", ""),
        sample.get("header", {}),
        body,
    )


def main():
    registry = load_yaml(FIELDS_PATH)["fields"]
    locale = load_yaml(LOCALE_PATH)["fields"]

    blank = build_document(registry, locale, "", {}, {})
    save_deterministic(blank, OUT_DIR / "idea-v12-blank.docx")

    generated = ["idea-v12-blank.docx"]
    for sample_path in sorted(SAMPLES_DIR.glob("*.yaml")):
        sample = load_yaml(sample_path)
        doc = build_sample_document(registry, locale, sample)
        out_name = f"idea-v12-{sample_path.stem}.docx"
        save_deterministic(doc, OUT_DIR / out_name)
        generated.append(out_name)

    print(f"Generated {', '.join(generated)}")


if __name__ == "__main__":
    main()
