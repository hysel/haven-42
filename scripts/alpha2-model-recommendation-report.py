#!/usr/bin/env python3
"""Explain Alpha 2 selector decisions without changing selection policy."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SELECTOR = _module("alpha2_selector_report", ROOT / "scripts/alpha2_model_selector.py")
RUNTIME = _module("alpha2_runtime_report", ROOT / "scripts/alpha2_runtime_compatibility.py")


def _evidence_match(record: dict[str, Any], model: dict[str, Any], profile: dict[str, Any]) -> bool:
    requested = set(profile["requestedCapabilities"])
    return (
        record["modelId"] == model["id"]
        and record["manifestDigest"] == model["manifestDigest"]
        and all(record[field] == profile[field] for field in (
            "platformFamily", "operatingSystemId", "architecture", "backendMode",
            "provider", "providerVersion",
        ))
        and profile["systemMemoryGiB"] >= record["minimumTestedSystemMemoryGiB"]
        and profile["usableGpuMemoryGiB"] >= record["minimumTestedUsableGpuMemoryGiB"]
        and requested.issubset(set(record["capabilities"]))
    )


def _evidence_reasons(records: list[dict[str, Any]], model: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    model_records = [record for record in records if record["modelId"] == model["id"]]
    if not model_records:
        return ["no-model-evidence"]
    fields = (
        "platformFamily", "operatingSystemId", "architecture", "backendMode",
        "provider", "providerVersion",
    )
    reasons: list[str] = []
    for field in fields:
        if not any(record[field] == profile[field] for record in model_records):
            reasons.append(f"no-evidence-for-{field}")
    if not any(profile["systemMemoryGiB"] >= record["minimumTestedSystemMemoryGiB"] for record in model_records):
        reasons.append("below-evidence-system-memory-floor")
    if not any(profile["usableGpuMemoryGiB"] >= record["minimumTestedUsableGpuMemoryGiB"] for record in model_records):
        reasons.append("below-evidence-gpu-memory-floor")
    requested = set(profile["requestedCapabilities"])
    if not any(requested.issubset(set(record["capabilities"])) for record in model_records):
        reasons.append("requested-capability-not-evidenced")
    return reasons or ["no-exact-profile-evidence"]


def explain(profile: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    policy, catalog = SELECTOR.load_policy()
    policy_digest = SELECTOR.canonical_sha256(policy)
    models = catalog["models"]
    model_by_id = {model["id"]: model for model in models}
    validated_profile = SELECTOR.validate_profile(profile, set(model_by_id))
    validated_evidence = SELECTOR.validate_evidence(evidence, model_by_id, policy_digest)
    decision = SELECTOR.select_model(validated_profile, validated_evidence)
    candidates = []
    for model in models:
        reasons: list[str] = []
        if model["id"] not in validated_profile["storageAdmittedModelIds"]:
            reasons.append("storage-not-admitted")
        if validated_profile["systemMemoryGiB"] < model["minimumSystemMemoryGiB"]:
            reasons.append("insufficient-system-memory")
        if validated_profile["usableGpuMemoryGiB"] < model["minimumUsableGpuMemoryGiB"]:
            reasons.append("insufficient-usable-gpu-memory")
        exact = next((record for record in validated_evidence if _evidence_match(record, model, validated_profile)), None)
        if not reasons and exact is None:
            reasons.extend(_evidence_reasons(validated_evidence, model, validated_profile))
        candidates.append({
            "modelId": model["id"],
            "candidatePriority": model["candidatePriority"],
            "status": "eligible" if not reasons else "rejected",
            "reasons": reasons,
            "evidenceId": exact["evidenceId"] if exact else None,
        })

    runtime = None
    if decision["selectedModelId"]:
        platform = f'{validated_profile["platformFamily"]}-{validated_profile["architecture"]}'
        backend = "rocm" if validated_profile["backendMode"] == "rocm" else "core"
        try:
            resolved = RUNTIME.resolve(decision["selectedModelId"], platform, backend)
            runtime = {
                "status": "admitted-route-found",
                "engine": resolved["engine"],
                "selectedRuntimeVersion": resolved["selectedRuntimeVersion"],
                "exactTag": resolved["modelArtifact"]["exactTag"],
            }
            if resolved["modelArtifact"]["exactTag"] != decision["selectedModel"]:
                runtime = {"status": "blocked", "reason": "selector-runtime-model-artifact-mismatch"}
        except RUNTIME.CompatibilityError as error:
            runtime = {"status": "blocked", "reason": str(error)}
    return {
        "schemaVersion": 1,
        "kind": "alpha2-model-recommendation-explanation",
        "selectorDecision": decision,
        "runtimeRoute": runtime,
        "candidates": candidates,
        "policyChanged": False,
        "downloadsPerformed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        profile = json.loads(args.profile.read_text(encoding="utf-8"))
        payload = json.loads(args.evidence.read_text(encoding="utf-8"))
        evidence = payload["records"] if isinstance(payload, dict) else payload
        result = explain(profile, evidence)
    except (OSError, json.JSONDecodeError, KeyError, SELECTOR.SelectionError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
