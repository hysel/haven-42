#!/usr/bin/env python3
"""Verify inactive embedding and encrypted-library preparation boundaries."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> int:
    checks = 0
    embedding = read("config/embedding-candidate-evaluation.json")
    assert len(embedding["candidates"]) == 3
    assert {item["licenseSpdx"] for item in embedding["candidates"]} <= {
        "Apache-2.0", "MIT"
    }
    assert all(item["parameters"] > 0 for item in embedding["candidates"])
    assert all(item["hardwareFit"].startswith("requires-") for item in embedding["candidates"])
    assert all(item["source"].startswith("https://huggingface.co/") for item in embedding["candidates"])
    nomic = next(item for item in embedding["candidates"] if item["id"] == "nomic-embed-text-v1.5")
    assert nomic["observedSafetensorsBytes"] is None
    assert nomic["upstreamReportedSafetensorsDisplaySize"] == "547 MB"
    assert not any(embedding["authority"].values())
    assert all(embedding["admissionRequirements"].values())
    checks += 9

    library = read("config/persistent-knowledge-library-contract.json")
    assert library["defaultMode"] == "memory-only-no-library"
    assert library["storage"]["plaintextFallbackAllowed"] is False
    assert library["storage"]["sharedMachineLibraryAllowed"] is False
    assert library["storage"]["networkFilesystemAllowed"] is False
    assert library["schemaLifecycle"]["atomicMigrationRequired"] is True
    assert library["schemaLifecycle"]["corruptionRecoveryReadOnly"] is True
    assert library["schemaLifecycle"]["automaticResetOrOverwriteAllowed"] is False
    assert library["contentLifecycle"]["liveFilesystemReferencesAllowed"] is False
    assert library["contentLifecycle"]["deletionCoversIndexesJournalsWalAndBackups"] is True
    assert library["contentLifecycle"]["uninstallDeletionRequiresExplicitChoice"] is True
    assert all(library["indexLifecycle"].values())
    assert not any(library["authority"].values())
    checks += 12

    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".py", ".js", ".html", ".css"}
    )
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    resources = (ROOT / "package/resource-integrity.json").read_text(encoding="utf-8")
    for marker in (
        "embedding-candidate-evaluation",
        "persistent-knowledge-library-contract",
        "test-retrieval-expansion-foundations",
    ):
        assert marker not in runtime
        assert marker not in package + resources
        checks += 2
    print(f"Retrieval expansion foundations passed {checks} inactive-boundary checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
