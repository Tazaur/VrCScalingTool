# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_all

_zc_datas, _zc_bins, _zc_hidden = collect_all('zeroconf')

a = Analysis(
    ['scaling_main.py'],
    pathex=[],
    binaries=_zc_bins,
    datas=[('TVST.ico', '.')] + collect_data_files('openvr') + _zc_datas,
    hiddenimports=['openvr', 'ifaddr'] + _zc_hidden,
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
    name='TazaursVrCScalingTool',
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
    icon=['TVST.ico'],
)
