# ALMUS PHONE LAB

**A professional Android phone servicing, diagnostics, ADB, Fastboot, APK management, and device-management toolkit for Windows.**

Developed by **ALMUS PRODUCTION**.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation (Prebuilt Release)](#installation-prebuilt-release)
- [Using the App](#using-the-app)
- [ADB Setup & USB Debugging](#adb-setup--usb-debugging)
- [Fastboot Overview](#fastboot-overview)
- [Building Locally](#building-locally)
- [Building via GitHub Actions](#building-via-github-actions)
- [Project Structure](#project-structure)
- [Safety & Scope](#safety--scope)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)
- [License](#license)
- [Credits](#credits)

---

## Overview

ALMUS PHONE LAB is a Windows desktop application for technicians and enthusiasts who
service, diagnose, and manage Android devices. It wraps the official Android
`adb` and `fastboot` tools in a modern, dark-themed PySide6 interface, with
modular pages for device diagnostics, app management, file transfer, screen
capture, log inspection, and more — all without freezing the UI while
commands run.

The app does **not** bundle any account-bypass, FRP-bypass, or IMEI-modification
functionality. It is built strictly for legitimate, owner-authorized device
servicing. See [Safety & Scope](#safety--scope).

## Features

- **Dashboard** — live device summary (manufacturer, model, Android version,
  battery, storage, RAM, CPU, screen resolution, serial) with quick actions
  (refresh, reboot to ADB/Fastboot/Recovery, power off).
- **Devices** — lists every detected ADB and Fastboot device; pick the active
  one when multiple phones are connected.
- **ADB Tools** — device state, reboot variants, install/uninstall APKs,
  push/pull files, package management (enable/disable/clear/force-stop),
  screenshots, logcat snapshot, and full device property/battery/storage/
  memory/CPU inspection.
- **Fastboot Tools** — device/variable inspection, reboot variants, flashing
  and erasing partitions (behind mandatory confirmation), booting a custom
  image, and slot management — all validated before execution.
- **APK Tools** — install single or multiple APKs, list/search installed
  packages, package info, launch/force-stop/clear-data/enable/disable,
  extract an installed APK back to your PC, uninstall.
- **File Manager** — browse device storage, push/pull, create folders,
  rename, and delete (with confirmation).
- **Screen Tools** — screenshots, timed screen recording (auto-pulled to your
  PC), optional scrcpy-based mirroring (only if you already have scrcpy),
  and basic input helpers (text injection, Home/Back/Power).
- **Diagnostics** — one-click full hardware/software/battery/connection
  report, exportable as TXT or JSON.
- **Logs** — live logcat streaming with pause/resume, search, level
  filtering, and export.
- **Drivers** — reports connected Android-related USB devices on Windows and
  ADB/Fastboot availability, plus troubleshooting guidance (no automatic
  driver installation).
- **Utilities** — an integrated ADB/Fastboot terminal for arbitrary safe
  commands, and a Platform Tools detector.
- **Settings** — theme, custom tool paths, default directories, confirmation
  preferences, auto-refresh interval, language preparation.
- **About** — version, credits, and license attributions.

## Requirements

### To run the built application
- Windows 10 or Windows 11 (64-bit)
- No separate Python installation required — the release is a standalone
  PyInstaller build.
- A USB cable and a device with **USB debugging** enabled (see below).

### To build from source
- Python 3.11+
- Windows (for producing a Windows build with PyInstaller); the source also
  runs cross-platform for development/testing purposes.
- Dependencies listed in `requirements.txt` (PySide6, PyInstaller).

## Installation (Prebuilt Release)

1. Go to the repository's **Releases** page (or the **Actions** tab if
   you're building from a fork) and download `ALMUS_PHONE_LAB_Windows.zip`.
2. Extract the ZIP anywhere on your PC.
3. Run `ALMUS_PHONE_LAB.exe` inside the extracted folder.
4. If the `tools\platform-tools` folder is empty in your build, either place
   `adb.exe`/`fastboot.exe` there yourself or point Settings at an existing
   Android SDK `platform-tools` installation.

## Using the App

1. Enable Developer Options and USB debugging on your Android phone (see
   [ADB Setup](#adb-setup--usb-debugging)).
2. Connect the phone via USB. The top bar and Dashboard update automatically
   once the device is detected.
3. Accept the "Allow USB debugging?" prompt on the phone.
4. Use the sidebar to navigate between Dashboard, ADB Tools, Fastboot Tools,
   APK Tools, File Manager, Screen Tools, Diagnostics, Logs, Drivers,
   Utilities, Settings, and About.
5. Any destructive action (uninstall, clear data, disable package, erase,
   flash, delete file, power off, etc.) always shows a confirmation dialog
   first. Flashing and erasing additionally require typing `CONFIRM`.

## ADB Setup & USB Debugging

1. On the phone: **Settings > About phone**, tap **Build number** 7 times to
   unlock Developer Options.
2. **Settings > System > Developer options**, enable **USB debugging**.
3. Connect the phone to your PC with a data-capable USB cable.
4. Accept the **Allow USB debugging?** dialog on the phone (optionally check
   "Always allow from this computer").
5. ALMUS PHONE LAB will show the device as soon as `adb devices` reports it
   in the `device` state (not `unauthorized` or `offline`).

## Fastboot Overview

Fastboot is a low-level protocol used when the phone is in bootloader mode
(usually reached via **Reboot Bootloader** from the Dashboard or Fastboot
Tools page). It's used for reading bootloader variables, flashing
partitions, and slot management on A/B devices. Flashing and erasing are
**destructive** and can render a device unbootable if the wrong image or
partition is used — always confirm you have the correct, device-specific
image before proceeding, and use the confirmation dialogs as the safety net
they're intended to be, not an obstacle to bypass.

## Building Locally

```powershell
git clone https://github.com/<your-username>/ALMUS_PHONE_LAB.git
cd ALMUS_PHONE_LAB
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Optional: place adb.exe / fastboot.exe (+ DLLs) into tools\platform-tools
# so the built app works without relying on system PATH.

python build.py
```

The built app will be in `dist\ALMUS_PHONE_LAB\ALMUS_PHONE_LAB.exe`.

To run from source without building an executable:

```powershell
python -m app.main
```

## Building via GitHub Actions

This repository includes two workflows:

- **`.github/workflows/build-windows.yml`** — runs on every push/PR to
  `main`/`master` (and manually via *Run workflow*). It installs
  dependencies, runs the test suite, downloads the official Android
  platform-tools, builds with PyInstaller, and uploads
  `ALMUS_PHONE_LAB_Windows.zip` as a workflow artifact (Actions tab >
  select the run > Artifacts).
- **`.github/workflows/release.yml`** — runs when you push a tag like
  `v1.0.0`, and additionally publishes a GitHub Release with the ZIP
  attached.

To trigger a release:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

## Project Structure

```
ALMUS_PHONE_LAB/
├── app/
│   ├── main.py                 # entry point
│   ├── ui/                     # main window, pages, reusable widgets, theme
│   ├── adb/                    # ADB command builders + client
│   ├── fastboot/                # Fastboot command builders + client
│   ├── device/                 # device info parsing + background monitor
│   ├── apk/                    # APK/package management
│   ├── files/                  # device file manager
│   ├── diagnostics/             # full diagnostic report engine
│   ├── screen/                  # screenshot/recording/mirroring
│   ├── drivers/                 # USB/driver status reporting
│   ├── logs/                    # logcat streaming/search/export
│   ├── utils/                   # process runner, tool detection, settings, validators
│   └── resources/               # QSS stylesheet
├── tools/platform-tools/        # adb.exe/fastboot.exe live here (not committed)
├── tests/                       # pytest suite
├── .github/workflows/           # CI build + release
├── requirements.txt
├── build.py
├── ALMUS_PHONE_LAB.spec
├── VERSION
└── README.md
```

## Safety & Scope

ALMUS PHONE LAB is built for **legitimate, owner-authorized** device
servicing and diagnostics. It intentionally does **not** implement:

- FRP (Factory Reset Protection) bypass
- Google / Samsung / iCloud account bypass or removal
- IMEI changing or cloning
- Network/SIM unlock bypass
- Screen-lock/pattern bypass or removal
- Any other circumvention of device security or ownership protections

A built-in validator (`app/utils/validators.py`) blocks command patterns
associated with the above, regardless of how a command is entered (buttons
or the integrated terminal). Separately, any operation considered
destructive-but-legitimate (erase, flash, format, delete, uninstall,
disable, etc.) always requires explicit on-screen confirmation before it
runs — the app never executes these silently.

## Troubleshooting

- **Device not detected**: see the in-app **Drivers** page for a live status
  check, and the troubleshooting checklist there (USB debugging, data
  cable, official manufacturer USB driver, trying a different port).
- **"ADB Not Found" / "Fastboot Not Found"**: place `adb.exe`/`fastboot.exe`
  in `tools\platform-tools`, install the Android SDK Platform Tools and add
  them to PATH, or set a custom path in **Settings**.
- **Fastboot device not listed**: some devices need a separate
  bootloader/Fastboot driver in addition to the ADB driver — check your
  manufacturer's developer pages.
- **"Failed to load Python DLL ... python311.dll — The specified module could
  not be found"**: the app was started without its `_internal` folder, or a
  Windows runtime is missing. Fix: (1) use `ALMUS_PHONE_LAB_Setup.exe` to
  install (it places everything in Program Files and installs the Visual C++
  runtime); (2) if using the ZIP, right-click → **Extract All** into a new
  folder (e.g. `C:\ALMUS_PHONE_LAB`) and never move the `.exe` out of that
  folder; (3) install the Microsoft Visual C++ 2015-2022 Redistributable
  (x64); (4) make sure Windows is 10/11 64-bit; (5) check antivirus
  quarantine for `python311.dll`.
- **App won't start**: run `ALMUS_PHONE_LAB.exe` from a terminal
  (`cmd`/PowerShell) to see any startup error text, and check that your
  antivirus hasn't quarantined a bundled DLL.
- **Screen mirroring says scrcpy not found**: this is optional; download
  scrcpy from https://github.com/Genymobile/scrcpy and place it next to
  ALMUS PHONE LAB or on your PATH, or set its path in Settings.

## Testing

```powershell
pip install pytest
python -m pytest tests -v
```

Tests cover ADB/Fastboot command construction, device-info parsing,
platform-tools detection, and destructive-command validation. The
application is designed to start successfully even with no phone
connected and no adb/fastboot detected — all tool lookups are defensive.

## License

This project is licensed under the [MIT License](LICENSE).

Android SDK Platform Tools (`adb`, `fastboot`) are distributed separately
by Google under their own license and are not redistributed as source in
this repository — see `tools/platform-tools/README.txt`.

## Credits

- **ALMUS PRODUCTION** — application design and development
- **Google / Android Open Source Project** — `adb`, `fastboot`, Android
  Platform Tools
- **Qt / PySide6** — GUI framework
- **scrcpy** (Genymobile) — optional, user-provided screen mirroring
- **PyInstaller** — Windows executable packaging
