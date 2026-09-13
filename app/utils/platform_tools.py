"""
platform_tools.py

Locates adb.exe / fastboot.exe (or adb / fastboot on non-Windows dev
machines) without requiring the user to configure PATH. Search order:

1. A user-configured custom path (from Settings)
2. Bundled tools/platform-tools directory next to the executable
   (works both when run from source and when frozen by PyInstaller)
3. System PATH

Also exposes version-check helpers used by the Dashboard/Settings pages.
"""
from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from typing import Optional

from app.utils.process_runner import run_sync

ADB_EXE = "adb.exe" if os.name == "nt" else "adb"
FASTBOOT_EXE = "fastboot.exe" if os.name == "nt" else "fastboot"


@dataclass
class ToolStatus:
    name: str
    path: Optional[str]
    version: Optional[str]
    found: bool
    source: str  # "bundled" | "system" | "custom" | "none"


def _app_root() -> str:
    """Directory of the running application - handles both a normal
    source checkout and a PyInstaller-frozen executable (sys._MEIPASS/exe
    directory)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # app/utils/platform_tools.py -> project root is two levels up
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def bundled_tools_dir() -> str:
    return os.path.join(_app_root(), "tools", "platform-tools")


def _find_tool(exe_name: str, custom_path: Optional[str] = None) -> tuple[Optional[str], str]:
    # 1. custom path from settings
    if custom_path:
        candidate = os.path.join(custom_path, exe_name)
        if os.path.isfile(candidate):
            return candidate, "custom"
        if os.path.isfile(custom_path) and os.path.basename(custom_path).lower() == exe_name.lower():
            return custom_path, "custom"

    # 2. bundled next to the app
    bundled = os.path.join(bundled_tools_dir(), exe_name)
    if os.path.isfile(bundled):
        return bundled, "bundled"

    # 3. system PATH
    found = shutil.which(exe_name) or shutil.which(exe_name.replace(".exe", ""))
    if found:
        return found, "system"

    return None, "none"


def get_adb_status(custom_path: Optional[str] = None) -> ToolStatus:
    path, source = _find_tool(ADB_EXE, custom_path)
    if not path:
        return ToolStatus("adb", None, None, False, "none")
    result = run_sync([path, "version"], timeout=8)
    version = None
    if result.success:
        first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
        version = first_line
    return ToolStatus("adb", path, version, result.success, source)


def get_fastboot_status(custom_path: Optional[str] = None) -> ToolStatus:
    path, source = _find_tool(FASTBOOT_EXE, custom_path)
    if not path:
        return ToolStatus("fastboot", None, None, False, "none")
    result = run_sync([path, "--version"], timeout=8)
    version = None
    if result.success:
        first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
        version = first_line
    return ToolStatus("fastboot", path, version, result.success, source)


def find_scrcpy(custom_path: Optional[str] = None) -> Optional[str]:
    """Optional integration - only used if the user already has scrcpy
    available (bundled or on PATH). Never downloaded/installed automatically."""
    exe = "scrcpy.exe" if os.name == "nt" else "scrcpy"
    path, _source = _find_tool(exe, custom_path)
    return path
