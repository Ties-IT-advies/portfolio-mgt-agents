"""Shared CLI utilities for idea-gate scripts."""
import argparse
import sys


def configure_utf8_streams() -> None:
    """Force stdout and stderr to UTF-8 regardless of terminal locale."""
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def build_eval_parser(default_fixture_glob: str) -> argparse.ArgumentParser:
    """Build and return the argument parser for run_eval."""
    parser = argparse.ArgumentParser(
        description="Run idea-gate skill on fixtures and validate results."
    )
    parser.add_argument(
        "--fixture",
        default=default_fixture_glob,
        metavar="GLOB",
        help="Glob relative to repo root (default: %(default)s)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        metavar="N",
        help="Runs per fixture (default: %(default)s)",
    )
    parser.add_argument(
        "--pairs",
        action="store_true",
        help="Compare language pairs from tests/fixtures/pairs.yaml",
    )
    return parser
