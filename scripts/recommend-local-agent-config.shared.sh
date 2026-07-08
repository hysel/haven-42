#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL_PROFILE_PATH=""
MODEL_CATALOG_PATH="$REPO_ROOT/config/model-recommendations.tsv"
EVIDENCE_CATALOG_PATH="$REPO_ROOT/config/evidence-catalog.tsv"
OUTPUT_PATH=""
VRAM_SELECTION_MODE="MaxDedicated"

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
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --vram-selection-mode|-VramSelectionMode)
      VRAM_SELECTION_MODE="$2"
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

python3 - "$MODEL_PROFILE_PATH" "$MODEL_CATALOG_PATH" "$EVIDENCE_CATALOG_PATH" "$OUTPUT_PATH" "$VRAM_SELECTION_MODE" <<'PY'
import json
import os
import re
import sys
from datetime import datetime

profile_path, model_catalog_path, evidence_catalog_path, output_path, vram_selection_mode = sys.argv[1:6]

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


def workflow_rank(status):
    return {"approved-write-ready": 0, "read-only-tool-validated": 1, "plan-review-candidate": 2}.get(status, 3)


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
    evidence = {}
    if not os.path.exists(path):
        return evidence
    with open(path, "r", encoding="utf-8") as handle:
        next(handle, None)
        for line in handle:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t", 7)
            if len(parts) < 8 or parts[0] != "model-tool-use":
                continue
            evidence.setdefault(parts[4], {"Status": parts[5], "Evidence": parts[6], "Notes": parts[7]})
    return evidence


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
evidence = read_evidence(evidence_catalog_path)
seen = set()
candidates = []


def add_candidate(model, source, row=None):
    model = (model or "").strip()
    if not model or model in seen:
        return
    seen.add(model)
    min_vram = recommended_min_vram(model)
    fits = True
    if min_vram >= 999999:
        fits = False
    elif vram_gb is not None and min_vram > 0:
        fits = min_vram <= vram_gb
    evidence_item = evidence.get(model)
    validation_status = evidence_item["Status"] if evidence_item else "candidate-only"
    eligible, reason = platform_eligibility(model, platform)
    candidates.append({
        "Model": model,
        "Source": source,
        "ValidationStatus": validation_status,
        "Evidence": evidence_item["Evidence"] if evidence_item else None,
        "RecommendedMinVramGb": min_vram if 0 < min_vram < 999999 else None,
        "FitsAvailableVram": bool(fits),
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

for model_name in evidence:
    add_candidate(model_name, "evidence-catalog")


def select_primary(purpose):
    eligible = [item for item in candidates if item["PlatformEligible"] and item["FitsAvailableVram"]]
    if purpose == "write":
        eligible = [item for item in eligible if item["ValidationStatus"] == "approved-write-ready"]
    elif purpose == "plan":
        eligible = [item for item in eligible if item["ValidationStatus"] in {"approved-write-ready", "read-only-tool-validated", "plan-review-candidate"}]
    else:
        eligible = [item for item in eligible if item["ValidationStatus"] != "candidate-only"]
    if not eligible:
        return None
    return sorted(eligible, key=lambda item: (
        workflow_rank(item["ValidationStatus"]),
        item["RecommendedMinVramGb"] if item["RecommendedMinVramGb"] is not None else 9999,
        preference_rank(item["Model"]),
        item["Model"],
    ))[0]


write_model = select_primary("write")
plan_model = select_primary("plan") or write_model
review_model = select_primary("review") or plan_model
status = "recommended" if write_model else "no-approved-write-model"
next_step = "Generate local Continue config from this recommendation, then run editor read-only and approved-write smoke tests." if write_model else "Run model validation before generating a write-enabled local config."

report = {
    "GeneratedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "ModelProfilePath": "redacted",
    "ModelCatalogPath": "redacted",
    "EvidenceCatalogPath": "redacted",
    "Platform": platform,
    "CpuArchitecture": profile.get("CpuArchitecture"),
    "SystemRamGb": profile.get("SystemRamGb"),
    "VramSelectionMode": vram_selection_mode,
    "AvailableVramGb": vram_gb,
    "InstalledModelCount": len(installed_models),
    "Recommendation": {
        "Status": status,
        "WriteSafeModel": write_model["Model"] if write_model else None,
        "PlanOnlyModel": plan_model["Model"] if plan_model else None,
        "DeepReviewModel": review_model["Model"] if review_model else None,
        "Reason": "Selected from catalog and validation evidence using platform compatibility, VRAM fit, and workflow validation status.",
        "NextStep": next_step,
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
