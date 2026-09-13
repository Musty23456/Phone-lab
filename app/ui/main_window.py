"""
main_window.py

Top-level QMainWindow: sidebar navigation + top device-status bar +
stacked page area. Owns the AppContext (shared state: settings, tool
paths, active device serials) and the background DeviceMonitor thread,
and wires device connect/disconnect events into the UI.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.device.device_monitor import DeviceMonitor
from app.ui.pages.about_page import AboutPage
from app.ui.pages.adb_tools import AdbToolsPage
from app.ui.pages.apk_tools import ApkToolsPage
from app.ui.pages.dashboard import DashboardPage
from app.ui.pages.devices_page import DevicesPage
from app.ui.pages.diagnostics_page import DiagnosticsPage
from app.ui.pages.drivers_page import DriversPage
from app.ui.pages.fastboot_tools import FastbootToolsPage
from app.ui.pages.file_manager_page import FileManagerPage
from app.ui.pages.logs_page import LogsPage
from app.ui.pages.screen_tools_page import ScreenToolsPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.utilities_page import UtilitiesPage
from app.ui.widgets.device_status_card import TopBarStatus
from app.ui.widgets.sidebar import Sidebar
from app.utils import platform_tools
from app.utils.settings_manager import SettingsManager


class AppContext(QObject):
    """Shared application state passed to every page. Centralizes tool
    paths, the active device selection, and settings so pages don't need
    to re-detect tools independently."""

    device_state_changed = Signal(list)          # generic "something changed" ping
    devices_updated = Signal(list, list)          # (adb_devices, fastboot_devices)

    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.adb_path: str | None = None
        self.fastboot_path: str | None = None
        self.active_adb_serial: str | None = None
        self.active_fastboot_serial: str | None = None
        self.refresh_tool_paths()

    def refresh_tool_paths(self):
        adb_status = platform_tools.get_adb_status(self.settings.get("adb_custom_path") or None)
        fastboot_status = platform_tools.get_fastboot_status(self.settings.get("fastboot_custom_path") or None)
        self.adb_path = adb_status.path
        self.fastboot_path = fastboot_status.path

    def apply_settings_changes(self):
        self.refresh_tool_paths()

    def set_active_adb_serial(self, serial: str | None):
        self.active_adb_serial = serial
        self.device_state_changed.emit([])

    def set_active_fastboot_serial(self, serial: str | None):
        self.active_fastboot_serial = serial
        self.device_state_changed.emit([])

    def on_devices_changed(self, adb_devices, fastboot_devices):
        # Auto-pick the first available device if nothing is selected yet,
        # and clear the selection if the previously active device vanished.
        adb_serials = [d.serial for d in adb_devices if d.state == "device"]
        if self.active_adb_serial not in adb_serials:
            self.active_adb_serial = adb_serials[0] if adb_serials else None

        fastboot_serials = [d.serial for d in fastboot_devices]
        if self.active_fastboot_serial not in fastboot_serials:
            self.active_fastboot_serial = fastboot_serials[0] if fastboot_serials else None

        self.devices_updated.emit(adb_devices, fastboot_devices)
        self.device_state_changed.emit(adb_devices)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ALMUS PHONE LAB - by ALMUS PRODUCTION")
        self.resize(1280, 800)

        self.ctx = AppContext()

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar()
        root_layout.addWidget(self.sidebar)

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.top_bar = TopBarStatus()
        right_layout.addWidget(self.top_bar)

        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack, 1)

        root_layout.addWidget(right_column, 1)

        self._pages: dict[str, QWidget] = {}
        self._register_pages()

        self.sidebar.page_selected.connect(self._show_page)
        self.ctx.devices_updated.connect(self._on_devices_updated)

        self._start_device_monitor()
        self._show_page("dashboard")

    def _register_pages(self):
        page_classes = {
            "dashboard": DashboardPage,
            "devices": DevicesPage,
            "adb": AdbToolsPage,
            "fastboot": FastbootToolsPage,
            "apk": ApkToolsPage,
            "files": FileManagerPage,
            "screen": ScreenToolsPage,
            "diagnostics": DiagnosticsPage,
            "logs": LogsPage,
            "drivers": DriversPage,
            "utilities": UtilitiesPage,
            "settings": SettingsPage,
            "about": AboutPage,
        }
        for key, cls in page_classes.items():
            page = cls(self.ctx)
            self._pages[key] = page
            self.stack.addWidget(page)

    def _show_page(self, key: str):
        page = self._pages.get(key)
        if page:
            self.stack.setCurrentWidget(page)
            self.sidebar.select(key)

    def _start_device_monitor(self):
        interval = self.ctx.settings.get("auto_refresh_interval_ms")
        self.monitor = DeviceMonitor(self.ctx.adb_path, self.ctx.fastboot_path, interval)
        self.monitor.devices_changed.connect(self.ctx.on_devices_changed)
        if self.ctx.settings.get("auto_refresh_devices"):
            self.monitor.start()

    def _on_devices_updated(self, adb_devices, fastboot_devices):
        connected_adb = [d for d in adb_devices if d.state == "device"]
        if connected_adb:
            serial = connected_adb[0].serial
            self.top_bar.set_connected(f"Device: {serial}  (ADB connected)")
        elif fastboot_devices:
            serial = fastboot_devices[0].serial
            self.top_bar.set_connected(f"Device: {serial}  (Fastboot mode)")
        else:
            self.top_bar.set_disconnected()

    def closeEvent(self, event):
        if hasattr(self, "monitor") and self.monitor.isRunning():
            self.monitor.stop()
            self.monitor.wait(1500)
        super().closeEvent(event)
