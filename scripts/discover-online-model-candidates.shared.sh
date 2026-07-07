#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_BASE_URL="https://ollama.com/library"
SOURCE_HTML_PATH=""
OUTPUT_PATH=""
TIMEOUT_SECONDS=30
MODEL_PROFILE_PATH=""
VRAM_SELECTION_MODE="TotalDedicated"
AVAILABLE_VRAM_GB=0
INCLUDE_OVERSIZED_MODELS=false
FAMILIES=(
  "qwen3.5"
  "qwen3-coder"
  "devstral"
  "devstral-small"
  "codestral"
  "gpt-oss"
  "glm"
)
CUSTOM_FAMILIES=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --family|-Family)
      if [ "$CUSTOM_FAMILIES" = false ]; then
        FAMILIES=()
        CUSTOM_FAMILIES=true
      fi
      FAMILIES+=("$2")
      shift 2
      ;;
    --families|-Families)
      if [ "$CUSTOM_FAMILIES" = false ]; then
        FAMILIES=()
        CUSTOM_FAMILIES=true
      fi
      IFS=',' read -r -a split_families <<< "$2"
      for family in "${split_families[@]}"; do
        FAMILIES+=("$(printf '%s' "$family" | sed 's/^ *//;s/ *$//')")
      done
      shift 2
      ;;
    --source-base-url|-SourceBaseUrl)
      SOURCE_BASE_URL="$2"
      shift 2
      ;;
    --source-html-path|-SourceHtmlPath)
      SOURCE_HTML_PATH="$2"
      shift 2
      ;;
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --timeout-seconds|-TimeoutSeconds)
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --model-profile-path|-ModelProfilePath)
      MODEL_PROFILE_PATH="$2"
      shift 2
      ;;
    --vram-selection-mode|-VramSelectionMode)
      VRAM_SELECTION_MODE="$2"
      shift 2
      ;;
    --available-vram-gb|-AvailableVramGb)
      AVAILABLE_VRAM_GB="$2"
      shift 2
      ;;
    --include-oversized-models|-IncludeOversizedModels)
      INCLUDE_OVERSIZED_MODELS=true
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is required for this discovery script.\n' >&2
  exit 1
fi

if [ -z "$OUTPUT_PATH" ]; then
  OUTPUT_PATH="$REPO_ROOT/runtime-validation-output/online-model-candidates-$(date '+%Y%m%d-%H%M%S').json"
fi

FAMILY_ARGS=()
for family in "${FAMILIES[@]}"; do
  [ -z "$family" ] && continue
  FAMILY_ARGS+=(--family "$family")
done

python3 - "$REPO_ROOT" "$SOURCE_BASE_URL" "$SOURCE_HTML_PATH" "$OUTPUT_PATH" "$TIMEOUT_SECONDS" "$MODEL_PROFILE_PATH" "$VRAM_SELECTION_MODE" "$AVAILABLE_VRAM_GB" "$INCLUDE_OVERSIZED_MODELS" "${FAMILY_ARGS[@]}" <<'PY'
import argparse
import json
import os
import platform as py_platform
import re
import sys
import time
import urllib.request

repo_root, source_base_url, source_html_path, output_path, timeout_seconds, model_profile_path, vram_selection_mode, available_vram_gb, include_oversized_models, *rest = sys.argv[1:]
timeout_seconds = int(timeout_seconds)
available_vram_gb = float(available_vram_gb or 0)
include_oversized_models = include_oversized_models.lower() == "true"

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--family", action="append", default=[])
args, _ = parser.parse_known_args(rest)
families = list(dict.fromkeys([family.strip() for family in args.family if family.strip()]))
source_base_url = source_base_url.rstrip("/")
print(f"Discovery families: {', '.join(families)}")
source_mode = "local HTML fixture" if source_html_path else "online Ollama library pages"
print(f"Source mode: {source_mode}")

def get_source_content(family):
    if source_html_path:
        if not os.path.exists(source_html_path):
            raise FileNotFoundError(f"SourceHtmlPath does not exist: {source_html_path}")
        with open(source_html_path, "r", encoding="utf-8") as handle:
            return {"Source": "local-html-fixture", "Url": "redacted", "Content": handle.read()}
    url = f"{source_base_url}/{family}"
    with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
        return {"Source": "ollama-library-page", "Url": url, "Content": response.read().decode("utf-8", errors="replace")}

def extract_model_tags(content, family):
    escaped = re.escape(family)
    patterns = [
        rf"(?i)\b{escaped}:[a-z0-9][a-z0-9._-]*\b",
        rf"(?i)/library/({escaped}:[a-z0-9][a-z0-9._-]*)",
        rf"(?i)\b([a-z0-9][a-z0-9._/-]*{escaped}[a-z0-9._/-]*:[a-z0-9][a-z0-9._-]*)\b",
    ]
    values = []
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            value = match.group(1) if match.groups() else match.group(0)
            value = value.strip().strip('"\'<>,.;)(')
            if value.startswith("/library/"):
                value = value[9:]
            if value.startswith("library/"):
                value = value[8:]
            if re.match(r"^[A-Za-z0-9][A-Za-z0-9._/-]*:[A-Za-z0-9][A-Za-z0-9._-]*$", value):
                values.append(value)
    return list(dict.fromkeys(values))


def model_size_billion(model):
    match = re.search(r"(?i)(\d+(?:\.\d+)?)b", model)
    if not match:
        return 0
    return float(match.group(1))

def recommended_min_vram_gb(model):
    if re.search(r"(?i)(cloud|-mlx)", model):
        return 999999
    size = model_size_billion(model)
    if size <= 0:
        return 0
    if size <= 1:
        return 4
    if size <= 2:
        return 6
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

def current_platform_name():
    if sys.platform == "darwin":
        return "macOS"
    if sys.platform.startswith("linux"):
        return "Linux"
    if sys.platform.startswith("win"):
        return "Windows"
    return "Unknown"

def model_host_platform(path):
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                profile = json.load(handle)
            if profile.get("Platform"):
                return str(profile["Platform"])
        except Exception:
            return current_platform_name()
    return current_platform_name()

def normalize_platform_name(value):
    value = str(value or "")
    if re.search(r"(?i)mac|darwin", value):
        return "macOS"
    if re.search(r"(?i)linux", value):
        return "Linux"
    if re.search(r"(?i)windows", value):
        return "Windows"
    return "Unknown"

def available_vram_from_profile(path, selection_mode):
    if not path:
        return None
    if not os.path.exists(path):
        raise FileNotFoundError(f"ModelProfilePath does not exist: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        profile = json.load(handle)
    values = []
    for gpu in profile.get("Gpus") or []:
        value = gpu.get("VramGb")
        memory_type = str(gpu.get("MemoryType") or "")
        if memory_type and not re.search(r"(?i)dedicated|unknown", memory_type):
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if value > 0:
            values.append(value)
    if not values:
        return None
    if selection_mode == "MaxDedicated":
        return round(max(values), 2)
    return round(sum(values), 2)

effective_available_vram_gb = available_vram_gb
vram_source = "explicit" if effective_available_vram_gb > 0 else None
if effective_available_vram_gb <= 0 and model_profile_path:
    print(f"Reading VRAM from model profile using {vram_selection_mode} mode. The profile is local-only and is not sent online.", file=sys.stderr)
    profile_vram = available_vram_from_profile(model_profile_path, vram_selection_mode)
    if profile_vram and profile_vram > 0:
        effective_available_vram_gb = profile_vram
        vram_source = f"model-profile:{vram_selection_mode}"
if effective_available_vram_gb > 0:
    print(f"Using local VRAM estimate: {effective_available_vram_gb} GB ({vram_source}).", file=sys.stderr)

model_host = model_host_platform(model_profile_path)
print(f"Model host platform: {model_host}")

def vram_recommendation(model):
    recommended = recommended_min_vram_gb(model)
    fits = True
    if effective_available_vram_gb > 0 and recommended > 0:
        fits = recommended <= effective_available_vram_gb
    return {
        "AvailableVramGb": effective_available_vram_gb if effective_available_vram_gb > 0 else None,
        "AvailableVramSource": vram_source,
        "RecommendedMinVramGb": recommended if 0 < recommended < 999999 else None,
        "FitsAvailableVram": bool(fits),
    }
def model_pull_eligibility(model, host_platform):
    normalized_platform = normalize_platform_name(host_platform)
    if re.search(r"(?i)cloud", model):
        return {
            "Pullable": False,
            "Reason": "Cloud catalog tag; local Ollama pull is not supported.",
            "FailureSignal": "MODEL_SKIPPED_FOR_PLATFORM",
        }
    if re.search(r"(?i)-mlx($|[-_:])", model) and normalized_platform != "macOS":
        return {
            "Pullable": False,
            "Reason": "MLX model tag requires a macOS Apple Silicon model host.",
            "FailureSignal": "MODEL_SKIPPED_FOR_PLATFORM",
        }
    return {
        "Pullable": True,
        "Reason": "Model tag is pullable for this host platform.",
        "FailureSignal": "none",
    }

def reason(model):
    if re.search(r"(?i)(coder|code|codestral|devstral)", model):
        return "Coding-oriented model name discovered online. Requires local tool validation."
    if re.search(r"(?i)(qwen|glm|gpt-oss)", model):
        return "General model family with prior local-agent interest. Requires local tool validation."
    return "Discovered online candidate. Requires local validation before use."

candidates = []
skipped_candidates = []
errors = []
for family in families:
    print(f"Checking family: {family}")
    try:
        source = get_source_content(family)
        model_tags = extract_model_tags(source["Content"], family)
        print(f"Found {len(model_tags)} candidate tag(s) for family: {family}")
        if not model_tags:
            print(f"No candidates found for family: {family}")
        for model in model_tags:
            pull_eligibility = model_pull_eligibility(model, model_host)
            if not pull_eligibility["Pullable"]:
                print(f"Skipped candidate: {model} ({pull_eligibility['Reason']})")
                skipped_candidates.append({
                    "Model": model,
                    "Family": family,
                    "Source": source["Source"],
                    "Status": "online candidate skipped for platform",
                    "Reason": pull_eligibility["Reason"],
                    "NextStep": "Do not pull this tag for the detected model host platform.",
                    "FailureSignal": pull_eligibility["FailureSignal"],
                    "ModelHostPlatform": model_host,
                })
                continue

            recommendation = vram_recommendation(model)
            fits = recommendation["FitsAvailableVram"] or include_oversized_models
            fit_label = "fits VRAM estimate" if recommendation["FitsAvailableVram"] else "above VRAM estimate"
            print(f"Discovered candidate: {model} ({fit_label})")
            candidates.append({
                "Model": model,
                "Family": family,
                "Source": source["Source"],
                "Status": "online candidate" if fits else "online candidate above vram estimate",
                "Reason": reason(model),
                "NextStep": "Pull and test locally with scripts/test-local-agent-models before using in Continue." if fits else "Do not pull by default on this hardware estimate. Use a larger model host, manual override, or IncludeOversizedModels before local testing.",
                "ModelHostPlatform": model_host,
                "VramRecommendation": recommendation,
            })
    except Exception as exc:
        source_name = "local-html-fixture" if source_html_path else "ollama-library-page"
        error_message = str(exc)
        print(f"Source error for family: {family} ({source_name}) - {error_message}")
        errors.append({"Family": family, "Source": source_name, "Error": error_message})

unique = {f"{item['Model']}|{item['Family']}": item for item in candidates}
candidates = sorted(unique.values(), key=lambda item: (item["Model"], item["Family"]))
unique_skipped = {f"{item['Model']}|{item['Family']}": item for item in skipped_candidates}
skipped_candidates = sorted(unique_skipped.values(), key=lambda item: (item["Model"], item["Family"]))
report = {
    "GeneratedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
    "DiscoveryMode": "local-fixture" if source_html_path else "online",
    "SourceBaseUrl": "redacted" if source_html_path else source_base_url,
    "RepositoryContentSent": False,
    "HardwareProfileSent": False,
    "ModelProfilePath": "redacted" if model_profile_path else None,
    "VramSelectionMode": vram_selection_mode,
    "AvailableVramGb": effective_available_vram_gb if effective_available_vram_gb > 0 else None,
    "AvailableVramSource": vram_source,
    "ModelHostPlatform": model_host,
    "IncludeOversizedModels": include_oversized_models,
    "PullsModels": False,
    "RewritesContinueConfig": False,
    "Candidates": candidates,
    "SkippedCandidates": skipped_candidates,
    "Errors": errors,
    "Note": "Online discovery reports candidate names only. It does not prove tool support, pull models, or update Continue config.",
}
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2)
print(f"Discovery summary: {len(candidates)} candidate(s), {len(skipped_candidates)} skipped candidate(s), {len(errors)} source error(s).")
for candidate in candidates:
    fits_available_vram = candidate.get("VramRecommendation", {}).get("FitsAvailableVram")
    if fits_available_vram is True:
        fit_label = "fits VRAM estimate"
    elif fits_available_vram is False:
        fit_label = "above VRAM estimate"
    else:
        fit_label = "not estimated"
    print(f"{candidate['Model']}: {candidate['Status']} ({fit_label})")
for candidate in skipped_candidates:
    print(f"{candidate['Model']}: skipped ({candidate['Reason']})")
if errors:
    print(f"Discovery completed with {len(errors)} source error(s). See report.")
if effective_available_vram_gb > 0:
    print("VRAM annotations were calculated locally and were not sent to the online source.")
print(f"Candidate report written to {output_path}")
PY
