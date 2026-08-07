# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

root = Path(SPECPATH).parent
version_info = str(root / "package/haven42-version-info.txt") if sys.platform == "win32" else None
resources = [
    ("web/static/index.html", "web/static"),
    ("web/static/accessibility.html", "web/static"),
    ("web/static/app.js", "web/static"),
    ("web/static/styles.css", "web/static"),
    ("config/text-capability-model-recommendations.json", "config"),
    ("config/evidence-catalog.tsv", "config"),
    ("config/agent-surface-capabilities.json", "config"),
    ("config/agent-surface-solutions.json", "config"),
    ("config/install-component-registry.json", "config"),
    ("config/workflows.json", "config"),
    ("config/windows-alpha-contract.json", "config"),
    ("config/windows-alpha-model-catalog.json", "config"),
    ("config/windows-alpha-component-registry.json", "config"),
    ("config/windows-alpha-resource-monitor-contract.json", "config"),
    ("config/windows-alpha-quantization-contract.json", "config"),
    ("package/resource-integrity.json", "package"),
]

a = Analysis(
    [str(root / "web" / "server.py")],
    pathex=[str(root / "scripts")],
    binaries=[],
    datas=[(str(root / source), destination) for source, destination in resources],
    hiddenimports=["diagnostic_logging", "windows_alpha", "windows_alpha_setup"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest"],
    noarchive=False,
    optimize=1,
)
if sys.platform == "win32":
    # Windows 10+ supplies the UCRT and API-set contract DLLs. PyInstaller may
    # otherwise resolve application-local copies from an unrelated host PATH
    # entry, making the package host-dependent. Keep Python's exact VCRUNTIME
    # files, but never collect these operating-system components.
    a.binaries = [
        entry
        for entry in a.binaries
        if not (
            Path(entry[0]).name.casefold().startswith("api-ms-win-")
            or Path(entry[0]).name.casefold() == "ucrtbase.dll"
        )
    ]
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
    version=version_info,
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
