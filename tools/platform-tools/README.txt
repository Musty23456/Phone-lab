ALMUS PHONE LAB - Platform Tools Folder
========================================

This folder is where ALMUS PHONE LAB looks for bundled Android SDK
Platform Tools (adb.exe and fastboot.exe) so the app works out of the
box without requiring the user to install anything separately or edit
their system PATH.

This repository does NOT commit adb.exe/fastboot.exe/AdbWinApi.dll,
etc. (see .gitignore) because they are distributed by Google under
their own license and change independently of this project.

How this folder gets populated:

1. Automatically in CI (recommended):
   The GitHub Actions workflow (.github/workflows/build-windows.yml)
   downloads the official Google "platform-tools-latest-windows.zip"
   from https://developer.android.com/tools/releases/platform-tools
   and extracts adb.exe / fastboot.exe / required DLLs into this
   folder before running PyInstaller, so the built .exe ships with
   working tools.

2. Manually for local development:
   Download platform-tools for Windows from the link above, extract
   it, and copy adb.exe, fastboot.exe, and the accompanying DLLs
   (AdbWinApi.dll, AdbWinUsbApi.dll) into this folder.

If this folder is empty, ALMUS PHONE LAB will still start normally -
it falls back to searching your system PATH, or a custom path you set
in Settings > ADB Path / Fastboot Path.
