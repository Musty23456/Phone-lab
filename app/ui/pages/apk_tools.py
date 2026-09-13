"""
apk_tools.py

Dedicated APK/package management page: install (single/multiple),
uninstall, extract, search installed packages, and per-package actions.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget,
)

from app.adb.adb_client import AdbClient
from app.apk.apk_manager import ApkManager
from app.ui.widgets.confirm_dialog import confirm_destructive, show_error, show_info
from app.ui.widgets.terminal_widget import TerminalWidget


class ApkToolsPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._build_ui()

    def _manager(self) -> ApkManager | None:
        if not self.ctx.adb_path:
            show_error(self, "ADB Not Found", "ADB was not detected.")
            return None
        return ApkManager(AdbClient(self.ctx.adb_path))

    def _serial(self):
        return self.ctx.active_adb_serial

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("APK Tools")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        install_row = QHBoxLayout()
        self.apk_paths_edit = QLineEdit()
        self.apk_paths_edit.setPlaceholderText("Selected APK(s) will appear here")
        browse_one_btn = QPushButton("Select APK")
        browse_multi_btn = QPushButton("Select Multiple APKs")
        install_btn = QPushButton("Install")
        install_btn.setObjectName("PrimaryButton")
        install_row.addWidget(self.apk_paths_edit, 1)
        install_row.addWidget(browse_one_btn)
        install_row.addWidget(browse_multi_btn)
        install_row.addWidget(install_btn)
        outer.addLayout(install_row)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search installed packages...")
        search_btn = QPushButton("Search / Refresh")
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(search_btn)
        outer.addLayout(search_row)

        self.package_list = QListWidget()
        outer.addWidget(self.package_list, 1)

        action_row = QHBoxLayout()
        info_btn = QPushButton("Package Info")
        launch_btn = QPushButton("Launch")
        settings_btn = QPushButton("App Settings")
        force_stop_btn = QPushButton("Force Stop")
        clear_btn = QPushButton("Clear Data")
        disable_btn = QPushButton("Disable")
        enable_btn = QPushButton("Enable")
        extract_btn = QPushButton("Extract APK")
        uninstall_btn = QPushButton("Uninstall")
        uninstall_btn.setObjectName("DangerButton")
        for b in (info_btn, launch_btn, settings_btn, force_stop_btn, clear_btn,
                  disable_btn, enable_btn, extract_btn, uninstall_btn):
            action_row.addWidget(b)
        outer.addLayout(action_row)

        self.terminal = TerminalWidget()
        outer.addWidget(self.terminal, 1)

        browse_one_btn.clicked.connect(self._browse_single)
        browse_multi_btn.clicked.connect(self._browse_multi)
        install_btn.clicked.connect(self._install)
        search_btn.clicked.connect(self._refresh_packages)
        info_btn.clicked.connect(self._package_info)
        launch_btn.clicked.connect(self._launch)
        settings_btn.clicked.connect(self._open_settings)
        force_stop_btn.clicked.connect(self._force_stop)
        clear_btn.clicked.connect(self._clear_data)
        disable_btn.clicked.connect(self._disable)
        enable_btn.clicked.connect(self._enable)
        extract_btn.clicked.connect(self._extract)
        uninstall_btn.clicked.connect(self._uninstall)

        self._pending_paths: list[str] = []

    def _selected_package(self) -> str | None:
        item = self.package_list.currentItem()
        return item.text() if item else None

    def _browse_single(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select APK", "", "APK Files (*.apk)")
        if path:
            self._pending_paths = [path]
            self.apk_paths_edit.setText(path)

    def _browse_multi(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select APKs", "", "APK Files (*.apk)")
        if paths:
            self._pending_paths = paths
            self.apk_paths_edit.setText("; ".join(paths))

    def _install(self):
        manager = self._manager()
        if not manager or not self._pending_paths:
            show_error(self, "No APK Selected", "Select an APK file first.")
            return
        if len(self._pending_paths) == 1:
            result = manager.install(self._pending_paths[0], self._serial())
        else:
            result = manager.install_multiple(self._pending_paths, self._serial())
        self.terminal.append_result_full(result)
        if result.success:
            show_info(self, "Install Complete", "The APK(s) were installed successfully.")

    def _refresh_packages(self):
        manager = self._manager()
        if not manager:
            return
        entries = manager.list_installed(self._serial(), only_third_party=True,
                                          search=self.search_edit.text().strip() or None)
        self.package_list.clear()
        for entry in entries:
            self.package_list.addItem(QListWidgetItem(entry.name))
        self.terminal.append_stdout(f"Found {len(entries)} package(s).")

    def _package_info(self):
        manager, package = self._manager(), self._selected_package()
        if not manager or not package:
            return
        info = manager.package_info(package, self._serial())
        self.terminal.append_command(f"adb shell dumpsys package {package}")
        self.terminal.append_stdout(info[:4000])  # keep the panel responsive

    def _launch(self):
        manager, package = self._manager(), self._selected_package()
        if not manager or not package:
            return
        self.terminal.append_result_full(manager.launch(package, self._serial()))

    def _open_settings(self):
        manager, package = self._manager(), self._selected_package()
        if not manager or not package:
            return
        self.terminal.append_result_full(manager.open_settings(package, self._serial()))

    def _force_stop(self):
        manager, package = self._manager(), self._selected_package()
        if not manager or not package:
            return
        self.terminal.append_result_full(manager.force_stop(package, self._serial()))

    def _clear_data(self):
        manager, package = self._manager(), self._selected_package()
        if not manager or not package:
            return
        if not confirm_destructive(self, "Clear App Data", f"This will erase all data for '{package}'."):
            return
        self.terminal.append_result_full(manager.clear_data(package, self._serial()))

    def _disable(self):
        manager, package = self._manager(), self._selected_package()
        if not manager or not package:
            return
        if not confirm_destructive(self, "Disable Package", f"This will disable '{package}'."):
            return
        self.terminal.append_result_full(manager.disable(package, self._serial()))

    def _enable(self):
        manager, package = self._manager(), self._selected_package()
        if not manager or not package:
            return
        self.terminal.append_result_full(manager.enable(package, self._serial()))

    def _extract(self):
        manager, package = self._manager(), self._selected_package()
        if not manager or not package:
            return
        remote_path = manager.extract_apk_path(package, self._serial())
        if not remote_path:
            show_error(self, "Not Found", "Could not determine the APK path for this package.")
            return
        local, _ = QFileDialog.getSaveFileName(self, "Save Extracted APK", f"{package}.apk", "APK Files (*.apk)")
        if not local:
            return
        result = manager.client.pull(remote_path, local, self._serial())
        self.terminal.append_result_full(result)

    def _uninstall(self):
        manager, package = self._manager(), self._selected_package()
        if not manager or not package:
            show_error(self, "No Package Selected", "Select a package from the list first.")
            return
        if not confirm_destructive(self, "Uninstall Package", f"This will uninstall '{package}'."):
            return
        result = manager.uninstall(package, self._serial())
        self.terminal.append_result_full(result)
