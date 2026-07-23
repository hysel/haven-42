#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_CONTINUE="$REPO_ROOT/.continue"
TARGET_REPO=""
DRY_RUN=false
AUTO_MODEL_CONFIG=false
MODEL_LANES=false
MLX_CONFIG=false
MLX_API_BASE="http://127.0.0.1:8080/v1"
INSTALL_PROFILE="default"
READ_ONLY_PROFILE=false
GLOBAL_CONFIG=false
GLOBAL_CONFIG_PATH="${HOME:-}/.continue/config.yaml"
GLOBAL_CONFIG_API_BASE=""
GLOBAL_CONFIG_INCLUDE_RULES=false
SHARED_ASSETS=false
SHARED_ASSETS_PATH=""

IFS=$'\t' read -r RUNTIME_RESIDENCY_MODE MAX_RESIDENT_MODELS PRELOAD_KEEP_ALIVE_MINUTES <<< "$("$SCRIPT_DIR/get-model-runtime-policy.shared.sh")"
CONTINUE_KEEP_ALIVE_SECONDS=$((PRELOAD_KEEP_ALIVE_MINUTES * 60))
if [ "$RUNTIME_RESIDENCY_MODE" = "unload-after-run" ]; then CONTINUE_KEEP_ALIVE_SECONDS=0; fi
export CONTINUE_KEEP_ALIVE_SECONDS

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-repo|-TargetRepo)
      TARGET_REPO="$2"
      shift 2
      ;;
    --dry-run|-DryRun)
      DRY_RUN=true
      shift
      ;;
    --auto-model-config|-AutoModelConfig)
      AUTO_MODEL_CONFIG=true
      shift
      ;;
    --model-lanes|-ModelLanes)
      MODEL_LANES=true
      shift
      ;;
    --mlx-config|-MlxConfig)
      MLX_CONFIG=true
      shift
      ;;
    --mlx-api-base|-MlxApiBase)
      MLX_API_BASE="$2"
      shift 2
      ;;
    --install-profile|-InstallProfile)
      INSTALL_PROFILE="$2"
      shift 2
      ;;
    --global-config|-GlobalConfig)
      GLOBAL_CONFIG=true
      shift
      ;;
    --global-config-path|-GlobalConfigPath)
      GLOBAL_CONFIG_PATH="$2"
      shift 2
      ;;
    --global-config-api-base|-GlobalConfigApiBase)
      GLOBAL_CONFIG_API_BASE="$2"
      shift 2
      ;;
    --global-config-include-rules|-GlobalConfigIncludeRules)
      GLOBAL_CONFIG_INCLUDE_RULES=true
      shift
      ;;
    --shared-assets|-SharedAssets)
      SHARED_ASSETS=true
      shift
      ;;
    --shared-assets-path|-SharedAssetsPath)
      SHARED_ASSETS_PATH="$2"
      shift 2
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

case "$INSTALL_PROFILE" in
  default)
    ;;
  read-only)
    READ_ONLY_PROFILE=true
    ;;
  approved-write)
    MODEL_LANES=true
    ;;
  *)
    printf 'Unknown install profile: %s. Use default, read-only, or approved-write.\n' "$INSTALL_PROFILE" >&2
    exit 1
    ;;
esac

if [ "$READ_ONLY_PROFILE" = true ] && { [ "$AUTO_MODEL_CONFIG" = true ] || [ "$MODEL_LANES" = true ] || [ "$MLX_CONFIG" = true ]; }; then
  printf 'The read-only install profile cannot be combined with --auto-model-config or --model-lanes.\n' >&2
  exit 1
fi

if [ "$AUTO_MODEL_CONFIG" = true ] && [ "$MODEL_LANES" = true ]; then
  printf 'Use either --auto-model-config or --model-lanes, not both.\n' >&2
  exit 1
fi

if [ "$MLX_CONFIG" = true ]; then
  if [ "$(uname -s 2>/dev/null || true)" != "Darwin" ]; then
    printf '%s\n' '--mlx-config is supported only on macOS Apple Silicon hosts.' >&2
    exit 1
  fi
  if [ "$AUTO_MODEL_CONFIG" = true ] || [ "$MODEL_LANES" = true ]; then
    printf '%s\n' '--mlx-config cannot be combined with --auto-model-config or --model-lanes.' >&2
    exit 1
  fi
  if [ "$GLOBAL_CONFIG" = false ]; then
    printf '%s\n' '--mlx-config requires --global-config so Continue uses the generated OpenAI-compatible MLX config.' >&2
    exit 1
  fi
  if [ -n "$GLOBAL_CONFIG_API_BASE" ]; then
    printf '%s\n' '--mlx-config uses --mlx-api-base. Do not also pass --global-config-api-base.' >&2
    exit 1
  fi
fi

if [ "$SHARED_ASSETS" = true ] && { [ "$AUTO_MODEL_CONFIG" = true ] || [ "$MODEL_LANES" = true ] || [ "$READ_ONLY_PROFILE" = true ] || [ "$MLX_CONFIG" = true ]; }; then
  printf 'Shared-assets mode currently supports reusable assets and global config generation only. Do not combine it with --auto-model-config, --model-lanes, --mlx-config, or read-only/approved-write install profiles.\n' >&2
  exit 1
fi

if [ "$SHARED_ASSETS" = true ] && [ -z "$SHARED_ASSETS_PATH" ]; then
  case "$(uname -s 2>/dev/null || true)" in
    Darwin*) SHARED_ASSETS_PATH="$HOME/Library/Application Support/LocalEngineeringAgentPack/assets" ;;
    *) SHARED_ASSETS_PATH="${XDG_DATA_HOME:-$HOME/.local/share}/haven-42/assets" ;;
  esac
fi

if [ "$SHARED_ASSETS" = true ]; then
  GLOBAL_CONFIG=true
fi

if [ ! -d "$SOURCE_CONTINUE" ]; then
  printf 'Source .continue folder does not exist: %s\n' "$SOURCE_CONTINUE" >&2
  exit 1
fi

if [ ! -d "$TARGET_REPO" ]; then
  printf 'Target repository path does not exist: %s\n' "$TARGET_REPO" >&2
  exit 1
fi

REPO_ROOT_RESOLVED="$(cd "$REPO_ROOT" && pwd)"
TARGET_RESOLVED="$(cd "$TARGET_REPO" && pwd)"

if [ "$REPO_ROOT_RESOLVED" = "$TARGET_RESOLVED" ]; then
  printf 'Target repository must be different from this pack repository.\n' >&2
  exit 1
fi

TARGET_CONTINUE="$TARGET_RESOLVED/.continue"
BACKUP_CONTINUE="$TARGET_RESOLVED/.continue.backup-$(date '+%Y%m%d-%H%M%S')"
BACKUP_GLOBAL_CONFIG="$GLOBAL_CONFIG_PATH.backup-$(date '+%Y%m%d-%H%M%S')"
BACKUP_SHARED_ASSETS="$SHARED_ASSETS_PATH.backup-$(date '+%Y%m%d-%H%M%S')"
PROJECT_PROFILE_PATH=""

cleanup_project_profile() {
  if [ -n "$PROJECT_PROFILE_PATH" ] && [ -f "$PROJECT_PROFILE_PATH" ]; then
    rm -f "$PROJECT_PROFILE_PATH"
  fi
}
trap cleanup_project_profile EXIT

if [ "$SHARED_ASSETS" = false ]; then
  PROJECT_PROFILE_PATH="$(mktemp)"
  "$REPO_ROOT/scripts/get-project-profile.shared.sh" \
    --target-repo "$TARGET_RESOLVED" \
    --output-path "$PROJECT_PROFILE_PATH" >/dev/null
  primary_ecosystem="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["PrimaryEcosystem"])' "$PROJECT_PROFILE_PATH" | tr -d '\r')"
  profile_confidence="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["Confidence"])' "$PROJECT_PROFILE_PATH" | tr -d '\r')"
  selected_rule_packs="$(python3 -c 'import json,sys; print(", ".join(json.load(open(sys.argv[1], encoding="utf-8"))["SelectedRulePackIds"]))' "$PROJECT_PROFILE_PATH" | tr -d '\r')"
fi

printf 'Installing Continue pack into %s\n' "$TARGET_RESOLVED"
printf 'Install profile: %s\n' "$INSTALL_PROFILE"
if [ "$SHARED_ASSETS" = true ]; then
  printf 'Shared-assets mode is enabled.\n'
  printf 'Shared assets target: %s\n' "$SHARED_ASSETS_PATH"
  printf 'Global Continue config update is enabled because shared-assets mode was requested.\n'
  printf 'Project-specific classification and rule activation are skipped in shared-assets mode.\n'
else
  printf 'Detected project ecosystem: %s (%s confidence)\n' "$primary_ecosystem" "$profile_confidence"
  printf 'Project rule packs selected: %s\n' "${selected_rule_packs:-none}"
fi


if [ "$DRY_RUN" = true ]; then
  printf 'Dry run only. No files will be changed.\n'
  if [ "$SHARED_ASSETS" = true ]; then
    if [ -d "$SHARED_ASSETS_PATH" ]; then
      printf 'Would back up existing shared assets to %s\n' "$BACKUP_SHARED_ASSETS"
    fi
    printf 'Would copy reusable assets to %s excluding config.local*.yaml.\n' "$SHARED_ASSETS_PATH"
  else
    if [ -d "$TARGET_CONTINUE" ]; then
      printf 'Would back up existing .continue to %s\n' "$BACKUP_CONTINUE"
    fi
    printf 'Would copy .continue files excluding config.local*.yaml.\n'
    printf 'Would write .continue/project-profile.json and activate selected project rule packs under .continue/rules/.\n'
  fi
  if [ "$AUTO_MODEL_CONFIG" = true ]; then
    printf 'Would generate .continue/config.local.yaml using the hardware profile recommended model.\n'
  fi
  if [ "$READ_ONLY_PROFILE" = true ]; then
    printf 'Would generate .continue/config.local.yaml for read-only review without edit/apply roles.\n'
  fi
  if [ "$MODEL_LANES" = true ]; then
    printf 'Would generate .continue/config.local.yaml with WRITE SAFE, PLAN ONLY, and DEEP REVIEW model profiles plus the embedding model.\n'
  fi
  if [ "$MLX_CONFIG" = true ]; then
    printf 'Would generate .continue/config.local.yaml with the detected macOS MLX recommendation and OpenAI-compatible endpoint.\n'
  fi
  if [ "$GLOBAL_CONFIG" = true ]; then
    printf 'Would write global Continue config with absolute file references to %s\n' "$GLOBAL_CONFIG_PATH"
    if [ -n "$GLOBAL_CONFIG_API_BASE" ]; then
      printf 'Would set Ollama apiBase in generated global config.\n'
    fi
    if [ "$GLOBAL_CONFIG_INCLUDE_RULES" = true ]; then
      printf 'Would include rules in generated global config.\n'
    else
      printf 'Would omit rules from generated global config to avoid duplicate rule warnings.\n'
    fi
  fi
  exit 0
fi

if [ "$SHARED_ASSETS" = true ]; then
  ASSET_ROOT="$SHARED_ASSETS_PATH"
  if [ -d "$ASSET_ROOT" ]; then
    mv "$ASSET_ROOT" "$BACKUP_SHARED_ASSETS"
    printf 'Backed up existing shared assets to %s\n' "$BACKUP_SHARED_ASSETS"
  fi
else
  ASSET_ROOT="$TARGET_CONTINUE"
  if [ -d "$TARGET_CONTINUE" ]; then
    mv "$TARGET_CONTINUE" "$BACKUP_CONTINUE"
    printf 'Backed up existing .continue to %s\n' "$BACKUP_CONTINUE"
  fi
fi

mkdir -p "$ASSET_ROOT"

while IFS= read -r source_file; do
  relative="${source_file#$SOURCE_CONTINUE/}"
  case "$relative" in
    config.local*.yaml|config.local*.yml) continue ;;
  esac

  destination="$ASSET_ROOT/$relative"
  mkdir -p "$(dirname "$destination")"
  cp "$source_file" "$destination"
done < <(find "$SOURCE_CONTINUE" -type f)

if [ "$SHARED_ASSETS" = false ]; then
  cp "$PROJECT_PROFILE_PATH" "$TARGET_CONTINUE/project-profile.json"
  while IFS=$'\t' read -r source_relative active_relative; do
    source_relative="${source_relative%$'\r'}"
    active_relative="${active_relative%$'\r'}"
    [ -z "$source_relative" ] && continue
    case "$source_relative|$active_relative" in
      /*|*'../'*|*'/..'*)
        printf 'Project profile contains an unsafe rule-pack path.\n' >&2
        exit 1
        ;;
    esac
    source_path="$TARGET_CONTINUE/$source_relative"
    destination_path="$TARGET_CONTINUE/$active_relative"
    if [ ! -f "$source_path" ]; then
      printf 'Selected project rule pack is missing: %s\n' "$source_relative" >&2
      exit 1
    fi
    mkdir -p "$(dirname "$destination_path")"
    cp "$source_path" "$destination_path"
  done < <(python3 - "$PROJECT_PROFILE_PATH" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    profile = json.load(handle)
for item in profile["SelectedRulePacks"]:
    print(f'{item["SourcePath"]}\t{item["ActivePath"]}')
PY
)
  printf 'Installed sanitized project profile: %s\n' "$TARGET_CONTINUE/project-profile.json"
  printf 'Activated project rule packs: %s\n' "${selected_rule_packs:-none}"
fi

if [ ! -f "$ASSET_ROOT/config.yaml" ]; then
  printf 'Installed config is missing: %s\n' "$ASSET_ROOT/config.yaml" >&2
  exit 1
fi

CONFIG_CONTENT="$(cat "$ASSET_ROOT/config.yaml")"
FILE_REFS="$(printf '%s\n' "$CONFIG_CONTENT" | grep -Eo 'file://\./[^[:space:]]+' | sed 's#file://./##' || true)"

while IFS= read -r ref; do
  [ -z "$ref" ] && continue
  if [ ! -e "$ASSET_ROOT/$ref" ]; then
    printf 'Installed file reference does not resolve: %s\n' "$ref" >&2
    exit 1
  fi
done <<EOF
$FILE_REFS
EOF

if find "$ASSET_ROOT" -maxdepth 1 -type f \( -name 'config.local*.yaml' -o -name 'config.local*.yml' \) | grep -q .; then
  printf 'Installed assets should not include local config overrides.\n' >&2
  exit 1
fi

if [ "$READ_ONLY_PROFILE" = true ]; then
  {
    printf '# Local-only Continue config generated by install-continue-pack.shared.sh.\n'
    printf '# Do not commit this file. It is scoped for read-only review workflows.\n'
    printf '# This profile intentionally omits edit/apply roles.\n'
    awk '
      function print_read_only_models() {
        print "models:"
        print "  - name: READ ONLY - qwen3.5:9b"
        print "    provider: ollama"
        print "    model: qwen3.5:9b"
        print "    roles:"
        print "      - chat"
        print "    capabilities:"
        print "      - tool_use"
        print "    defaultCompletionOptions:"
        print "      temperature: 0.2"
        print "      contextLength: 16384"
        print "      maxTokens: 2048"
        print "      keepAlive: " ENVIRON["CONTINUE_KEEP_ALIVE_SECONDS"]
        print "  - name: Ollama Nomic Embed"
        print "    provider: ollama"
        print "    model: nomic-embed-text"
        print "    roles:"
        print "      - embed"
      }
      /^models:[[:space:]]*$/ {
        print_read_only_models()
        skip = 1
        next
      }
      skip && /^[A-Za-z_][A-Za-z0-9_-]*:/ {
        skip = 0
      }
      !skip { print }
    ' "$TARGET_CONTINUE/config.yaml"
  } > "$TARGET_CONTINUE/config.local.yaml"

  printf 'Generated read-only profile config: %s\n' "$TARGET_CONTINUE/config.local.yaml"
fi

if [ "$AUTO_MODEL_CONFIG" = true ]; then
  case "$(uname -s 2>/dev/null || true)" in
    Darwin*) profile_script="$REPO_ROOT/scripts/get-local-model-profile.macos.sh" ;;
    *) profile_script="$REPO_ROOT/scripts/get-local-model-profile.linux.sh" ;;
  esac

  if [ ! -x "$profile_script" ]; then
    printf 'Hardware profile script is missing or not executable: %s\n' "$profile_script" >&2
    exit 1
  fi

  profile_json="$("$profile_script" --json)"
  recommended_model="$(printf '%s\n' "$profile_json" | sed -n 's/.*"PrimaryModel":"\([^"]*\)".*/\1/p' | head -n 1)"

  if [ -z "$recommended_model" ]; then
    printf 'Hardware profile did not return a recommended model.\n' >&2
    exit 1
  fi

  {
    printf '# Local-only Continue config generated by install-continue-pack.shared.sh.\n'
    printf '# Do not commit this file. It may contain machine-specific model choices.\n'
    awk -v model="$recommended_model" '
      BEGIN { replaced = 0 }
      /^[[:space:]]*model:[[:space:]]*/ && replaced == 0 {
        sub(/model:.*/, "model: " model)
        replaced = 1
      }
      { print }
    ' "$TARGET_CONTINUE/config.yaml"
  } > "$TARGET_CONTINUE/config.local.yaml"

  printf 'Generated local model config: %s\n' "$TARGET_CONTINUE/config.local.yaml"
  printf 'Selected model: %s\n' "$recommended_model"
fi

if [ "$MLX_CONFIG" = true ]; then
  profile_script="$REPO_ROOT/scripts/get-local-model-profile.macos.sh"
  if [ ! -x "$profile_script" ]; then
    printf 'macOS hardware profile script is missing or not executable: %s\n' "$profile_script" >&2
    exit 1
  fi

  profile_json="$("$profile_script" --json)"
  mlx_status="$(printf '%s\n' "$profile_json" | sed -n 's/.*"MlxStatus":[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
  recommended_mlx_model="$(printf '%s\n' "$profile_json" | sed -n 's/.*"MlxRecommendation":[[:space:]]*{"PrimaryModel":"\([^"]*\)".*/\1/p' | head -n 1)"

  if [ "$mlx_status" != "detected" ]; then
    printf '%s\n' 'MLX tooling was not detected. Install a reviewed exact MLX environment through a user-managed workflow, then rerun discovery.' >&2
    exit 1
  fi
  if [ -z "$recommended_mlx_model" ] || [ "$recommended_mlx_model" = "Not available" ]; then
    printf '%s\n' 'The macOS profile did not return an MLX model recommendation.' >&2
    exit 1
  fi

  {
    printf '# Local-only Continue config generated by install-continue-pack.shared.sh.\n'
    printf '# Do not commit this file. It is for a loopback-only MLX endpoint on this Mac.\n'
    awk -v model="$recommended_mlx_model" -v api_base="$MLX_API_BASE" '
      function print_mlx_model() {
        print "models:"
        print "  - name: Local MLX - " model
        print "    provider: openai"
        print "    model: " model
        print "    apiBase: " api_base
        print "    apiKey: local"
        print "    roles:"
        print "      - chat"
        print "      - edit"
        print "      - apply"
        print "    capabilities:"
        print "      - tool_use"
        print "    defaultCompletionOptions:"
        print "      temperature: 0.2"
        print "      contextLength: 16384"
        print "      maxTokens: 2048"
      }
      /^models:[[:space:]]*$/ {
        print_mlx_model()
        skip = 1
        next
      }
      skip && /^[A-Za-z_][A-Za-z0-9_-]*:/ {
        skip = 0
      }
      !skip { print }
    ' "$TARGET_CONTINUE/config.yaml"
  } > "$TARGET_CONTINUE/config.local.yaml"

  printf 'Generated MLX local config: %s\n' "$TARGET_CONTINUE/config.local.yaml"
  printf 'Selected MLX model: %s\n' "$recommended_mlx_model"
  printf 'MLX API base: %s\n' "$MLX_API_BASE"
fi

if [ "$MODEL_LANES" = true ]; then
  {
    printf '# Local-only Continue config generated by install-continue-pack.shared.sh.\n'
    printf '# Do not commit this file. It contains workflow-specific model lane choices.\n'
    printf '# Only the WRITE SAFE lane has edit/apply roles. Validate it before real code changes.\n'
    awk '
      function print_model_lanes() {
        print "models:"
        print "  - name: 1 - WRITE SAFE - qwen3.5:9b"
        print "    provider: ollama"
        print "    model: qwen3.5:9b"
        print "    roles:"
        print "      - chat"
        print "      - edit"
        print "      - apply"
        print "    capabilities:"
        print "      - tool_use"
        print "    defaultCompletionOptions:"
        print "      temperature: 0.1"
        print "      contextLength: 16384"
        print "      maxTokens: 2048"
        print "      keepAlive: " ENVIRON["CONTINUE_KEEP_ALIVE_SECONDS"]
        print "  - name: 2 - PLAN ONLY - qwen3.5:9b"
        print "    provider: ollama"
        print "    model: qwen3.5:9b"
        print "    roles:"
        print "      - chat"
        print "    capabilities:"
        print "      - tool_use"
        print "    defaultCompletionOptions:"
        print "      temperature: 0.2"
        print "      contextLength: 16384"
        print "      maxTokens: 2048"
        print "      keepAlive: " ENVIRON["CONTINUE_KEEP_ALIVE_SECONDS"]
        print "  - name: 3 - DEEP REVIEW - qwen3.5:9b"
        print "    provider: ollama"
        print "    model: qwen3.5:9b"
        print "    roles:"
        print "      - chat"
        print "    capabilities:"
        print "      - tool_use"
        print "    defaultCompletionOptions:"
        print "      temperature: 0.2"
        print "      contextLength: 16384"
        print "      maxTokens: 2048"
        print "      keepAlive: " ENVIRON["CONTINUE_KEEP_ALIVE_SECONDS"]
        print "  - name: Ollama Nomic Embed"
        print "    provider: ollama"
        print "    model: nomic-embed-text"
        print "    roles:"
        print "      - embed"
      }
      /^models:[[:space:]]*$/ {
        print_model_lanes()
        skip = 1
        next
      }
      skip && /^[A-Za-z_][A-Za-z0-9_-]*:/ {
        skip = 0
      }
      !skip { print }
    ' "$TARGET_CONTINUE/config.yaml"
  } > "$TARGET_CONTINUE/config.local.yaml"

  printf 'Generated model lanes config: %s\n' "$TARGET_CONTINUE/config.local.yaml"
fi

if [ "$GLOBAL_CONFIG" = true ]; then
  if [ "$SHARED_ASSETS" = true ]; then
    config_root="$SHARED_ASSETS_PATH"
  else
    config_root="$TARGET_CONTINUE"
  fi

  if [ -f "$config_root/config.local.yaml" ]; then
    source_config="$config_root/config.local.yaml"
  else
    source_config="$config_root/config.yaml"
  fi

  if [ ! -f "$source_config" ]; then
    printf 'Cannot write global config because source config is missing: %s\n' "$source_config" >&2
    exit 1
  fi

  mkdir -p "$(dirname "$GLOBAL_CONFIG_PATH")"

  if [ -f "$GLOBAL_CONFIG_PATH" ]; then
    cp "$GLOBAL_CONFIG_PATH" "$BACKUP_GLOBAL_CONFIG"
    printf 'Backed up existing global Continue config to %s\n' "$BACKUP_GLOBAL_CONFIG"
  fi

  file_uri_base="file://$config_root"

  {
    printf '# Global Continue config generated by install-continue-pack.shared.sh.\n'
    printf '# This file points Continue at reusable pack assets.\n'
    printf '# The rules section is omitted by default to avoid duplicate rules when the opened repository also has .continue/rules.\n'
    printf '# Regenerate it when you move or reinstall the referenced asset folder.\n'
    sed "s#file://./#${file_uri_base}/#g" "$source_config" |
      if [ "$GLOBAL_CONFIG_INCLUDE_RULES" = true ]; then
        cat
      else
        awk '
          /^rules:[[:space:]]*$/ {
            skip = 1
            next
          }
          skip && /^[A-Za-z_][A-Za-z0-9_-]*:/ {
            skip = 0
          }
          !skip { print }
        '
      fi |
      awk -v api_base="$GLOBAL_CONFIG_API_BASE" '
        function maybe_add_api_base() {
          if (in_ollama_model && !saw_api_base && api_base != "") {
            print "    apiBase: " api_base
          }
        }
        /^[[:space:]]{2}-[[:space:]]+name:/ {
          maybe_add_api_base()
          in_model = 1
          in_ollama_model = 0
          saw_api_base = 0
        }
        in_model && /^[[:space:]]{4}provider:[[:space:]]*ollama[[:space:]]*$/ {
          in_ollama_model = 1
        }
        in_ollama_model && /^[[:space:]]{4}apiBase:/ {
          if (api_base != "") {
            print "    apiBase: " api_base
            saw_api_base = 1
            next
          }
        }
        in_model && /^[A-Za-z_][A-Za-z0-9_-]*:/ {
          maybe_add_api_base()
          in_model = 0
          in_ollama_model = 0
          saw_api_base = 0
        }
        { print }
        END {
          maybe_add_api_base()
        }
      '
  } > "$GLOBAL_CONFIG_PATH"

  printf 'Updated global Continue config: %s\n' "$GLOBAL_CONFIG_PATH"
fi

if [ "$SHARED_ASSETS" = true ]; then
  printf 'Installed shared assets to %s\n' "$SHARED_ASSETS_PATH"
else
  printf 'Installed .continue to %s\n' "$TARGET_CONTINUE"
fi

printf 'Install complete.\n'
