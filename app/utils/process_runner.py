"""
process_runner.py

Provides asynchronous execution of external commands (adb, fastboot, etc.)
without blocking the Qt GUI thread. Wraps QProcess for streaming output and
also exposes a simple synchronous helper for short-lived calls used by
non-GUI code (tests, quick lookups).
"""
from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from PySide6.QtCore import QObject, QProcess, Signal


@dataclass
class CommandResult:
    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    duration_ms: int = 0
    timed_out: bool = False
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and self.error is None


def run_sync(args: list[str], timeout: float = 20.0, cwd: Optional[str] = None) -> CommandResult:
    """Run a command synchronously. Used for quick, blocking lookups (tool
    version checks, tests) where spinning up a QProcess is unnecessary.
    Never raises; all failure modes are captured in CommandResult.error.
    """
    command_str = " ".join(shlex.quote(a) for a in args)
    start = time.monotonic()
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        return CommandResult(
            command=command_str,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            exit_code=proc.returncode,
            duration_ms=duration_ms,
        )
    except FileNotFoundError:
        return CommandResult(command=command_str, error="Executable not found.")
    except subprocess.TimeoutExpired:
        duration_ms = int((time.monotonic() - start) * 1000)
        return CommandResult(
            command=command_str,
            duration_ms=duration_ms,
            timed_out=True,
            error="Command timed out.",
        )
    except OSError as exc:
        return CommandResult(command=command_str, error=f"OS error: {exc}")


class AsyncProcessRunner(QObject):
    """Runs a single external command using QProcess and emits signals as
    output streams in, so the calling page can update a terminal widget
    live without blocking the UI.
    """

    output_ready = Signal(str)       # a line of stdout
    error_ready = Signal(str)        # a line of stderr
    finished = Signal(CommandResult)  # final result once process exits
    started_signal = Signal(str)     # emitted with the full command string

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._process: Optional[QProcess] = None
        self._command_str = ""
        self._stdout_buf: list[str] = []
        self._stderr_buf: list[str] = []
        self._start_time = 0.0

    def is_running(self) -> bool:
        return self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning

    def run(self, args: list[str], cwd: Optional[str] = None, input_text: Optional[str] = None):
        if self.is_running():
            self.error_ready.emit("A command is already running on this runner.")
            return

        if not args:
            self.error_ready.emit("No command specified.")
            return

        program, *rest = args
        self._command_str = " ".join(shlex.quote(a) for a in args)
        self._stdout_buf = []
        self._stderr_buf = []
        self._start_time = time.monotonic()

        process = QProcess(self)
        if cwd:
            process.setWorkingDirectory(cwd)
        process.readyReadStandardOutput.connect(self._on_stdout)
        process.readyReadStandardError.connect(self._on_stderr)
        process.finished.connect(self._on_finished)
        process.errorOccurred.connect(self._on_error_occurred)
        self._process = process

        self.started_signal.emit(self._command_str)
        process.start(program, rest)
        if input_text is not None:
            process.write(input_text.encode("utf-8"))
            process.closeWriteChannel()

    def write(self, text: str):
        if self.is_running():
            self._process.write((text + "\n").encode("utf-8"))

    def terminate(self):
        if self.is_running():
            self._process.terminate()
            if not self._process.waitForFinished(2000):
                self._process.kill()

    def _on_stdout(self):
        data = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self._stdout_buf.append(data)
            self.output_ready.emit(data)

    def _on_stderr(self):
        data = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
        if data:
            self._stderr_buf.append(data)
            self.error_ready.emit(data)

    def _on_error_occurred(self, error):
        result = CommandResult(
            command=self._command_str,
            stdout="".join(self._stdout_buf),
            stderr="".join(self._stderr_buf),
            exit_code=-1,
            duration_ms=int((time.monotonic() - self._start_time) * 1000),
            error=f"Process error: {error}",
        )
        self.finished.emit(result)

    def _on_finished(self, exit_code: int, _exit_status):
        result = CommandResult(
            command=self._command_str,
            stdout="".join(self._stdout_buf),
            stderr="".join(self._stderr_buf),
            exit_code=exit_code,
            duration_ms=int((time.monotonic() - self._start_time) * 1000),
        )
        self.finished.emit(result)
