#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "config/alpha-2-rx5700xt-certification-result.json"
PLAN = ROOT / "config/alpha-2-rx5700xt-certification-plan.json"
INVENTORY = ROOT / "config/alpha-2-model-version-inventory.json"
MATRIX = ROOT / "config/alpha-2-model-qualification-matrix.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def canonical_sha256(value: dict) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    result = load(RESULT)
    assert result["kind"] == "haven42-alpha2-exact-hardware-certification-result"
    assert result["status"] == "exact-profile-engineering-evidence-complete"
    assert result["runtime"] == {"provider": "ollama", "version": "0.32.13"}
    assert result["hardwareProfile"]["model"] == "Radeon RX 5700 XT"
    assert result["hardwareProfile"]["backend"] == "vulkan-radv"

    bindings = result["bindings"]
    assert bindings["plan"]["canonicalSha256"] == canonical_sha256(load(PLAN))
    assert bindings["inventoryCanonicalSha256"] == canonical_sha256(load(INVENTORY))
    assert bindings["matrixCanonicalSha256"] == canonical_sha256(load(MATRIX))

    passed = set(result["coreQualification"]["passed"])
    failed = set(result["coreQualification"]["failedTaskGate"])
    assert passed
    assert failed
    assert passed.isdisjoint(failed)
    assert len(passed | failed) == 16
    assert len(result["safeRefusalsBeforeDownload"]) == 3

    stability = result["stability"]
    assert stability["outcome"] == "passed"
    assert stability["currentBootCpuSmokeSeconds"] == 600
    assert stability["currentBootHardwareIncidentCount"] == 0
    assert stability["finalProfileMemoryTestComplete"] is False

    power = result["power"]
    assert power["scope"] == "gpu-board-sysfs-power1-average"
    assert 0 < power["idleAverageWatts"] < power["activeAverageWatts"]
    assert power["activeAverageWatts"] <= power["peakWatts"]
    assert power["activeEnergyWattHours"] > 0
    assert power["outputTokensPerWattHour"] > 0

    for forbidden in ("192.168.", "/home/", "root@", "haven42@", '"hostname"'):
        assert forbidden not in RESULT.read_text(encoding="utf-8").lower()
    assert result["containsPrivateMachineIdentity"] is False
    assert result["containsNetworkIdentity"] is False
    assert result["containsRawPromptsOrResponses"] is False
    assert result["automaticDefaultChangeAllowed"] is False
    assert result["automaticSupportChangeAllowed"] is False
    print("RX 5700 XT exact-profile certification result passed fail-closed checks.")


if __name__ == "__main__":
    main()
