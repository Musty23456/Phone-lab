"""
apk_manager.py

Higher-level APK/package management operations layered on top of
AdbClient. Kept separate from the ADB client itself so the UI can depend
on a small, task-focused API for the APK Tools page.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.adb.adb_client import AdbClient
from app.utils.process_runner import CommandResult


@dataclass
class PackageEntry:
    name: str


class ApkManager:
    def __init__(self, client: AdbClient):
        self.client = client

    def list_installed(self, serial: Optional[str] = None, only_third_party: bool = True,
                        search: Optional[str] = None) -> list[PackageEntry]:
        packages = self.client.list_packages(serial, only_third_party=only_third_party)
        if search:
            search_lower = search.lower()
            packages = [p for p in packages if search_lower in p.lower()]
        return [PackageEntry(name=p) for p in packages]

    def package_info(self, package: str, serial: Optional[str] = None) -> str:
        result = self.client.shell_sync(f"dumpsys package {package}", serial, timeout=15)
        return result.stdout if result.success else (result.stderr or result.error or "No data")

    def install(self, apk_path: str, serial: Optional[str] = None, reinstall: bool = True) -> CommandResult:
        from app.adb import commands as cmd
        from app.utils.process_runner import run_sync
        args = cmd.install_apk(self.client.adb_path, apk_path, serial, reinstall=reinstall, grant_permissions=True)
        return run_sync(args, timeout=180)

    def install_multiple(self, apk_paths: list[str], serial: Optional[str] = None) -> CommandResult:
        from app.adb import commands as cmd
        from app.utils.process_runner import run_sync
        args = cmd.install_multiple_apks(self.client.adb_path, apk_paths, serial, reinstall=True)
        return run_sync(args, timeout=240)

    def uninstall(self, package: str, serial: Optional[str] = None, keep_data: bool = False) -> CommandResult:
        return self.client.uninstall_package(package, serial, keep_data)

    def clear_data(self, package: str, serial: Optional[str] = None) -> CommandResult:
        return self.client.clear_app_data(package, serial)

    def force_stop(self, package: str, serial: Optional[str] = None) -> CommandResult:
        return self.client.force_stop(package, serial)

    def enable(self, package: str, serial: Optional[str] = None) -> CommandResult:
        return self.client.enable_package(package, serial)

    def disable(self, package: str, serial: Optional[str] = None) -> CommandResult:
        return self.client.disable_package(package, serial)

    def launch(self, package: str, serial: Optional[str] = None) -> CommandResult:
        from app.adb import commands as cmd
        from app.utils.process_runner import run_sync
        args = cmd.start_app(self.client.adb_path, package, serial=serial)
        return run_sync(args, timeout=15)

    def open_settings(self, package: str, serial: Optional[str] = None) -> CommandResult:
        from app.adb import commands as cmd
        from app.utils.process_runner import run_sync
        args = cmd.open_app_settings(self.client.adb_path, package, serial)
        return run_sync(args, timeout=10)

    def extract_apk_path(self, package: str, serial: Optional[str] = None) -> Optional[str]:
        """Returns the on-device path(s) reported by `pm path`, which the
        caller can then `adb pull` to extract the installed APK."""
        result = self.client.shell_sync(f"pm path {package}", serial, timeout=10)
        if not result.success:
            return None
        for line in result.stdout.splitlines():
            if line.startswith("package:"):
                return line[len("package:"):].strip()
        return None
