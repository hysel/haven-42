#!/usr/bin/env python3
"""Evaluate an offline installer lifecycle request without machine effects."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "offline-installer-lifecycle-contract.json"
ARTIFACT_REGISTRY_PATH = ROOT / "config" / "install-artifact-registry.json"
REQUEST_PATH = ROOT / "examples" / "fixtures" / "offline-installer-lifecycle-request.json"
MAX_INPUT_BYTES = 131072
HEX64 = re.compile(r"[0-9a-f]{64}")
TRANSACTION_ID = re.compile(r"txn-[0-9a-f]{16,64}")
SAFE_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
VERSION = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)(?:-[A-Za-z0-9][A-Za-z0-9.-]{0,63})?")
WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul", "clock$",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


class InstallerLifecycleError(ValueError):
    pass


def strict_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise InstallerLifecycleError("duplicate-json-key")
        result[key] = value
    return result


def read_json(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        if size > MAX_INPUT_BYTES:
            raise InstallerLifecycleError("input-too-large")
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_pairs)
    except InstallerLifecycleError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InstallerLifecycleError("invalid-json") from error
    if not isinstance(value, dict):
        raise InstallerLifecycleError("invalid-json-root")
    return value


def exact(value: object, fields: list[str] | set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(fields):
        raise InstallerLifecycleError(f"invalid-{label}-shape")
    return value


def load_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    contract = read_json(CONTRACT_PATH)
    registry = read_json(ARTIFACT_REGISTRY_PATH)
    if (
        contract.get("schemaVersion") != 1
        or contract.get("contractId") != "haven42.offline-installer-lifecycle"
        or contract.get("implementationStatus") != "simulation-only"
        or contract.get("runtimeAdmitted") is not False
        or registry.get("schemaVersion") != 1
        or registry.get("registryId") != "haven42.install-artifacts"
        or registry.get("defaultDecision") != "deny"
        or registry.get("runtimeAdmitted") is not False
        or registry.get("artifacts") != []
    ):
        raise InstallerLifecycleError("unsafe-contract-or-registry")
    effects = contract.get("machineEffects")
    if not isinstance(effects, dict) or not effects or any(value is not False for value in effects.values()):
        raise InstallerLifecycleError("machine-effects-enabled")
    return contract, registry


def validate_segment(value: object, platform: str) -> str:
    if not isinstance(value, str) or not SAFE_TOKEN.fullmatch(value):
        raise InstallerLifecycleError("unsafe-path-segment")
    if value in {".", ".."} or value.endswith((".", " ")):
        raise InstallerLifecycleError("unsafe-path-segment")
    stem = value.split(".", 1)[0].casefold()
    if platform == "windows" and stem in WINDOWS_RESERVED:
        raise InstallerLifecycleError("unsafe-path-segment")
    return value


def validate_destination(value: object, contract: dict[str, Any], platform: str) -> list[str]:
    destination = exact(
        value,
        {
            "rootKind", "relativeSegments", "ownedByCurrentUser", "writable",
            "trustedPermissions", "pathProof",
        },
        "destination",
    )
    if destination["rootKind"] not in contract["approvedRootKinds"]:
        raise InstallerLifecycleError("unapproved-destination-root")
    segments = destination["relativeSegments"]
    if not isinstance(segments, list) or not 1 <= len(segments) <= 16:
        raise InstallerLifecycleError("invalid-destination-segments")
    normalized = [validate_segment(segment, platform) for segment in segments]
    folded = [segment.casefold() for segment in normalized]
    if len(folded) != len(set(folded)) and len(normalized) > 1:
        raise InstallerLifecycleError("ambiguous-destination-segments")
    if any(destination[field] is not True for field in (
        "ownedByCurrentUser", "writable", "trustedPermissions",
    )):
        raise InstallerLifecycleError("destination-permission-preflight-failed")
    proof = exact(
        destination["pathProof"],
        {
            "canonical", "withinApprovedRoot", "symlink", "junction",
            "reparsePoint", "mountEscape", "overlapsApplicationRoot",
            "overlapsRepositoryRoot", "overlapsUserDataRoot",
        },
        "path-proof",
    )
    if proof["canonical"] is not True or proof["withinApprovedRoot"] is not True:
        raise InstallerLifecycleError("path-not-canonical-or-contained")
    forbidden = (
        "symlink", "junction", "reparsePoint", "mountEscape",
        "overlapsApplicationRoot", "overlapsRepositoryRoot", "overlapsUserDataRoot",
    )
    if any(proof[field] is not False for field in forbidden):
        raise InstallerLifecycleError("unsafe-path-proof")
    return normalized


def validate_artifact(value: object, contract: dict[str, Any], platform: str, architecture: str) -> dict[str, Any]:
    artifact = exact(value, contract["artifactIdentityFields"], "artifact")
    for field in ("fileName", "version"):
        validate_segment(artifact[field], platform)
    if not VERSION.fullmatch(artifact["version"]):
        raise InstallerLifecycleError("invalid-artifact-version")
    if artifact["platform"] != platform or artifact["architecture"] != architecture:
        raise InstallerLifecycleError("artifact-platform-mismatch")
    if not isinstance(artifact["byteLength"], int) or isinstance(artifact["byteLength"], bool) or not 1 <= artifact["byteLength"] <= 2**40:
        raise InstallerLifecycleError("invalid-artifact-size")
    if not isinstance(artifact["sha256"], str) or not HEX64.fullmatch(artifact["sha256"]):
        raise InstallerLifecycleError("invalid-artifact-digest")
    if artifact["sourceType"] not in contract["artifactSourceTypes"]:
        raise InstallerLifecycleError("unapproved-artifact-source")
    if artifact["licenseReviewed"] is not True or artifact["integrityVerified"] is not True:
        raise InstallerLifecycleError("artifact-not-verified")
    return artifact


def validate_storage(value: object, artifact_size: int, contract: dict[str, Any]) -> dict[str, int]:
    storage = exact(value, {"destinationAvailableBytes", "temporaryAvailableBytes"}, "storage")
    if any(
        not isinstance(storage[field], int)
        or isinstance(storage[field], bool)
        or storage[field] < 0
        for field in storage
    ):
        raise InstallerLifecycleError("invalid-storage-preflight")
    policy = contract["storagePolicy"]
    destination_required = artifact_size * policy["destinationMultiplier"] + policy["fixedReserveBytes"]
    temporary_required = artifact_size * policy["temporaryMultiplier"] + policy["fixedReserveBytes"]
    if storage["destinationAvailableBytes"] < destination_required:
        raise InstallerLifecycleError("destination-space-insufficient")
    if storage["temporaryAvailableBytes"] < temporary_required:
        raise InstallerLifecycleError("temporary-space-insufficient")
    return {
        "destinationRequiredBytes": destination_required,
        "temporaryRequiredBytes": temporary_required,
    }


def digest_entry(entry: dict[str, Any]) -> str:
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def validate_journal(value: object, transaction_id: str, contract: dict[str, Any]) -> str:
    if not isinstance(value, list) or len(value) > 64:
        raise InstallerLifecycleError("invalid-journal")
    previous = "0" * 64
    for expected_sequence, raw in enumerate(value, start=1):
        entry = exact(
            raw,
            {"sequence", "transactionId", "event", "previousDigest", "digest"},
            "journal-entry",
        )
        if entry["sequence"] != expected_sequence or entry["transactionId"] != transaction_id:
            raise InstallerLifecycleError("journal-state-confusion")
        if entry["event"] not in contract["transactionPhases"]:
            raise InstallerLifecycleError("invalid-journal-event")
        if entry["previousDigest"] != previous:
            raise InstallerLifecycleError("journal-chain-broken")
        unsigned = {key: entry[key] for key in entry if key != "digest"}
        if not isinstance(entry["digest"], str) or entry["digest"] != digest_entry(unsigned):
            raise InstallerLifecycleError("journal-digest-invalid")
        previous = entry["digest"]
    return previous


def append_journal(transaction_id: str, events: list[str], previous: str, start: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for sequence, event in enumerate(events, start=start):
        unsigned = {
            "sequence": sequence,
            "transactionId": transaction_id,
            "event": event,
            "previousDigest": previous,
        }
        entry = {**unsigned, "digest": digest_entry(unsigned)}
        result.append(entry)
        previous = entry["digest"]
    return result


def validate_state(value: object, transaction_id: str, operation: str, version: str, limit: int) -> dict[str, Any]:
    state = exact(
        value,
        {
            "installedVersions", "activeVersion", "partialTransactionId",
            "completedTransactionIds", "stateDigest",
        },
        "current-state",
    )
    versions = state["installedVersions"]
    if (
        not isinstance(versions, list)
        or len(versions) > limit
        or len(versions) != len(set(versions))
        or not all(isinstance(item, str) and VERSION.fullmatch(item) for item in versions)
    ):
        raise InstallerLifecycleError("invalid-retained-versions")
    if state["activeVersion"] is not None and state["activeVersion"] not in versions:
        raise InstallerLifecycleError("active-version-state-confusion")
    partial = state["partialTransactionId"]
    if partial is not None and (not isinstance(partial, str) or not TRANSACTION_ID.fullmatch(partial)):
        raise InstallerLifecycleError("invalid-partial-transaction")
    completed = state["completedTransactionIds"]
    if (
        not isinstance(completed, list)
        or len(completed) > 16
        or len(completed) != len(set(completed))
        or not all(isinstance(item, str) and TRANSACTION_ID.fullmatch(item) for item in completed)
    ):
        raise InstallerLifecycleError("invalid-completed-transactions")
    if transaction_id in completed:
        raise InstallerLifecycleError("transaction-replay")
    if not isinstance(state["stateDigest"], str) or not HEX64.fullmatch(state["stateDigest"]):
        raise InstallerLifecycleError("invalid-state-digest")
    if operation == "install" and versions:
        raise InstallerLifecycleError("install-requires-absent-state")
    if operation in {"update", "rollback", "cleanup", "uninstall"} and not versions:
        raise InstallerLifecycleError("operation-requires-present-state")
    if operation == "update" and version in versions:
        raise InstallerLifecycleError("replay-or-same-version-update")
    if operation == "update" and state["activeVersion"] is not None:
        candidate = tuple(int(item) for item in VERSION.fullmatch(version).groups())
        active = tuple(int(item) for item in VERSION.fullmatch(state["activeVersion"]).groups())
        if candidate < active:
            raise InstallerLifecycleError("downgrade-rejected")
    if operation == "rollback" and version not in versions:
        raise InstallerLifecycleError("rollback-target-not-installed")
    if operation in {"cleanup", "uninstall"} and version != state["activeVersion"]:
        raise InstallerLifecycleError("artifact-state-mismatch")
    if operation == "recover" and partial is None:
        raise InstallerLifecycleError("recover-requires-partial-state")
    if operation != "recover" and partial is not None and partial != transaction_id:
        raise InstallerLifecycleError("partial-state-conflict")
    return state


def validate_uninstall_files(value: object, operation: str, platform: str, contract: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > contract["uninstallPolicy"]["maximumFileRecords"]:
        raise InstallerLifecycleError("invalid-uninstall-file-list")
    if operation == "uninstall" and not value:
        raise InstallerLifecycleError("exact-uninstall-files-required")
    if operation != "uninstall" and value:
        raise InstallerLifecycleError("unexpected-uninstall-files")
    normalized: list[dict[str, Any]] = []
    identities: set[tuple[str, ...]] = set()
    for raw in value:
        item = exact(raw, {"relativeSegments", "sha256", "ownedByTransaction"}, "uninstall-file")
        segments = item["relativeSegments"]
        if not isinstance(segments, list) or not 1 <= len(segments) <= 24:
            raise InstallerLifecycleError("invalid-uninstall-path")
        identity = tuple(validate_segment(segment, platform) for segment in segments)
        folded = tuple(segment.casefold() for segment in identity)
        if folded in identities:
            raise InstallerLifecycleError("duplicate-uninstall-file")
        identities.add(folded)
        if not isinstance(item["sha256"], str) or not HEX64.fullmatch(item["sha256"]):
            raise InstallerLifecycleError("invalid-uninstall-digest")
        if item["ownedByTransaction"] is not True:
            raise InstallerLifecycleError("unowned-uninstall-file")
        normalized.append(item)
    return normalized


def evaluate(request: dict[str, Any]) -> dict[str, Any]:
    contract, registry = load_contract()
    required = {
        "schemaVersion", "operation", "transactionId", "platform", "architecture",
        "componentId", "artifact", "storage", "destination", "currentState",
        "interruption", "userDataChoice", "uninstallFiles", "journal",
    }
    request = exact(request, required, "request")
    if request["schemaVersion"] != 1:
        raise InstallerLifecycleError("invalid-request-version")
    operation = request["operation"]
    if operation not in contract["operations"]:
        raise InstallerLifecycleError("invalid-operation")
    transaction_id = request["transactionId"]
    if not isinstance(transaction_id, str) or not TRANSACTION_ID.fullmatch(transaction_id):
        raise InstallerLifecycleError("invalid-transaction-id")
    platform = request["platform"]
    if platform not in contract["platformChecklists"]:
        raise InstallerLifecycleError("unsupported-platform")
    architecture = request["architecture"]
    if architecture not in {"x86_64", "arm64"}:
        raise InstallerLifecycleError("unsupported-architecture")
    if not isinstance(request["componentId"], str) or not SAFE_TOKEN.fullmatch(request["componentId"]):
        raise InstallerLifecycleError("invalid-component-id")
    artifact = validate_artifact(request["artifact"], contract, platform, architecture)
    storage = validate_storage(request["storage"], artifact["byteLength"], contract)
    destination = validate_destination(request["destination"], contract, platform)
    state = validate_state(
        request["currentState"], transaction_id, operation, artifact["version"],
        contract["retainedVersionLimit"],
    )
    interruption = request["interruption"]
    if interruption is not None and interruption not in contract["transactionPhases"][:-1]:
        raise InstallerLifecycleError("invalid-interruption-phase")
    if request["userDataChoice"] not in {"preserve", "delete"}:
        raise InstallerLifecycleError("invalid-user-data-choice")
    if operation != "uninstall" and request["userDataChoice"] != "preserve":
        raise InstallerLifecycleError("user-data-delete-outside-uninstall")
    uninstall_files = validate_uninstall_files(request["uninstallFiles"], operation, platform, contract)
    previous = validate_journal(request["journal"], transaction_id, contract)
    if state["partialTransactionId"] and request["journal"] == []:
        raise InstallerLifecycleError("partial-state-journal-required")

    base_events = list(contract["transactionPhases"][:-1])
    if interruption:
        stop = base_events.index(interruption) + 1
        events = base_events[:stop]
        status = "interrupted-recovery-plan"
        next_operation = "recover"
    else:
        events = base_events + ["complete"]
        status = f"{operation}-plan"
        next_operation = None
    journal = append_journal(transaction_id, events, previous, len(request["journal"]) + 1)

    versions = list(state["installedVersions"])
    if operation in {"install", "update"} and artifact["version"] not in versions:
        versions.append(artifact["version"])
    if operation == "uninstall":
        versions = []
    retained = versions[-contract["retainedVersionLimit"]:]
    would_remove = versions[:-contract["retainedVersionLimit"]]
    return {
        "schemaVersion": 1,
        "status": status,
        "transactionId": transaction_id,
        "componentId": request["componentId"],
        "artifactRegistryDecision": registry["defaultDecision"],
        "runtimeAdmitted": False,
        "executionAllowed": False,
        "destination": {
            "rootKind": request["destination"]["rootKind"],
            "relativeSegments": destination,
        },
        "storagePreflight": storage,
        "plannedEvents": events,
        "journalAppend": journal,
        "recoveryRequired": interruption is not None,
        "nextOperation": next_operation,
        "wouldRetainVersions": retained,
        "wouldRemoveVersions": would_remove,
        "exactUninstallFileCount": len(uninstall_files),
        "userDataChoice": request["userDataChoice"],
        "platformChecklist": contract["platformChecklists"][platform],
        "machineEffects": dict(contract["machineEffects"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-path", type=Path, default=REQUEST_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = evaluate(read_json(args.request_path))
    except InstallerLifecycleError as error:
        print(f"Offline installer lifecycle rejected input: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f"Offline installer lifecycle simulation passed: {result['status']}; "
            "execution remains disabled."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
