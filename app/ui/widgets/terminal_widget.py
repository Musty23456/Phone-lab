"""
terminal_widget.py

Reusable monospace output panel used by ADB Tools, Fastboot Tools, and
the integrated Terminal page. Shows streamed stdout/stderr plus a final
summary line (exit code + duration) when a command finishes.
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from app.utils.process_runner import CommandResult


class TerminalWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.output = QPlainTextEdit()
        self.output.setObjectName("TerminalOutput")
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(10000)
        layout.addWidget(self.output)

    def append_command(self, command_str: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.output.appendPlainText(f"\n[{stamp}] $ {command_str}")

    def append_stdout(self, text: str):
        self.output.appendPlainText(text.rstrip("\n"))

    def append_stderr(self, text: str):
        self.output.appendPlainText(text.rstrip("\n"))

    def append_result_summary(self, result: CommandResult):
        if result.error:
            self.output.appendPlainText(f"[error] {result.error}")
        self.output.appendPlainText(
            f"[exit code: {result.exit_code}] [duration: {result.duration_ms} ms]"
        )

    def append_result_full(self, result: CommandResult):
        self.append_command(result.command)
        if result.stdout:
            self.append_stdout(result.stdout)
        if result.stderr:
            self.append_stderr(result.stderr)
        self.append_result_summary(result)

    def clear(self):
        self.output.clear()

    def save_text(self) -> str:
        return self.output.toPlainText()
