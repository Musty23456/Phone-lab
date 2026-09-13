"""
device_status_card.py

Small stat "card" used across the Dashboard/Diagnostics pages, plus a
compact top-bar status summary showing connection state.
"""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "-", parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("")  # rely on global QSS via class selector
        self.setObjectName("StatCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "CardTitle")
        self.value_label = QLabel(value)
        self.value_label.setProperty("class", "CardValue")
        self.value_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class TopBarStatus(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        self.title_label = QLabel("ALMUS PHONE LAB")
        self.title_label.setObjectName("TopBarTitle")

        self.status_label = QLabel("🔴  Device: No device connected")
        self.status_label.setObjectName("StatusDot")

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)

    def set_disconnected(self):
        self.status_label.setText("🔴  Device: No device connected")

    def set_connected(self, description: str):
        self.status_label.setText(f"🟢  {description}")
