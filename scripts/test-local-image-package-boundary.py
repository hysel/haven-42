#!/usr/bin/env python3
"""Keep image-provider candidates and payloads outside shipping packages."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    contract = json.loads((ROOT / "config/local-image-source-package-parity-contract.json").read_text(encoding="utf-8"))
    spec = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    integrity = json.loads((ROOT / "package/resource-integrity.json").read_text(encoding="utf-8"))
    resources = "\n".join(entry["path"] for entry in integrity["resources"])
    assert contract["status"] == "candidate-test-contract-only"
    assert contract["nativeExecutionRequiredForCompletion"] is True
    for key in ("packageMayReadRepository", "packageMayContainProviderRuntime", "packageMayContainCheckpoint", "packageMayContainGeneratedArtifact"):
        assert contract[key] is False
    assert contract["externalProviderSoftwareMustRemainSeparate"] is True
    assert contract["providerAcquisitionIsNotPackageAuthority"] is True
    assert len(contract["profiles"]) == 3
    assert len(contract["requiredEquivalentChecks"]) == 9
    forbidden = ("local-image-candidate-profiles.json", "local-image-source-package-parity-contract.json", "comfyui", "sdxl", ".safetensors", ".ckpt", ".png")
    lowered = (spec + "\n" + resources).casefold()
    for marker in forbidden:
        assert marker.casefold() not in lowered, marker
    onboarding = json.loads((ROOT / "config/local-image-onboarding-contract.json").read_text(encoding="utf-8"))
    boundary = onboarding["distributionBoundary"]
    for key in (
        "externalProviderSoftwareBundled",
        "providerModelsBundled",
        "acceleratorDriversOrRuntimesBundled",
        "providerInstallersOrUpdaterPayloadsBundled",
    ):
        assert boundary[key] is False
    assert boundary["existingProviderConnectionAllowed"] is True
    assert boundary["separateUserManagedAcquisitionRequired"] is True
    assert boundary["havenRuntimeDependenciesMayBeBundledOnlyWhenReviewed"] is True
    print("Local image package boundary passed 16 separation and payload exclusions.")


if __name__ == "__main__":
    main()
