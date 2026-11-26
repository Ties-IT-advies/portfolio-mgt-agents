"""Detect the language (nl/en) of project idea answer text.

Callers must pass only the submitter's free-text answers — not field labels or
template guidance text, which contain both languages and would skew detection.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path


def _load_i18n():
    spec = importlib.util.spec_from_file_location(
        "i18n", Path(__file__).parent / "i18n.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_SUPPORTED = frozenset(_load_i18n().SUPPORTED_LANGS)

_NL_STOP_WORDS = frozenset({
    "de", "het", "een", "van", "zijn", "die", "ook", "maar",
    "er", "aan", "bij", "door", "uit", "om", "als", "naar",
    "ze", "kan", "heeft", "nog", "wel", "zich", "dit", "worden",
    "deze", "geen", "hun", "hem", "haar", "je", "jij", "mij",
    "ons", "meer", "veel", "moet", "zou", "zal", "dan", "over",
    "zo", "na", "elk", "elke", "met",
})

_EN_STOP_WORDS = frozenset({
    "the", "a", "an", "to", "it", "that", "for", "was", "with",
    "as", "at", "from", "by", "are", "be", "have", "been", "not",
    "but", "they", "he", "she", "will", "which", "there", "their",
    "has", "had", "do", "does", "did", "about", "would", "could",
    "should", "if", "some", "its", "any", "our", "your", "all",
    "this", "what", "who", "how", "when", "where", "so", "no",
    "than", "then", "each", "and", "or", "can",
})

# Minimum number of words before detection is attempted.
MIN_WORD_COUNT = 10

# A language wins only when its stop-word count strictly exceeds
# the other language's count multiplied by this factor.
DOMINANCE_RATIO = 2.0


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+", text.lower())


def detect_language(text: str) -> str:
    """Detect whether *text* is Dutch (nl), English (en), or unknown.

    Returns "nl", "en", or "unknown".

    Pass only the submitter's free-text answers. Field labels and template
    guidance text must be excluded before calling this function.

    Returns "en" when the text contains no words (empty document rule: an
    empty document has no language; English is canonical per DEC-008).
    Returns "unknown" when the text has at least one word but fewer than
    MIN_WORD_COUNT, or when neither language's stop-word count clearly
    dominates.
    """
    words = _tokenize(text)
    if len(words) == 0:
        return "en"
    if len(words) < MIN_WORD_COUNT:
        return "unknown"

    nl_hits = sum(1 for w in words if w in _NL_STOP_WORDS)
    en_hits = sum(1 for w in words if w in _EN_STOP_WORDS)

    if nl_hits == 0 and en_hits == 0:
        return "unknown"
    if nl_hits > en_hits * DOMINANCE_RATIO:
        return "nl"
    if en_hits > nl_hits * DOMINANCE_RATIO:
        return "en"
    return "unknown"


def resolve_language(text: str, override: str | None = None) -> str:
    """Return the language for *text*, honouring any explicit *override*.

    - A valid override ("nl" or "en") always wins, regardless of detection.
    - An override outside the supported set raises ValueError.
    - Without an override, detection result is returned as-is.
    """
    if override is not None:
        if override not in _SUPPORTED:
            raise ValueError(
                f"Unsupported language override: {override!r}. "
                f"Supported: {sorted(_SUPPORTED)}"
            )
        return override
    return detect_language(text)


if __name__ == "__main__":
    import argparse
    import json
    import sys
    from cli_utils import configure_utf8_streams
    configure_utf8_streams()

    parser = argparse.ArgumentParser(
        description="Detect the language of a project idea answers JSON file."
    )
    parser.add_argument("answers_json", help="Path to <name>.answers.json")
    parser.add_argument(
        "--override",
        choices=["en", "nl"],
        help="Override the detected language",
    )
    _args = parser.parse_args()

    with open(_args.answers_json, encoding="utf-8") as _fh:
        _answers = json.load(_fh)

    _combined = " ".join(v for v in _answers["fields"].values() if v.strip())
    print(resolve_language(_combined, override=_args.override))
