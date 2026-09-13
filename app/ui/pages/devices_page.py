"""
devices_page.py

Shows every currently detected ADB and Fastboot device, and lets the
user pick which one is "active" for the rest of the app (dashboard,
tools pages) when multiple devices are plugged in.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


class DevicesPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._build_ui()
        self.ctx.devices_updated.connect(self.refresh)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("Devices")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)

        layout.addWidget(QLabel("ADB Devices"))
        self.adb_table = QTableWidget(0, 3)
        self.adb_table.setHorizontalHeaderLabels(["Serial", "State", "Details"])
        self.adb_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.adb_table.verticalHeader().setVisible(False)
        layout.addWidget(self.adb_table)

        layout.addWidget(QLabel("Fastboot Devices"))
        self.fastboot_table = QTableWidget(0, 2)
        self.fastboot_table.setHorizontalHeaderLabels(["Serial", "State"])
        self.fastboot_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.fastboot_table.verticalHeader().setVisible(False)
        layout.addWidget(self.fastboot_table)

        self.set_active_btn = QPushButton("Set Selected ADB Device as Active")
        self.set_active_btn.setObjectName("PrimaryButton")
        self.set_active_btn.clicked.connect(self._set_active_from_selection)
        layout.addWidget(self.set_active_btn)

        layout.addStretch(1)

    def refresh(self, adb_devices, fastboot_devices):
        self.adb_table.setRowCount(len(adb_devices))
        for row, dev in enumerate(adb_devices):
            self.adb_table.setItem(row, 0, QTableWidgetItem(dev.serial))
            self.adb_table.setItem(row, 1, QTableWidgetItem(dev.state))
            self.adb_table.setItem(row, 2, QTableWidgetItem(dev.extra))

        self.fastboot_table.setRowCount(len(fastboot_devices))
        for row, dev in enumerate(fastboot_devices):
            self.fastboot_table.setItem(row, 0, QTableWidgetItem(dev.serial))
            self.fastboot_table.setItem(row, 1, QTableWidgetItem(dev.state))

    def _set_active_from_selection(self):
        selected = self.adb_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        serial_item = self.adb_table.item(row, 0)
        if serial_item:
            self.ctx.set_active_adb_serial(serial_item.text())
