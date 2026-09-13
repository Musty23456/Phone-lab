"""
drivers_page.py

Reports connected Android USB devices (Windows), ADB/Fastboot tool
availability, and provides driver troubleshooting guidance. Never
installs drivers automatically.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from app.drivers.driver_info import (
    DRIVER_TROUBLESHOOTING_TEXT, list_usb_devices, tool_availability_summary,
)


class DriversPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("Driver Management")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Driver / Tool Status")
        refresh_btn.setObjectName("PrimaryButton")
        row.addWidget(refresh_btn)
        row.addStretch(1)
        outer.addLayout(row)

        self.status_view = QPlainTextEdit()
        self.status_view.setReadOnly(True)
        self.status_view.setObjectName("TerminalOutput")
        self.status_view.setMaximumBlockCount(4000)
        outer.addWidget(self.status_view, 1)

        outer.addWidget(QLabel("Troubleshooting"))
        self.troubleshoot_view = QPlainTextEdit()
        self.troubleshoot_view.setReadOnly(True)
        self.troubleshoot_view.setPlainText(DRIVER_TROUBLESHOOTING_TEXT)
        outer.addWidget(self.troubleshoot_view, 1)

        refresh_btn.clicked.connect(self._refresh)
        self._refresh()

    def _refresh(self):
        self.status_view.clear()
        summary = tool_availability_summary(
            self.ctx.settings.get("adb_custom_path"),
            self.ctx.settings.get("fastboot_custom_path"),
        )
        self.status_view.appendPlainText("-- Tool Availability --")
        self.status_view.appendPlainText(f"ADB found       : {summary['adb_found']}")
        self.status_view.appendPlainText(f"ADB path        : {summary['adb_path']}")
        self.status_view.appendPlainText(f"ADB version     : {summary['adb_version']}")
        self.status_view.appendPlainText(f"Fastboot found  : {summary['fastboot_found']}")
        self.status_view.appendPlainText(f"Fastboot path   : {summary['fastboot_path']}")
        self.status_view.appendPlainText(f"Fastboot version: {summary['fastboot_version']}")

        entries, note = list_usb_devices()
        self.status_view.appendPlainText("")
        self.status_view.appendPlainText("-- Connected Android-related USB Devices --")
        if note:
            self.status_view.appendPlainText(note)
        elif not entries:
            self.status_view.appendPlainText("No Android-related USB devices detected.")
        else:
            for e in entries:
                self.status_view.appendPlainText(f"{e.description}  [{e.status}]  ({e.instance_id})")
