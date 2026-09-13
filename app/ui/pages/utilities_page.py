"""
utilities_page.py

Integrated command terminal (ADB / Fastboot mode toggle, arbitrary
command entry with validation) plus a Platform Tools manager panel
showing detected adb/fastboot binaries and their source.
"""
from __future__ import annotations

import shlex

from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from app.adb.adb_client import AdbClient
from app.fastboot.fastboot_client import FastbootClient
from app.ui.widgets.confirm_dialog import confirm_destructive, show_error
from app.ui.widgets.terminal_widget import TerminalWidget
from app.utils import platform_tools
from app.utils.validators import is_destructive, validate_command


class UtilitiesPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("Utilities - Integrated Terminal")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["ADB", "Fastboot"])
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch(1)
        outer.addLayout(mode_row)

        cmd_row = QHBoxLayout()
        self.command_edit = QLineEdit()
        self.command_edit.setPlaceholderText("e.g. shell pm list packages   or   getvar all")
        self.command_edit.returnPressed.connect(self._execute)
        run_btn = QPushButton("Run")
        run_btn.setObjectName("PrimaryButton")
        cmd_row.addWidget(self.command_edit, 1)
        cmd_row.addWidget(run_btn)
        outer.addLayout(cmd_row)

        outer.addWidget(QLabel(
            "Enter arguments only (without 'adb'/'fastboot'). Destructive commands "
            "(erase, flash, format, delete, uninstall, disable, ...) require confirmation. "
            "Bypass/unlock/IMEI-related commands are always blocked."
        ))

        self.terminal = TerminalWidget()
        outer.addWidget(self.terminal, 1)

        outer.addWidget(QLabel("Platform Tools"))
        tools_row = QHBoxLayout()
        detect_btn = QPushButton("Detect Platform Tools")
        tools_row.addWidget(detect_btn)
        tools_row.addStretch(1)
        outer.addLayout(tools_row)

        run_btn.clicked.connect(self._execute)
        detect_btn.clicked.connect(self._detect_tools)

    def _execute(self):
        text = self.command_edit.text().strip()
        if not text:
            return
        try:
            arg_list = shlex.split(text)
        except ValueError as exc:
            show_error(self, "Invalid Command", f"Could not parse command: {exc}")
            return

        mode = self.mode_combo.currentText()
        if mode == "ADB":
            if not self.ctx.adb_path:
                show_error(self, "ADB Not Found", "ADB was not detected.")
                return
            full_args = [self.ctx.adb_path]
            if self.ctx.active_adb_serial:
                full_args += ["-s", self.ctx.active_adb_serial]
            full_args += arg_list
        else:
            if not self.ctx.fastboot_path:
                show_error(self, "Fastboot Not Found", "Fastboot was not detected.")
                return
            full_args = [self.ctx.fastboot_path]
            if self.ctx.active_fastboot_serial:
                full_args += ["-s", self.ctx.active_fastboot_serial]
            full_args += arg_list

        allowed, reason = validate_command(full_args)
        if not allowed:
            show_error(self, "Command Blocked", reason)
            self.terminal.append_stdout(f"[blocked] {reason}")
            return

        if is_destructive(text):
            if not confirm_destructive(
                self, "Confirm Destructive Command",
                f"This command looks destructive: '{text}'. Proceed?",
                require_type_confirm=True,
            ):
                return

        from app.utils.process_runner import run_sync
        result = run_sync(full_args, timeout=60)
        self.terminal.append_result_full(result)
        self.command_edit.clear()

    def _detect_tools(self):
        adb_status = platform_tools.get_adb_status(self.ctx.settings.get("adb_custom_path"))
        fastboot_status = platform_tools.get_fastboot_status(self.ctx.settings.get("fastboot_custom_path"))
        self.terminal.append_stdout("-- Platform Tools Detection --")
        self.terminal.append_stdout(
            f"ADB: found={adb_status.found} source={adb_status.source} path={adb_status.path} version={adb_status.version}"
        )
        self.terminal.append_stdout(
            f"Fastboot: found={fastboot_status.found} source={fastboot_status.source} "
            f"path={fastboot_status.path} version={fastboot_status.version}"
        )
