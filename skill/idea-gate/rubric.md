# Idea Gate — Rating Rubric

This rubric defines the three rating values and the rules for selecting quotes
and writing reasons. It applies to all body fields regardless of template
version or document language.

---

## Ratings

Apply exactly one rating to each body field. The rating is stored as a locale
key; display text is loaded at render time.

### `sufficient`

The answer addresses the field's guidance fully. The required elements are
present — a name where one is asked for, a measure where measurability is
required, an explanation where reasoning is expected. A reviewer would not
hold back the submission on this field's account.

### `point_of_attention`

The answer partially addresses the guidance. Something useful is present, but
at least one required element is missing, vague, or unsubstantiated. A
reviewer would flag this field but would not block the submission on it alone.
Use this rating when the submitter made a genuine attempt that falls short on
one criterion, not on most.

### `insufficient`

The answer fails to meet the guidance. This rating applies when:

- the answer is empty,
- the answer is a placeholder ("TBD", "nader te bepalen", "n.v.t." without
  further explanation),
- the answer is a copy of the guidance text itself (the reader script strips
  recognised guidance strings; check the extracted answer, not the raw cell),
- or the answer is so vague that no real information is conveyed.

---

## Uncertainty rule

Apply this rule when an answer contains an estimate, a range, or an
acknowledged gap in knowledge. It determines whether the field is
`point_of_attention` or `insufficient`; it does not override a `sufficient`
rating.

### Explained uncertainty → `point_of_attention`

Rate `point_of_attention` when the answer gives an estimate, range, or
provisional value **and** states why the value is uncertain or when it will
be settled.

Examples:
- "€40–60k; vendor quote expected in March" ← estimate + reason
- "Three months, pending final scope sign-off by end of Q1" ← range + condition

The `reason` names what is confirmed and what is still open.

### Unexplained gap → `insufficient`

Rate `insufficient` when the answer has one of these patterns:

- empty or placeholder text ("TBD", "nader te bepalen")
- uncertainty stated without an estimate ("costs are still unknown")
- an estimate or range given without any explanation of why it is uncertain
  or when it will be resolved

A number without context is an unexplained gap if no reasoning accompanies it.

---

## Picking the quote

The `quote` is evidence, not a summary. Its purpose is to anchor the rating to
the actual text so a reviewer can verify it.

- Pick the **shortest continuous excerpt** from the answer that carries the
  evidence for the rating decision.
- The excerpt must be a **verbatim substring** of that field's own answer,
  case-sensitive. Do not quote from another field.
- When checking containment, collapse runs of whitespace (spaces, newlines,
  tabs) to a single space in both the quote and the answer. Store the original
  text, not the collapsed version.
- When the answer is empty after trimming, set `quote` to `null`.
- For `insufficient` ratings on non-empty answers, quote the part of the
  answer that most clearly shows the deficiency — typically the placeholder
  phrase or the vague claim being rated.

---

## Writing the reason

Write `reason` in the **language of the document** — the `language` value
determined in Step 2 (`en` or `nl`).

A good reason:
- names specifically what is present or absent,
- ties the finding to the guidance criterion (not to the rating label),
- is one to three sentences.

It does not repeat the rating word or restate the guidance verbatim.

**For `sufficient`:** name the evidence that satisfies the criterion.
**For `point_of_attention`:** name what is present and what is missing or unclear.
**For `insufficient`:** name what is absent or why the answer fails the criterion.
