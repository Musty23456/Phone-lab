"""
settings_manager.py

Thin wrapper around QSettings for storing user preferences: theme,
custom tool paths, default directories, confirmation preferences,
auto-refresh interval, and language preparation.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSettings

ORG_NAME = "ALMUS PRODUCTION"
APP_NAME = "ALMUS PHONE LAB"

DEFAULTS: dict[str, Any] = {
    "theme": "dark",
    "adb_custom_path": "",
    "fastboot_custom_path": "",
    "scrcpy_custom_path": "",
    "download_dir": "",
    "log_dir": "",
    "confirm_destructive": True,
    "auto_refresh_devices": True,
    "auto_refresh_interval_ms": 2000,
    "language": "en",
}


class SettingsManager:
    def __init__(self):
        self._settings = QSettings(ORG_NAME, APP_NAME)

    def get(self, key: str) -> Any:
        default = DEFAULTS.get(key)
        value = self._settings.value(key, default)
        # QSettings can return strings for bools/ints on some platforms
        if isinstance(default, bool) and isinstance(value, str):
            return value.lower() in ("1", "true", "yes")
        if isinstance(default, int) and not isinstance(default, bool) and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        self._settings.setValue(key, value)

    def all(self) -> dict[str, Any]:
        return {k: self.get(k) for k in DEFAULTS}

    def reset_defaults(self) -> None:
        for k, v in DEFAULTS.items():
            self._settings.setValue(k, v)
