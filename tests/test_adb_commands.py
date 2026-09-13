import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.adb import commands as adb_cmd


def test_devices_command():
    assert adb_cmd.devices("adb.exe") == ["adb.exe", "devices", "-l"]


def test_shell_with_serial():
    args = adb_cmd.shell("adb.exe", "ls /sdcard", serial="ABC123")
    assert args == ["adb.exe", "-s", "ABC123", "shell", "ls /sdcard"]


def test_shell_without_serial():
    args = adb_cmd.shell("adb.exe", "getprop")
    assert args == ["adb.exe", "shell", "getprop"]


def test_reboot_modes():
    assert adb_cmd.reboot("adb.exe") == ["adb.exe", "reboot"]
    assert adb_cmd.reboot("adb.exe", "recovery") == ["adb.exe", "reboot", "recovery"]
    assert adb_cmd.reboot("adb.exe", "bootloader", serial="XYZ") == [
        "adb.exe", "-s", "XYZ", "reboot", "bootloader"
    ]


def test_install_apk_flags():
    args = adb_cmd.install_apk("adb.exe", "app.apk", reinstall=True, grant_permissions=True)
    assert args == ["adb.exe", "install", "-r", "-g", "app.apk"]


def test_install_apk_no_flags():
    args = adb_cmd.install_apk("adb.exe", "app.apk")
    assert args == ["adb.exe", "install", "app.apk"]


def test_install_multiple_apks():
    args = adb_cmd.install_multiple_apks("adb.exe", ["a.apk", "b.apk"], reinstall=True)
    assert args == ["adb.exe", "install-multiple", "-r", "a.apk", "b.apk"]


def test_uninstall_package():
    args = adb_cmd.uninstall_package("adb.exe", "com.example.app", keep_data=True)
    assert args == ["adb.exe", "uninstall", "-k", "com.example.app"]


def test_pull_and_push():
    assert adb_cmd.pull_file("adb.exe", "/sdcard/a.txt", "a.txt") == ["adb.exe", "pull", "/sdcard/a.txt", "a.txt"]
    assert adb_cmd.push_file("adb.exe", "a.txt", "/sdcard/a.txt") == ["adb.exe", "push", "a.txt", "/sdcard/a.txt"]


def test_list_packages_third_party_and_filter():
    args = adb_cmd.list_packages("adb.exe", only_third_party=True, filter_text="com.example")
    assert args == ["adb.exe", "shell", "pm list packages -3 com.example"]


def test_package_lifecycle_commands():
    assert adb_cmd.enable_package("adb.exe", "com.a") == ["adb.exe", "shell", "pm enable com.a"]
    assert adb_cmd.disable_package("adb.exe", "com.a") == ["adb.exe", "shell", "pm disable-user com.a"]
    assert adb_cmd.clear_app_data("adb.exe", "com.a") == ["adb.exe", "shell", "pm clear com.a"]
    assert adb_cmd.force_stop("adb.exe", "com.a") == ["adb.exe", "shell", "am force-stop com.a"]


def test_screencap_and_screenrecord():
    assert adb_cmd.screencap("adb.exe") == ["adb.exe", "shell", "screencap -p /sdcard/almus_screenshot.png"]
    args = adb_cmd.screenrecord("adb.exe", time_limit=10)
    assert args == ["adb.exe", "shell", "screenrecord --time-limit 10 /sdcard/almus_record.mp4"]


def test_remove_path_recursive():
    args = adb_cmd.remove_path("adb.exe", "/sdcard/temp", recursive=True)
    assert args == ["adb.exe", "shell", "rm -rf /sdcard/temp"]


def test_remove_path_non_recursive():
    args = adb_cmd.remove_path("adb.exe", "/sdcard/temp.txt", recursive=False)
    assert args == ["adb.exe", "shell", "rm -f /sdcard/temp.txt"]
