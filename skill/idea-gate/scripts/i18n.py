"""Locale loader: text(key, lang) returns the string for a dotted key."""
import yaml
from pathlib import Path

SUPPORTED_LANGS = {"en", "nl"}
_LOCALES_DIR = Path(__file__).parent.parent / "locales"
_cache: dict[str, dict] = {}


def _load(lang: str) -> dict:
    if lang not in SUPPORTED_LANGS:
        raise ValueError(
            f"Unsupported language: {lang!r}. Supported: {sorted(SUPPORTED_LANGS)}"
        )
    path = _LOCALES_DIR / f"{lang}.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_data(lang: str) -> dict:
    if lang not in _cache:
        _cache[lang] = _load(lang)
    return _cache[lang]


def text(key: str, lang: str) -> str:
    """Return the string for a dotted key in the given language.

    Raises ValueError for an unsupported language.
    Raises KeyError for a missing key or a key that resolves to a non-string.
    """
    data = _get_data(lang)
    parts = key.split(".")
    node = data
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"Key {key!r} not found in locale {lang!r}")
        node = node[part]
    if not isinstance(node, str):
        raise KeyError(
            f"Key {key!r} in locale {lang!r} resolves to a non-string value"
        )
    return node


if __name__ == "__main__":
    import sys
    from cli_utils import configure_utf8_streams
    configure_utf8_streams()

    if len(sys.argv) != 3:
        print("Usage: python i18n.py <key> <lang>", file=sys.stderr)
        sys.exit(1)
    _key, _lang = sys.argv[1], sys.argv[2]
    print(text(_key, _lang))
