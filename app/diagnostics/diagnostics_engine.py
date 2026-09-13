"""
diagnostics_engine.py

Runs a full diagnostic pass against a connected device and produces a
structured report that the Diagnostics page can render and export as
TXT or JSON.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.adb.adb_client import AdbClient
from app.device.device_info import DeviceInfo, build_device_info
from app.utils import platform_tools


@dataclass
class DiagnosticReport:
    generated_at: str
    device: DeviceInfo
    adb_status: dict
    fastboot_status: dict
    connection: dict

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "generated_by": "ALMUS PHONE LAB",
            "device": self.device.as_dict(),
            "tools": {
                "adb": self.adb_status,
                "fastboot": self.fastboot_status,
            },
            "connection": self.connection,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_text(self) -> str:
        d = self.device
        lines = [
            "=" * 60,
            "ALMUS PHONE LAB - DEVICE DIAGNOSTIC REPORT",
            "=" * 60,
            f"Generated: {self.generated_at}",
            "",
            "-- HARDWARE --",
            f"Manufacturer     : {d.manufacturer}",
            f"Model            : {d.model}",
            f"Brand            : {d.brand}",
            f"CPU ABI          : {d.cpu_abi}",
            f"RAM Total        : {d.ram_total_mb} MB" if d.ram_total_mb else "RAM Total        : Unknown",
            f"Storage          : {d.storage_summary}",
            f"Screen Resolution: {d.screen_resolution}",
            "",
            "-- SOFTWARE --",
            f"Android Version  : {d.android_version}",
            f"SDK Version      : {d.sdk_version}",
            f"Build Number     : {d.build_number}",
            f"Security Patch   : {d.security_patch}",
            f"Bootloader State : {d.bootloader_state}",
            "",
            "-- BATTERY --",
            f"Percentage       : {d.battery_percent}%" if d.battery_percent is not None else "Percentage       : Unknown",
            f"Temperature      : {d.battery_temperature_c} C" if d.battery_temperature_c is not None else "Temperature      : Unknown",
            f"Voltage          : {d.battery_voltage_v} V" if d.battery_voltage_v is not None else "Voltage          : Unknown",
            f"Status           : {d.battery_status}",
            f"Health           : {d.battery_health}",
            f"Charging         : {'Yes' if d.charging else 'No'}",
            "",
            "-- CONNECTION --",
            f"Serial           : {d.serial}",
            f"Connection Type  : {d.connection}",
            f"ADB Available    : {self.adb_status.get('found')}",
            f"Fastboot Available: {self.fastboot_status.get('found')}",
            "=" * 60,
        ]
        return "\n".join(lines)


def run_full_diagnostic(adb_path: Optional[str], fastboot_path: Optional[str],
                         serial: str) -> DiagnosticReport:
    adb_status_obj = platform_tools.get_adb_status(adb_path)
    fastboot_status_obj = platform_tools.get_fastboot_status(fastboot_path)

    device_info = DeviceInfo(serial=serial)
    if adb_path:
        client = AdbClient(adb_path)
        device_info = build_device_info(client, serial)

    connection = {
        "usb_state": "connected" if serial else "no device",
    }

    return DiagnosticReport(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        device=device_info,
        adb_status={
            "found": adb_status_obj.found,
            "path": adb_status_obj.path,
            "version": adb_status_obj.version,
            "source": adb_status_obj.source,
        },
        fastboot_status={
            "found": fastboot_status_obj.found,
            "path": fastboot_status_obj.path,
            "version": fastboot_status_obj.version,
            "source": fastboot_status_obj.source,
        },
        connection=connection,
    )
