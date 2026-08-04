#!/usr/bin/env python3
"""Keep candidate non-Continue public-repository profiles non-executable."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    profiles = json.loads((ROOT / "config/non-continue-validation-profiles.json").read_text(encoding="utf-8"))
    surfaces = json.loads((ROOT / "config/agent-surface-solutions.json").read_text(encoding="utf-8"))
    assert profiles["schemaVersion"] == 1
    assert profiles["status"] == "candidate-profiles-not-runtime-admitted"
    known = {item["id"]: item for item in surfaces["surfaces"]}
    entries = profiles["profiles"]
    assert {item["surfaceId"] for item in entries} == {"aider", "opencode"}
    assert len(entries) == len({item["id"] for item in entries}) == 2
    for item in entries:
        assert re.fullmatch(r"[a-z][a-z0-9-]{2,79}", item["id"])
        assert item["surfaceId"] in known and item["surfaceId"] != "continue"
        assert set(item["operations"]) == {"repository-discovery", "read-only-review", "plan-only"}
        assert all(item[name] is False for name in (
            "writeAllowed", "automaticCommitAllowed", "networkBeyondExplicitProviderAllowed", "promotionAllowed"
        ))
    requirements = profiles["repositoryRequirements"]
    assert all(requirements[name] is True for name in (
        "publicRepositoryRequired", "permissiveLicenseEvidenceRequired", "immutableCommitRequired",
        "ignoredDisposableCloneRequired", "cleanTreeRequired",
    ))
    assert all(requirements[name] is False for name in (
        "submodulesAllowed", "gitLfsSmudgeAllowed", "repositoryHooksAllowed", "packageInstallationAllowed",
        "buildScriptsAllowed", "testsFromTargetRepositoryAllowed",
    ))
    assert all(value is False for value in profiles["authority"].values())
    assert all(value is False for key, value in profiles["evidence"].items() if key != "sanitizedSummaryOnly")
    assert profiles["evidence"]["sanitizedSummaryOnly"] is True
    serialized = json.dumps(profiles)
    assert "http://" not in serialized.casefold() and "https://" not in serialized.casefold()
    assert "agentCommand" not in serialized and "argumentsTemplate" not in serialized
    print("Non-Continue validation profiles passed 15 candidate-only safety checks.")


if __name__ == "__main__":
    main()
