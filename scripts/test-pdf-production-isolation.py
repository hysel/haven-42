#!/usr/bin/env python3
"""Fail closed unless PDF production isolation remains explicitly unadmitted."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    assessment = json.loads(
        (ROOT / "config/pdf-production-isolation-assessment.json").read_text(
            encoding="utf-8"
        )
    )
    prototype = json.loads(
        (ROOT / "config/pdf-parser-worker-prototype-contract.json").read_text(
            encoding="utf-8"
        )
    )
    checks = 0
    assert assessment["status"] == "assessment-complete-production-isolation-not-satisfied"
    checks += 1
    common = assessment["commonRequirements"]
    assert all(
        common[name]
        for name in (
            "separateProcessRequired",
            "singleDocumentPerProcessRequired",
            "boundedByteTransportRequired",
            "networkNamespaceOrOsDenialRequired",
            "filesystemReadAllowlistRequired",
            "processTreeTerminationRequired",
            "cpuMemoryWallAndOutputLimitsRequired",
            "privilegeReductionRequired",
            "packageComponentIntegrityRequired",
            "crashResidueScanRequired",
        )
    )
    assert common["documentPathTransportAllowed"] is False
    assert common["filesystemWriteAllowed"] is False
    assert common["temporaryFilesAllowed"] is False
    assert common["childProcessesAllowed"] is False
    checks += 5
    platforms = assessment["platforms"]
    assert set(platforms) == {"windows", "linux", "macos"}
    checks += 1
    for name, expected_source in (("windows", True), ("linux", True), ("macos", False)):
        value = platforms[name]
        assert value["sourceEvidence"] is expected_source
        assert value["productionIsolationSatisfied"] is False
        assert value["requiredBeforeProduction"]
        checks += 3
    assert "restricted-token-or-appcontainer-equivalent" in platforms["windows"]["requiredBeforeProduction"]
    assert "os-enforced-network-denial" in platforms["windows"]["requiredBeforeProduction"]
    assert "seccomp-or-equivalent-system-call-policy" in platforms["linux"]["requiredBeforeProduction"]
    assert "landlock-or-equivalent-filesystem-policy" in platforms["linux"]["requiredBeforeProduction"]
    assert "seatbelt-or-equivalent-sandbox-policy" in platforms["macos"]["requiredBeforeProduction"]
    checks += 5
    assert prototype["containment"]["productionGradeIsolationClaimed"] is False
    assert prototype["reviewAuthority"]["runtimeRouteAllowed"] is False
    assert prototype["reviewAuthority"]["packageInclusionAllowed"] is False
    checks += 3
    assert not any(assessment["admission"].values())
    checks += 1
    runtime = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "web").rglob("*.py")
    )
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert "restricted-pdf-worker" not in runtime
    assert "restricted-pdf-worker" not in package
    checks += 2
    print(f"PDF production isolation assessment passed {checks} fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
