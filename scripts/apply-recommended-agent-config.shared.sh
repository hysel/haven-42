#!/usr/bin/env bash
set -euo pipefail

TARGET_REPO=""
RECOMMENDATION_PATH=""
OLLAMA_BASE_URL=""
DRY_RUN=false
GLOBAL_CONFIG=false
GLOBAL_CONFIG_PATH="$HOME/.continue/config.yaml"
GLOBAL_CONFIG_INCLUDE_RULES=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-repo|-TargetRepo)
      TARGET_REPO="$2"
      shift 2
      ;;
    --recommendation-path|-RecommendationPath)
      RECOMMENDATION_PATH="$2"
      shift 2
      ;;
    --ollama-base-url|-OllamaBaseUrl)
      OLLAMA_BASE_URL="$2"
      shift 2
      ;;
    --dry-run|-DryRun)
      DRY_RUN=true
      shift
      ;;
    --global-config|-GlobalConfig)
      GLOBAL_CONFIG=true
      shift
      ;;
    --global-config-path|-GlobalConfigPath)
      GLOBAL_CONFIG_PATH="$2"
      shift 2
      ;;
    --global-config-include-rules|-GlobalConfigIncludeRules)
      GLOBAL_CONFIG_INCLUDE_RULES=true
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [ -z "$TARGET_REPO" ]; then
  printf 'Target repository is required. Use --target-repo <path>.\n' >&2
  exit 1
fi

if [ -z "$RECOMMENDATION_PATH" ]; then
  printf 'Recommendation path is required. Use --recommendation-path <path>.\n' >&2
  exit 1
fi

BASE_CONFIG="$TARGET_REPO/.continue/config.yaml"
LOCAL_CONFIG="$TARGET_REPO/.continue/config.local.yaml"
TARGET_CONTINUE="$TARGET_REPO/.continue"

if [ ! -f "$BASE_CONFIG" ]; then
  printf 'Target repository must already have .continue/config.yaml. Install the pack first.\n' >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is required for this config generation script.\n' >&2
  exit 1
fi

if [ "$DRY_RUN" = true ]; then
  python3 - "$RECOMMENDATION_PATH" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    recommendation = json.load(handle)
status = recommendation.get("Recommendation", {}).get("Status")
write_model = recommendation.get("Recommendation", {}).get("WriteSafeModel")
if status != "recommended" or not write_model:
    raise SystemExit("Recommendation is not write-ready. Run model validation before generating a write-enabled local config.")
print(write_model)
PY
  printf 'Would apply hardware-aware recommendation to local-only Continue config.\n'
  printf 'Target config: %s\n' "$LOCAL_CONFIG"
  [ -n "$OLLAMA_BASE_URL" ] && printf 'Would include a machine-specific Ollama endpoint in the local-only config.\n'
  if [ "$GLOBAL_CONFIG" = true ]; then
    printf 'Would write global Continue config: %s\n' "$GLOBAL_CONFIG_PATH"
    [ "$GLOBAL_CONFIG_INCLUDE_RULES" = false ] && printf 'Would omit rules from generated global config to avoid duplicate rule warnings.\n'
  fi
  exit 0
fi

SOURCE_CONFIG="$BASE_CONFIG"
if [ -f "$LOCAL_CONFIG" ]; then
  SOURCE_CONFIG="$LOCAL_CONFIG"
fi

python3 - "$SOURCE_CONFIG" "$LOCAL_CONFIG" "$RECOMMENDATION_PATH" "$OLLAMA_BASE_URL" "$GLOBAL_CONFIG" "$GLOBAL_CONFIG_PATH" "$GLOBAL_CONFIG_INCLUDE_RULES" "$TARGET_CONTINUE" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
recommendation_path = Path(sys.argv[3])
api_base = sys.argv[4].strip()
global_config = sys.argv[5].lower() == "true"
global_config_path = Path(sys.argv[6]).expanduser()
global_config_include_rules = sys.argv[7].lower() == "true"
target_continue = Path(sys.argv[8])

recommendation = json.loads(recommendation_path.read_text(encoding="utf-8"))
summary = recommendation.get("Recommendation", {})
if summary.get("Status") != "recommended" or not summary.get("WriteSafeModel"):
    raise SystemExit("Recommendation is not write-ready. Run model validation before generating a write-enabled local config.")

profiles = recommendation.get("ContinueProfiles") or {}
lanes = [
    ("WriteSafe", "1 - WRITE SAFE", ["chat", "edit", "apply"]),
    ("PlanOnly", "2 - PLAN ONLY", ["chat"]),
    ("DeepReview", "3 - DEEP REVIEW", ["chat"]),
]

replacement = ["models:"]
for key, label, fallback_roles in lanes:
    profile = profiles.get(key) or {}
    model = str(profile.get("Model") or "").strip()
    if not model:
        continue
    roles = [str(role) for role in profile.get("Roles") or fallback_roles]
    context_length = int(profile.get("ContextLength") or 16384)
    max_tokens = int(profile.get("MaxTokens") or 2048)
    keep_alive = int(profile.get("KeepAlive") or 1800)
    replacement.extend([
        f"  - name: {label} - {model}",
        "    provider: ollama",
        f"    model: {model}",
    ])
    if api_base:
        replacement.append(f"    apiBase: {api_base}")
    replacement.append("    roles:")
    replacement.extend([f"      - {role}" for role in roles])
    replacement.extend([
        "    capabilities:",
        "      - tool_use",
        "    defaultCompletionOptions:",
        "      temperature: 0.2",
        f"      contextLength: {context_length}",
        f"      maxTokens: {max_tokens}",
        f"      keepAlive: {keep_alive}",
    ])

replacement.extend([
    "  - name: Ollama Nomic Embed",
    "    provider: ollama",
    "    model: nomic-embed-text",
])
if api_base:
    replacement.append(f"    apiBase: {api_base}")
replacement.extend([
    "    roles:",
    "      - embed",
])

lines = source.read_text(encoding="utf-8").splitlines()
updated = []
skip = False
inserted = False
for line in lines:
    if line.strip() == "models:" and not line.startswith((" ", "\t")):
        updated.extend(replacement)
        skip = True
        inserted = True
        continue
    if skip and line and not line.startswith((" ", "\t")) and line.split(":", 1)[0].replace("-", "").replace("_", "").isalnum():
        skip = False
    if not skip:
        updated.append(line)

if not inserted:
    raise SystemExit("Could not find top-level models section in config.")

local_header = [
    "# Local-only Continue config generated by apply-recommended-agent-config.shared.sh.",
    "# Do not commit this file. It may contain machine-specific model choices or endpoints.",
    "# Source recommendation path is intentionally not recorded to avoid local path leaks.",
]
local_lines = local_header + updated
target.write_text("\n".join(local_lines) + "\n", encoding="utf-8")

if global_config:
    global_config_path.parent.mkdir(parents=True, exist_ok=True)
    if global_config_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = global_config_path.with_name(global_config_path.name + f".backup-{timestamp}")
        backup_path.write_text(global_config_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        backup_path = None

    target_continue_uri = "file://" + str(target_continue.resolve()).replace("\\", "/")
    global_lines = [line.replace("file://./", target_continue_uri + "/") for line in local_lines]

    if not global_config_include_rules:
        stripped = []
        skipping = False
        for line in global_lines:
            if line == "rules:":
                skipping = True
                continue
            if skipping and line and not line.startswith((" ", "\t")) and line.split(":", 1)[0].replace("-", "").replace("_", "").isalnum():
                skipping = False
            if not skipping:
                stripped.append(line)
        global_lines = stripped

    global_header = [
        "# Global Continue config generated by apply-recommended-agent-config.shared.sh.",
        "# This file points Continue at pack assets installed in a target repository.",
        "# The rules section is omitted by default to avoid duplicate rules when the opened repository also has .continue/rules.",
        "# Regenerate it when you move or reinstall the target repository.",
    ]
    global_config_path.write_text("\n".join(global_header + global_lines) + "\n", encoding="utf-8")
    print(f"GLOBAL_CONFIG={global_config_path}")
    if backup_path:
        print(f"GLOBAL_CONFIG_BACKUP={backup_path}")

print(summary.get("WriteSafeModel"))
print(summary.get("PlanOnlyModel"))
print(summary.get("DeepReviewModel"))
PY

printf 'Updated local Continue config: %s\n' "$LOCAL_CONFIG"
if [ "$GLOBAL_CONFIG" = true ]; then
  printf 'Updated global Continue config: %s\n' "$GLOBAL_CONFIG_PATH"
fi
