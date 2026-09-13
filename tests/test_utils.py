import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.validators import is_blocked, is_destructive, validate_command
from app.utils.process_runner import run_sync, CommandResult


def test_is_destructive_detects_keywords():
    assert is_destructive("fastboot flash boot boot.img")
    assert is_destructive("fastboot erase cache")
    assert is_destructive("adb uninstall com.example")
    assert not is_destructive("adb shell getprop")


def test_is_blocked_detects_bypass_terms():
    assert is_blocked("some frp bypass tool")
    assert is_blocked("remove google account lock")
    assert is_blocked("google account removal tool")
    assert is_blocked("change imei value")
    assert is_blocked("remove screen lock pattern")
    assert not is_blocked("adb shell pm list packages")
    assert not is_blocked("adb shell pm disable-user com.example.app")


def test_validate_command_blocks_bypass():
    allowed, reason = validate_command(["adb", "shell", "frp_bypass_tool"])
    assert allowed is False
    assert "bypass" in reason.lower() or "FRP" in reason


def test_validate_command_allows_normal_commands():
    allowed, reason = validate_command(["adb", "shell", "pm", "list", "packages"])
    assert allowed is True
    assert reason == "OK"


def test_run_sync_missing_executable_does_not_raise():
    result = run_sync(["definitely_not_a_real_binary_xyz"], timeout=2)
    assert isinstance(result, CommandResult)
    assert result.success is False
    assert result.error is not None


def test_run_sync_echo_command_succeeds():
    # Use a universally available command to sanity-check the sync runner.
    if os.name == "nt":
        result = run_sync(["cmd", "/c", "echo hello"], timeout=5)
    else:
        result = run_sync(["echo", "hello"], timeout=5)
    assert result.success is True
    assert "hello" in result.stdout
