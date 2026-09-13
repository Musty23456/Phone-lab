"""
settings_page.py

User-configurable preferences, persisted via SettingsManager (QSettings):
theme, custom tool paths, default directories, confirmation behavior,
auto-refresh interval, and language preparation (UI text stays English
for v1.0.0; the key exists for future localization).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from app.ui.widgets.confirm_dialog import show_info


class SettingsPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("Settings")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        form.addRow("Theme:", self.theme_combo)

        self.adb_path_edit, adb_row = self._path_row("Custom ADB folder (optional)")
        form.addRow("ADB Path:", adb_row)

        self.fastboot_path_edit, fastboot_row = self._path_row("Custom Fastboot folder (optional)")
        form.addRow("Fastboot Path:", fastboot_row)

        self.scrcpy_path_edit, scrcpy_row = self._path_row("Custom scrcpy folder (optional)")
        form.addRow("scrcpy Path:", scrcpy_row)

        self.download_dir_edit, download_row = self._path_row("Default download/output directory")
        form.addRow("Download Directory:", download_row)

        self.log_dir_edit, log_row = self._path_row("Default log export directory")
        form.addRow("Log Directory:", log_row)

        self.confirm_checkbox = QCheckBox("Require confirmation for destructive operations")
        form.addRow("", self.confirm_checkbox)

        self.auto_refresh_checkbox = QCheckBox("Automatically refresh connected devices")
        form.addRow("", self.auto_refresh_checkbox)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(500, 30000)
        self.interval_spin.setSingleStep(500)
        self.interval_spin.setSuffix(" ms")
        form.addRow("Refresh Interval:", self.interval_spin)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["en"])
        form.addRow("Language (prepared):", self.language_combo)

        outer.addLayout(form)

        button_row = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("PrimaryButton")
        reset_btn = QPushButton("Reset to Defaults")
        button_row.addWidget(save_btn)
        button_row.addWidget(reset_btn)
        button_row.addStretch(1)
        outer.addLayout(button_row)
        outer.addStretch(1)

        save_btn.clicked.connect(self._save)
        reset_btn.clicked.connect(self._reset)

    def _path_row(self, placeholder: str):
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self._browse_into(edit))
        layout.addWidget(edit, 1)
        layout.addWidget(browse_btn)
        return edit, row_widget

    def _browse_into(self, edit: QLineEdit):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder")
        if directory:
            edit.setText(directory)

    def _load_current(self):
        s = self.ctx.settings
        self.theme_combo.setCurrentText(s.get("theme"))
        self.adb_path_edit.setText(s.get("adb_custom_path"))
        self.fastboot_path_edit.setText(s.get("fastboot_custom_path"))
        self.scrcpy_path_edit.setText(s.get("scrcpy_custom_path"))
        self.download_dir_edit.setText(s.get("download_dir"))
        self.log_dir_edit.setText(s.get("log_dir"))
        self.confirm_checkbox.setChecked(s.get("confirm_destructive"))
        self.auto_refresh_checkbox.setChecked(s.get("auto_refresh_devices"))
        self.interval_spin.setValue(s.get("auto_refresh_interval_ms"))
        self.language_combo.setCurrentText(s.get("language"))

    def _save(self):
        s = self.ctx.settings
        s.set("theme", self.theme_combo.currentText())
        s.set("adb_custom_path", self.adb_path_edit.text().strip())
        s.set("fastboot_custom_path", self.fastboot_path_edit.text().strip())
        s.set("scrcpy_custom_path", self.scrcpy_path_edit.text().strip())
        s.set("download_dir", self.download_dir_edit.text().strip())
        s.set("log_dir", self.log_dir_edit.text().strip())
        s.set("confirm_destructive", self.confirm_checkbox.isChecked())
        s.set("auto_refresh_devices", self.auto_refresh_checkbox.isChecked())
        s.set("auto_refresh_interval_ms", self.interval_spin.value())
        s.set("language", self.language_combo.currentText())
        self.ctx.apply_settings_changes()
        show_info(self, "Settings Saved", "Your preferences have been saved.")

    def _reset(self):
        self.ctx.settings.reset_defaults()
        self._load_current()
        self.ctx.apply_settings_changes()
        show_info(self, "Settings Reset", "Settings restored to defaults.")
