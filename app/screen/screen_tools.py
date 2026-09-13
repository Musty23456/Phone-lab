"""
screen_tools.py

Screenshot, screen-recording, and optional scrcpy-based mirroring.
Mirroring only launches an already-available, user-provided scrcpy
binary (bundled or on PATH) - this project does not implement any
proprietary or bypass-based mirroring method.
"""
from __future__ import annotations

import subprocess
from typing import Optional

from app.adb import commands as cmd
from app.adb.adb_client import AdbClient
from app.utils.process_runner import CommandResult, run_sync
from app.utils import platform_tools


class ScreenTools:
    def __init__(self, client: AdbClient):
        self.client = client

    def take_screenshot(self, local_path: str, serial: Optional[str] = None) -> CommandResult:
        return self.client.screencap_and_pull(local_path, serial)

    def start_screenrecord(self, remote_path: str = "/sdcard/almus_record.mp4",
                            time_limit: int = 30, serial: Optional[str] = None):
        """Returns an AsyncProcessRunner already started; caller connects
        to `finished` to know when the recording (bounded by time_limit)
        has completed, then can pull the resulting file."""
        args = cmd.screenrecord(self.client.adb_path, remote_path, time_limit, serial)
        runner = self.client.new_runner()
        runner.run(args)
        return runner

    def pull_recording(self, local_path: str, remote_path: str = "/sdcard/almus_record.mp4",
                        serial: Optional[str] = None) -> CommandResult:
        return self.client.pull(remote_path, local_path, serial)

    def send_keyevent(self, keycode: str, serial: Optional[str] = None) -> CommandResult:
        return run_sync(cmd.input_keyevent(self.client.adb_path, keycode, serial), timeout=8)

    def send_text(self, text: str, serial: Optional[str] = None) -> CommandResult:
        return run_sync(cmd.input_text(self.client.adb_path, text, serial), timeout=8)

    def launch_scrcpy(self, serial: Optional[str] = None, custom_path: Optional[str] = None) -> tuple[bool, str]:
        scrcpy_path = platform_tools.find_scrcpy(custom_path)
        if not scrcpy_path:
            return False, (
                "scrcpy was not found. Screen mirroring is optional and only "
                "activates if you place scrcpy.exe next to ALMUS PHONE LAB or "
                "on your system PATH. Download it from "
                "https://github.com/Genymobile/scrcpy"
            )
        args = [scrcpy_path]
        if serial:
            args += ["-s", serial]
        try:
            subprocess.Popen(args, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return True, "scrcpy launched."
        except OSError as exc:
            return False, f"Failed to launch scrcpy: {exc}"
