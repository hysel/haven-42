#!/usr/bin/env python3
"""Evaluate one exact model against a reviewed hardware-fit plan without downloading it."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = ROOT / "config/alpha-2-rx5700xt-certification-plan.json"
INVENTORY = ROOT / "config/alpha-2-model-version-inventory.json"
CATALOG = ROOT / "config/alpha-2-model-catalog.json"
MAX_BYTES = 2 * 1024 * 1024
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9.-]{0,95}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class AdmissionError(ValueError):
    """The plan or candidate could not be evaluated safely."""


def _load(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise AdmissionError("unsafe-admission-input")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AdmissionError("invalid-admission-input") from error
    if not isinstance(value, dict):
        raise AdmissionError("invalid-admission-input")
    return value


def _canonical_sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()


def _candidate_records(inventory: dict[str, Any], catalog: dict[str, Any]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for family in inventory.get("families", []):
        if not isinstance(family, dict):
            raise AdmissionError("invalid-model-source")
        for version in family.get("versions", []):
            if not isinstance(version, dict):
                raise AdmissionError("invalid-model-source")
            for candidate in version.get("candidates", []):
                if isinstance(candidate, dict):
                    values.append(candidate)
    for candidate in catalog.get("models", []):
        if isinstance(candidate, dict):
            values.append(candidate)
    return values


def evaluate(model_id: str, plan_path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    if not SAFE_ID.fullmatch(model_id):
        raise AdmissionError("invalid-model-id")
    plan = _load(plan_path)
    inventory = _load(INVENTORY)
    catalog = _load(CATALOG)
    if plan.get("planId") != "haven42.alpha2.amd-radeon-rx5700xt-8g":
        raise AdmissionError("unreviewed-hardware-plan")
    ladder = plan.get("modelLadder")
    hardware = plan.get("hardwareClass")
    execution = plan.get("execution")
    if not all(isinstance(value, dict) for value in (ladder, hardware, execution)):
        raise AdmissionError("invalid-hardware-plan")
    tiers = {
        "expected-fit": ladder.get("expectedFit"),
        "measured-boundary": ladder.get("measuredBoundaryOnly"),
        "oversized-refusal": ladder.get("oversizedRefusal"),
    }
    if any(
        not isinstance(values, list)
        or any(not isinstance(value, str) for value in values)
        for values in tiers.values()
    ):
        raise AdmissionError("invalid-hardware-plan")
    matching_tiers = [tier for tier, values in tiers.items() if model_id in values]
    if len(matching_tiers) != 1:
        raise AdmissionError("unreviewed-hardware-cell")
    candidates = [
        value for value in _candidate_records(inventory, catalog)
        if value.get("id") == model_id
    ]
    if len(candidates) != 1:
        raise AdmissionError("ambiguous-or-missing-model")
    candidate = candidates[0]
    digest = candidate.get("manifestDigest")
    model_bytes = candidate.get("modelBytes")
    if (
        not isinstance(digest, str)
        or not SHA256.fullmatch(digest)
        or isinstance(model_bytes, bool)
        or not isinstance(model_bytes, int)
        or model_bytes <= 0
    ):
        raise AdmissionError("invalid-model-artifact")
    memory_gib = hardware.get("memoryGiB")
    fixed_headroom_gib = execution.get("requiredHeadroomGiB")
    percent_headroom = execution.get("requiredHeadroomPercent")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value <= 0
        for value in (memory_gib, fixed_headroom_gib, percent_headroom)
    ):
        raise AdmissionError("invalid-hardware-plan")
    physical_bytes = int(float(memory_gib) * 1024**3)
    required_headroom = max(
        int(float(fixed_headroom_gib) * 1024**3),
        math.ceil(physical_bytes * float(percent_headroom) / 100),
    )
    maximum_model_bytes = physical_bytes - required_headroom
    exceeds = model_bytes > maximum_model_bytes
    tier = matching_tiers[0]
    if tier == "oversized-refusal" and not exceeds:
        raise AdmissionError("policy-artifact-disagreement")
    decision = (
        "refused-before-download"
        if exceeds
        else "requires-runtime-headroom-measurement"
    )
    return {
        "schemaVersion": 1,
        "kind": "alpha2-hardware-model-admission-evidence",
        "hardwarePlanId": plan["planId"],
        "modelId": model_id,
        "tier": tier,
        "manifestDigest": digest,
        "modelBytes": model_bytes,
        "physicalGpuMemoryBytes": physical_bytes,
        "requiredHeadroomBytes": required_headroom,
        "maximumModelBytesBeforeRuntimeOverhead": maximum_model_bytes,
        "decision": decision,
        "outcome": "passed" if tier == "oversized-refusal" and exceeds else "inconclusive",
        "reason": (
            "exact-model-layer-alone-exceeds-reviewed-headroom-envelope"
            if exceeds
            else "artifact-size-alone-cannot-prove-runtime-fit"
        ),
        "planCanonicalSha256": _canonical_sha256(plan),
        "inventoryCanonicalSha256": _canonical_sha256(inventory),
        "catalogCanonicalSha256": _canonical_sha256(catalog),
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "downloadPerformed": False,
        "executionPerformed": False,
        "automaticPromotionAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    args = parser.parse_args()
    try:
        result = evaluate(args.model_id, args.plan)
    except AdmissionError as error:
        print(json.dumps({
            "schemaVersion": 1,
            "kind": "alpha2-hardware-model-admission-evidence",
            "modelId": args.model_id,
            "outcome": "failed",
            "errorCode": str(error),
            "containsRawPromptsOrResponses": False,
            "containsPrivateMachineIdentity": False,
            "downloadPerformed": False,
            "executionPerformed": False,
            "automaticPromotionAllowed": False,
        }, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
