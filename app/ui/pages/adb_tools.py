"""
adb_tools.py

Full ADB Tools page: device detection, reboot variants, install/uninstall,
push/pull, package listing, app lifecycle actions, screenshot/recording
triggers, logcat snapshot, and device/battery/storage/memory/cpu info -
all backed by AdbClient and run without freezing the GUI.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from app.adb.adb_client import AdbClient
from app.ui.widgets.confirm_dialog import confirm_destructive, show_error, show_info
from app.ui.widgets.terminal_widget import TerminalWidget
from app.utils.process_runner import CommandResult


class AdbToolsPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._runners = []  # keep references alive while async commands run
        self._build_ui()

    def _client(self) -> AdbClient | None:
        if not self.ctx.adb_path:
            show_error(self, "ADB Not Found", "ADB was not detected. Check Settings / Drivers page.")
            return None
        return AdbClient(self.ctx.adb_path)

    def _serial(self) -> str | None:
        return self.ctx.active_adb_serial

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("ADB Tools")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        tabs = QTabWidget()
        outer.addWidget(tabs, 1)

        tabs.addTab(self._build_device_tab(), "Device")
        tabs.addTab(self._build_apps_tab(), "Apps")
        tabs.addTab(self._build_files_tab(), "Files")
        tabs.addTab(self._build_capture_tab(), "Capture")
        tabs.addTab(self._build_info_tab(), "Device Info")

        self.terminal = TerminalWidget()
        outer.addWidget(self.terminal, 1)

    # ---------- Device tab ----------

    def _build_device_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        row1 = QHBoxLayout()
        btn_devices = QPushButton("adb devices")
        btn_state = QPushButton("Device State")
        btn_serial = QPushButton("Get Serial")
        for b in (btn_devices, btn_state, btn_serial):
            row1.addWidget(b)
        row1.addStretch(1)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        btn_reboot = QPushButton("Reboot")
        btn_recovery = QPushButton("Reboot Recovery")
        btn_bootloader = QPushButton("Reboot Bootloader")
        btn_system = QPushButton("Reboot System")
        for b in (btn_reboot, btn_recovery, btn_bootloader, btn_system):
            row2.addWidget(b)
        row2.addStretch(1)
        layout.addLayout(row2)
        layout.addStretch(1)

        btn_devices.clicked.connect(self._list_devices)
        btn_state.clicked.connect(self._check_state)
        btn_serial.clicked.connect(self._get_serial)
        btn_reboot.clicked.connect(lambda: self._reboot(None))
        btn_recovery.clicked.connect(lambda: self._reboot("recovery", destructive=True))
        btn_bootloader.clicked.connect(lambda: self._reboot("bootloader", destructive=True))
        btn_system.clicked.connect(lambda: self._reboot(""))

        return widget

    def _get_serial(self):
        client = self._client()
        if not client:
            return
        from app.adb import commands as cmd
        from app.utils.process_runner import run_sync
        result = run_sync(cmd.get_serialno(client.adb_path))
        self.terminal.append_result_full(result)

    def _reboot(self, mode, destructive: bool = False):
        client = self._client()
        if not client:
            return
        if destructive and not confirm_destructive(
            self, "Confirm Reboot", f"The device will reboot into {mode} mode."
        ):
            return
        result = client.reboot(mode or None, self._serial())
        self.terminal.append_result_full(result)

    def _check_state(self):
        client = self._client()
        if not client:
            return
        state = client.get_state(self._serial())
        self.terminal.append_command("adb get-state")
        self.terminal.append_stdout(state)

    def _list_devices(self):
        client = self._client()
        if not client:
            return
        devices = client.list_devices()
        self.terminal.append_command("adb devices -l")
        if not devices:
            self.terminal.append_stdout("No devices found.")
        for d in devices:
            self.terminal.append_stdout(f"{d.serial}\t{d.state}\t{d.extra}")

    # ---------- Apps tab ----------

    def _build_apps_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        install_row = QHBoxLayout()
        self.apk_path_edit = QLineEdit()
        self.apk_path_edit.setPlaceholderText("Select an APK file...")
        browse_btn = QPushButton("Browse")
        install_btn = QPushButton("Install APK")
        install_btn.setObjectName("PrimaryButton")
        install_row.addWidget(self.apk_path_edit, 1)
        install_row.addWidget(browse_btn)
        install_row.addWidget(install_btn)
        layout.addLayout(install_row)

        pkg_row = QHBoxLayout()
        self.package_edit = QLineEdit()
        self.package_edit.setPlaceholderText("com.example.package")
        uninstall_btn = QPushButton("Uninstall")
        uninstall_btn.setObjectName("DangerButton")
        clear_btn = QPushButton("Clear Data")
        disable_btn = QPushButton("Disable")
        enable_btn = QPushButton("Enable")
        force_stop_btn = QPushButton("Force Stop")
        start_btn = QPushButton("Start App")
        pkg_row.addWidget(self.package_edit, 1)
        for b in (uninstall_btn, clear_btn, disable_btn, enable_btn, force_stop_btn, start_btn):
            pkg_row.addWidget(b)
        layout.addLayout(pkg_row)

        list_row = QHBoxLayout()
        list_packages_btn = QPushButton("List Installed Packages")
        list_row.addWidget(list_packages_btn)
        list_row.addStretch(1)
        layout.addLayout(list_row)
        layout.addStretch(1)

        browse_btn.clicked.connect(self._browse_apk)
        install_btn.clicked.connect(self._install_apk)
        uninstall_btn.clicked.connect(self._uninstall_package)
        clear_btn.clicked.connect(self._clear_data)
        disable_btn.clicked.connect(self._disable_package)
        enable_btn.clicked.connect(self._enable_package)
        force_stop_btn.clicked.connect(self._force_stop)
        start_btn.clicked.connect(self._start_app)
        list_packages_btn.clicked.connect(self._list_packages)

        return widget

    def _browse_apk(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select APK", "", "APK Files (*.apk)")
        if path:
            self.apk_path_edit.setText(path)

    def _install_apk(self):
        client = self._client()
        if not client:
            return
        apk_path = self.apk_path_edit.text().strip()
        if not apk_path:
            show_error(self, "Missing APK", "Please select an APK file first.")
            return
        from app.adb import commands as cmd
        from app.utils.process_runner import run_sync
        args = cmd.install_apk(client.adb_path, apk_path, self._serial(), reinstall=True, grant_permissions=True)
        result = run_sync(args, timeout=180)
        self.terminal.append_result_full(result)

    def _uninstall_package(self):
        client = self._client()
        package = self.package_edit.text().strip()
        if not client or not package:
            show_error(self, "Missing Package", "Enter a package name first.")
            return
        if not confirm_destructive(self, "Uninstall Package",
                                    f"This will uninstall '{package}' from the device."):
            return
        result = client.uninstall_package(package, self._serial())
        self.terminal.append_result_full(result)

    def _clear_data(self):
        client, package = self._client(), self.package_edit.text().strip()
        if not client or not package:
            return
        if not confirm_destructive(self, "Clear App Data", f"This will erase all data for '{package}'."):
            return
        self.terminal.append_result_full(client.clear_app_data(package, self._serial()))

    def _disable_package(self):
        client, package = self._client(), self.package_edit.text().strip()
        if not client or not package:
            return
        if not confirm_destructive(self, "Disable Package", f"This will disable '{package}'."):
            return
        self.terminal.append_result_full(client.disable_package(package, self._serial()))

    def _enable_package(self):
        client, package = self._client(), self.package_edit.text().strip()
        if not client or not package:
            return
        self.terminal.append_result_full(client.enable_package(package, self._serial()))

    def _force_stop(self):
        client, package = self._client(), self.package_edit.text().strip()
        if not client or not package:
            return
        self.terminal.append_result_full(client.force_stop(package, self._serial()))

    def _start_app(self):
        client, package = self._client(), self.package_edit.text().strip()
        if not client or not package:
            return
        from app.adb import commands as cmd
        from app.utils.process_runner import run_sync
        result = run_sync(cmd.start_app(client.adb_path, package, serial=self._serial()))
        self.terminal.append_result_full(result)

    def _list_packages(self):
        client = self._client()
        if not client:
            return
        packages = client.list_packages(self._serial())
        self.terminal.append_command("adb shell pm list packages")
        if not packages:
            self.terminal.append_stdout("No packages returned (or device not connected).")
        for p in packages:
            self.terminal.append_stdout(p)

    # ---------- Files tab ----------

    def _build_files_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        pull_row = QHBoxLayout()
        self.pull_remote_edit = QLineEdit()
        self.pull_remote_edit.setPlaceholderText("/sdcard/DCIM/Camera/photo.jpg")
        pull_btn = QPushButton("Pull File...")
        pull_row.addWidget(QLabel("Remote path:"))
        pull_row.addWidget(self.pull_remote_edit, 1)
        pull_row.addWidget(pull_btn)
        layout.addLayout(pull_row)

        push_row = QHBoxLayout()
        self.push_local_edit = QLineEdit()
        push_browse_btn = QPushButton("Browse Local...")
        self.push_remote_edit = QLineEdit()
        self.push_remote_edit.setPlaceholderText("/sdcard/Download/file.ext")
        push_btn = QPushButton("Push File")
        push_row.addWidget(self.push_local_edit, 1)
        push_row.addWidget(push_browse_btn)
        push_row.addWidget(self.push_remote_edit, 1)
        push_row.addWidget(push_btn)
        layout.addLayout(push_row)
        layout.addStretch(1)

        pull_btn.clicked.connect(self._pull_file)
        push_browse_btn.clicked.connect(self._browse_push_file)
        push_btn.clicked.connect(self._push_file)

        return widget

    def _pull_file(self):
        client = self._client()
        remote = self.pull_remote_edit.text().strip()
        if not client or not remote:
            show_error(self, "Missing Path", "Enter a remote file path to pull.")
            return
        local, _ = QFileDialog.getSaveFileName(self, "Save Pulled File")
        if not local:
            return
        result = client.pull(remote, local, self._serial())
        self.terminal.append_result_full(result)

    def _browse_push_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File To Push")
        if path:
            self.push_local_edit.setText(path)

    def _push_file(self):
        client = self._client()
        local = self.push_local_edit.text().strip()
        remote = self.push_remote_edit.text().strip()
        if not client or not local or not remote:
            show_error(self, "Missing Info", "Select a local file and enter a remote destination.")
            return
        result = client.push(local, remote, self._serial())
        self.terminal.append_result_full(result)

    # ---------- Capture tab ----------

    def _build_capture_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        row = QHBoxLayout()
        screenshot_btn = QPushButton("Take Screenshot")
        screenshot_btn.setObjectName("PrimaryButton")
        logcat_btn = QPushButton("Get Logcat Snapshot")
        row.addWidget(screenshot_btn)
        row.addWidget(logcat_btn)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(1)

        screenshot_btn.clicked.connect(self._take_screenshot)
        logcat_btn.clicked.connect(self._logcat_snapshot)
        return widget

    def _take_screenshot(self):
        client = self._client()
        if not client:
            return
        local, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", "screenshot.png", "PNG Files (*.png)")
        if not local:
            return
        result = client.screencap_and_pull(local, self._serial())
        self.terminal.append_result_full(result)
        if result.success:
            show_info(self, "Screenshot Saved", f"Saved to {local}")

    def _logcat_snapshot(self):
        client = self._client()
        if not client:
            return
        from app.adb import commands as cmd
        from app.utils.process_runner import run_sync
        args = cmd.logcat(client.adb_path, self._serial()) + ["-d"]  # -d = dump and exit
        result = run_sync(args, timeout=20)
        self.terminal.append_result_full(result)

    # ---------- Device Info tab ----------

    def _build_info_tab(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)
        specs = [
            ("Battery Info", self._show_battery),
            ("Storage Info", self._show_storage),
            ("Memory Info", self._show_meminfo),
            ("CPU Info", self._show_cpuinfo),
            ("Android Version / Build", self._show_version),
            ("Manufacturer / Model", self._show_manufacturer),
            ("Screen Resolution", self._show_resolution),
            ("All Properties (getprop)", self._show_all_props),
        ]
        for i, (label, handler) in enumerate(specs):
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            layout.addWidget(btn, i // 2, i % 2)
        return widget

    def _show_battery(self):
        client = self._client()
        if not client:
            return
        info = client.battery_info(self._serial())
        self.terminal.append_command("adb shell dumpsys battery")
        for k, v in info.items():
            self.terminal.append_stdout(f"{k}: {v}")

    def _show_storage(self):
        client = self._client()
        if not client:
            return
        self.terminal.append_command("adb shell df /data /sdcard")
        self.terminal.append_stdout(client.storage_info(self._serial()) or "No data.")

    def _show_meminfo(self):
        client = self._client()
        if not client:
            return
        self.terminal.append_command("adb shell cat /proc/meminfo")
        self.terminal.append_stdout(client.meminfo(self._serial()) or "No data.")

    def _show_cpuinfo(self):
        client = self._client()
        if not client:
            return
        self.terminal.append_command("adb shell cat /proc/cpuinfo")
        self.terminal.append_stdout(client.cpuinfo(self._serial()) or "No data.")

    def _show_version(self):
        client = self._client()
        if not client:
            return
        props = client.getprop_all(self._serial())
        self.terminal.append_command("adb shell getprop (version/build)")
        for key in ("ro.build.version.release", "ro.build.version.sdk", "ro.build.display.id"):
            self.terminal.append_stdout(f"{key}: {props.get(key, 'unknown')}")

    def _show_manufacturer(self):
        client = self._client()
        if not client:
            return
        props = client.getprop_all(self._serial())
        self.terminal.append_command("adb shell getprop (manufacturer/model)")
        for key in ("ro.product.manufacturer", "ro.product.model", "ro.product.brand"):
            self.terminal.append_stdout(f"{key}: {props.get(key, 'unknown')}")

    def _show_resolution(self):
        client = self._client()
        if not client:
            return
        self.terminal.append_command("adb shell wm size")
        self.terminal.append_stdout(client.screen_resolution(self._serial()) or "No data.")

    def _show_all_props(self):
        client = self._client()
        if not client:
            return
        props = client.getprop_all(self._serial())
        self.terminal.append_command("adb shell getprop")
        for k, v in props.items():
            self.terminal.append_stdout(f"[{k}]: [{v}]")
