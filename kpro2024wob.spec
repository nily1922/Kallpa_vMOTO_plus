# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['kpro2024wob.py'],
    pathex=[],
    binaries=[],
    datas=[('CITDI_LOGO_SINFONDO.png', '.'), ('citdi_theme.json', '.'), ('MANUAL DE SOFTWARE.pdf', '.'), ('logo_kp.ico', '.')],
    hiddenimports=[],
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
    name='kpro2024wob',
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
    icon=['logo_kp.ico'],
)
