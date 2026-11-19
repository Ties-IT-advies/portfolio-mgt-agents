"""Key-parity check: exits non-zero when en and nl key sets differ."""
import sys
import yaml
from pathlib import Path

_LOCALES_DIR = Path(__file__).parent.parent / "locales"


def _flatten_keys(data: dict, prefix: str = "") -> set:
    """Recursively collect dotted key paths for all non-dict leaf values."""
    keys = set()
    for k, v in data.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys |= _flatten_keys(v, path)
        else:
            keys.add(path)
    return keys


def load_keys(lang: str) -> set:
    path = _LOCALES_DIR / f"{lang}.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return _flatten_keys(data)


def check() -> bool:
    """Return True if en and nl key sets match, False otherwise."""
    en_keys = load_keys("en")
    nl_keys = load_keys("nl")

    missing_in_nl = en_keys - nl_keys
    missing_in_en = nl_keys - en_keys

    ok = True
    if missing_in_nl:
        print("Keys in en but missing in nl:")
        for k in sorted(missing_in_nl):
            print(f"  {k}")
        ok = False
    if missing_in_en:
        print("Keys in nl but missing in en:")
        for k in sorted(missing_in_en):
            print(f"  {k}")
        ok = False

    if ok:
        print("Locale key sets match.")
    return ok


if __name__ == "__main__":
    sys.exit(0 if check() else 1)
