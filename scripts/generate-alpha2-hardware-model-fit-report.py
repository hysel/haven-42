#!/usr/bin/env python3
"""Compare completed model evidence per hardware without changing selection."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any


MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_FILES_PER_PROFILE = 500
SAFE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,99}")
SAFE_DIGEST = re.compile(r"[0-9a-f]{64}")
SAFE_TEXT = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._()+:/,!-]{0,199}")
TASKS = ("general.chat", "content.write", "content.summarize")
SCOPES = {"shared-baseline", "hardware-fit-expansion", "os-anchor"}
KNOWN_KINDS = {
    "alpha2-lab-model-soak-evidence",
    "haven42-amd-common-baseline-soak",
    "haven42-intel-common-baseline-soak",
}


class ComparisonError(ValueError):
    """The comparison request or evidence was unsafe, ambiguous, or invalid."""


def load_object(path: Path, code: str) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_JSON_BYTES:
            raise ComparisonError(code)
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ComparisonError(code) from error
    if not isinstance(value, dict):
        raise ComparisonError(code)
    return value


def safe_text(value: Any) -> str:
    if not isinstance(value, str) or not SAFE_TEXT.fullmatch(value):
        raise ComparisonError("unsafe-comparison-text")
    return value


def safe_relative(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value or len(value) > 300:
        raise ComparisonError("unsafe-comparison-path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ComparisonError("unsafe-comparison-path")
    return value


def finite_number(value: Any, *, minimum: float = 0, maximum: float = 1_000_000_000_000) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ComparisonError("invalid-comparison-number")
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ComparisonError("invalid-comparison-number")
    return number


def resolve_under(root: Path, value: Any, *, directory: bool) -> Path:
    relative = safe_relative(value)
    unresolved = root / relative
    if unresolved.is_symlink():
        raise ComparisonError("unsafe-comparison-path")
    candidate = unresolved.resolve()
    resolved_root = root.resolve()
    if resolved_root != candidate and resolved_root not in candidate.parents:
        raise ComparisonError("unsafe-comparison-path")
    if (directory and not candidate.is_dir()) or (not directory and not candidate.is_file()):
        raise ComparisonError("missing-comparison-source")
    return candidate


def normalize_request(path: Path, evidence_root: Path) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    value = load_object(path, "invalid-comparison-request")
    if set(value) != {"schemaVersion", "kind", "hardwareProfiles", "qualityReviews"} or value.get("schemaVersion") != 1 or value.get("kind") != "haven42-alpha2-hardware-model-comparison-request":
        raise ComparisonError("invalid-comparison-request")
    profiles = value["hardwareProfiles"]
    reviews = value["qualityReviews"]
    if not isinstance(profiles, list) or not profiles or not isinstance(reviews, list):
        raise ComparisonError("invalid-comparison-request")
    normalized_profiles: list[dict[str, Any]] = []
    seen_profiles: set[str] = set()
    profile_fields = {"id", "label", "vendor", "operatingSystem", "runtime", "usableAcceleratorMemoryBytes", "campaignScope", "evidenceDirectories"}
    for profile in profiles:
        if not isinstance(profile, dict) or set(profile) != profile_fields:
            raise ComparisonError("invalid-hardware-profile")
        profile_id = profile["id"]
        if not isinstance(profile_id, str) or not SAFE_ID.fullmatch(profile_id) or profile_id in seen_profiles:
            raise ComparisonError("invalid-hardware-profile")
        seen_profiles.add(profile_id)
        scope = profile["campaignScope"]
        directories = profile["evidenceDirectories"]
        memory = int(finite_number(profile["usableAcceleratorMemoryBytes"], minimum=1))
        if scope not in SCOPES or not isinstance(directories, list) or not directories:
            raise ComparisonError("invalid-hardware-profile")
        normalized_profiles.append({
            "id": profile_id,
            "label": safe_text(profile["label"]),
            "vendor": safe_text(profile["vendor"]),
            "operatingSystem": safe_text(profile["operatingSystem"]),
            "runtime": safe_text(profile["runtime"]),
            "usableAcceleratorMemoryBytes": memory,
            "campaignScope": scope,
            "evidenceDirectories": [resolve_under(evidence_root, item, directory=True) for item in directories],
        })
    normalized_reviews: dict[tuple[str, str], dict[str, Any]] = {}
    review_fields = {"hardwareId", "modelId", "scores", "evidenceReference"}
    for review in reviews:
        if not isinstance(review, dict) or set(review) != review_fields:
            raise ComparisonError("invalid-quality-review")
        hardware_id, model_id = review["hardwareId"], review["modelId"]
        if hardware_id not in seen_profiles or not isinstance(model_id, str) or not SAFE_ID.fullmatch(model_id):
            raise ComparisonError("invalid-quality-review")
        scores = review["scores"]
        if not isinstance(scores, dict) or set(scores) != set(TASKS):
            raise ComparisonError("invalid-quality-review")
        normalized_scores = {task: round(finite_number(scores[task], maximum=100), 3) for task in TASKS}
        reference = safe_relative(review["evidenceReference"])
        resolve_under(evidence_root, reference, directory=False)
        key = (hardware_id, model_id)
        if key in normalized_reviews:
            raise ComparisonError("duplicate-quality-review")
        normalized_reviews[key] = {"scores": normalized_scores, "evidenceReference": reference}
    return normalized_profiles, normalized_reviews


def evidence_files(directories: list[Path]) -> list[Path]:
    files: dict[Path, None] = {}
    for directory in directories:
        for path in directory.rglob("*.json"):
            if path.name == "status.json" or path.is_symlink() or not path.is_file():
                continue
            files[path.resolve()] = None
            if len(files) > MAX_FILES_PER_PROFILE:
                raise ComparisonError("too-many-comparison-files")
    return sorted(files)


def task_coverage(value: dict[str, Any]) -> dict[str, bool]:
    counts = value.get("capabilityCounts")
    if isinstance(counts, dict):
        return {task: isinstance(counts.get(task), int) and not isinstance(counts.get(task), bool) and counts[task] > 0 for task in TASKS}
    metrics = value.get("metrics")
    if value.get("kind") == "alpha2-lab-model-soak-evidence" and isinstance(metrics, dict):
        cycles = metrics.get("cyclesPassed")
        samples = metrics.get("samplesPassed")
        complete = isinstance(cycles, int) and cycles > 0 and isinstance(samples, int) and samples >= cycles * len(TASKS) * 3
        return {task: complete for task in TASKS}
    return {task: False for task in TASKS}


def parse_result(path: Path, profile: dict[str, Any]) -> dict[str, Any] | None:
    value = load_object(path, "invalid-comparison-evidence")
    if value.get("kind") not in KNOWN_KINDS:
        return None
    if value.get("containsRawPromptsOrResponses") is not False or value.get("containsPrivateMachineIdentity") is not False or value.get("automaticPromotionAllowed") is not False:
        raise ComparisonError("unsafe-comparison-evidence")
    model_id, model, digest = value.get("modelId"), value.get("model"), value.get("manifestDigest")
    if not isinstance(model_id, str) or not SAFE_ID.fullmatch(model_id) or not isinstance(digest, str) or not SAFE_DIGEST.fullmatch(digest):
        raise ComparisonError("invalid-comparison-evidence")
    outcome = value.get("outcome")
    if outcome not in {"passed", "failed"}:
        raise ComparisonError("invalid-comparison-evidence")
    model = safe_text(model if model is not None else model_id)
    if outcome == "failed":
        failure_code = safe_text(value.get("failureCode", "unspecified-evidence-failure"))
        return {
            "modelId": model_id,
            "model": model,
            "manifestDigest": digest,
            "outcome": outcome,
            "failureCode": failure_code,
            "taskCoverage": {task: False for task in TASKS},
            "averageTokensPerSecond": None,
            "peakAcceleratorMemoryBytes": None,
            "memoryHeadroomBytes": None,
            "memoryHeadroomPercent": None,
            "fitStatus": "not-assessed",
            "backend": "not-observed",
            "fullAcceleratorOffload": None,
            "averagePowerWatts": None,
            "eligibilityBlockers": [
                "soak-not-passed",
                "task-coverage-incomplete",
                "full-offload-proof-missing",
                "fit-not-assessed",
            ],
            "eligibleForRecommendationReview": False,
        }
    metrics = value.get("metrics")
    if not isinstance(metrics, dict):
        raise ComparisonError("invalid-comparison-evidence")
    rate = round(finite_number(metrics.get("averageTokensPerSecond"), minimum=0.001), 3)
    peak = metrics.get("peakGpuMemoryBytes", metrics.get("peakGpuResidentBytes"))
    peak_bytes = int(finite_number(peak, minimum=1))
    residency = value.get("residency")
    full_offload: bool | None = None
    backend = "accelerator-observed"
    if isinstance(residency, dict):
        full_value = residency.get("fullGpuOffload")
        if not isinstance(full_value, bool):
            raise ComparisonError("invalid-comparison-evidence")
        full_offload = full_value
        backend = safe_text(residency.get("backend"))
    coverage = task_coverage(value)
    usable = profile["usableAcceleratorMemoryBytes"]
    headroom = usable - peak_bytes
    headroom_ratio = headroom / usable
    if headroom < 0:
        fit = "does-not-fit"
    elif headroom_ratio >= 0.25:
        fit = "comfortable"
    elif headroom_ratio >= 0.10:
        fit = "workable"
    else:
        fit = "borderline"
    blockers: list[str] = []
    if value.get("outcome") != "passed":
        blockers.append("soak-not-passed")
    if not all(coverage.values()):
        blockers.append("task-coverage-incomplete")
    if full_offload is not True:
        blockers.append("full-offload-proof-missing" if full_offload is None else "partial-offload-observed")
    if fit not in {"comfortable", "workable"}:
        blockers.append("insufficient-recovery-headroom")
    power = value.get("powerEvidence")
    average_power = None
    if isinstance(power, dict) and power.get("collected") is True:
        average_power = round(finite_number(power.get("averagePowerWatts"), minimum=0.001), 3)
    return {
        "modelId": model_id,
        "model": model,
        "manifestDigest": digest,
        "outcome": outcome,
        "failureCode": None,
        "taskCoverage": coverage,
        "averageTokensPerSecond": rate,
        "peakAcceleratorMemoryBytes": peak_bytes,
        "memoryHeadroomBytes": headroom,
        "memoryHeadroomPercent": round(headroom_ratio * 100, 2),
        "fitStatus": fit,
        "backend": backend,
        "fullAcceleratorOffload": full_offload,
        "averagePowerWatts": average_power,
        "eligibilityBlockers": blockers,
        "eligibleForRecommendationReview": not blockers,
    }


def fallback_candidate(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    eligible = [item for item in results if item["eligibleForRecommendationReview"]]
    if not eligible:
        return None
    selected = min(eligible, key=lambda item: (item["peakAcceleratorMemoryBytes"], -item["averageTokensPerSecond"], item["modelId"]))
    return {"modelId": selected["modelId"], "model": selected["model"], "basis": "smallest-measured-accelerator-footprint-among-eligible-results"}


def task_proposals(profile_id: str, results: list[dict[str, Any]], reviews: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    proposals: dict[str, Any] = {}
    eligible = [item for item in results if item["eligibleForRecommendationReview"]]
    for task in TASKS:
        reviewed = []
        for result in eligible:
            review = reviews.get((profile_id, result["modelId"]))
            if review is None:
                continue
            reviewed.append({
                "modelId": result["modelId"], "model": result["model"],
                "qualityScore": review["scores"][task],
                "averageTokensPerSecond": result["averageTokensPerSecond"],
                "memoryHeadroomPercent": result["memoryHeadroomPercent"],
                "evidenceReference": review["evidenceReference"],
            })
        reviewed.sort(key=lambda item: (-item["qualityScore"], -item["averageTokensPerSecond"], -item["memoryHeadroomPercent"], item["modelId"]))
        if len(reviewed) < 2:
            proposals[task] = {"status": "quality-review-required", "proposedModelId": None, "reviewedCandidates": reviewed}
        else:
            proposals[task] = {"status": "owner-review-required", "proposedModelId": reviewed[0]["modelId"], "reviewedCandidates": reviewed}
    return proposals


def build_report(request_path: Path, evidence_root: Path) -> dict[str, Any]:
    profiles, reviews = normalize_request(request_path, evidence_root)
    hardware: list[dict[str, Any]] = []
    model_hardware: dict[str, list[dict[str, Any]]] = {}
    for profile in profiles:
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for path in evidence_files(profile["evidenceDirectories"]):
            result = parse_result(path, profile)
            if result is None:
                continue
            if result["modelId"] in seen:
                raise ComparisonError("duplicate-model-hardware-evidence")
            seen.add(result["modelId"])
            results.append(result)
        results.sort(key=lambda item: (item["peakAcceleratorMemoryBytes"] is None, item["peakAcceleratorMemoryBytes"] or 0, item["modelId"]))
        for result in results:
            model_hardware.setdefault(result["modelId"], []).append({
                "hardwareId": profile["id"], "hardwareLabel": profile["label"],
                "outcome": result["outcome"], "fitStatus": result["fitStatus"],
                "fullAcceleratorOffload": result["fullAcceleratorOffload"],
                "averageTokensPerSecond": result["averageTokensPerSecond"],
            })
        hardware.append({
            **{key: profile[key] for key in ("id", "label", "vendor", "operatingSystem", "runtime", "usableAcceleratorMemoryBytes", "campaignScope")},
            "completedEvidenceCount": len(results),
            "eligibleCandidateCount": sum(item["eligibleForRecommendationReview"] for item in results),
            "results": results,
            "taskRecommendationProposals": task_proposals(profile["id"], results, reviews),
            "fallbackCandidate": fallback_candidate(results),
        })
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-hardware-model-fit-report",
        "generatedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "hardware": hardware,
        "crossHardwareModels": [
            {"modelId": model_id, "hardwareResults": sorted(items, key=lambda item: item["hardwareId"])}
            for model_id, items in sorted(model_hardware.items()) if len(items) > 1
        ],
        "disclosures": {
            "automaticSelectionChanged": False,
            "automaticPromotionAllowed": False,
            "ownerReviewRequired": True,
            "modelCountUsedAsQualityScore": False,
            "unreviewedThroughputUsedAsQualityScore": False,
            "privateMachineIdentityRetained": False,
            "evidencePathsRetained": False,
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha 2 hardware and model fit report", "",
        "This is a recommendation proposal, not a product-default change. Different",
        "hardware may test different model sets. Counts show coverage, not quality.", "",
        f"Generated: `{report['generatedAtUtc']}`", "",
    ]
    for hardware in report["hardware"]:
        gib = hardware["usableAcceleratorMemoryBytes"] / 1024**3
        lines.extend([
            f"## {hardware['label']}", "",
            f"{hardware['operatingSystem']} · {hardware['runtime']} · {gib:.0f} GiB usable accelerator memory · {hardware['campaignScope']}", "",
            f"Completed evidence: **{hardware['completedEvidenceCount']}** · Eligible for recommendation review: **{hardware['eligibleCandidateCount']}**", "",
            "| Model | Tasks | Fit | Offload | Speed | Headroom | Review status |", "|---|---|---|---|---:|---:|---|",
        ])
        for item in hardware["results"]:
            tasks = ", ".join(task.split(".")[-1] for task, passed in item["taskCoverage"].items() if passed) or "incomplete"
            offload = "Full" if item["fullAcceleratorOffload"] is True else "Partial" if item["fullAcceleratorOffload"] is False else "Not proven"
            status = "Eligible" if item["eligibleForRecommendationReview"] else ", ".join(item["eligibilityBlockers"])
            speed = f"{item['averageTokensPerSecond']:.1f} tok/s" if item["averageTokensPerSecond"] is not None else "Not measured"
            headroom = f"{item['memoryHeadroomPercent']:.1f}%" if item["memoryHeadroomPercent"] is not None else "Not assessed"
            if item["failureCode"]:
                status = f"{status}; {item['failureCode']}"
            lines.append(f"| {item['model']} | {tasks} | {item['fitStatus']} | {offload} | {speed} | {headroom} | {status} |")
        fallback = hardware["fallbackCandidate"]
        lines.extend(["", f"Fallback candidate: **{fallback['model']}** ({fallback['basis']})." if fallback else "Fallback candidate: **none yet**; required fit or offload evidence is incomplete.", ""])
        for task, proposal in hardware["taskRecommendationProposals"].items():
            label = task.replace("general.", "").replace("content.", "").title()
            if proposal["proposedModelId"]:
                lines.append(f"- {label}: proposed `{proposal['proposedModelId']}`; owner review is required.")
            else:
                lines.append(f"- {label}: no winner yet; at least two eligible candidates need task-quality review.")
        lines.append("")
    lines.extend(["No automatic model selection, download, runtime, or hardware state was changed.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    if any(path.exists() or path.is_symlink() for path in (args.output_json, args.output_markdown)):
        parser.error("output-already-exists")
    try:
        report = build_report(args.request, args.evidence_root)
        for path in (args.output_json, args.output_markdown):
            path.parent.mkdir(parents=True, exist_ok=True)
        with args.output_json.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        with args.output_markdown.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(markdown(report))
    except (ComparisonError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({"hardwareProfiles": len(report["hardware"]), "automaticSelectionChanged": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
