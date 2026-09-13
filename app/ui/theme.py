"""
theme.py

Loads the QSS stylesheet bundled in app/resources. Works both running
from source and frozen under PyInstaller.
"""
from __future__ import annotations

import os
import sys


def _resource_path(relative_path: str) -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base, relative_path)


def load_stylesheet() -> str:
    path = _resource_path(os.path.join("app", "resources", "styles.qss"))
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""
