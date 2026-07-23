#!/usr/bin/env python3
"""Build a read-only, license-aware and hardware-aware model catalog."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
ARTIFACT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:+\-]{0,255}$")
REVISION_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
VALIDATED_STATUSES = {
    "approved-write-ready",
    "review-validated",
    "plan-validated",
    "write-smoke-validated",
    "read-only-tool-validated",
    "read-only-cli-validated",
    "validated-by-tests",
}
STRONG_STATUSES = {"approved-write-ready", "review-validated", "plan-validated"}


class CatalogError(ValueError):
    pass


def read_json(path: Path, max_bytes: int):
    if not path.is_file():
        raise CatalogError(f"Input file does not exist: {path.name}")
    if path.stat().st_size > max_bytes:
        raise CatalogError(f"Input exceeds the {max_bytes}-byte limit: {path.name}")
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"Invalid JSON in {path.name}: {exc.msg}") from exc


def clean_string(value, field: str, limit: int, required: bool = False):
    if value is None:
        if required:
            raise CatalogError(f"{field} is required.")
        return None
    if not isinstance(value, str):
        raise CatalogError(f"{field} must be a string.")
    value = value.strip()
    if required and not value:
        raise CatalogError(f"{field} must not be empty.")
    if len(value) > limit or CONTROL_RE.search(value):
        raise CatalogError(f"{field} contains unsafe or oversized text.")
    return value or None


def clean_list(value, field: str, max_items: int, max_string: int):
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > max_items:
        raise CatalogError(f"{field} must be a bounded list.")
    cleaned = []
    for item in value:
        text = clean_string(item, field, max_string, required=True)
        if text not in cleaned:
            cleaned.append(text)
    return sorted(cleaned, key=str.lower)


def normalize_license(value):
    if not value:
        return None
    aliases = {
        "apache 2.0": "Apache-2.0",
        "apache-2.0": "Apache-2.0",
        "mit": "MIT",
        "bsd-2-clause": "BSD-2-Clause",
        "bsd-3-clause": "BSD-3-Clause",
        "isc": "ISC",
        "0bsd": "0BSD",
    }
    return aliases.get(value.lower(), value)


def license_decision(reported, contract):
    normalized = normalize_license(reported)
    if not normalized:
        return {
            "reported": None,
            "normalized": None,
            "decision": "blocked",
            "reason": "No model license was reported; automatic promotion and installation are denied.",
        }
    lowered = normalized.lower()
    if any(signal.lower() in lowered for signal in contract["blockedLicenseSignals"]):
        return {
            "reported": reported,
            "normalized": normalized,
            "decision": "blocked",
            "reason": "The reported license contains a noncommercial or proprietary-use signal.",
        }
    if normalized in contract["permissiveLicenseIds"]:
        return {
            "reported": reported,
            "normalized": normalized,
            "decision": "permissive-recorded",
            "reason": "A catalog-approved permissive SPDX identifier was reported; exact artifact review is still required.",
        }
    return {
        "reported": reported,
        "normalized": normalized,
        "decision": "review-required",
        "reason": "A custom or unrecognized license requires explicit review and cannot be promoted automatically.",
    }


def load_evidence(path: Path, max_bytes: int, max_string: int):
    if not path.is_file():
        raise CatalogError(f"Evidence catalog does not exist: {path.name}")
    if path.stat().st_size > max_bytes:
        raise CatalogError("Evidence catalog exceeds the input limit.")
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"model", "status", "operation", "surface", "provider", "os", "evidence"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise CatalogError("Evidence catalog is missing required columns.")
        for index, row in enumerate(reader, start=2):
            cleaned = {}
            for key, value in row.items():
                cleaned[key] = clean_string(value, f"evidence row {index} {key}", max_string) or ""
            rows.append(cleaned)
    return rows


def evidence_for(candidate, rows):
    identities = {
        candidate["Model"].lower(),
        candidate["ArtifactId"].lower(),
    }
    matching = [row for row in rows if row.get("model", "").lower() in identities]
    revision_bound = bool(candidate["Revision"]) and any(
        row.get("artifact_revision", "").lower() == candidate["Revision"].lower()
        for row in matching
    )
    statuses = sorted({row["status"] for row in matching})
    operations = sorted({row["operation"] for row in matching})
    if not matching:
        state = "recommended-only"
    elif not revision_bound or any(status not in VALIDATED_STATUSES for status in statuses):
        state = "tested-partial"
    elif any(status in STRONG_STATUSES for status in statuses):
        state = "tested-passed"
    else:
        state = "tested-partial"
    return {
        "state": state,
        "statuses": statuses,
        "operations": operations,
        "exactArtifactRevisionBound": revision_bound,
        "records": [
            {
                "surface": row["surface"],
                "provider": row["provider"],
                "os": row["os"],
                "operation": row["operation"],
                "status": row["status"],
                "evidence": row["evidence"],
            }
            for row in matching
        ],
    }


def hardware_fit(record):
    if not isinstance(record, dict):
        return {
            "label": "unknown",
            "availableVramGb": None,
            "recommendedMinVramGb": None,
            "confidence": "unknown",
            "reason": "No bounded hardware-fit estimate was supplied.",
        }
    available = record.get("AvailableVramGb")
    required = record.get("RecommendedMinVramGb")
    fits = record.get("FitsAvailableVram")
    if not isinstance(available, (int, float)) or available <= 0:
        label = "unknown"
        reason = "No available VRAM value was supplied, so fit remains unknown."
    elif fits is False:
        label = "slow-or-oversized"
        reason = "The candidate exceeds the supplied VRAM estimate."
    elif isinstance(available, (int, float)) and isinstance(required, (int, float)) and available >= required * 1.25:
        label = "excellent"
        reason = "The supplied VRAM estimate includes at least 25% headroom."
    elif fits is True and required:
        label = "usable"
        reason = "The candidate fits the supplied low-confidence VRAM estimate."
    else:
        label = "unknown"
        reason = "Hardware fit cannot be established from the supplied metadata."
    return {
        "label": label,
        "availableVramGb": available if isinstance(available, (int, float)) else None,
        "recommendedMinVramGb": required if isinstance(required, (int, float)) else None,
        "confidence": str(record.get("Confidence") or "unknown")[:128],
        "reason": reason,
    }


def validate_candidate(raw, contract):
    if not isinstance(raw, dict):
        raise CatalogError("Every discovery candidate must be an object.")
    limits = contract["limits"]
    missing = [field for field in contract["requiredCandidateFields"] if field not in raw]
    if missing:
        raise CatalogError(f"Candidate is missing required fields: {', '.join(missing)}")
    model = clean_string(raw.get("Model"), "Model", limits["maxStringLength"], required=True)
    artifact = clean_string(raw.get("ArtifactId"), "ArtifactId", limits["maxStringLength"], required=True)
    source_id = clean_string(raw.get("SourceId"), "SourceId", limits["maxStringLength"], required=True)
    source_type = clean_string(raw.get("SourceType"), "SourceType", limits["maxStringLength"], required=True)
    if not ARTIFACT_RE.fullmatch(model) or ".." in model or "\\" in model:
        raise CatalogError("Model contains an unsafe identifier.")
    if not ARTIFACT_RE.fullmatch(artifact) or ".." in artifact or "\\" in artifact:
        raise CatalogError("ArtifactId contains an unsafe identifier.")
    gated = raw.get("Gated", False)
    if not (type(gated) is bool or gated is None or (isinstance(gated, str) and gated in ("", "false", "manual", "auto"))):
        raise CatalogError("Gated contains an unsupported value.")
    revision = clean_string(raw.get("Revision"), "Revision", limits["maxStringLength"])
    license_name = clean_string(raw.get("License"), "License", limits["maxStringLength"])
    formats = clean_list(raw.get("Formats"), "Formats", limits["maxListItems"], limits["maxStringLength"])
    runtimes = clean_list(raw.get("RuntimeCandidates"), "RuntimeCandidates", limits["maxListItems"], limits["maxStringLength"])
    quantizations = clean_list(raw.get("QuantizationSignals"), "QuantizationSignals", limits["maxListItems"], limits["maxStringLength"])
    return {
        "Model": model,
        "ArtifactId": artifact,
        "Family": clean_string(raw.get("Family"), "Family", limits["maxStringLength"]),
        "SourceId": source_id,
        "SourceType": source_type,
        "Publisher": clean_string(raw.get("Publisher"), "Publisher", limits["maxStringLength"]),
        "Revision": revision,
        "License": license_name,
        "Gated": gated,
        "PipelineTag": clean_string(raw.get("PipelineTag"), "PipelineTag", limits["maxStringLength"]),
        "Formats": formats,
        "RuntimeCandidates": runtimes,
        "QuantizationSignals": quantizations,
        "ProvenanceStatus": clean_string(raw.get("ProvenanceStatus"), "ProvenanceStatus", limits["maxStringLength"], required=True),
        "ValidationStatus": clean_string(raw.get("ValidationStatus"), "ValidationStatus", limits["maxStringLength"], required=True),
        "VramRecommendation": raw.get("VramRecommendation"),
    }


def catalog_entry(candidate, contract, evidence_rows):
    license_info = license_decision(candidate["License"], contract)
    fit = hardware_fit(candidate["VramRecommendation"])
    evidence = evidence_for(candidate, evidence_rows)
    safe_formats = sorted(set(candidate["Formats"]).intersection(contract["safeArtifactFormats"]))
    blockers = []
    if license_info["decision"] != "permissive-recorded":
        blockers.append("license-not-automatically-admissible")
    if not candidate["Revision"] or not REVISION_RE.fullmatch(candidate["Revision"]):
        blockers.append("immutable-revision-missing")
    if candidate["ProvenanceStatus"] != "immutable-revision-recorded":
        blockers.append("immutable-provenance-unverified")
    if candidate["Gated"] not in (False, None, "", "false"):
        blockers.append("artifact-access-gated")
    if not safe_formats:
        blockers.append("safe-format-not-recorded")
    if fit["label"] == "slow-or-oversized":
        blockers.append("hardware-fit-failed")
    if evidence["state"] != "tested-passed":
        blockers.append("exact-validation-incomplete")
    if evidence["records"] and not evidence["exactArtifactRevisionBound"]:
        blockers.append("evidence-revision-unbound")
    promotion = not blockers
    state = evidence["state"]
    if any(item in blockers for item in (
        "license-not-automatically-admissible",
        "immutable-revision-missing",
        "immutable-provenance-unverified",
        "artifact-access-gated",
        "safe-format-not-recorded",
        "hardware-fit-failed",
    )):
        state = "blocked"
    identity = f"{candidate['SourceId']}\0{candidate['ArtifactId']}\0{candidate['Revision'] or ''}"
    catalog_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    beginner_reason = (
        "Exact artifact, permissive license, hardware fit, safe format, and validation evidence satisfy the catalog gate."
        if promotion else
        "Not recommended automatically: " + ", ".join(blockers) + "."
    )
    return {
        "catalogId": catalog_id,
        "displayName": candidate["Model"],
        "family": candidate["Family"],
        "artifact": {
            "id": candidate["ArtifactId"],
            "sourceId": candidate["SourceId"],
            "sourceType": candidate["SourceType"],
            "publisher": candidate["Publisher"],
            "revision": candidate["Revision"],
            "gated": candidate["Gated"],
            "formats": candidate["Formats"],
            "safeFormats": safe_formats,
            "quantizationSignals": candidate["QuantizationSignals"],
        },
        "license": license_info,
        "hardwareFit": fit,
        "readiness": evidence,
        "security": {
            "remoteCodeAllowed": False,
            "automaticDownloadAllowed": False,
            "automaticPromotionEligible": promotion,
            "blockers": blockers,
        },
        "beginner": {
            "recommendedForThisComputer": promotion,
            "reason": beginner_reason,
        },
        "advanced": {
            "runtimeCandidates": candidate["RuntimeCandidates"],
            "pipelineTag": candidate["PipelineTag"],
            "reportedProvenanceStatus": candidate["ProvenanceStatus"],
            "reportedDiscoveryValidationStatus": candidate["ValidationStatus"],
            "licenseReviewRequired": license_info["decision"] == "review-required",
            "manualArtifactSelectionRequired": True,
        },
        "state": state,
    }


def write_exclusive(path: Path, payload: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-path", required=True)
    parser.add_argument("--discovery-report", required=True)
    parser.add_argument("--evidence-catalog", required=True)
    parser.add_argument("--output-path", required=True)
    args = parser.parse_args()
    try:
        contract_path = Path(args.contract_path)
        contract = read_json(contract_path, 1024 * 1024)
        if contract.get("schemaVersion") != 1:
            raise CatalogError("Unsupported model catalog contract version.")
        limits = contract["limits"]
        discovery = read_json(Path(args.discovery_report), limits["maxInputBytes"])
        candidates = discovery.get("Candidates")
        if not isinstance(candidates, list) or len(candidates) > limits["maxCandidates"]:
            raise CatalogError("Discovery report contains an invalid or oversized candidate list.")
        evidence_rows = load_evidence(Path(args.evidence_catalog), limits["maxInputBytes"], limits["maxStringLength"])
        entries = [
            catalog_entry(validate_candidate(candidate, contract), contract, evidence_rows)
            for candidate in candidates
        ]
        entries.sort(key=lambda item: (not item["beginner"]["recommendedForThisComputer"], item["displayName"].lower()))
        report = {
            "schemaVersion": contract["schemaVersion"],
            "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
            "mode": "read-only-catalog-assembly",
            "sourceDiscoverySchemaVersion": discovery.get("SchemaVersion"),
            "modelHostPlatform": clean_string(
                discovery.get("ModelHostPlatform"), "ModelHostPlatform", limits["maxStringLength"]
            ),
            "summary": {
                "entryCount": len(entries),
                "beginnerRecommendedCount": sum(item["beginner"]["recommendedForThisComputer"] for item in entries),
                "blockedCount": sum(item["state"] == "blocked" for item in entries),
                "licenseReviewCount": sum(item["license"]["decision"] == "review-required" for item in entries),
            },
            "effects": {
                "pullsModels": False,
                "writesRuntimeConfig": False,
                "executesRemoteCode": False,
                "sendsHardwareProfile": False,
            },
            "entries": entries,
        }
        write_exclusive(Path(args.output_path), json.dumps(report, indent=2) + "\n")
        print(
            f"Catalog summary: {len(entries)} entry(s), "
            f"{report['summary']['beginnerRecommendedCount']} beginner recommendation(s), "
            f"{report['summary']['blockedCount']} blocked."
        )
        print(f"Catalog written exclusively to {args.output_path}")
        return 0
    except (CatalogError, OSError, KeyError, TypeError) as exc:
        print(f"MODEL_CATALOG_REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
