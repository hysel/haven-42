# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH).parent
resources = [
    ("web/static/index.html", "web/static"),
    ("web/static/app.js", "web/static"),
    ("web/static/styles.css", "web/static"),
    ("config/text-capability-model-recommendations.json", "config"),
    ("config/evidence-catalog.tsv", "config"),
    ("config/install-component-registry.json", "config"),
    ("config/workflows.json", "config"),
    ("package/resource-integrity.json", "package"),
]

a = Analysis(
    [str(root / "web" / "server.py")],
    pathex=[str(root / "scripts")],
    binaries=[],
    datas=[(str(root / source), destination) for source, destination in resources],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="haven42",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="haven42",
)
