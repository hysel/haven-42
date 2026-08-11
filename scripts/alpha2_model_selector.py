#!/usr/bin/env python3
"""Effect-free, fail-closed model selection core for Haven 42 Alpha 2."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


SOURCE_ROOT = Path(__file__).resolve().parent.parent
ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
POLICY_PATH = ROOT / "config" / "alpha-2-model-selection-policy.json"
SAFE_ID = re.compile(r"[a-z0-9][a-z0-9.-]{0,79}")
SAFE_VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}")
HEX64 = re.compile(r"[0-9a-f]{64}")
PLATFORMS = {"windows", "linux", "macos"}
ARCHITECTURES = {"x64", "arm64"}
BACKENDS = {"cpu", "cuda", "rocm", "vulkan", "metal"}
CAPABILITIES = {"general.chat", "content.write", "content.summarize"}


class SelectionError(ValueError):
    """Raised when selection input is malformed or not policy-bound."""


def _load_json(path: Path, label: str) -> Any:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise SelectionError(f"Unsafe {label} file.")
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SelectionError(f"Cannot read {label}.") from error


def _catalog_path(policy: dict[str, Any], policy_path: Path) -> Path:
    source = policy["sourceCatalog"]
    relative = Path(source["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise SelectionError("Unsafe source catalog path.")
    candidate = (policy_path.resolve().parent.parent / relative).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as error:
        raise SelectionError("Source catalog escapes the repository.") from error
    return candidate


def load_policy(path: Path = POLICY_PATH) -> tuple[dict[str, Any], dict[str, Any]]:
    policy = _load_json(path, "model selection policy")
    validate_policy(policy)
    catalog_path = _catalog_path(policy, path)
    catalog = _load_json(catalog_path, "source model catalog")
    canonical = json.dumps(
        catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != policy["sourceCatalog"]["canonicalSha256"]:
        raise SelectionError("Source catalog canonical digest mismatch.")
    validate_catalog_binding(policy, catalog)
    return policy, catalog


def canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_policy(policy: Any) -> None:
    required = {
        "schemaVersion", "policyId", "release", "status", "sourceCatalog",
        "capabilities", "selectionPolicy", "fitLadder", "comparisonCandidates",
        "promotionRequirements",
    }
    expected_rules = {
        "largestValidatedComfortableFit": True,
        "exactArtifactDigestRequired": True,
        "exactExecutionProfileEvidenceRequired": True,
        "testedMemoryFloorRequired": True,
        "allRequestedCapabilitiesRequired": True,
        "platformStorageAdmissionRequired": True,
        "unknownGpuCapacityMeansZero": True,
        "silentCpuFallbackAllowed": False,
        "unverifiedModelAutomaticSelectionAllowed": False,
        "manualSelectionOfUnverifiedInstalledModelAllowed": True,
        "downloadsAllowedBySelector": False,
    }
    if (
        not isinstance(policy, dict)
        or set(policy) != required
        or policy.get("schemaVersion") != 1
        or policy.get("policyId") != "haven42.alpha2.model-selection"
        or policy.get("release") != "0.4.0-alpha.2"
        or policy.get("status") != "evidence-collection-no-new-product-promotion"
        or policy.get("selectionPolicy") != expected_rules
        or policy.get("capabilities") != [
            "general.chat", "content.write", "content.summarize"
        ]
    ):
        raise SelectionError("Invalid Alpha 2 model selection policy.")
    source = policy["sourceCatalog"]
    if (
        not isinstance(source, dict)
        or set(source) != {"path", "canonicalSha256"}
        or source.get("path") != "config/alpha-2-model-catalog.json"
        or not isinstance(source.get("canonicalSha256"), str)
        or not HEX64.fullmatch(source["canonicalSha256"])
    ):
        raise SelectionError("Invalid source catalog binding.")
    ladder = policy["fitLadder"]
    if (
        not isinstance(ladder, list)
        or len(ladder) != 6
        or len(set(ladder)) != len(ladder)
        or any(not isinstance(item, str) or not SAFE_ID.fullmatch(item) for item in ladder)
    ):
        raise SelectionError("Invalid fit ladder.")
    comparisons = policy["comparisonCandidates"]
    if not isinstance(comparisons, list) or len(comparisons) != 4:
        raise SelectionError("Invalid comparison candidate list.")
    seen: set[tuple[str, str]] = set()
    comparison_ids: set[str] = set()
    for item in comparisons:
        if (
            not isinstance(item, dict)
            or set(item) != {
                "id", "model", "digest", "purpose", "capabilities", "automaticPromotionAllowed"
            }
            or not isinstance(item["id"], str)
            or not SAFE_ID.fullmatch(item["id"])
            or not isinstance(item["model"], str)
            or not item["model"]
            or len(item["model"]) > 120
            or not HEX64.fullmatch(str(item["digest"]))
            or not isinstance(item["purpose"], str)
            or not 1 <= len(item["purpose"]) <= 120
            or item["capabilities"] != policy["capabilities"]
            or item["automaticPromotionAllowed"] is not False
            or item["id"] in comparison_ids
            or (item["model"], item["digest"]) in seen
        ):
            raise SelectionError("Invalid comparison candidate.")
        comparison_ids.add(item["id"])
        seen.add((item["model"], item["digest"]))
    requirements = policy["promotionRequirements"]
    if (
        not isinstance(requirements, list)
        or len(requirements) != 10
        or len(set(requirements)) != len(requirements)
        or "owner-approval" not in requirements
        or any(not isinstance(item, str) or not SAFE_ID.fullmatch(item) for item in requirements)
    ):
        raise SelectionError("Invalid promotion requirements.")


def validate_catalog_binding(policy: dict[str, Any], catalog: Any) -> None:
    if not isinstance(catalog, dict) or not isinstance(catalog.get("models"), list):
        raise SelectionError("Invalid source model catalog.")
    models = catalog["models"]
    ids = [item.get("id") for item in models if isinstance(item, dict)]
    if ids != policy["fitLadder"]:
        raise SelectionError("Fit ladder does not exactly match the source catalog.")
    priorities = [item.get("candidatePriority") for item in models]
    if any(isinstance(item, bool) or not isinstance(item, int) for item in priorities):
        raise SelectionError("Invalid source model priority.")
    if priorities != sorted(priorities) or len(set(priorities)) != len(priorities):
        raise SelectionError("Source model priorities are not strictly ordered.")


def validate_profile(profile: Any, model_ids: set[str]) -> dict[str, Any]:
    required = {
        "platformFamily", "operatingSystemId", "architecture", "backendMode", "systemMemoryGiB",
        "usableGpuMemoryGiB", "storageAdmittedModelIds", "requestedCapabilities",
        "provider", "providerVersion",
    }
    if not isinstance(profile, dict) or set(profile) != required:
        raise SelectionError("Invalid hardware profile shape.")
    if profile["platformFamily"] not in PLATFORMS:
        raise SelectionError("Unsupported platform family.")
    if (
        not isinstance(profile["operatingSystemId"], str)
        or not SAFE_ID.fullmatch(profile["operatingSystemId"])
    ):
        raise SelectionError("Invalid operating system id.")
    if profile["architecture"] not in ARCHITECTURES:
        raise SelectionError("Unsupported architecture.")
    if profile["backendMode"] not in BACKENDS:
        raise SelectionError("Unsupported backend mode.")
    for field in ("systemMemoryGiB", "usableGpuMemoryGiB"):
        value = profile[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1024:
            raise SelectionError(f"Invalid {field}.")
    storage = profile["storageAdmittedModelIds"]
    requested = profile["requestedCapabilities"]
    if (
        not isinstance(storage, list)
        or len(storage) != len(set(storage))
        or any(item not in model_ids for item in storage)
        or not isinstance(requested, list)
        or not requested
        or len(requested) != len(set(requested))
        or any(item not in CAPABILITIES for item in requested)
        or profile["provider"] != "ollama"
        or not isinstance(profile["providerVersion"], str)
        or not SAFE_VERSION.fullmatch(profile["providerVersion"])
    ):
        raise SelectionError("Invalid profile admission data.")
    if profile["backendMode"] == "cpu" and profile["usableGpuMemoryGiB"] != 0:
        raise SelectionError("CPU profile cannot claim usable GPU memory.")
    return profile


def validate_evidence(
    records: Any,
    model_by_id: dict[str, dict[str, Any]],
    selector_policy_sha256: str,
) -> list[dict[str, Any]]:
    required = {
        "evidenceId", "modelId", "manifestDigest", "platformFamily", "operatingSystemId",
        "architecture", "backendMode", "provider", "providerVersion",
        "minimumTestedSystemMemoryGiB", "minimumTestedUsableGpuMemoryGiB",
        "capabilities", "status", "selectorPolicyCanonicalSha256",
    }
    if not isinstance(records, list) or len(records) > 512:
        raise SelectionError("Invalid evidence list.")
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        model = model_by_id.get(record.get("modelId")) if isinstance(record, dict) else None
        if (
            not isinstance(record, dict)
            or set(record) != required
            or not isinstance(record["evidenceId"], str)
            or not SAFE_ID.fullmatch(record["evidenceId"])
            or record["evidenceId"] in seen
            or model is None
            or record["manifestDigest"] != model["manifestDigest"]
            or not isinstance(record["selectorPolicyCanonicalSha256"], str)
            or not HEX64.fullmatch(record["selectorPolicyCanonicalSha256"])
            or record["selectorPolicyCanonicalSha256"] != selector_policy_sha256
            or record["platformFamily"] not in PLATFORMS
            or not isinstance(record["operatingSystemId"], str)
            or not SAFE_ID.fullmatch(record["operatingSystemId"])
            or record["architecture"] not in ARCHITECTURES
            or record["backendMode"] not in BACKENDS
            or record["provider"] != "ollama"
            or not isinstance(record["providerVersion"], str)
            or not SAFE_VERSION.fullmatch(record["providerVersion"])
            or isinstance(record["minimumTestedSystemMemoryGiB"], bool)
            or not isinstance(record["minimumTestedSystemMemoryGiB"], (int, float))
            or not 0 < record["minimumTestedSystemMemoryGiB"] <= 1024
            or isinstance(record["minimumTestedUsableGpuMemoryGiB"], bool)
            or not isinstance(record["minimumTestedUsableGpuMemoryGiB"], (int, float))
            or not 0 <= record["minimumTestedUsableGpuMemoryGiB"] <= 1024
            or (
                record["backendMode"] == "cpu"
                and record["minimumTestedUsableGpuMemoryGiB"] != 0
            )
            or (
                record["backendMode"] != "cpu"
                and record["minimumTestedUsableGpuMemoryGiB"] <= 0
            )
            or not isinstance(record["capabilities"], list)
            or not record["capabilities"]
            or len(record["capabilities"]) != len(set(record["capabilities"]))
            or any(item not in CAPABILITIES for item in record["capabilities"])
            or record["status"] != "passed"
        ):
            raise SelectionError("Invalid exact-profile evidence record.")
        seen.add(record["evidenceId"])
        result.append(record)
    return result


def select_model(
    profile: dict[str, Any],
    evidence: list[dict[str, Any]],
    *,
    policy_path: Path = POLICY_PATH,
) -> dict[str, Any]:
    policy, catalog = load_policy(policy_path)
    selector_policy_sha256 = canonical_sha256(policy)
    models = catalog["models"]
    model_by_id = {item["id"]: item for item in models}
    validated_profile = validate_profile(profile, set(model_by_id))
    validated_evidence = validate_evidence(
        evidence, model_by_id, selector_policy_sha256
    )
    fit: list[dict[str, Any]] = []
    for model in models:
        if model["id"] not in validated_profile["storageAdmittedModelIds"]:
            continue
        if validated_profile["systemMemoryGiB"] < model["minimumSystemMemoryGiB"]:
            continue
        if validated_profile["usableGpuMemoryGiB"] < model["minimumUsableGpuMemoryGiB"]:
            continue
        fit.append(model)
    requested = set(validated_profile["requestedCapabilities"])
    admitted: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for model in fit:
        exact = next((
            record for record in validated_evidence
            if record["modelId"] == model["id"]
            and record["manifestDigest"] == model["manifestDigest"]
            and record["platformFamily"] == validated_profile["platformFamily"]
            and record["operatingSystemId"] == validated_profile["operatingSystemId"]
            and record["architecture"] == validated_profile["architecture"]
            and record["backendMode"] == validated_profile["backendMode"]
            and record["provider"] == validated_profile["provider"]
            and record["providerVersion"] == validated_profile["providerVersion"]
            and validated_profile["systemMemoryGiB"]
                >= record["minimumTestedSystemMemoryGiB"]
            and validated_profile["usableGpuMemoryGiB"]
                >= record["minimumTestedUsableGpuMemoryGiB"]
            and requested.issubset(set(record["capabilities"]))
        ), None)
        if exact is not None:
            admitted.append((model, exact))
    selected_pair = max(
        admitted,
        key=lambda pair: pair[0]["candidatePriority"],
        default=None,
    )
    selected = selected_pair[0] if selected_pair else None
    selected_evidence = selected_pair[1] if selected_pair else None
    return {
        "schemaVersion": 1,
        "kind": "alpha2-model-selection-decision",
        "decision": "automatic-selection" if selected else "no-validated-model",
        "selectedModelId": selected["id"] if selected else None,
        "selectedModel": selected["name"] if selected else None,
        "manifestDigest": selected["manifestDigest"] if selected else None,
        "evidenceId": selected_evidence["evidenceId"] if selected_evidence else None,
        "fitModelIds": [item["id"] for item in fit],
        "evidencePendingModelIds": [
            item["id"] for item in fit if item["id"] not in {pair[0]["id"] for pair in admitted}
        ],
        "automaticExecutionAllowed": selected is not None,
        "downloadsPerformed": False,
        "fallbackPerformed": False,
        "reason": (
            "The largest fitting model with exact execution-profile evidence was selected."
            if selected
            else "No fitting model has exact evidence for this platform, backend, provider version, and capability set."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        profile = _load_json(args.profile, "hardware profile")
        evidence = _load_json(args.evidence, "evidence")
        print(json.dumps(select_model(profile, evidence), indent=2, sort_keys=True))
    except SelectionError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
