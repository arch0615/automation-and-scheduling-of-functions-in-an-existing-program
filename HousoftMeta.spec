# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Housoft Meta-Automation.
# Produces:  dist/HousoftMeta/HousoftMeta.exe  +  dist/HousoftMeta/_internal/
# The Inno Setup script then wraps that tree into HousoftMeta_Setup.exe.
#
# Layout decisions:
#   - web/templates and web/static must be inside the bundle (Flask reads them at runtime).
#   - templates/*.png (GUI screenshots) and config/schedule.json are NOT bundled here —
#     Inno Setup copies them next to HousoftMeta.exe so users can edit/add their own.
#   - .env and LEIA-ME.txt likewise live next to the .exe and are written by Inno Setup.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('web/templates', 'web/templates'),
        ('web/static', 'web/static'),
    ],
    hiddenimports=[
        'pyngrok',
        'pyngrok.ngrok',
        'anthropic',
        'pywinauto',
        'pywinauto.application',
        'pywinauto.findwindows',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'pytest',
        'core.gui_engine',
        'core.window_manager',
        'core.mock_gui_engine',
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HousoftMeta',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='HousoftMeta',
)
