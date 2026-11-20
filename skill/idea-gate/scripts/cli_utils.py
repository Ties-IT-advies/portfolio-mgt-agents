"""Shared CLI utilities for idea-gate scripts."""
import sys


def configure_utf8_streams() -> None:
    """Force stdout and stderr to UTF-8 regardless of terminal locale."""
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
