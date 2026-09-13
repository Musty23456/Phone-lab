"""
commands.py (fastboot)

Pure functions that build fastboot argument lists. No process execution
here - keeps this module trivially unit-testable.
"""
from __future__ import annotations

from typing import Optional


def _base(fastboot_path: str, serial: Optional[str] = None) -> list[str]:
    args = [fastboot_path]
    if serial:
        args += ["-s", serial]
    return args


def devices(fastboot_path: str) -> list[str]:
    return [fastboot_path, "devices"]


def getvar(fastboot_path: str, var: str = "all", serial: Optional[str] = None) -> list[str]:
    return _base(fastboot_path, serial) + ["getvar", var]


def reboot(fastboot_path: str, mode: Optional[str] = None, serial: Optional[str] = None) -> list[str]:
    args = _base(fastboot_path, serial) + ["reboot"]
    if mode:
        args.append(mode)  # "bootloader" | "recovery" | "fastboot"
    return args


def continue_boot(fastboot_path: str, serial: Optional[str] = None) -> list[str]:
    return _base(fastboot_path, serial) + ["continue"]


def flash_partition(fastboot_path: str, partition: str, image_path: str,
                     serial: Optional[str] = None) -> list[str]:
    return _base(fastboot_path, serial) + ["flash", partition, image_path]


def erase_partition(fastboot_path: str, partition: str, serial: Optional[str] = None) -> list[str]:
    return _base(fastboot_path, serial) + ["erase", partition]


def boot_image(fastboot_path: str, image_path: str, serial: Optional[str] = None) -> list[str]:
    return _base(fastboot_path, serial) + ["boot", image_path]


def get_current_slot(fastboot_path: str, serial: Optional[str] = None) -> list[str]:
    return getvar(fastboot_path, "current-slot", serial)


def set_active_slot(fastboot_path: str, slot: str, serial: Optional[str] = None) -> list[str]:
    return _base(fastboot_path, serial) + ["--set-active=" + slot]


def oem_command(fastboot_path: str, oem_args: str, serial: Optional[str] = None) -> list[str]:
    """Generic passthrough for vendor-safe 'fastboot oem <subcommand>'
    calls the user explicitly types in the terminal. Still passes through
    validate_command() at the client layer, which blocks bypass-related
    subcommands regardless of what is typed here."""
    return _base(fastboot_path, serial) + ["oem"] + oem_args.split()
