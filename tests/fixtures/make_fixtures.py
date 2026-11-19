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

FIXED_AUTHOR = "hall-of-automata"
FIXED_DATE = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
FIXED_ZIP_TIME = (2024, 1, 1, 0, 0, 0)

SAMPLE_PROJECT_NAME = "Digitaal Klantportaal"

SAMPLE_HEADER = {
    "prepared_by": "J. de Vries, Projectleider",
    "date": "2024-01-15",
    "status": "Concept",
}

SAMPLE_BODY = {
    "background": (
        "Klanten van Verbogen BV kunnen momenteel alleen telefonisch of per e-mail contact "
        "opnemen. Dit leidt tot lange wachttijden en hoge beheerlasten. Een digitaal klantportaal "
        "biedt zelfbediening en vermindert het aantal handmatige handelingen met ~40%."
    ),
    "objective": (
        "Het doel is een zelfbedieningsportaal live te hebben voor 500 klanten per Q3 2024. "
        "Succesmaatstaf: 80% van de standaard klantvragen afgehandeld zonder menselijke tussenkomst."
    ),
    "sponsor": "M. Bakker, Directeur Klantbeleving",
    "people_involved": (
        "Project Manager: S. Jansen (IT). "
        "Inhoudelijk expert: R. Hoekstra (Klantenservice). "
        "Content owner: L. Smits (Marketing)."
    ),
    "costs": (
        "Interne capaciteit: 320 uur over 6 maanden (analist + developer). "
        "Projectkosten: €45.000 realisatie, €8.000/jaar onderhoud. "
        "Aanname: licentiekosten SaaS-platform €12.000/jaar."
    ),
    "budget": (
        "€57.000 beschikbaar vanuit het IT-innovatiefonds 2024. "
        "Goedkeuring directie ontvangen op 10-01-2024."
    ),
    "benefits": (
        "€30.000/jaar besparing op klantenservice FTE; "
        "NPS-verbetering verwacht van +8 punten. "
        "Nadeel: initiële weerstand bij medewerkers klantenservice (change management nodig)."
    ),
    "timelines": (
        "Start: februari 2024. "
        "Mijlpalen: prototype gereed april 2024, pilot 50 klanten mei 2024, go-live juli 2024. "
        "Vertrouwensniveau planning: gemiddeld (afhankelijk van leveranciersbeschikbaarheid)."
    ),
    "risks": (
        "1. Leveranciersvertraging — mitigatie: contractuele deadline, alternatieve leverancier "
        "geïdentificeerd; eigenaar: S. Jansen.\n"
        "2. Lage klantadoptie — mitigatie: communicatiecampagne + onboarding-tour; "
        "eigenaar: L. Smits.\n"
        "3. Datastoring bij migratie klantgegevens — mitigatie: testmigratieronde + "
        "rollback-procedure; eigenaar: R. Hoekstra."
    ),
    "departments_involved": (
        "IT, Klantenservice, Marketing. "
        "Meerdere afdelingen betrokken — projectclassificatie: cross-functioneel."
    ),
    "complexity": (
        "Inschatting: Gemiddeld. "
        "Technisch: standaard SaaS-integratie, beperkte maatwerk. "
        "Organisatorisch: drie afdelingen, change management vereist. "
        "Afhankelijkheden: leveranciersselectie nog niet afgerond."
    ),
}

# (objective_key, item_index, free_text_explanation)
SAMPLE_STRATEGIC_PICKS = [
    ("operational_excellence", 3, ""),
    ("revenue_growth", 3, ""),
]


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


def main():
    registry = load_yaml(FIELDS_PATH)["fields"]
    locale = load_yaml(LOCALE_PATH)["fields"]

    blank = build_document(registry, locale, "", {}, {})
    save_deterministic(blank, OUT_DIR / "idea-v12-blank.docx")

    strategic_text = build_strategic_contribution(locale, SAMPLE_STRATEGIC_PICKS)
    sample_body = {**SAMPLE_BODY, "strategic_contribution": strategic_text}
    sample = build_document(registry, locale, SAMPLE_PROJECT_NAME, SAMPLE_HEADER, sample_body)
    save_deterministic(sample, OUT_DIR / "idea-v12-sample.docx")

    print("Generated idea-v12-blank.docx and idea-v12-sample.docx")


if __name__ == "__main__":
    main()
