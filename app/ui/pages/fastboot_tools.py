"""
fastboot_tools.py

Fastboot Tools page. Safe informational commands (devices, getvar,
reboot, current-slot) execute immediately. Destructive commands (flash,
erase, set-active) always require the DestructiveActionDialog, and
flash/erase additionally require typing CONFIRM.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from app.fastboot.fastboot_client import FastbootClient
from app.ui.widgets.confirm_dialog import confirm_destructive, show_error
from app.ui.widgets.terminal_widget import TerminalWidget


class FastbootToolsPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._build_ui()

    def _client(self) -> FastbootClient | None:
        if not self.ctx.fastboot_path:
            show_error(self, "Fastboot Not Found", "Fastboot was not detected. Check Settings / Drivers page.")
            return None
        return FastbootClient(self.ctx.fastboot_path)

    def _serial(self):
        return self.ctx.active_fastboot_serial

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("Fastboot Tools")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        warn = QLabel(
            "⚠️  Flashing and erasing partitions can permanently damage a device if used "
            "incorrectly. Only proceed if you know exactly what you are doing."
        )
        warn.setWordWrap(True)
        outer.addWidget(warn)

        row1 = QHBoxLayout()
        btn_devices = QPushButton("fastboot devices")
        btn_getvar = QPushButton("Get All Variables")
        btn_slot = QPushButton("Get Current Slot")
        for b in (btn_devices, btn_getvar, btn_slot):
            row1.addWidget(b)
        row1.addStretch(1)
        outer.addLayout(row1)

        row2 = QHBoxLayout()
        btn_reboot = QPushButton("Reboot")
        btn_reboot_bl = QPushButton("Reboot Bootloader")
        btn_reboot_recovery = QPushButton("Reboot Recovery")
        btn_continue = QPushButton("Continue Boot")
        for b in (btn_reboot, btn_reboot_bl, btn_reboot_recovery, btn_continue):
            row2.addWidget(b)
        row2.addStretch(1)
        outer.addLayout(row2)

        flash_row = QHBoxLayout()
        self.partition_edit = QLineEdit()
        self.partition_edit.setPlaceholderText("partition name (e.g. boot, recovery)")
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setPlaceholderText("Select image file (.img)")
        browse_btn = QPushButton("Browse")
        flash_btn = QPushButton("Flash Partition")
        flash_btn.setObjectName("DangerButton")
        erase_btn = QPushButton("Erase Partition")
        erase_btn.setObjectName("DangerButton")
        boot_btn = QPushButton("Boot Image")
        flash_row.addWidget(self.partition_edit)
        flash_row.addWidget(self.image_path_edit, 1)
        flash_row.addWidget(browse_btn)
        flash_row.addWidget(flash_btn)
        flash_row.addWidget(erase_btn)
        flash_row.addWidget(boot_btn)
        outer.addLayout(flash_row)

        slot_row = QHBoxLayout()
        self.slot_edit = QLineEdit()
        self.slot_edit.setPlaceholderText("a or b")
        set_slot_btn = QPushButton("Set Active Slot")
        set_slot_btn.setObjectName("DangerButton")
        slot_row.addWidget(QLabel("Slot:"))
        slot_row.addWidget(self.slot_edit)
        slot_row.addWidget(set_slot_btn)
        slot_row.addStretch(1)
        outer.addLayout(slot_row)

        self.terminal = TerminalWidget()
        outer.addWidget(self.terminal, 1)

        btn_devices.clicked.connect(self._list_devices)
        btn_getvar.clicked.connect(self._getvar_all)
        btn_slot.clicked.connect(self._current_slot)
        btn_reboot.clicked.connect(lambda: self._reboot(None))
        btn_reboot_bl.clicked.connect(lambda: self._reboot("bootloader"))
        btn_reboot_recovery.clicked.connect(lambda: self._reboot("recovery"))
        btn_continue.clicked.connect(self._continue_boot)
        browse_btn.clicked.connect(self._browse_image)
        flash_btn.clicked.connect(self._flash_partition)
        erase_btn.clicked.connect(self._erase_partition)
        boot_btn.clicked.connect(self._boot_image)
        set_slot_btn.clicked.connect(self._set_active_slot)

    def _list_devices(self):
        client = self._client()
        if not client:
            return
        devices = client.list_devices()
        self.terminal.append_command("fastboot devices")
        if not devices:
            self.terminal.append_stdout("No fastboot devices found.")
        for d in devices:
            self.terminal.append_stdout(f"{d.serial}\t{d.state}")

    def _getvar_all(self):
        client = self._client()
        if not client:
            return
        info = client.getvar_all(self._serial())
        self.terminal.append_command("fastboot getvar all")
        for k, v in info.items():
            self.terminal.append_stdout(f"{k}: {v}")

    def _current_slot(self):
        client = self._client()
        if not client:
            return
        self.terminal.append_command("fastboot getvar current-slot")
        self.terminal.append_stdout(client.get_current_slot(self._serial()))

    def _reboot(self, mode):
        client = self._client()
        if not client:
            return
        result = client.reboot(mode, self._serial())
        self.terminal.append_result_full(result)

    def _continue_boot(self):
        client = self._client()
        if not client:
            return
        self.terminal.append_result_full(client.continue_boot(self._serial()))

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", "Image Files (*.img);;All Files (*)")
        if path:
            self.image_path_edit.setText(path)

    def _flash_partition(self):
        client = self._client()
        partition = self.partition_edit.text().strip()
        image = self.image_path_edit.text().strip()
        if not client or not partition or not image:
            show_error(self, "Missing Info", "Enter a partition name and select an image file.")
            return
        if not confirm_destructive(
            self, "Confirm Flash Partition",
            f"This will FLASH partition '{partition}' with '{image}'. "
            "This can make the device unbootable if the wrong image or partition is used.",
            require_type_confirm=True,
        ):
            return
        result = client.flash_partition(partition, image, self._serial())
        self.terminal.append_result_full(result)

    def _erase_partition(self):
        client = self._client()
        partition = self.partition_edit.text().strip()
        if not client or not partition:
            show_error(self, "Missing Info", "Enter a partition name to erase.")
            return
        if not confirm_destructive(
            self, "Confirm Erase Partition",
            f"This will ERASE partition '{partition}'. This is destructive and cannot be undone.",
            require_type_confirm=True,
        ):
            return
        result = client.erase_partition(partition, self._serial())
        self.terminal.append_result_full(result)

    def _boot_image(self):
        client = self._client()
        image = self.image_path_edit.text().strip()
        if not client or not image:
            show_error(self, "Missing Info", "Select an image file to boot.")
            return
        result = client.boot_image(image, self._serial())
        self.terminal.append_result_full(result)

    def _set_active_slot(self):
        client = self._client()
        slot = self.slot_edit.text().strip()
        if not client or not slot:
            show_error(self, "Missing Info", "Enter a slot (a or b).")
            return
        if not confirm_destructive(
            self, "Confirm Set Active Slot",
            f"This will change the active boot slot to '{slot}'.",
        ):
            return
        result = client.set_active_slot(slot, self._serial())
        self.terminal.append_result_full(result)
