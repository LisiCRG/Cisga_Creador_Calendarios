# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH)

holidays_datas, holidays_binaries, holidays_hiddenimports = collect_all("holidays")

a = Analysis(
    ['main.py'],
    pathex=[str(root / 'src')],
    binaries=holidays_binaries,
    datas=[
        (str(root / 'assets'), 'assets'),
        (str(root / 'data'), 'data'),
        (str(root / 'templates'), 'templates'),
        (str(root / 'templates_tipo'), 'templates_tipo'),
    ] + holidays_datas,
    hiddenimports=['openpyxl'] + holidays_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GENERADOR_TURNOS',
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
    icon=str(root / 'assets' / 'cisga.ico'),
    version=str(root / 'version_info.txt'),
)
