#!/usr/bin/env python3
"""Validate exact, unpromoted local image-provider candidate records."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "local-image-candidate-profiles.json"
FIXTURES = ROOT / "examples" / "fixtures" / "local-image-hardware-profile-cases.json"
DIGEST = re.compile(r"[0-9a-f]{64}")


def select_profile(manifest: dict, case: dict) -> str | None:
    for profile in manifest["profiles"]:
        accelerator = profile["accelerator"]
        if (
            profile["selectionAvailability"] == "available"
            and profile["operatingSystem"] == case["os"]
            and profile["architecture"] == case["architecture"]
            and accelerator["vendor"] == case["vendor"]
            and accelerator["model"] == case["model"]
            and accelerator["runtime"] == case["runtime"]
            and accelerator["runtimeVersion"] == case["runtimeVersion"]
            and profile["driverIdentity"] == case["driverIdentity"]
            and case["vramBytes"] >= accelerator["vramBytes"]
        ):
            return profile["id"]
    return None


def validate(manifest: dict) -> None:
    assert manifest["status"] == "candidate-only-unpromoted"
    assert manifest["runtimeAdmitted"] is False
    assert manifest["packageInclusionAllowed"] is False
    assert manifest["crossProfileEvidenceInheritanceAllowed"] is False
    assert manifest["silentCpuFallbackAllowed"] is False
    assert manifest["requiredEndpoint"] == {
        "scheme": "http",
        "host": "127.0.0.1",
        "port": 8188,
        "redirectsAllowed": False,
        "browserAutoLaunchAllowed": False,
    }
    assert len(manifest["requiredProcessIdentity"]) == 7
    assert DIGEST.fullmatch(manifest["checkpoint"]["sha256"])
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["checkpoint"]["revision"])
    assert len(manifest["profiles"]) == 3
    assert {profile["accelerator"]["vendor"] for profile in manifest["profiles"]} == {
        "AMD", "NVIDIA", "Intel"
    }
    ids = set()
    digests = set()
    for profile in manifest["profiles"]:
        assert profile["id"] not in ids
        ids.add(profile["id"])
        assert profile["status"] == "partial-pass-unpromoted"
        assert profile["operatingSystem"] == "windows"
        assert profile["architecture"] == "x86_64"
        assert profile["accelerator"]["vramBytes"] >= 12 * 1024**3
        assert profile["minimumAvailableStorageBytes"] is None
        assert profile["selectionAvailability"].startswith("blocked-")
        assert profile["storageFitStatus"].startswith("blocked-")
        assert (ROOT / profile["evidence"]).is_file()
        roles = {artifact["role"] for artifact in profile["artifacts"]}
        assert roles == {"known-good", "validated-candidate"}
        for artifact in profile["artifacts"]:
            assert DIGEST.fullmatch(artifact["sha256"])
            assert artifact["sha256"] not in digests
            digests.add(artifact["sha256"])
            assert artifact["sizeBytes"] is None or artifact["sizeBytes"] > 0
    assert manifest["consent"] == {
        "singleUse": True,
        "effectBound": True,
        "disclosesNetworkWritesProcessesRetentionAndCleanup": True,
        "unknownArtifactApprovalAllowed": False,
    }
    assert len(manifest["packageExclusions"]) == 5


def reject_mutation(manifest: dict, mutate) -> None:
    candidate = copy.deepcopy(manifest)
    mutate(candidate)
    try:
        validate(candidate)
    except (AssertionError, KeyError, TypeError):
        return
    raise AssertionError("unsafe candidate manifest mutation was accepted")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate(manifest)
    cases = json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"]
    assert len(cases) == 7
    for case in cases:
        assert select_profile(manifest, case) == case["expected"], case["id"]
    reject_mutation(manifest, lambda value: value.__setitem__("runtimeAdmitted", True))
    reject_mutation(manifest, lambda value: value.__setitem__("packageInclusionAllowed", True))
    reject_mutation(manifest, lambda value: value.__setitem__("silentCpuFallbackAllowed", True))
    reject_mutation(manifest, lambda value: value["requiredEndpoint"].__setitem__("host", "0.0.0.0"))
    reject_mutation(manifest, lambda value: value["profiles"][0].__setitem__("status", "promoted"))
    reject_mutation(manifest, lambda value: value["profiles"][0]["artifacts"][0].__setitem__("sha256", "0" * 63))
    print("Local image candidate profiles passed 7 selection and 6 hostile cases.")


if __name__ == "__main__":
    main()
