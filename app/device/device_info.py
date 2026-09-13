"""
device_info.py

Aggregates raw adb getprop/dumpsys output into a structured DeviceInfo
object used across the Dashboard and Diagnostics pages.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from app.adb.adb_client import AdbClient

PROP_MANUFACTURER = "ro.product.manufacturer"
PROP_MODEL = "ro.product.model"
PROP_BRAND = "ro.product.brand"
PROP_ANDROID_VERSION = "ro.build.version.release"
PROP_SDK = "ro.build.version.sdk"
PROP_BUILD_ID = "ro.build.display.id"
PROP_SECURITY_PATCH = "ro.build.version.security_patch"
PROP_CPU_ABI = "ro.product.cpu.abi"
PROP_SERIAL = "ro.serialno"
PROP_BOOTLOADER_STATE = "ro.boot.verifiedbootstate"


@dataclass
class DeviceInfo:
    serial: str = ""
    connection: str = "ADB"
    manufacturer: str = "Unknown"
    model: str = "Unknown"
    brand: str = "Unknown"
    android_version: str = "Unknown"
    sdk_version: str = "Unknown"
    build_number: str = "Unknown"
    security_patch: str = "Unknown"
    bootloader_state: str = "Unknown"
    cpu_abi: str = "Unknown"
    battery_percent: Optional[int] = None
    battery_temperature_c: Optional[float] = None
    battery_voltage_v: Optional[float] = None
    battery_status: str = "Unknown"
    battery_health: str = "Unknown"
    charging: bool = False
    ram_total_mb: Optional[int] = None
    storage_summary: str = "Unknown"
    screen_resolution: str = "Unknown"

    def as_dict(self) -> dict:
        return {
            "serial": self.serial,
            "connection": self.connection,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "brand": self.brand,
            "android_version": self.android_version,
            "sdk_version": self.sdk_version,
            "build_number": self.build_number,
            "security_patch": self.security_patch,
            "bootloader_state": self.bootloader_state,
            "cpu_abi": self.cpu_abi,
            "battery_percent": self.battery_percent,
            "battery_temperature_c": self.battery_temperature_c,
            "battery_voltage_v": self.battery_voltage_v,
            "battery_status": self.battery_status,
            "battery_health": self.battery_health,
            "charging": self.charging,
            "ram_total_mb": self.ram_total_mb,
            "storage_summary": self.storage_summary,
            "screen_resolution": self.screen_resolution,
        }


_BATTERY_STATUS_MAP = {
    "1": "Unknown",
    "2": "Charging",
    "3": "Discharging",
    "4": "Not charging",
    "5": "Full",
}

_BATTERY_HEALTH_MAP = {
    "1": "Unknown",
    "2": "Good",
    "3": "Overheat",
    "4": "Dead",
    "5": "Over voltage",
    "6": "Unspecified failure",
    "7": "Cold",
}


def parse_meminfo_total_mb(meminfo_text: str) -> Optional[int]:
    match = re.search(r"MemTotal:\s+(\d+)\s*kB", meminfo_text)
    if match:
        return int(match.group(1)) // 1024
    return None


def build_device_info(client: AdbClient, serial: str) -> DeviceInfo:
    """Query a connected ADB device and assemble a DeviceInfo snapshot.
    Every lookup is defensive - a failed/missing property never raises,
    it just leaves the corresponding field at its default."""
    info = DeviceInfo(serial=serial, connection="ADB")

    props = client.getprop_all(serial)
    info.manufacturer = props.get(PROP_MANUFACTURER, "Unknown").title()
    info.model = props.get(PROP_MODEL, "Unknown")
    info.brand = props.get(PROP_BRAND, "Unknown").title()
    info.android_version = props.get(PROP_ANDROID_VERSION, "Unknown")
    info.sdk_version = props.get(PROP_SDK, "Unknown")
    info.build_number = props.get(PROP_BUILD_ID, "Unknown")
    info.security_patch = props.get(PROP_SECURITY_PATCH, "Unknown")
    info.cpu_abi = props.get(PROP_CPU_ABI, "Unknown")
    info.bootloader_state = props.get(PROP_BOOTLOADER_STATE, "Unknown")

    battery = client.battery_info(serial)
    level = battery.get("level")
    if level and level.isdigit():
        info.battery_percent = int(level)
    temp = battery.get("temperature")
    if temp and temp.lstrip("-").isdigit():
        info.battery_temperature_c = int(temp) / 10.0
    voltage = battery.get("voltage")
    if voltage and voltage.isdigit():
        info.battery_voltage_v = int(voltage) / 1000.0
    status_code = battery.get("status")
    info.battery_status = _BATTERY_STATUS_MAP.get(status_code, "Unknown")
    health_code = battery.get("health")
    info.battery_health = _BATTERY_HEALTH_MAP.get(health_code, "Unknown")
    ac_powered = battery.get("AC powered", "false").lower() == "true"
    usb_powered = battery.get("USB powered", "false").lower() == "true"
    info.charging = ac_powered or usb_powered or info.battery_status == "Charging"

    meminfo_text = client.meminfo(serial)
    info.ram_total_mb = parse_meminfo_total_mb(meminfo_text)

    storage_raw = client.storage_info(serial)
    info.storage_summary = _summarize_storage(storage_raw)

    info.screen_resolution = client.screen_resolution(serial) or "Unknown"

    return info


def _summarize_storage(df_output: str) -> str:
    for line in df_output.splitlines():
        if line.strip().endswith("/data") or "/data" in line:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    size_kb = int(parts[1])
                    used_kb = int(parts[2])
                    return f"{used_kb / 1024 / 1024:.1f} GB used / {size_kb / 1024 / 1024:.1f} GB total"
                except (ValueError, IndexError):
                    continue
    return "Unavailable"
