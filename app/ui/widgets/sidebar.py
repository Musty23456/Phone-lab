"""
sidebar.py

Left-hand navigation sidebar. Emits `page_selected(str)` with the page
key when a nav button is clicked. Buttons are checkable and mutually
exclusive via a QButtonGroup so the active page is always visually
highlighted.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QLabel, QPushButton, QVBoxLayout, QWidget

NAV_ITEMS = [
    ("dashboard", "🏠  Dashboard"),
    ("devices", "📱  Devices"),
    ("adb", "🔧  ADB Tools"),
    ("fastboot", "⚡  Fastboot Tools"),
    ("apk", "📦  APK Tools"),
    ("files", "🗂️  File Manager"),
    ("screen", "🖥️  Screen Tools"),
    ("diagnostics", "🩺  Diagnostics"),
    ("logs", "📜  Logs"),
    ("drivers", "🔌  Drivers"),
    ("utilities", "🛠️  Utilities"),
    ("settings", "⚙️  Settings"),
    ("about", "ℹ️  About"),
]


class Sidebar(QWidget):
    page_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(230)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)

        title = QLabel("ALMUS PHONE LAB")
        title.setObjectName("BrandTitle")
        subtitle = QLabel("by ALMUS PRODUCTION")
        subtitle.setObjectName("BrandSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}

        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt_ARROW_CURSOR())
            btn.clicked.connect(lambda checked, k=key: self._on_clicked(k))
            self._group.addButton(btn)
            self._buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch(1)

        self._buttons["dashboard"].setChecked(True)

    def _on_clicked(self, key: str):
        self.page_selected.emit(key)

    def select(self, key: str):
        if key in self._buttons:
            self._buttons[key].setChecked(True)


def Qt_ARROW_CURSOR():
    # Small helper to avoid importing QCursor/Qt at module import time
    # in a way that could fail before QApplication exists in some
    # embedding contexts; kept simple and explicit.
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QCursor
    return QCursor(Qt.CursorShape.PointingHandCursor)
