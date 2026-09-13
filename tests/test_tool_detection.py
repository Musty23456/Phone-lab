import os
import sys
import stat

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils import platform_tools


def test_bundled_tools_dir_ends_with_expected_path():
    path = platform_tools.bundled_tools_dir()
    assert path.endswith(os.path.join("tools", "platform-tools"))


def test_find_tool_returns_none_when_missing(tmp_path, monkeypatch):
    # Point bundled dir lookup at an empty temp dir and clear PATH so
    # detection cleanly reports "not found" instead of finding a real
    # system adb on the test machine.
    monkeypatch.setattr(platform_tools, "_app_root", lambda: str(tmp_path))
    monkeypatch.setenv("PATH", "")
    path, source = platform_tools._find_tool("adb_that_does_not_exist.exe")
    assert path is None
    assert source == "none"


def test_find_tool_finds_custom_path(tmp_path):
    fake_adb = tmp_path / "adb.exe"
    fake_adb.write_text("not a real binary")
    path, source = platform_tools._find_tool("adb.exe", custom_path=str(tmp_path))
    assert path == str(fake_adb)
    assert source == "custom"


def test_find_tool_finds_bundled(tmp_path, monkeypatch):
    bundled_dir = tmp_path / "tools" / "platform-tools"
    bundled_dir.mkdir(parents=True)
    fake_adb = bundled_dir / "adb.exe"
    fake_adb.write_text("not a real binary")
    monkeypatch.setattr(platform_tools, "_app_root", lambda: str(tmp_path))
    path, source = platform_tools._find_tool("adb.exe")
    assert path == str(fake_adb)
    assert source == "bundled"


def test_get_adb_status_when_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(platform_tools, "_app_root", lambda: str(tmp_path))
    monkeypatch.setenv("PATH", "")
    status = platform_tools.get_adb_status()
    assert status.found is False
    assert status.path is None
