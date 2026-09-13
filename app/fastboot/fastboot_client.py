"""
fastboot_client.py

High-level Fastboot client. All destructive operations (flash, erase,
set-active) pass through validate_command() and are additionally gated
by an explicit confirmation dialog at the UI layer (see
ui/widgets/confirm_dialog.py) before ever reaching this client.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.fastboot import commands as cmd
from app.utils.process_runner import AsyncProcessRunner, CommandResult, run_sync
from app.utils.validators import validate_command


@dataclass
class FastbootDevice:
    serial: str
    state: str = "fastboot"


class FastbootClient:
    def __init__(self, fastboot_path: str):
        self.fastboot_path = fastboot_path

    def list_devices(self) -> list[FastbootDevice]:
        result = run_sync(cmd.devices(self.fastboot_path), timeout=10)
        devices: list[FastbootDevice] = []
        if not result.success:
            return devices
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            serial = parts[0]
            state = parts[1] if len(parts) > 1 else "fastboot"
            devices.append(FastbootDevice(serial=serial, state=state))
        return devices

    def getvar_all(self, serial: Optional[str] = None) -> dict[str, str]:
        # fastboot writes getvar output to stderr historically
        result = run_sync(cmd.getvar(self.fastboot_path, "all", serial), timeout=15)
        text = (result.stdout or "") + "\n" + (result.stderr or "")
        info: dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("(bootloader)"):
                line = line[len("(bootloader)"):].strip()
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if key:
                    info[key] = value
        return info

    def get_current_slot(self, serial: Optional[str] = None) -> str:
        result = run_sync(cmd.get_current_slot(self.fastboot_path, serial), timeout=10)
        text = (result.stdout or "") + (result.stderr or "")
        for line in text.splitlines():
            if "current-slot" in line:
                return line.split(":")[-1].strip()
        return "unknown"

    def reboot(self, mode: Optional[str] = None, serial: Optional[str] = None) -> CommandResult:
        args = cmd.reboot(self.fastboot_path, mode, serial)
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=15)

    def continue_boot(self, serial: Optional[str] = None) -> CommandResult:
        return run_sync(cmd.continue_boot(self.fastboot_path, serial), timeout=15)

    def flash_partition(self, partition: str, image_path: str, serial: Optional[str] = None) -> CommandResult:
        args = cmd.flash_partition(self.fastboot_path, partition, image_path, serial)
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=300)

    def erase_partition(self, partition: str, serial: Optional[str] = None) -> CommandResult:
        args = cmd.erase_partition(self.fastboot_path, partition, serial)
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=60)

    def boot_image(self, image_path: str, serial: Optional[str] = None) -> CommandResult:
        args = cmd.boot_image(self.fastboot_path, image_path, serial)
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=120)

    def set_active_slot(self, slot: str, serial: Optional[str] = None) -> CommandResult:
        args = cmd.set_active_slot(self.fastboot_path, slot, serial)
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=30)

    def run_raw(self, raw_args: list[str], serial: Optional[str] = None) -> CommandResult:
        """Used by the integrated terminal for arbitrary fastboot
        sub-commands the user types. Still validated - blocked patterns
        are refused before any process is spawned."""
        args = [self.fastboot_path]
        if serial:
            args += ["-s", serial]
        args += raw_args
        allowed, reason = validate_command(args)
        if not allowed:
            return CommandResult(command=" ".join(args), error=reason)
        return run_sync(args, timeout=60)

    def new_runner(self) -> AsyncProcessRunner:
        return AsyncProcessRunner()
