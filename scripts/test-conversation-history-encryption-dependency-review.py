#!/usr/bin/env python3
"""Fail-closed checks for the conversation-history encryption dependency review."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = json.loads((ROOT / "config/conversation-history-encryption-dependency-review.json").read_text(encoding="utf-8"))


def main() -> int:
    checks = 0
    assert REVIEW["schemaVersion"] == 1; checks += 1
    assert REVIEW["status"] == "no-encryption-dependency-admitted"; checks += 1
    core = REVIEW["coreCandidate"]
    assert core["version"] == "4.17.0" and core["releaseTag"] == "v4.17.0"; checks += 1
    assert len(core["commitSha"]) == 40 and len(core["tagObjectSha"]) == 40; checks += 1
    assert core["sqliteBaseline"] == "3.53.3"; checks += 1
    verification = core["verification"]
    assert verification["annotatedTagVerifiedByGitHub"] is False; checks += 1
    assert verification["commitVerifiedByGitHub"] is False; checks += 1
    assert verification["desktopCommunityReleaseAssetsPublished"] is False; checks += 1
    assert verification["generatedSourceArchiveDigestTreatedAsStableReleaseIdentity"] is False; checks += 1
    license_record = core["license"]
    assert license_record["expression"] == "BSD-3-Clause"; checks += 1
    assert license_record["userAccessibleAttributionRequired"] is True; checks += 1
    assert license_record["communityEditionIsFipsValidated"] is False; checks += 1
    sqlcipher3, legacy = REVIEW["bindingCandidates"]
    assert sqlcipher3["name"] == "sqlcipher3" and sqlcipher3["version"] == "0.6.2"; checks += 1
    assert sqlcipher3["status"] == "rejected-for-current-admission"; checks += 1
    assert sqlcipher3["embeddedSqlcipherVersion"] == "4.12.0"; checks += 1
    assert {item["platform"] for item in sqlcipher3["artifacts"]} == {
        "windows-x86_64-cpython314", "linux-x86_64-cpython314",
        "macos-universal2-cpython314", "source",
    }; checks += 1
    assert all(len(item["sha256"]) == 64 and item["trustedPublishing"] is False for item in sqlcipher3["artifacts"]); checks += 1
    assert legacy["name"] == "pysqlcipher3" and legacy["status"] == "rejected-unmaintained"; checks += 1
    assert not any(REVIEW["authority"].values()); checks += 1
    package_spec = (ROOT / "package" / "haven42.spec").read_text(encoding="utf-8")
    assert "sqlcipher3" not in package_spec and "pysqlcipher3" not in package_spec; checks += 1
    print(f"Conversation-history encryption dependency review passed {checks} fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
