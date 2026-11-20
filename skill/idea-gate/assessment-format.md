# Assessment format

One assessment per submitted project idea. The five validation rules are enforced by `scripts/validate_assessment.py`.

## Top-level keys

| Key | Type | Rule |
|-----|------|------|
| `template_version` | string | A version present in `fields.yaml` (`v9`, `v12`) |
| `language` | string | `en` or `nl` |
| `fields` | list | One entry per **body** field of that version, in registry order; header fields are not rated |

## Field entry keys (`fields[*]`)

| Key | Type | Rule |
|-----|------|------|
| `id` | string | Field id from `fields.yaml` |
| `rating` | string | One of `sufficient`, `point_of_attention`, `insufficient` (the `ratings.*` locale keys) |
| `quote` | string or null | Verbatim excerpt of that field's own answer; `null` only when the answer is empty |
| `reason` | string | Non-empty explanation written in `language` |

## Answers input

The validator takes a second file — the reader output — with format:

```json
{
  "fields": {
    "<id>": "<answer text>"
  }
}
```

## Validation rules

1. **Coverage and order:** Every body field of `template_version` appears exactly once; no unknown ids; no duplicates. Wrong order is reported as a separate violation.
2. **Rating values:** `rating` is one of `sufficient`, `point_of_attention`, or `insufficient`.
3. **Verbatim quote:** After collapsing whitespace and trimming, `quote` is a substring of **that field's own** answer, not of another field's. Case-sensitive.
4. **Quote and answer agreement:** Empty answer (after trimming) → `rating` must be `insufficient`, `quote` must be `null`. Non-empty answer → `quote` must be a non-empty string.
5. **Non-empty reason:** `reason` must be a non-empty, non-whitespace string.
