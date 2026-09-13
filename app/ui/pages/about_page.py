"""
about_page.py

Static About page: version, developer, licensing, and attributions.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

VERSION = "1.0.0"

ABOUT_TEXT = f"""\
ALMUS PHONE LAB
Version {VERSION}

Developed by:
ALMUS PRODUCTION

A professional Android phone servicing, diagnostics, ADB, Fastboot,
APK management, and device-management toolkit for Windows.

--------------------------------------------------------------------
Project
--------------------------------------------------------------------
GitHub: https://github.com/<your-username>/ALMUS_PHONE_LAB
  (replace with your actual repository URL after publishing)

--------------------------------------------------------------------
Open-Source Licenses & Attributions
--------------------------------------------------------------------
- PySide6 (Qt for Python) - LGPL v3 / Commercial, https://www.qt.io
- Android SDK Platform Tools (adb, fastboot) - distributed by Google
  under the Android SDK License; not redistributed by this project.
  https://developer.android.com/tools/releases/platform-tools
- scrcpy (optional screen mirroring, if provided by the user) -
  Apache License 2.0. https://github.com/Genymobile/scrcpy
- PyInstaller - GPL v2 with an exception permitting distribution of
  the bundled application. https://pyinstaller.org

--------------------------------------------------------------------
Intended Use
--------------------------------------------------------------------
ALMUS PHONE LAB is designed for legitimate, owner-authorized Android
device servicing, diagnostics, and repair workflows. It does not
implement or support FRP bypass, account-lock bypass, IMEI
modification, or any other circumvention of device security or
ownership protections.
"""


class AboutPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("About")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)

        text_view = QPlainTextEdit()
        text_view.setReadOnly(True)
        text_view.setPlainText(ABOUT_TEXT)
        layout.addWidget(text_view)
