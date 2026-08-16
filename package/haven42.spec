# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os
import sys

root = Path(SPECPATH).parent
default_version = "0.4.0-alpha.2" if sys.platform.startswith("linux") else "0.4.0-alpha.1"
build_version = os.environ.get("HAVEN42_BUILD_VERSION", default_version)
if build_version not in {"0.4.0-alpha.1", "0.4.0-alpha.2"}:
    raise ValueError("Invalid Haven 42 build version")
if sys.platform.startswith("linux") and build_version != "0.4.0-alpha.2":
    raise ValueError("Linux packaging is restricted to Alpha 2")
version_file = (
    "package/haven42-alpha2-version-info.txt"
    if build_version == "0.4.0-alpha.2"
    else "package/haven42-version-info.txt"
)
runtime_hook = (
    "package/runtime-hook-alpha2.py"
    if build_version == "0.4.0-alpha.2"
    else "package/runtime-hook-alpha1.py"
)
version_info = str(root / version_file) if sys.platform == "win32" else None
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
    ("config/windows-alpha-2-contract.json", "config"),
    ("config/windows-alpha-model-catalog.json", "config"),
    ("config/windows-alpha-component-registry.json", "config"),
    ("config/windows-alpha-resource-monitor-contract.json", "config"),
    ("config/windows-alpha-quantization-contract.json", "config"),
    ("config/linux-alpha-contract.json", "config"),
    ("config/linux-alpha-component-registry.json", "config"),
    ("config/alpha-2-model-catalog.json", "config"),
    ("config/alpha-2-model-selection-evidence.json", "config"),
    ("config/alpha-2-model-selection-policy.json", "config"),
    ("config/alpha-2-model-version-inventory.json", "config"),
    ("config/alpha-2-model-runtime-requirements.json", "config"),
    ("config/alpha-2-runtime-compatibility.json", "config"),
    ("config/linux-runtime-artifact-review.json", "config"),
    ("config/linux-model-artifact-review.json", "config"),
    ("config/web-research-query-adapter.json", "config"),
    ("config/web-research-native-query-transport.json", "config"),
    ("config/web-research-native-page-transport.json", "config"),
    ("config/web-research-page-foundation.json", "config"),
    ("scripts/validate-web-research-query-adapter.py", "scripts"),
    ("package/resource-integrity.json", "package"),
]

a = Analysis(
    [str(root / "web" / "server.py")],
    pathex=[str(root / "scripts")],
    binaries=[],
    datas=[(str(root / source), destination) for source, destination in resources],
    hiddenimports=[
        "alpha2_model_selector", "alpha2_runtime_compatibility", "alpha_platform", "diagnostic_logging", "electricity_rate_service", "linux_alpha",
        "linux_alpha_runtime", "linux_alpha_setup", "windows_alpha",
        "windows_alpha_setup", "web_research_query_adapter",
        "web_research_native_transport", "web_research_native_page_transport",
        "web_research_general_transport",
        "offline_research_page_text",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(root / runtime_hook)],
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
