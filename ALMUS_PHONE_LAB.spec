# -*- mode: python ; coding: utf-8 -*-
"""
ALMUS_PHONE_LAB.spec

PyInstaller build spec for ALMUS PHONE LAB. Produces a one-directory
(onedir) Windows build under dist/ALMUS_PHONE_LAB/, bundling:
  - the compiled Python application
  - app/resources (QSS stylesheet, icons)
  - tools/platform-tools (adb.exe/fastboot.exe if present at build time;
    if absent, the app still runs and falls back to system PATH)

Onedir (rather than onefile) is used deliberately: it starts faster,
makes it easy to inspect bundled DLLs/tools, and matches the layout the
project ships (ALMUS_PHONE_LAB.exe next to a tools/ folder).
"""

import os

block_cipher = None

project_root = os.path.abspath(os.getcwd())

datas = [
    (os.path.join("app", "resources"), os.path.join("app", "resources")),
]

# Bundle platform-tools only if the folder actually has files in it at
# build time (CI downloads them into tools/platform-tools before this
# spec runs; local/dev builds may not have them, which is fine - the
# app then falls back to system PATH / Settings custom path).
platform_tools_dir = os.path.join(project_root, "tools", "platform-tools")
if os.path.isdir(platform_tools_dir) and os.listdir(platform_tools_dir):
    datas.append((platform_tools_dir, os.path.join("tools", "platform-tools")))

hidden_imports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

a = Analysis(
    [os.path.join("app", "main.py")],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ALMUS_PHONE_LAB",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ALMUS_PHONE_LAB",
)
