import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.fastboot import commands as fb_cmd


def test_devices_command():
    assert fb_cmd.devices("fastboot.exe") == ["fastboot.exe", "devices"]


def test_getvar_all():
    assert fb_cmd.getvar("fastboot.exe") == ["fastboot.exe", "getvar", "all"]
    assert fb_cmd.getvar("fastboot.exe", "product", serial="SN1") == [
        "fastboot.exe", "-s", "SN1", "getvar", "product"
    ]


def test_reboot_variants():
    assert fb_cmd.reboot("fastboot.exe") == ["fastboot.exe", "reboot"]
    assert fb_cmd.reboot("fastboot.exe", "bootloader") == ["fastboot.exe", "reboot", "bootloader"]


def test_flash_and_erase():
    args = fb_cmd.flash_partition("fastboot.exe", "boot", "boot.img", serial="SN1")
    assert args == ["fastboot.exe", "-s", "SN1", "flash", "boot", "boot.img"]

    args = fb_cmd.erase_partition("fastboot.exe", "cache")
    assert args == ["fastboot.exe", "erase", "cache"]


def test_boot_image():
    args = fb_cmd.boot_image("fastboot.exe", "boot.img")
    assert args == ["fastboot.exe", "boot", "boot.img"]


def test_slot_commands():
    assert fb_cmd.get_current_slot("fastboot.exe") == ["fastboot.exe", "getvar", "current-slot"]
    assert fb_cmd.set_active_slot("fastboot.exe", "a") == ["fastboot.exe", "--set-active=a"]


def test_oem_command():
    args = fb_cmd.oem_command("fastboot.exe", "device-info")
    assert args == ["fastboot.exe", "oem", "device-info"]
