"""
file_manager.py

Device-side file browsing/management via `adb shell` + push/pull.
Parses `ls -la` output into structured entries for the File Manager page.
All deletions require the caller (UI layer) to have already obtained
explicit user confirmation - this module does not prompt itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.adb.adb_client import AdbClient
from app.utils.process_runner import CommandResult


@dataclass
class RemoteFileEntry:
    name: str
    is_dir: bool
    size_bytes: Optional[int]
    permissions: str
    raw_line: str


def _parse_ls_line(line: str) -> Optional[RemoteFileEntry]:
    line = line.rstrip()
    if not line or line.startswith("total"):
        return None
    parts = line.split(maxsplit=8)
    if len(parts) < 8:
        return None
    permissions = parts[0]
    is_dir = permissions.startswith("d")
    # size is typically at index 4 for `ls -la` on Android toybox, but
    # varies with symlinks/owner widths - fall back gracefully.
    size_bytes = None
    for token in parts[3:6]:
        if token.isdigit():
            size_bytes = int(token)
            break
    name = parts[-1]
    if name in (".", ".."):
        return None
    if " -> " in name:
        name = name.split(" -> ")[0]
    return RemoteFileEntry(name=name, is_dir=is_dir, size_bytes=size_bytes,
                            permissions=permissions, raw_line=line)


class DeviceFileManager:
    def __init__(self, client: AdbClient):
        self.client = client

    def list_dir(self, path: str, serial: Optional[str] = None) -> tuple[list[RemoteFileEntry], Optional[str]]:
        result = self.client.list_dir(path, serial)
        if not result.success:
            return [], (result.stderr or result.error or "Unable to list directory")
        entries = []
        for line in result.stdout.splitlines():
            entry = _parse_ls_line(line)
            if entry:
                entries.append(entry)
        entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
        return entries, None

    def push(self, local_path: str, remote_path: str, serial: Optional[str] = None) -> CommandResult:
        return self.client.push(local_path, remote_path, serial)

    def pull(self, remote_path: str, local_path: str, serial: Optional[str] = None) -> CommandResult:
        return self.client.pull(remote_path, local_path, serial)

    def delete(self, remote_path: str, recursive: bool = False, serial: Optional[str] = None) -> CommandResult:
        return self.client.remove_path(remote_path, recursive, serial)

    def make_dir(self, remote_path: str, serial: Optional[str] = None) -> CommandResult:
        return self.client.make_dir(remote_path, serial)

    def rename(self, old_path: str, new_path: str, serial: Optional[str] = None) -> CommandResult:
        return self.client.rename_path(old_path, new_path, serial)

    @staticmethod
    def join_path(base: str, name: str) -> str:
        base = base.rstrip("/")
        return f"{base}/{name}"

    @staticmethod
    def parent_path(path: str) -> str:
        path = path.rstrip("/")
        if not path or path == "/sdcard" or path == "":
            return "/sdcard"
        parent = path.rsplit("/", 1)[0]
        return parent or "/"
