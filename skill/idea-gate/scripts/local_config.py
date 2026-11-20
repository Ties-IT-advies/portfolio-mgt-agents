"""Resolves the local config folder and standard paths within it."""
from __future__ import annotations

import os
from pathlib import Path


def config_dir() -> Path:
    env = os.environ.get("PMA_CONFIG_DIR")
    if env:
        return Path(env)
    return Path.home() / ".portfolio-mgt-agents"


def denylist_path() -> Path:
    return config_dir() / "denylist.txt"


def config_yaml_path() -> Path:
    return config_dir() / "config.yaml"


def templates_dir() -> Path:
    return config_dir() / "templates"


def calibration_dir() -> Path:
    return config_dir() / "calibration"
