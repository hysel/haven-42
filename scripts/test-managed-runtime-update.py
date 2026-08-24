#!/usr/bin/env python3
"""Offline approval and rollback-contract tests for managed runtime updates."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from managed_runtime_update import (  # noqa: E402
    ManagedRuntimeUpdateCoordinator,
    ManagedRuntimeUpdateError,
    read_runtime_selection,
)


CERTIFIED = {
    "version": "0.32.14", "sha256": "a" * 64, "byteLength": 100,
}


class Process:
    def stop(self):
        return True


class Setup:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.process = Process()


def main() -> int:
    original = ManagedRuntimeUpdateCoordinator._certified_component
    ManagedRuntimeUpdateCoordinator._certified_component = staticmethod(lambda: dict(CERTIFIED))
    try:
        with tempfile.TemporaryDirectory(prefix="haven42-runtime-update-") as temporary:
            root = Path(temporary)
            coordinator = ManagedRuntimeUpdateCoordinator("s" * 32, Setup(root))
            coordinator._root = lambda create: root  # type: ignore[method-assign]
            component = {
                "id": "ollama-runtime",
                "displayName": "Ollama local AI engine",
                "managedVersion": "0.32.14",
                "latestStableVersion": "0.32.15",
                "newerOfficialVersionAvailable": True,
                "managedVersionIsLatest": False,
                "availableForManagedSetup": False,
                "certificationStatus": "official-unverified",
                "releaseUrl": "https://github.com/ollama/ollama/releases/tag/v0.32.15",
                "downloadUrl": "https://github.com/ollama/ollama/releases/download/v0.32.15/ollama-windows-amd64.zip",
                "artifactName": "ollama-windows-amd64.zip",
                "downloadBytes": 101,
                "sha256": "b" * 64,
            }
            plan = coordinator.prepare(component, "latest-official")
            assert plan["certificationStatus"] == "official-unverified"
            assert plan["warning"] and plan["modelsAndUserDataKept"] is True
            assert "downloadUrl" not in plan and plan["certifiedVersionRetained"] == "0.32.14"
            try:
                coordinator.approve(plan["planId"], [])
                raise AssertionError("mismatched effects were accepted")
            except ManagedRuntimeUpdateError:
                pass
            plan = coordinator.prepare(component, "latest-official")
            token = coordinator.approve(plan["planId"], plan["effects"])
            coordinator._run = lambda value: coordinator._progress("complete", 100)  # type: ignore[method-assign]
            coordinator.start(token)
            coordinator.thread.join(timeout=5)
            assert coordinator.public_status()["phase"] == "complete"

            coordinator._write_selection(root, {
                "version": "0.32.15", "certificationStatus": "official-unverified",
                "sha256": "b" * 64,
            })
            status = coordinator.public_status()
            assert status["rollbackAvailable"] is True and status["activeVersion"] == "0.32.15"
            rollback = coordinator.prepare({}, "certified")
            assert rollback["version"] == "0.32.14" and rollback["certificationStatus"] == "certified"

            (root / "active-runtime.json").write_text("not-json", encoding="ascii")
            assert read_runtime_selection(root, CERTIFIED)["version"] == "0.32.14"
    finally:
        ManagedRuntimeUpdateCoordinator._certified_component = original
    print("Managed runtime update approval and rollback contract passed 16 checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
