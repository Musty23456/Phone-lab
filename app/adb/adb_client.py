"""
adb_client.py

High-level ADB client used by the UI. Wraps command builders (commands.py)
with:
  - command validation (utils.validators) before anything is executed
  - synchronous helpers for quick lookups (device list, getprop, etc.)
  - an async runner factory for long-running/streaming commands (logcat,
    screenrecord, shell sessions) so the GUI thread never blocks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.adb import commands as cmd
from app.utils.process_runner import AsyncProcessRunner, CommandResult, run_sync
from app.utils.validators import validate_command


@dataclass
class AdbDevice:
    serial: str
    state: str  # device, unauthorized, offline, recovery, sideload
    extra: str = ""


class AdbClient:
    def __init__(self, adb_path: str):
        self.adb_path = adb_path

    # ---------- synchronous, quick lookups ----------

    def list_devices(self) -> list[AdbDevice]:
        result = run_sync(cmd.devices(self.adb_path), timeout=10)
        devices: list[AdbDevice] = []
        if not result.success:
            return devices
        lines = result.stdout.strip().splitlines()
        for line in lines[1:]:  # skip "List of devices attached"
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            serial = parts[0]
            rest = parts[1] if len(parts) > 1 else ""
            state = rest.split()[0] if rest else "unknown"
            devices.append(AdbDevice(serial=serial, state=state, extra=rest))
        return devices

    def get_state(self, serial: Optional[str] = None) -> str:
        result = run_sync(cmd.get_state(self.adb_path, serial), timeout=8)
        return result.stdout.strip() if result.success else "unknown"

    def shell_sync(self, shell_cmd: str, serial: Optional[str] = None, timeout: float = 15) -> CommandResult:
        args = cmd.shell(self.adb_path, shell_cmd, serial)
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=timeout)

    def getprop_all(self, serial: Optional[str] = None) -> dict[str, str]:
        result = run_sync(cmd.getprop(self.adb_path, serial), timeout=10)
        props: dict[str, str] = {}
        if not result.success:
            return props
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("[") and "]: [" in line:
                try:
                    key, value = line.split("]: [", 1)
                    key = key.lstrip("[")
                    value = value.rstrip("]")
                    props[key] = value
                except ValueError:
                    continue
        return props

    def battery_info(self, serial: Optional[str] = None) -> dict[str, str]:
        result = run_sync(cmd.dumpsys_battery(self.adb_path, serial), timeout=10)
        info: dict[str, str] = {}
        if not result.success:
            return info
        for line in result.stdout.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                info[key.strip()] = value.strip()
        return info

    def storage_info(self, serial: Optional[str] = None) -> str:
        result = run_sync(cmd.storage_info(self.adb_path, serial), timeout=10)
        return result.stdout if result.success else ""

    def meminfo(self, serial: Optional[str] = None) -> str:
        result = run_sync(cmd.meminfo(self.adb_path, serial), timeout=10)
        return result.stdout if result.success else ""

    def cpuinfo(self, serial: Optional[str] = None) -> str:
        result = run_sync(cmd.cpuinfo(self.adb_path, serial), timeout=10)
        return result.stdout if result.success else ""

    def screen_resolution(self, serial: Optional[str] = None) -> str:
        result = run_sync(cmd.wm_size(self.adb_path, serial), timeout=8)
        return result.stdout.strip() if result.success else ""

    def list_packages(self, serial: Optional[str] = None, only_third_party: bool = False,
                       filter_text: Optional[str] = None) -> list[str]:
        result = run_sync(cmd.list_packages(self.adb_path, serial, only_third_party, filter_text), timeout=15)
        if not result.success:
            return []
        packages = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                packages.append(line[len("package:"):])
        return sorted(packages)

    def list_dir(self, remote_dir: str, serial: Optional[str] = None) -> CommandResult:
        return self.shell_sync(f"ls -la {remote_dir}", serial)

    # ---------- validated one-shot actions (still synchronous, short) ----------

    def reboot(self, mode: Optional[str] = None, serial: Optional[str] = None) -> CommandResult:
        args = cmd.reboot(self.adb_path, mode, serial)
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=15)

    def uninstall_package(self, package: str, serial: Optional[str] = None,
                           keep_data: bool = False) -> CommandResult:
        args = cmd.uninstall_package(self.adb_path, package, serial, keep_data)
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=30)

    def clear_app_data(self, package: str, serial: Optional[str] = None) -> CommandResult:
        return self.shell_sync(f"pm clear {package}", serial, timeout=20)

    def disable_package(self, package: str, serial: Optional[str] = None) -> CommandResult:
        return self.shell_sync(f"pm disable-user {package}", serial, timeout=15)

    def enable_package(self, package: str, serial: Optional[str] = None) -> CommandResult:
        return self.shell_sync(f"pm enable {package}", serial, timeout=15)

    def force_stop(self, package: str, serial: Optional[str] = None) -> CommandResult:
        return self.shell_sync(f"am force-stop {package}", serial, timeout=10)

    def remove_path(self, remote_path: str, recursive: bool = False,
                     serial: Optional[str] = None) -> CommandResult:
        args = cmd.remove_path(self.adb_path, remote_path, recursive, serial)
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=20)

    def make_dir(self, remote_dir: str, serial: Optional[str] = None) -> CommandResult:
        return self.shell_sync(f"mkdir -p {remote_dir}", serial, timeout=10)

    def rename_path(self, old_path: str, new_path: str, serial: Optional[str] = None) -> CommandResult:
        return self.shell_sync(f"mv {old_path} {new_path}", serial, timeout=10)

    def pull(self, remote_path: str, local_path: str, serial: Optional[str] = None) -> CommandResult:
        return run_sync(cmd.pull_file(self.adb_path, remote_path, local_path, serial), timeout=120)

    def push(self, local_path: str, remote_path: str, serial: Optional[str] = None) -> CommandResult:
        return run_sync(cmd.push_file(self.adb_path, local_path, remote_path, serial), timeout=120)

    def screencap_and_pull(self, local_path: str, serial: Optional[str] = None) -> CommandResult:
        remote = "/sdcard/almus_screenshot.png"
        cap_result = run_sync(cmd.screencap(self.adb_path, remote, serial), timeout=15)
        if not cap_result.success:
            return cap_result
        return self.pull(remote, local_path, serial)

    # ---------- async runner factory for long-running/streaming commands ----------

    def new_runner(self) -> AsyncProcessRunner:
        return AsyncProcessRunner()

    def build_args(self, kind: str, **kwargs) -> list[str]:
        """Builds argument lists for commands that are typically run via
        an AsyncProcessRunner (install, install-multiple, push, pull,
        logcat, screenrecord, shell session) so callers can validate +
        run them asynchronously from the page code."""
        builders = {
            "install": cmd.install_apk,
            "install_multiple": cmd.install_multiple_apks,
            "push": cmd.push_file,
            "pull": cmd.pull_file,
            "logcat": cmd.logcat,
            "screenrecord": cmd.screenrecord,
            "shell": cmd.shell,
        }
        builder = builders.get(kind)
        if not builder:
            raise ValueError(f"Unknown async command kind: {kind}")
        return builder(self.adb_path, **kwargs)
