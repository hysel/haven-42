#!/usr/bin/env python3
"""Run an explicitly requested, sanitized live startup/stop proof on macOS."""

from __future__ import annotations

import json
import platform
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from macos_installed_ollama import (  # noqa: E402
    MacOSInstalledOllamaCoordinator,
    OLLAMA_URL,
)


def main() -> int:
    if platform.system() != "Darwin" or platform.machine().lower() != "arm64":
        raise SystemExit("live-macos-installed-ollama-proof-requires-macos-arm64")
    coordinator = MacOSInstalledOllamaCoordinator("live-validation-session-only")
    stopped = False
    try:
        plan = coordinator.register_plan()
        approval = coordinator.approve(plan["planId"], plan["effects"])
        result = coordinator.start(approval)
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as response:
            tags = json.loads(response.read(1024 * 1024).decode("utf-8"))
        models = tags.get("models", []) if isinstance(tags, dict) else []
        if not isinstance(models, list):
            raise RuntimeError("macos-ollama-invalid-model-list")
        stopped = coordinator.close()
        print(json.dumps({
            "schemaVersion": 1,
            "kind": "macos-installed-ollama-live-proof",
            "status": "passed" if stopped else "failed",
            "appVersion": result["appVersion"],
            "runtimeVersion": result["runtimeVersion"],
            "signatureVerified": result["signatureVerified"],
            "gatekeeperAccepted": result["gatekeeperAccepted"],
            "ownedProcess": result["ownedProcess"],
            "modelCount": len(models),
            "downloadPerformed": result["downloadPerformed"],
            "installationPerformed": result["installationPerformed"],
            "modelDownloadPerformed": result["modelDownloadPerformed"],
            "processStopped": stopped,
            "privatePathsIncluded": False,
        }, sort_keys=True))
        return 0 if stopped else 1
    finally:
        if not stopped:
            coordinator.close()


if __name__ == "__main__":
    raise SystemExit(main())
