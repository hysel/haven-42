#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "config/alpha-2-august-2026-model-qualification-result.json"
INVENTORY = ROOT / "config/alpha-2-model-version-inventory.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def inventory_ids(inventory: dict) -> set[str]:
    result: set[str] = set()
    for family in inventory["families"]:
        for version in family["versions"]:
            for candidate in version.get("candidates", []):
                result.add(candidate["id"])
    return result


def main() -> None:
    result = load(RESULT)
    assert result["kind"] == "haven42-alpha2-multi-model-qualification-result"
    assert result["runtime"] == {"provider": "ollama", "version": "0.32.13"}
    assert result["metadata"]["snapshotCount"] == 4
    assert result["metadata"]["modelProfileResultCount"] == 26
    assert result["metadata"]["fullGpuResidencyResultCount"] == 8

    groups = [set(value) for value in result["outcomes"].values()]
    assert all(groups)
    for index, group in enumerate(groups):
        for other in groups[index + 1:]:
            assert group.isdisjoint(other)
    recorded = set().union(*groups)
    assert recorded <= inventory_ids(load(INVENTORY))
    assert set(result["additionalCapabilityFailures"]) <= recorded
    assert set(result["promotionBlocks"]) <= recorded

    encoded = RESULT.read_text(encoding="utf-8").lower()
    for forbidden in ("192.168.", "/home/", "root@", "haven42@", '"hostname"'):
        assert forbidden not in encoded
    assert result["containsPrivateMachineIdentity"] is False
    assert result["containsNetworkIdentity"] is False
    assert result["containsRawPromptsOrResponses"] is False
    assert result["automaticDefaultChangeAllowed"] is False
    assert result["automaticSelectionEvidenceAllowed"] is False
    assert result["automaticSupportChangeAllowed"] is False
    print("August 2026 model qualification result passed fail-closed checks.")


if __name__ == "__main__":
    main()
