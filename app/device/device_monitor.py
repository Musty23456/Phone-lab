"""
device_monitor.py

Polls `adb devices` and `fastboot devices` on a background QThread so the
GUI never freezes, and emits Qt signals whenever the connected-device
picture changes. The Dashboard/header status widgets connect to these
signals to update automatically on connect/disconnect.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QThread, Signal

from app.adb.adb_client import AdbClient
from app.fastboot.fastboot_client import FastbootClient


class DeviceMonitor(QThread):
    devices_changed = Signal(list, list)  # (adb_devices, fastboot_devices)
    error_occurred = Signal(str)

    def __init__(self, adb_path: Optional[str], fastboot_path: Optional[str],
                 interval_ms: int = 2000, parent=None):
        super().__init__(parent)
        self.adb_path = adb_path
        self.fastboot_path = fastboot_path
        self.interval_ms = max(500, interval_ms)
        self._running = False
        self._last_signature: Optional[tuple] = None

    def update_paths(self, adb_path: Optional[str], fastboot_path: Optional[str]):
        self.adb_path = adb_path
        self.fastboot_path = fastboot_path

    def set_interval(self, interval_ms: int):
        self.interval_ms = max(500, interval_ms)

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            adb_list = []
            fastboot_list = []
            try:
                if self.adb_path:
                    adb_list = AdbClient(self.adb_path).list_devices()
            except Exception as exc:  # never let the monitor thread die
                self.error_occurred.emit(f"ADB monitor error: {exc}")
            try:
                if self.fastboot_path:
                    fastboot_list = FastbootClient(self.fastboot_path).list_devices()
            except Exception as exc:
                self.error_occurred.emit(f"Fastboot monitor error: {exc}")

            signature = (
                tuple((d.serial, d.state) for d in adb_list),
                tuple((d.serial, d.state) for d in fastboot_list),
            )
            if signature != self._last_signature:
                self._last_signature = signature
                self.devices_changed.emit(adb_list, fastboot_list)

            self.msleep(self.interval_ms)
