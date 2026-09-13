"""
dashboard.py

Landing page: shows connected-device summary and quick action buttons
(Refresh, ADB Mode, Fastboot Mode, Recovery, Reboot, Power Off).
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from app.adb.adb_client import AdbClient
from app.device.device_info import DeviceInfo, build_device_info
from app.ui.widgets.confirm_dialog import confirm_destructive, show_error
from app.ui.widgets.device_status_card import StatCard


class DashboardPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._build_ui()
        self.ctx.device_state_changed.connect(self.refresh)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Dashboard")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)

        self.device_headline = QLabel("Device: No device connected")
        self.device_headline.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(self.device_headline)

        grid = QGridLayout()
        grid.setSpacing(12)
        self.cards = {
            "connection": StatCard("Connection"),
            "manufacturer": StatCard("Manufacturer"),
            "model": StatCard("Model"),
            "android": StatCard("Android Version"),
            "build": StatCard("Build Number"),
            "battery": StatCard("Battery"),
            "storage": StatCard("Storage"),
            "ram": StatCard("RAM"),
            "cpu": StatCard("CPU Architecture"),
            "resolution": StatCard("Screen Resolution"),
            "serial": StatCard("Serial Number"),
            "temp": StatCard("Battery Temperature"),
        }
        positions = list(self.cards.keys())
        for i, key in enumerate(positions):
            grid.addWidget(self.cards[key], i // 4, i % 4)
        layout.addLayout(grid)

        button_row = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh Device")
        self.btn_refresh.setObjectName("PrimaryButton")
        self.btn_adb_mode = QPushButton("ADB Mode")
        self.btn_fastboot_mode = QPushButton("Fastboot Mode")
        self.btn_recovery = QPushButton("Recovery")
        self.btn_reboot = QPushButton("Reboot")
        self.btn_power_off = QPushButton("Power Off")
        self.btn_power_off.setObjectName("DangerButton")

        for btn in (self.btn_refresh, self.btn_adb_mode, self.btn_fastboot_mode,
                    self.btn_recovery, self.btn_reboot, self.btn_power_off):
            button_row.addWidget(btn)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        layout.addStretch(1)

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_adb_mode.clicked.connect(self._reboot_system)
        self.btn_fastboot_mode.clicked.connect(self._reboot_bootloader)
        self.btn_recovery.clicked.connect(self._reboot_recovery)
        self.btn_reboot.clicked.connect(self._reboot_system)
        self.btn_power_off.clicked.connect(self._power_off)

    # ---------- data refresh ----------

    def refresh(self, *_):
        serial = self.ctx.active_adb_serial
        adb_path = self.ctx.adb_path
        if not serial or not adb_path:
            self.device_headline.setText("Device: No device connected")
            for card in self.cards.values():
                card.set_value("-")
            return

        client = AdbClient(adb_path)
        info: DeviceInfo = build_device_info(client, serial)
        self.device_headline.setText(f"Device: {info.manufacturer} {info.model}")

        self.cards["connection"].set_value(info.connection)
        self.cards["manufacturer"].set_value(info.manufacturer)
        self.cards["model"].set_value(info.model)
        self.cards["android"].set_value(info.android_version)
        self.cards["build"].set_value(info.build_number)
        battery_text = f"{info.battery_percent}%" if info.battery_percent is not None else "Unknown"
        if info.charging:
            battery_text += " (charging)"
        self.cards["battery"].set_value(battery_text)
        self.cards["storage"].set_value(info.storage_summary)
        self.cards["ram"].set_value(f"{info.ram_total_mb} MB" if info.ram_total_mb else "Unknown")
        self.cards["cpu"].set_value(info.cpu_abi)
        self.cards["resolution"].set_value(info.screen_resolution)
        self.cards["serial"].set_value(info.serial)
        temp_text = f"{info.battery_temperature_c} °C" if info.battery_temperature_c is not None else "Unknown"
        self.cards["temp"].set_value(temp_text)

    # ---------- quick actions ----------

    def _require_client(self) -> Optional[AdbClient]:
        if not self.ctx.adb_path or not self.ctx.active_adb_serial:
            show_error(self, "No Device", "No ADB device is currently connected.")
            return None
        return AdbClient(self.ctx.adb_path)

    def _reboot_system(self):
        client = self._require_client()
        if not client:
            return
        client.reboot(None, self.ctx.active_adb_serial)

    def _reboot_bootloader(self):
        client = self._require_client()
        if not client:
            return
        if confirm_destructive(self, "Reboot to Fastboot",
                                "The device will reboot into Fastboot/Bootloader mode."):
            client.reboot("bootloader", self.ctx.active_adb_serial)

    def _reboot_recovery(self):
        client = self._require_client()
        if not client:
            return
        if confirm_destructive(self, "Reboot to Recovery",
                                "The device will reboot into Recovery mode."):
            client.reboot("recovery", self.ctx.active_adb_serial)

    def _power_off(self):
        client = self._require_client()
        if not client:
            return
        if confirm_destructive(self, "Power Off Device",
                                "This will power off the connected device."):
            client.shell_sync("reboot -p", self.ctx.active_adb_serial)
