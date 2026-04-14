# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for MeetAvatar Camera Client.

Build with:
    pyinstaller build.spec
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ["camera_client/main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "pyvirtualcam",
        "pyvirtualcam._native_windows",
        "PyQt6",
        "PyQt6.sip",
        "aiohttp",
        "PIL",
        "cv2",
        "numpy",
        "requests",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "scipy",
        "pandas",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MeetAvatar Camera",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
