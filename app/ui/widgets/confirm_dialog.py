"""
confirm_dialog.py

Confirmation dialog required before any destructive operation (flash,
erase, format, delete, uninstall, package disable, etc.) is executed.
For the most dangerous operations (flash/erase), the user must type the
word CONFIRM to enable the action button - a plain Yes/No click is not
enough for these.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QMessageBox, QVBoxLayout,
)


class DestructiveActionDialog(QDialog):
    def __init__(self, title: str, message: str, require_type_confirm: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self._require_type_confirm = require_type_confirm

        layout = QVBoxLayout(self)

        warning_label = QLabel(f"⚠️  {message}")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        self._confirm_input = None
        if require_type_confirm:
            hint = QLabel("Type CONFIRM below to enable this action:")
            layout.addWidget(hint)
            self._confirm_input = QLineEdit()
            self._confirm_input.textChanged.connect(self._update_ok_state)
            layout.addWidget(self._confirm_input)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        if require_type_confirm:
            self._update_ok_state()

    def _update_ok_state(self):
        ok_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if self._require_type_confirm:
            ok_button.setEnabled(self._confirm_input.text().strip().upper() == "CONFIRM")
        else:
            ok_button.setEnabled(True)


def confirm_destructive(parent, title: str, message: str, require_type_confirm: bool = False) -> bool:
    """Convenience helper: shows the dialog and returns True only if the
    user explicitly confirmed."""
    dialog = DestructiveActionDialog(title, message, require_type_confirm, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted


def show_error(parent, title: str, message: str):
    QMessageBox.critical(parent, title, message)


def show_info(parent, title: str, message: str):
    QMessageBox.information(parent, title, message)
