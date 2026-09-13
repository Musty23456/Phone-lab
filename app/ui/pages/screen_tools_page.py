"""
screen_tools_page.py

Screenshot capture, screen recording (record on device -> pull to PC),
optional scrcpy mirroring launch, and basic input helpers.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from app.adb.adb_client import AdbClient
from app.screen.screen_tools import ScreenTools
from app.ui.widgets.confirm_dialog import show_error, show_info
from app.ui.widgets.terminal_widget import TerminalWidget


class ScreenToolsPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self._runner = None
        self._pending_local_path = None
        self._build_ui()

    def _tools(self) -> ScreenTools | None:
        if not self.ctx.adb_path:
            show_error(self, "ADB Not Found", "ADB was not detected.")
            return None
        return ScreenTools(AdbClient(self.ctx.adb_path))

    def _serial(self):
        return self.ctx.active_adb_serial

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("Screen Tools")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        row1 = QHBoxLayout()
        screenshot_btn = QPushButton("Take Screenshot")
        screenshot_btn.setObjectName("PrimaryButton")
        row1.addWidget(screenshot_btn)
        row1.addStretch(1)
        outer.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Recording length (seconds):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 180)
        self.duration_spin.setValue(15)
        record_btn = QPushButton("Start Screen Recording")
        row2.addWidget(self.duration_spin)
        row2.addWidget(record_btn)
        row2.addStretch(1)
        outer.addLayout(row2)

        row3 = QHBoxLayout()
        mirror_btn = QPushButton("Launch Screen Mirroring (scrcpy)")
        row3.addWidget(mirror_btn)
        row3.addStretch(1)
        outer.addLayout(row3)

        input_row = QHBoxLayout()
        self.text_input_edit = QLineEdit()
        self.text_input_edit.setPlaceholderText("Text to send to device")
        send_text_btn = QPushButton("Send Text")
        home_btn = QPushButton("Home")
        back_btn = QPushButton("Back")
        power_btn = QPushButton("Power")
        input_row.addWidget(self.text_input_edit, 1)
        input_row.addWidget(send_text_btn)
        input_row.addWidget(home_btn)
        input_row.addWidget(back_btn)
        input_row.addWidget(power_btn)
        outer.addLayout(input_row)

        self.terminal = TerminalWidget()
        outer.addWidget(self.terminal, 1)

        screenshot_btn.clicked.connect(self._take_screenshot)
        record_btn.clicked.connect(self._start_recording)
        mirror_btn.clicked.connect(self._launch_mirror)
        send_text_btn.clicked.connect(self._send_text)
        home_btn.clicked.connect(lambda: self._keyevent("KEYCODE_HOME"))
        back_btn.clicked.connect(lambda: self._keyevent("KEYCODE_BACK"))
        power_btn.clicked.connect(lambda: self._keyevent("KEYCODE_POWER"))

    def _take_screenshot(self):
        tools = self._tools()
        if not tools:
            return
        local, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", "screenshot.png", "PNG Files (*.png)")
        if not local:
            return
        result = tools.take_screenshot(local, self._serial())
        self.terminal.append_result_full(result)
        if result.success:
            show_info(self, "Screenshot Saved", f"Saved to {local}")

    def _start_recording(self):
        tools = self._tools()
        if not tools:
            return
        local, _ = QFileDialog.getSaveFileName(self, "Save Recording As", "recording.mp4", "MP4 Files (*.mp4)")
        if not local:
            return
        self._pending_local_path = local
        duration = self.duration_spin.value()
        self.terminal.append_command(f"adb shell screenrecord --time-limit {duration} /sdcard/almus_record.mp4")
        self.terminal.append_stdout(f"Recording for {duration} seconds... please wait.")
        self._runner = tools.start_screenrecord(time_limit=duration, serial=self._serial())
        self._runner.finished.connect(self._on_recording_finished)

    def _on_recording_finished(self, result):
        self.terminal.append_result_summary(result)
        tools = self._tools()
        if not tools or not self._pending_local_path:
            return
        pull_result = tools.pull_recording(self._pending_local_path, serial=self._serial())
        self.terminal.append_result_full(pull_result)
        if pull_result.success:
            show_info(self, "Recording Saved", f"Saved to {self._pending_local_path}")
        self._pending_local_path = None

    def _launch_mirror(self):
        tools = self._tools()
        if not tools:
            return
        ok, message = tools.launch_scrcpy(self._serial(), self.ctx.settings.get("scrcpy_custom_path"))
        self.terminal.append_stdout(message)
        if not ok:
            show_info(self, "Screen Mirroring", message)

    def _send_text(self):
        tools = self._tools()
        text = self.text_input_edit.text()
        if not tools or not text:
            return
        result = tools.send_text(text, self._serial())
        self.terminal.append_result_full(result)

    def _keyevent(self, keycode: str):
        tools = self._tools()
        if not tools:
            return
        result = tools.send_keyevent(keycode, self._serial())
        self.terminal.append_result_full(result)
