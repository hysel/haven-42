"""Validate final Alpha 2 evidence without granting a workflow publication rights.

The original promotion contract is a historical candidate snapshot. This module
adds an evidence-bound final path; it never edits that snapshot or executes GitHub
operations. Actual publication additionally requires current hosted checks.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

SHA = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
NAMES = {
    "windows-x64": "haven42-0.4.0-alpha.2-windows-x64-signed.zip",
    "linux-x64": "haven42-0.4.0-alpha.2-linux-x64-unsigned.tar.gz",
    "macos-arm64": "haven42-0.4.0-alpha.2-macos-arm64-signed-notarized.zip",
}
TRUST = {
    "windows-x64": {"authenticode", "expected-publisher", "trusted-timestamp"},
    "linux-x64": set(),
    "macos-arm64": {"developer-id", "hardened-runtime", "notarization", "stapling", "gatekeeper"},
}
CHECKS = {
    "exact-source-ci", "security-privacy-review", "supply-chain-review",
    "release-documentation", "windows-11-x64-nvidia", "ubuntu-26.04-x64-nvidia",
    "bazzite-44-x64-nvidia", "macos-arm64",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def shape(value, keys):
    require(isinstance(value, dict) and set(value) == set(keys), "invalid-final-record-shape")


def evidence(item, root, source=None, hashes=None):
    shape(item, {"path", "sha256"})
    name = item["path"]
    require(isinstance(name, str) and name and "\\" not in name, "invalid-evidence-path")
    path = Path(name)
    require(not path.is_absolute() and ".." not in path.parts and ":" not in name,
            "invalid-evidence-path")
    require(isinstance(item["sha256"], str) and SHA.fullmatch(item["sha256"]), "invalid-evidence-hash")
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root.resolve()) and resolved.is_file(), "missing-or-unsafe-evidence")
    # JSON semantic digest is stable across Git's platform line-ending conversion.
    record = json.loads(resolved.read_text(encoding="utf-8"))
    payload = json.dumps(record,
                         sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    require(hashlib.sha256(payload).hexdigest() == item["sha256"], "evidence-hash-mismatch")
    if source is not None:
        require(isinstance(record, dict) and record.get("sourceCommit") == source
                and record.get("artifactSha256") == hashes, "evidence-content-binding-mismatch")


def evaluate_final(value, root: Path, artifact_directory: Path | None = None):
    shape(value, {"schemaVersion", "kind", "version", "sourceCommit", "prerelease",
                  "productionReady", "artifacts", "checks", "manualAccessibility", "ownerApproval"})
    require(type(value["schemaVersion"]) is int and value["schemaVersion"] == 1
            and value["kind"] == "haven42-alpha2-final-release-evidence"
            and value["version"] == "0.4.0-alpha.2", "invalid-final-record-identity")
    source = value["sourceCommit"]
    require(isinstance(source, str) and COMMIT.fullmatch(source), "invalid-source-commit")
    require(value["prerelease"] is True and value["productionReady"] is False, "release-scope-broadened")
    archives = value["artifacts"]
    require(isinstance(archives, dict) and set(archives) == set(NAMES), "incomplete-platform-set")
    blockers = []
    digest_set = {}
    for platform, item in archives.items():
        shape(item, {"name", "sha256", "sizeBytes", "sourceCommit", "trust", "evidence"})
        require(item["name"] == NAMES[platform] and item["sourceCommit"] == source, "artifact-source-or-name-mismatch")
        require(isinstance(item["sha256"], str) and SHA.fullmatch(item["sha256"])
                and type(item["sizeBytes"]) is int and item["sizeBytes"] > 0, "invalid-artifact-digest-or-size")
        require(isinstance(item["trust"], dict) and set(item["trust"]) == TRUST[platform]
                and all(v is True for v in item["trust"].values()), "platform-trust-incomplete")
        evidence(item["evidence"], root)
        digest_set[platform] = item["sha256"]
        if artifact_directory is not None:
            base = artifact_directory.resolve()
            path = base / item["name"]
            require(not path.is_symlink() and path.resolve().is_relative_to(base)
                    and path.is_file(), "artifact-missing-or-unsafe")
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            require(path.stat().st_size == item["sizeBytes"] and digest == item["sha256"], "artifact-bytes-mismatch")
    for item in archives.values():
        evidence(item["evidence"], root, source, digest_set)
    checks = value["checks"]
    require(isinstance(checks, dict) and set(checks) == CHECKS, "incomplete-check-set")
    for name, item in checks.items():
        shape(item, {"status", "sourceCommit", "artifactSha256", "evidence"})
        require(item["status"] in ("passed", "not-run", "failed", "blocked"), "invalid-check-status")
        require(item["sourceCommit"] == source and item["artifactSha256"] == digest_set,
                "check-not-bound-to-final-artifacts")
        if item["status"] == "passed":
            evidence(item["evidence"], root, source, digest_set)
        else:
            require(item["evidence"] is None, "pending-check-must-not-claim-evidence")
            blockers.append(name)
    accessibility = value["manualAccessibility"]
    shape(accessibility, {"status", "sourceCommit", "artifactSha256", "ownerApprovedDeferral", "evidence"})
    require(accessibility["sourceCommit"] == source and accessibility["artifactSha256"] == digest_set,
            "accessibility-not-bound-to-final-artifacts")
    require(accessibility["status"] in ("passed", "deferred-not-run", "failed", "not-run"), "invalid-accessibility-status")
    require(type(accessibility["ownerApprovedDeferral"]) is bool, "invalid-deferral-authority")
    if accessibility["status"] == "deferred-not-run":
        require(accessibility["ownerApprovedDeferral"] is True, "deferral-not-approved")
        evidence(accessibility["evidence"], root, source, digest_set)
    elif accessibility["status"] == "passed":
        require(accessibility["ownerApprovedDeferral"] is False, "deferral-is-not-a-pass")
        evidence(accessibility["evidence"], root, source, digest_set)
    else:
        require(accessibility["ownerApprovedDeferral"] is False and accessibility["evidence"] is None,
                "failed-accessibility-cannot-be-waived")
        blockers.append("manual-accessibility-validation")
    approval = value["ownerApproval"]
    shape(approval, {"approved", "sourceCommit", "artifactSha256", "evidence"})
    require(type(approval["approved"]) is bool and approval["sourceCommit"] == source
            and approval["artifactSha256"] == digest_set, "approval-not-bound-to-final-artifacts")
    if approval["approved"]:
        evidence(approval["evidence"], root, source, digest_set)
    else:
        require(approval["evidence"] is None, "unapproved-record-must-not-claim-evidence")
        blockers.append("publication-approval")
    if artifact_directory is None:
        blockers.append("final-archive-byte-verification")
    return {"Version": value["version"], "SourceCommit": source,
            "RemainingGates": sorted(blockers), "PublicationAllowed": not blockers,
            "ManualAccessibility": accessibility["status"], "ProductionReady": False,
            "AutomaticPublicationAllowed": False}
