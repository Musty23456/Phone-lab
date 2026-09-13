"""
commands.py (adb)

Pure functions that build adb argument lists. Kept free of any process
execution or Qt dependency so they can be unit tested directly and reused
by both the async client and the CLI-style terminal.
"""
from __future__ import annotations

from typing import Optional


def _base(adb_path: str, serial: Optional[str] = None) -> list[str]:
    args = [adb_path]
    if serial:
        args += ["-s", serial]
    return args


def devices(adb_path: str) -> list[str]:
    return [adb_path, "devices", "-l"]


def get_state(adb_path: str, serial: Optional[str] = None) -> list[str]:
    return _base(adb_path, serial) + ["get-state"]


def get_serialno(adb_path: str) -> list[str]:
    return [adb_path, "get-serialno"]


def shell(adb_path: str, shell_cmd: str, serial: Optional[str] = None) -> list[str]:
    return _base(adb_path, serial) + ["shell", shell_cmd]


def reboot(adb_path: str, mode: Optional[str] = None, serial: Optional[str] = None) -> list[str]:
    args = _base(adb_path, serial) + ["reboot"]
    if mode:
        args.append(mode)  # "recovery" | "bootloader" | "sideload" | "" (system)
    return args


def install_apk(adb_path: str, apk_path: str, serial: Optional[str] = None,
                 reinstall: bool = False, grant_permissions: bool = False) -> list[str]:
    args = _base(adb_path, serial) + ["install"]
    if reinstall:
        args.append("-r")
    if grant_permissions:
        args.append("-g")
    args.append(apk_path)
    return args


def install_multiple_apks(adb_path: str, apk_paths: list[str], serial: Optional[str] = None,
                           reinstall: bool = False) -> list[str]:
    args = _base(adb_path, serial) + ["install-multiple"]
    if reinstall:
        args.append("-r")
    args += apk_paths
    return args


def uninstall_package(adb_path: str, package: str, serial: Optional[str] = None,
                       keep_data: bool = False) -> list[str]:
    args = _base(adb_path, serial) + ["uninstall"]
    if keep_data:
        args.append("-k")
    args.append(package)
    return args


def pull_file(adb_path: str, remote_path: str, local_path: str, serial: Optional[str] = None) -> list[str]:
    return _base(adb_path, serial) + ["pull", remote_path, local_path]


def push_file(adb_path: str, local_path: str, remote_path: str, serial: Optional[str] = None) -> list[str]:
    return _base(adb_path, serial) + ["push", local_path, remote_path]


def list_packages(adb_path: str, serial: Optional[str] = None, only_third_party: bool = False,
                   filter_text: Optional[str] = None) -> list[str]:
    shell_cmd = "pm list packages"
    if only_third_party:
        shell_cmd += " -3"
    if filter_text:
        shell_cmd += f" {filter_text}"
    return shell(adb_path, shell_cmd, serial)


def enable_package(adb_path: str, package: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"pm enable {package}", serial)


def disable_package(adb_path: str, package: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"pm disable-user {package}", serial)


def clear_app_data(adb_path: str, package: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"pm clear {package}", serial)


def force_stop(adb_path: str, package: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"am force-stop {package}", serial)


def start_app(adb_path: str, package: str, activity: Optional[str] = None,
              serial: Optional[str] = None) -> list[str]:
    target = f"{package}/{activity}" if activity else package
    if activity:
        return shell(adb_path, f"am start -n {target}", serial)
    return shell(adb_path, f"monkey -p {package} -c android.intent.category.LAUNCHER 1", serial)


def open_app_settings(adb_path: str, package: str, serial: Optional[str] = None) -> list[str]:
    return shell(
        adb_path,
        f"am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{package}",
        serial,
    )


def screencap(adb_path: str, remote_path: str = "/sdcard/almus_screenshot.png",
              serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"screencap -p {remote_path}", serial)


def screenrecord(adb_path: str, remote_path: str = "/sdcard/almus_record.mp4",
                  time_limit: int = 30, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"screenrecord --time-limit {time_limit} {remote_path}", serial)


def logcat(adb_path: str, serial: Optional[str] = None, filter_spec: Optional[str] = None,
           clear_first: bool = False) -> list[str]:
    args = _base(adb_path, serial) + ["logcat"]
    if filter_spec:
        args += filter_spec.split()
    return args


def logcat_clear(adb_path: str, serial: Optional[str] = None) -> list[str]:
    return _base(adb_path, serial) + ["logcat", "-c"]


def getprop(adb_path: str, serial: Optional[str] = None, prop: Optional[str] = None) -> list[str]:
    if prop:
        return shell(adb_path, f"getprop {prop}", serial)
    return shell(adb_path, "getprop", serial)


def dumpsys_battery(adb_path: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, "dumpsys battery", serial)


def storage_info(adb_path: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, "df /data /sdcard", serial)


def meminfo(adb_path: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, "cat /proc/meminfo", serial)


def cpuinfo(adb_path: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, "cat /proc/cpuinfo", serial)


def wm_size(adb_path: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, "wm size", serial)


def list_dir(adb_path: str, remote_dir: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"ls -la {remote_dir}", serial)


def make_dir(adb_path: str, remote_dir: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"mkdir -p {remote_dir}", serial)


def remove_path(adb_path: str, remote_path: str, recursive: bool = False,
                 serial: Optional[str] = None) -> list[str]:
    flag = "-rf" if recursive else "-f"
    return shell(adb_path, f"rm {flag} {remote_path}", serial)


def rename_path(adb_path: str, old_path: str, new_path: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"mv {old_path} {new_path}", serial)


def input_keyevent(adb_path: str, keycode: str, serial: Optional[str] = None) -> list[str]:
    return shell(adb_path, f"input keyevent {keycode}", serial)


def input_text(adb_path: str, text: str, serial: Optional[str] = None) -> list[str]:
    escaped = text.replace(" ", "%s")
    return shell(adb_path, f"input text {escaped}", serial)
