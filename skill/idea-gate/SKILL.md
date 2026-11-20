---
name: idea-gate
description: Assess a submitted Project Idea .docx — rate every field against the rubric and field guidance, write a validated assessment JSON next to the input, and show the user a summary table.
---

# Idea Gate Skill

Assess a submitted Project Idea document. Never edit the input `.docx`.

All scripts live in `skill/idea-gate/scripts/`. Install dependencies if needed:
`python -m pip install -r requirements-dev.txt`.

---

## Step 1 — Extract answers

Run `extract_idea.py` on the given `.docx`:

```bash
python skill/idea-gate/scripts/extract_idea.py <path/to/file.docx>
```

This returns a JSON object with keys `project_name`, `fields` (id → answer text),
`unmatched_labels`, and `missing_fields`.

Derive `<name>` as the input file's stem (no extension, no directory).
Write the JSON to `<name>.answers.json` next to the input file.

---

## Step 2 — Detect language

Run `detect_language.py` on the answers JSON:

```bash
python skill/idea-gate/scripts/detect_language.py <name>.answers.json
```

Capture the output as `lang` (`nl`, `en`, or `unknown`).

If `lang` is `unknown`, ask the user:
> "Could not detect the document language automatically. Is this English (`en`) or Dutch (`nl`)?"

Re-run with the confirmed value:

```bash
python skill/idea-gate/scripts/detect_language.py <name>.answers.json --override en
```

Use the final output as `language` in the assessment.

---

## Step 3 — Determine template version

<!-- KR 1.5 — Template-version detection: not yet implemented -->
> **[KR 1.5 — pending]** Full template-version detection logic is pending KR 1.5.

**Interim rule:** Inspect the extracted `fields` dict. If all three v12-only
field ids (`strategic_contribution`, `departments_involved`, `complexity`) are
present as keys (regardless of whether their values are empty), use `"v12"`.
Otherwise use `"v9"`.

---

## Step 4 — Rate each body field

Load `skill/idea-gate/fields.yaml`. Filter to body fields (`section: body`) for
the detected `template_version`, in registry order.

For each body field, following `skill/idea-gate/rubric.md`:

1. Read the field's `guidance` from `fields.yaml`.
2. Read the field's answer from the answers object (empty string if absent).
3. Apply the rubric to choose a rating key: `sufficient`, `point_of_attention`,
   or `insufficient`.
4. Select the **shortest verbatim excerpt** from the answer that carries the
   evidence for the rating. This is `quote`. Set `quote` to `null` only when
   the answer is empty.
5. Write `reason` in the document's language. One to three sentences naming
   what is present or absent relative to the guidance criterion.

Store the rating as a locale key — `sufficient`, `point_of_attention`, or
`insufficient` — never as the display string.

<!-- KR 1.4 / V7 — Uncertainty rule: not yet implemented -->
> **[KR 1.4 — pending]** Uncertainty rule pending KR 1.4.

---

## Step 5 — Write assessment JSON

Write the assessment to `<name>.assessment.json` next to the input file:

```json
{
  "template_version": "<v9 or v12>",
  "language": "<en or nl>",
  "fields": [
    {
      "id": "<field_id>",
      "rating": "<sufficient | point_of_attention | insufficient>",
      "quote": "<verbatim excerpt, or null>",
      "reason": "<explanation in the document language>"
    }
  ]
}
```

Fields must appear in registry order (the order they appear in `fields.yaml`
for the detected version).

<!-- KR 1.6 — Classification: not yet implemented -->
> **[KR 1.6 — pending]** Classification (not a project / normal project /
> portfolio project) is pending KR 1.6.

---

## Step 6 — Validate and self-correct

```bash
python skill/idea-gate/scripts/validate_assessment.py \
  <name>.assessment.json \
  <name>.answers.json
```

If validation reports violations, fix the assessment JSON and re-run. Attempt
at most **2 retries** (3 total runs). If violations remain after the second
retry, stop: report every violation to the user and do not write a final result.

---

## Step 7 — Show results

Present a Markdown table — one row per rated field.

| Field | Rating | Quote | Reason |
|-------|--------|-------|--------|

- **Field**: run `python skill/idea-gate/scripts/i18n.py fields.<id>.label <language>`.
- **Rating**: run `python skill/idea-gate/scripts/i18n.py ratings.<rating> <language>`.
- **Quote**: the verbatim excerpt, or `—` when null.
- **Reason**: the reason from the assessment.

All user-visible labels and rating names must go through the locale loader.
No display strings hard-coded here.
