"""
diagnostics_page.py

Runs a full device diagnostic and shows a categorized report, with
export to TXT or JSON.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from app.diagnostics.diagnostics_engine import run_full_diagnostic
from app.ui.widgets.confirm_dialog import show_error, show_info


class DiagnosticsPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._last_report = None
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("Device Diagnostics")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        run_row = QHBoxLayout()
        run_btn = QPushButton("Run Full Diagnostic")
        run_btn.setObjectName("PrimaryButton")
        export_txt_btn = QPushButton("Export as TXT")
        export_json_btn = QPushButton("Export as JSON")
        run_row.addWidget(run_btn)
        run_row.addWidget(export_txt_btn)
        run_row.addWidget(export_json_btn)
        run_row.addStretch(1)
        outer.addLayout(run_row)

        self.report_view = QPlainTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setObjectName("TerminalOutput")
        outer.addWidget(self.report_view, 1)

        run_btn.clicked.connect(self._run_diagnostic)
        export_txt_btn.clicked.connect(self._export_txt)
        export_json_btn.clicked.connect(self._export_json)

    def _run_diagnostic(self):
        serial = self.ctx.active_adb_serial
        if not serial:
            show_error(self, "No Device", "Connect a device over ADB before running diagnostics.")
            return
        report = run_full_diagnostic(self.ctx.adb_path, self.ctx.fastboot_path, serial)
        self._last_report = report
        self.report_view.setPlainText(report.to_text())

    def _export_txt(self):
        if not self._last_report:
            show_error(self, "No Report", "Run a diagnostic first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "almus_diagnostic_report.txt", "Text Files (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._last_report.to_text())
        show_info(self, "Exported", f"Report saved to {path}")

    def _export_json(self):
        if not self._last_report:
            show_error(self, "No Report", "Run a diagnostic first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "almus_diagnostic_report.json", "JSON Files (*.json)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._last_report.to_json())
        show_info(self, "Exported", f"Report saved to {path}")
