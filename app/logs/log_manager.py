"""
log_manager.py

Manages live logcat streaming (via an AsyncProcessRunner owned by the
Logs page), plus in-memory buffering, search/filter, and export to a
local .log file.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from app.adb import commands as cmd
from app.adb.adb_client import AdbClient
from app.utils.process_runner import AsyncProcessRunner, run_sync


class LogManager:
    def __init__(self, client: AdbClient):
        self.client = client
        self.buffer: list[str] = []
        self._paused = False

    def clear_device_logs(self, serial: Optional[str] = None):
        run_sync(cmd.logcat_clear(self.client.adb_path, serial), timeout=10)

    def clear_buffer(self):
        self.buffer.clear()

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    def start_stream(self, serial: Optional[str] = None, filter_spec: Optional[str] = None) -> AsyncProcessRunner:
        args = cmd.logcat(self.client.adb_path, serial, filter_spec)
        runner = self.client.new_runner()
        runner.output_ready.connect(self._on_output)
        runner.run(args)
        return runner

    def _on_output(self, chunk: str):
        if self._paused:
            return
        for line in chunk.splitlines():
            self.buffer.append(line)
        # Cap buffer to avoid unbounded memory growth on long sessions
        if len(self.buffer) > 20000:
            self.buffer = self.buffer[-15000:]

    def search(self, query: str, case_sensitive: bool = False) -> list[str]:
        if not query:
            return list(self.buffer)
        if case_sensitive:
            return [line for line in self.buffer if query in line]
        query_lower = query.lower()
        return [line for line in self.buffer if query_lower in line.lower()]

    def filter_by_level(self, level: str) -> list[str]:
        """level: one of V, D, I, W, E, F matching standard logcat tag format
        '<Date> <Time> <PID> <TID> <Level> <Tag>: <Message>'."""
        if not level or level == "ALL":
            return list(self.buffer)
        marker = f" {level}/"
        return [line for line in self.buffer if marker in line or f" {level} " in line]

    def export(self, path: str) -> tuple[bool, str]:
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.buffer))
            return True, path
        except OSError as exc:
            return False, str(exc)

    @staticmethod
    def default_log_filename(prefix: str = "almus_logcat") -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{stamp}.log"
