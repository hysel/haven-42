#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL_PROFILE_PATH=""
MODEL_CATALOG_PATH="$REPO_ROOT/config/model-recommendations.tsv"
MODEL_FIT_CATALOG_PATH="$REPO_ROOT/config/model-fit-profiles.json"
EVIDENCE_CATALOG_PATH="$REPO_ROOT/config/evidence-catalog.tsv"
OUTPUT_PATH=""
VRAM_SELECTION_MODE="MaxDedicated"
SURFACE="Continue Agent"
SURFACE_VERSION="not-recorded"
PROVIDER="Ollama"
CONTEXT_TARGET_TOKENS="16384"
MEMORY_RESERVE_GB=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --model-profile-path|-ModelProfilePath)
      MODEL_PROFILE_PATH="$2"
      shift 2
      ;;
    --model-catalog-path|-ModelCatalogPath)
      MODEL_CATALOG_PATH="$2"
      shift 2
      ;;
    --evidence-catalog-path|-EvidenceCatalogPath)
      EVIDENCE_CATALOG_PATH="$2"
      shift 2
      ;;
    --model-fit-catalog-path|-ModelFitCatalogPath)
      MODEL_FIT_CATALOG_PATH="$2"
      shift 2
      ;;
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --vram-selection-mode|-VramSelectionMode)
      VRAM_SELECTION_MODE="$2"
      shift 2
      ;;
    --surface|-Surface)
      SURFACE="$2"
      shift 2
      ;;
    --surface-version|-SurfaceVersion)
      SURFACE_VERSION="$2"
      shift 2
      ;;
    --provider|-Provider)
      PROVIDER="$2"
      shift 2
      ;;
    --context-target-tokens|-ContextTargetTokens)
      CONTEXT_TARGET_TOKENS="$2"
      shift 2
      ;;
    --memory-reserve-gb|-MemoryReserveGb)
      MEMORY_RESERVE_GB="$2"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [ -z "$MODEL_PROFILE_PATH" ]; then
  printf 'Model profile path is required. Use --model-profile-path <path>.\n' >&2
  exit 1
fi

if [ -z "$OUTPUT_PATH" ]; then
  timestamp="$(date +%Y%m%d-%H%M%S)"
  OUTPUT_PATH="$REPO_ROOT/runtime-validation-output/model-config-recommendation-$timestamp.json"
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is required for this recommendation script.\n' >&2
  exit 1
fi

printf '[1/5] Reading local model profile...\n'
printf '[2/5] Reading model and evidence catalogs...\n'
printf '[3/5] Building hardware-aware candidate list...\n'
printf '[4/5] Selecting model lanes and config defaults...\n'

python3 - "$MODEL_PROFILE_PATH" "$MODEL_CATALOG_PATH" "$MODEL_FIT_CATALOG_PATH" "$EVIDENCE_CATALOG_PATH" "$OUTPUT_PATH" "$VRAM_SELECTION_MODE" "$SURFACE" "$SURFACE_VERSION" "$PROVIDER" "$CONTEXT_TARGET_TOKENS" "$MEMORY_RESERVE_GB" <<'PY'
import json
import os
import re
import sys
from datetime import datetime

profile_path, model_catalog_path, model_fit_catalog_path, evidence_catalog_path, output_path, vram_selection_mode, surface, surface_version, provider, context_target_text, reserve_override_text = sys.argv[1:12]
context_target_tokens = int(context_target_text)
if context_target_tokens < 1024:
    raise SystemExit("Context target tokens must be at least 1024.")
reserve_override_gb = float(reserve_override_text) if reserve_override_text else None
if reserve_override_gb is not None and reserve_override_gb < 0:
    raise SystemExit("Memory reserve must not be negative.")

with open(profile_path, "r", encoding="utf-8") as handle:
    profile = json.load(handle)


def normalized_platform(value):
    text = str(value or "")
    if re.search(r"mac|darwin", text, re.I):
        return "macOS"
    if re.search(r"linux", text, re.I):
        return "Linux"
    if re.search(r"windows", text, re.I):
        return "Windows"
    return "Unknown"


def model_size_billion(model):
    match = re.search(r"(\d+(?:\.\d+)?)b", model, re.I)
    return float(match.group(1)) if match else 0.0


def recommended_min_vram(model):
    if re.search(r"cloud|-mlx", model, re.I):
        return 999999
    size = model_size_billion(model)
    if size <= 0:
        return 0
    if size <= 4:
        return 8
    if size <= 9:
        return 12
    if size <= 14:
        return 20
    if size <= 27:
        return 36
    if size <= 35:
        return 48
    if size <= 80:
        return 80
    if size <= 122:
        return 128
    return 512


def read_fit_catalog(path):
    with open(path, "r", encoding="utf-8") as handle:
        catalog = json.load(handle)
    if catalog.get("schemaVersion") != 1 or "defaults" not in catalog or "profiles" not in catalog:
        raise SystemExit("Model fit catalog must use schemaVersion 1 and define defaults and profiles.")
    return catalog


def model_fit_estimate(model):
    profile_row = next((row for row in fit_catalog["profiles"] if re.search(row["matchPattern"], model)), None)
    if profile_row:
        baseline = max(1.0, float(profile_row["baselineContextTokens"]))
        kv_cache = float(profile_row["kvCacheGbAtBaseline"]) * (context_target_tokens / baseline)
        subtotal = float(profile_row["estimatedWeightsGb"]) + kv_cache + float(profile_row["runtimeOverheadGb"])
        fixed_reserve = reserve_override_gb if reserve_override_gb is not None else float(profile_row.get("memoryReserveGb", fit_catalog["defaults"]["memoryReserveGb"]))
        reserve_percent = float(profile_row.get("memoryReservePercent", fit_catalog["defaults"]["memoryReservePercent"]))
        reserve = fixed_reserve if reserve_override_gb is not None else max(fixed_reserve, subtotal * (reserve_percent / 100.0))
        return {
            "Source": "model-fit-catalog",
            "Confidence": "curated-estimate",
            "ProfileId": profile_row["id"],
            "Architecture": profile_row["architecture"],
            "ParameterCountBillion": profile_row["parameterCountBillion"],
            "ActiveParameterCountBillion": profile_row.get("activeParameterCountBillion"),
            "QuantizationAssumption": profile_row["quantizationAssumption"],
            "ContextTargetTokens": context_target_tokens,
            "EstimatedWeightsGb": round(float(profile_row["estimatedWeightsGb"]), 2),
            "EstimatedKvCacheGb": round(kv_cache, 2),
            "RuntimeOverheadGb": round(float(profile_row["runtimeOverheadGb"]), 2),
            "MemoryReserveGb": round(reserve, 2),
            "EstimatedRequiredVramGb": round(subtotal + reserve, 2),
        }
    heuristic = recommended_min_vram(model)
    reserve = reserve_override_gb if reserve_override_gb is not None and 0 < heuristic < 999999 else 0
    return {
        "Source": "model-name-heuristic",
        "Confidence": "low",
        "ProfileId": None,
        "Architecture": "unknown",
        "ParameterCountBillion": model_size_billion(model),
        "ActiveParameterCountBillion": None,
        "QuantizationAssumption": "unknown",
        "ContextTargetTokens": context_target_tokens,
        "EstimatedWeightsGb": None,
        "EstimatedKvCacheGb": None,
        "RuntimeOverheadGb": None,
        "MemoryReserveGb": reserve if reserve > 0 else None,
        "EstimatedRequiredVramGb": round(heuristic + reserve, 2) if 0 < heuristic < 999999 else None,
    }


def workflow_rank(status):
    return {"approved-write-ready": 0, "review-validated": 0, "plan-validated": 0, "read-only-tool-validated": 1, "plan-review-candidate": 2}.get(status, 3)


def preference_rank(model):
    if re.search(r"^qwen3\.5:9b$", model, re.I):
        return 0
    if re.search(r"devstral|coder|code|codestral", model, re.I):
        return 1
    if re.search(r"qwen|gpt-oss|llama3\.1", model, re.I):
        return 2
    return 3


def available_vram(profile_obj):
    values = []
    for gpu in profile_obj.get("Gpus") or []:
        if gpu is None or gpu.get("VramGb") is None:
            continue
        memory_type = str(gpu.get("MemoryType") or "")
        if memory_type and not re.search(r"dedicated|unknown", memory_type, re.I):
            continue
        try:
            value = float(gpu.get("VramGb"))
        except (TypeError, ValueError):
            continue
        if value > 0:
            values.append(value)
    if not values:
        return None
    if vram_selection_mode == "TotalDedicated":
        return round(sum(values), 2)
    return round(max(values), 2)


def read_catalog(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("|", 4)
            if len(parts) < 5:
                continue
            rows.append({
                "Tier": parts[0],
                "MatchPattern": parts[1],
                "FallbackModel": parts[2],
                "RecommendedUse": parts[3],
                "ValidationNote": parts[4],
            })
    return rows


def read_evidence(path):
    evidence = []
    if not os.path.exists(path):
        return evidence
    with open(path, "r", encoding="utf-8") as handle:
        import csv
        evidence.extend(csv.DictReader(handle, delimiter="\t"))
    return evidence


def evidence_rank(status):
    return {
        "approved-write-ready": 100,
        "review-validated": 95,
        "plan-validated": 90,
        "write-smoke-validated": 80,
        "read-only-tool-validated": 70,
        "read-only-cli-validated": 60,
        "plan-review-candidate": 50,
        "validated-by-tests": 45,
        "static-validated": 40,
        "partial-pass": 20,
        "candidate-only": 10,
    }.get(status, 0)


def aggregate_evidence(model, operation, validation_mode):
    matches = [
        row for row in evidence
        if row.get("schema_version") == "2"
        and row.get("area") == "model-tool-use"
        and row.get("model") == model
        and row.get("surface") == surface
        and row.get("surface_version") == surface_version
        and row.get("provider") == provider
        and row.get("os") == platform
        and row.get("operation") == operation
        and row.get("validation_mode") == validation_mode
    ]
    if not matches:
        return None
    conservative = sorted(matches, key=lambda row: evidence_rank(row.get("status")))[0]
    return {
        "Status": conservative["status"],
        "RecordCount": len(matches),
        "Evidence": sorted({row["evidence"] for row in matches}),
        "Notes": sorted({row["notes"] for row in matches}),
        "Key": {
            "Surface": surface,
            "SurfaceVersion": surface_version,
            "Provider": provider,
            "Model": model,
            "OS": platform,
            "Operation": operation,
            "ValidationMode": validation_mode,
        },
    }


def platform_eligibility(model, platform):
    if re.search(r"cloud", model, re.I):
        return False, "Cloud catalog tag; local Ollama pull is not supported."
    if re.search(r"-mlx($|[-_:])", model, re.I) and platform != "macOS":
        return False, "MLX model tag requires a macOS Apple Silicon model host."
    return True, "Model tag is compatible with the detected model host platform."


platform = normalized_platform(profile.get("Platform"))
vram_gb = available_vram(profile)
installed_models = [str(model) for model in profile.get("OllamaModels") or []]
catalog_rows = read_catalog(model_catalog_path)
fit_catalog = read_fit_catalog(model_fit_catalog_path)
evidence = read_evidence(evidence_catalog_path)
seen = set()
candidates = []


def add_candidate(model, source, row=None):
    model = (model or "").strip()
    if not model or model in seen:
        return
    seen.add(model)
    fit_estimate = model_fit_estimate(model)
    min_vram = fit_estimate["EstimatedRequiredVramGb"]
    if min_vram is None:
        min_vram = 999999 if re.search(r"cloud|-mlx", model, re.I) else 0
    fits = True
    if min_vram >= 999999:
        fits = False
    elif vram_gb is not None and min_vram > 0:
        fits = min_vram <= vram_gb
    write_evidence = aggregate_evidence(model, "scoped-write", "editor-agent")
    plan_evidence = aggregate_evidence(model, "plan", "editor-agent")
    review_evidence = aggregate_evidence(model, "review", "editor-agent")
    validation_status = write_evidence["Status"] if write_evidence else "candidate-only"
    eligible, reason = platform_eligibility(model, platform)
    candidates.append({
        "Model": model,
        "Source": source,
        "ValidationStatus": validation_status,
        "Evidence": write_evidence["Evidence"] if write_evidence else [],
        "OperationEvidence": {
            "ScopedWrite": write_evidence,
            "Plan": plan_evidence,
            "Review": review_evidence,
        },
        "RecommendedMinVramGb": min_vram if 0 < min_vram < 999999 else None,
        "ModelFit": fit_estimate,
        "FitsAvailableVram": bool(fits),
        "Installed": model in installed_models,
        "ModelSizeBillion": model_size_billion(model),
        "PlatformEligible": bool(eligible),
        "PlatformReason": reason,
        "RecommendedUse": row["RecommendedUse"] if row else "Validate locally before relying on this model.",
        "ValidationNote": row["ValidationNote"] if row else "Run read-only and approved-write smoke tests before granting edit/apply roles.",
    })


for row in catalog_rows:
    pattern = row["MatchPattern"]
    if pattern:
        for installed in installed_models:
            if re.search(pattern, installed):
                add_candidate(installed, "installed-catalog-match", row)
    if row["FallbackModel"]:
        add_candidate(row["FallbackModel"], "catalog-fallback", row)

for model_name in sorted({
    row["model"] for row in evidence
    if row.get("schema_version") == "2"
    and row.get("area") == "model-tool-use"
    and row.get("surface") == surface
    and row.get("surface_version") == surface_version
    and row.get("provider") == provider
    and row.get("os") == platform
}):
    add_candidate(model_name, "evidence-catalog")


def lane_score(item, purpose):
    lane_name = {"write": "WRITE SAFE", "plan": "PLAN ONLY", "review": "DEEP REVIEW"}[purpose]
    evidence_key = {"write": "ScopedWrite", "plan": "Plan", "review": "Review"}[purpose]
    required = {"write": "approved-write-ready", "plan": "plan-validated", "review": "review-validated"}[purpose]
    lane_evidence = item["OperationEvidence"][evidence_key]
    reasons = []
    if not item["PlatformEligible"]:
        reasons.append(item["PlatformReason"])
    if not item["FitsAvailableVram"]:
        reasons.append("Model does not fit the selected VRAM estimate.")
    if not lane_evidence or lane_evidence["Status"] != required:
        actual = lane_evidence["Status"] if lane_evidence else "missing"
        reasons.append(f"Exact {purpose} evidence requires {required}; found {actual}.")
    eligible = not reasons
    score = 0.0
    if eligible:
        score += evidence_rank(lane_evidence["Status"]) * 100
        if item["Installed"]:
            score += 500 if purpose == "write" else 100
            reasons.append("Installed model bonus applied.")
        if purpose == "write":
            if vram_gb is not None and item["RecommendedMinVramGb"] is not None:
                headroom = max(0.0, vram_gb - item["RecommendedMinVramGb"])
                score += headroom * 10
                reasons.append(f"Reliability-first VRAM headroom score: {round(headroom, 2)} GB.")
            score -= preference_rank(item["Model"]) * 10
        else:
            capacity = item["ModelSizeBillion"] or item["RecommendedMinVramGb"] or 0
            score += capacity * 20
            reasons.append(f"Capacity score applied for a fitting {lane_name} model: {capacity}.")
    return {
        "Eligible": eligible,
        "Score": round(score, 2),
        "RequiredStatus": required,
        "EvidenceStatus": lane_evidence["Status"] if lane_evidence else "missing",
        "Rationale": reasons,
    }


for candidate in candidates:
    candidate["LaneScores"] = {
        "WriteSafe": lane_score(candidate, "write"),
        "PlanOnly": lane_score(candidate, "plan"),
        "DeepReview": lane_score(candidate, "review"),
    }


def select_primary(purpose):
    score_key = {"write": "WriteSafe", "plan": "PlanOnly", "review": "DeepReview"}[purpose]
    eligible = [item for item in candidates if item["LaneScores"][score_key]["Eligible"]]
    if not eligible:
        return None
    return sorted(eligible, key=lambda item: (
        -item["LaneScores"][score_key]["Score"],
        item["Model"],
    ))[0]


write_model = select_primary("write")
plan_model = select_primary("plan")
review_model = select_primary("review")
status = "recommended" if write_model else "no-approved-write-model"
next_step = "Generate local Continue config from this recommendation, then run editor read-only and approved-write smoke tests." if write_model else "Run model validation before generating a write-enabled local config."

report = {
    "GeneratedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "ModelProfilePath": "redacted",
    "ModelCatalogPath": "redacted",
    "ModelFitCatalogPath": "redacted",
    "EvidenceCatalogPath": "redacted",
    "Platform": platform,
    "EvidenceContractVersion": 2,
    "EvidenceTarget": {
        "Surface": surface,
        "SurfaceVersion": surface_version,
        "Provider": provider,
        "OS": platform,
    },
    "CpuArchitecture": profile.get("CpuArchitecture"),
    "SystemRamGb": profile.get("SystemRamGb"),
    "VramSelectionMode": vram_selection_mode,
    "AvailableVramGb": vram_gb,
    "InstalledModelCount": len(installed_models),
    "FitPolicy": {
        "Version": 1,
        "ContextTargetTokens": context_target_tokens,
        "MemoryReserveOverrideGb": reserve_override_gb,
        "CatalogSchemaVersion": fit_catalog["schemaVersion"],
        "UnknownModelPolicy": fit_catalog["defaults"]["unknownModelPolicy"],
        "Note": "Catalog values are planning estimates; verify the installed artifact and runtime behavior before relying on a borderline fit.",
    },
    "SelectionPolicy": {
        "Version": 1,
        "WriteSafe": "Exact approved-write evidence first; prefer installed models and greater VRAM headroom.",
        "PlanOnly": "Exact plan evidence first; prefer greater fitting model capacity with a small installed-model bonus.",
        "DeepReview": "Exact review evidence first; prefer greater fitting model capacity with a small installed-model bonus.",
        "UnknownModelSizeBehavior": "Unknown sizes receive no capacity bonus and remain subject to exact evidence and platform checks.",
    },
    "Recommendation": {
        "Status": status,
        "WriteSafeModel": write_model["Model"] if write_model else None,
        "PlanOnlyModel": plan_model["Model"] if plan_model else None,
        "DeepReviewModel": review_model["Model"] if review_model else None,
        "Reason": "Selected with lane-specific evidence, platform, VRAM, installation, headroom, and capacity scores.",
        "NextStep": next_step,
    },
    "ModelLanes": {
        "Contract": "surface-neutral",
        "WriteSafe": {
            "Model": write_model["Model"] if write_model else None,
            "RequiresValidationStatus": "approved-write-ready",
            "ToolUse": "approved-write",
            "RecommendedRoles": ["chat", "edit", "apply"],
            "RequiresSurfaceConfigGenerator": True,
            "RequiresEditorSmokeTest": True,
        },
        "PlanOnly": {
            "Model": plan_model["Model"] if plan_model else None,
            "RequiresValidationStatus": "plan-validated for the exact capability key",
            "ToolUse": "plan-review",
            "RecommendedRoles": ["chat"],
            "RequiresSurfaceConfigGenerator": True,
            "RequiresEditorSmokeTest": True,
        },
        "DeepReview": {
            "Model": review_model["Model"] if review_model else None,
            "RequiresValidationStatus": "review-validated for the exact capability key",
            "ToolUse": "deep-review",
            "RecommendedRoles": ["chat"],
            "RequiresSurfaceConfigGenerator": True,
            "RequiresEditorSmokeTest": True,
        },
    },
    "ContinueProfiles": {
        "WriteSafe": {"Model": write_model["Model"] if write_model else None, "Roles": ["chat", "edit", "apply"], "ContextLength": 16384, "MaxTokens": 2048, "KeepAlive": 1800, "RequiresEditorSmokeTest": True},
        "PlanOnly": {"Model": plan_model["Model"] if plan_model else None, "Roles": ["chat"], "ContextLength": 16384, "MaxTokens": 2048, "KeepAlive": 1800},
        "DeepReview": {"Model": review_model["Model"] if review_model else None, "Roles": ["chat"], "ContextLength": 32768, "MaxTokens": 4096, "KeepAlive": 1800},
    },
    "Candidates": sorted(candidates, key=lambda item: (workflow_rank(item["ValidationStatus"]), item["RecommendedMinVramGb"] if item["RecommendedMinVramGb"] is not None else 9999, item["Model"])),
    "Privacy": {
        "RepositoryContentSent": False,
        "HardwareProfileSentOnline": False,
        "PrivatePathsWritten": False,
        "EndpointsWritten": False,
        "Note": "The recommendation output redacts input paths and does not include hostnames, usernames, endpoints, repository paths, or raw hardware reports.",
    },
}

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2)
    handle.write("\n")

print(report["Recommendation"]["Status"])
print(report["Recommendation"]["WriteSafeModel"] or "none")
print(report["Recommendation"]["PlanOnlyModel"] or "none")
print(report["Recommendation"]["DeepReviewModel"] or "none")
print(output_path)
PY

printf '[5/5] Recommendation written to %s\n' "$OUTPUT_PATH"
printf 'Use the recommendation JSON to generate local-only config after editor smoke tests pass.\n'
