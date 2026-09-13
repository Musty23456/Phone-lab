"""
driver_info.py

Reports Windows USB/driver information relevant to Android servicing:
connected Android-related USB devices (via PnP utility), and whether
adb/fastboot are currently reachable. Does not install or modify any
driver - only reports status and gives the user guidance.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from app.utils.process_runner import run_sync
from app.utils import platform_tools


@dataclass
class UsbDeviceEntry:
    instance_id: str
    description: str
    status: str


ANDROID_HINTS = ("android", "adb", "composite", "usb", "adb interface", "bootloader")


def list_usb_devices() -> tuple[list[UsbDeviceEntry], str]:
    """Uses Windows' built-in pnputil to enumerate USB devices. Returns
    an empty list with a note on non-Windows platforms (dev/test)."""
    if os.name != "nt":
        return [], "Driver enumeration is only available on Windows."

    result = run_sync(["pnputil", "/enum-devices", "/connected"], timeout=15)
    if not result.success:
        return [], "Unable to query Windows PnP device list (pnputil unavailable)."

    entries: list[UsbDeviceEntry] = []
    block: dict[str, str] = {}
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            if block:
                entries.append(_block_to_entry(block))
                block = {}
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            block[key.strip()] = value.strip()
    if block:
        entries.append(_block_to_entry(block))

    android_related = [
        e for e in entries
        if any(hint in e.description.lower() for hint in ANDROID_HINTS)
    ]
    return android_related, ""


def _block_to_entry(block: dict) -> UsbDeviceEntry:
    return UsbDeviceEntry(
        instance_id=block.get("Instance ID", "Unknown"),
        description=block.get("Device Description", block.get("Device Name", "Unknown")),
        status=block.get("Status", "Unknown"),
    )


def tool_availability_summary(adb_custom: str = "", fastboot_custom: str = "") -> dict:
    adb_status = platform_tools.get_adb_status(adb_custom or None)
    fastboot_status = platform_tools.get_fastboot_status(fastboot_custom or None)
    return {
        "adb_found": adb_status.found,
        "adb_path": adb_status.path,
        "adb_version": adb_status.version,
        "fastboot_found": fastboot_status.found,
        "fastboot_path": fastboot_status.path,
        "fastboot_version": fastboot_status.version,
    }


DRIVER_TROUBLESHOOTING_TEXT = """\
If your device is not detected:

1. Enable Developer Options on the phone:
   Settings > About phone > tap "Build number" 7 times.
2. Enable USB debugging:
   Settings > System > Developer options > USB debugging.
3. Use a data-capable USB cable (some cables are charge-only).
4. When prompted on the phone, tap "Allow" on the
   "Allow USB debugging?" dialog and optionally check
   "Always allow from this computer".
5. If Windows shows an unknown device or "no driver" in Device
   Manager, install your phone manufacturer's official USB
   driver, or Google's "Google USB Driver" from the Android SDK
   Manager for Nexus/Pixel-class devices.
6. For Fastboot mode, some manufacturers require a separate
   Fastboot/bootloader driver, distinct from the ADB driver -
   check your manufacturer's developer/support pages.
7. Try a different USB port, preferably a USB 2.0 port directly
   on the motherboard rather than a front-panel hub.
"""
