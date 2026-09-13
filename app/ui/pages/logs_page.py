"""
logs_page.py

Live ADB logcat viewer: start/pause/resume/clear streaming, search and
level-filter the buffered output, and export the current buffer to a
.log file.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from app.adb.adb_client import AdbClient
from app.logs.log_manager import LogManager
from app.ui.widgets.confirm_dialog import show_error, show_info


class LogsPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self.log_manager: LogManager | None = None
        self._runner = None
        self._build_ui()

    def _serial(self):
        return self.ctx.active_adb_serial

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("Logs")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        control_row = QHBoxLayout()
        self.start_btn = QPushButton("Start Logcat")
        self.start_btn.setObjectName("PrimaryButton")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.clear_view_btn = QPushButton("Clear View")
        self.clear_device_btn = QPushButton("Clear Device Buffer")
        self.export_btn = QPushButton("Export Log")
        for b in (self.start_btn, self.pause_btn, self.resume_btn, self.clear_view_btn,
                  self.clear_device_btn, self.export_btn):
            control_row.addWidget(b)
        outer.addLayout(control_row)

        filter_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search logs...")
        search_btn = QPushButton("Search")
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "V", "D", "I", "W", "E", "F"])
        filter_btn = QPushButton("Apply Level Filter")
        filter_row.addWidget(self.search_edit, 1)
        filter_row.addWidget(search_btn)
        filter_row.addWidget(QLabel("Level:"))
        filter_row.addWidget(self.level_combo)
        filter_row.addWidget(filter_btn)
        outer.addLayout(filter_row)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("TerminalOutput")
        self.log_view.setMaximumBlockCount(20000)
        outer.addWidget(self.log_view, 1)

        self.start_btn.clicked.connect(self._start)
        self.pause_btn.clicked.connect(self._pause)
        self.resume_btn.clicked.connect(self._resume)
        self.clear_view_btn.clicked.connect(self._clear_view)
        self.clear_device_btn.clicked.connect(self._clear_device)
        self.export_btn.clicked.connect(self._export)
        search_btn.clicked.connect(self._search)
        filter_btn.clicked.connect(self._filter_level)

    def _start(self):
        if not self.ctx.adb_path:
            show_error(self, "ADB Not Found", "ADB was not detected.")
            return
        if self._runner and self._runner.is_running():
            show_info(self, "Already Running", "Logcat is already streaming.")
            return
        client = AdbClient(self.ctx.adb_path)
        self.log_manager = LogManager(client)
        self.log_view.clear()
        self._runner = self.log_manager.start_stream(self._serial())
        self._runner.output_ready.connect(self._append_output)
        self._runner.error_ready.connect(self._append_output)

    def _append_output(self, text: str):
        if self.log_manager and self.log_manager.is_paused:
            return
        self.log_view.appendPlainText(text.rstrip("\n"))

    def _pause(self):
        if self.log_manager:
            self.log_manager.pause()

    def _resume(self):
        if self.log_manager:
            self.log_manager.resume()

    def _clear_view(self):
        self.log_view.clear()
        if self.log_manager:
            self.log_manager.clear_buffer()

    def _clear_device(self):
        if not self.ctx.adb_path:
            return
        LogManager(AdbClient(self.ctx.adb_path)).clear_device_logs(self._serial())
        show_info(self, "Cleared", "Device logcat buffer cleared.")

    def _export(self):
        if not self.log_manager:
            show_error(self, "Nothing To Export", "Start logcat first.")
            return
        default_name = LogManager.default_log_filename()
        path, _ = QFileDialog.getSaveFileName(self, "Export Log", default_name, "Log Files (*.log);;Text Files (*.txt)")
        if not path:
            return
        success, message = self.log_manager.export(path)
        if success:
            show_info(self, "Exported", f"Log saved to {message}")
        else:
            show_error(self, "Export Failed", message)

    def _search(self):
        if not self.log_manager:
            return
        results = self.log_manager.search(self.search_edit.text().strip())
        self.log_view.setPlainText("\n".join(results))

    def _filter_level(self):
        if not self.log_manager:
            return
        results = self.log_manager.filter_by_level(self.level_combo.currentText())
        self.log_view.setPlainText("\n".join(results))
