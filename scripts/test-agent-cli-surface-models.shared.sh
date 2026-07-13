#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SURFACE_NAME=""
SURFACE_KEY="aider-cli"
TARGET_REPO="$REPO_ROOT/runtime-validation-output/sample-repositories/python-api"
OUTPUT_PATH=""
OLLAMA_BASE_URL="http://127.0.0.1:11434"
AGENT_COMMAND=""
AGENT_ARGS_TEMPLATE=""
MODEL_ARGS_TEMPLATE=""
INSTALL_HINT=""
TIMEOUT_SECONDS=600
INCLUDE_WRITE_SMOKE=false
ALLOW_NON_GENERATED_TARGET=false
DRY_RUN=false
UNLOAD_AFTER_EACH=false
MODELS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --surface-name|-SurfaceName) SURFACE_NAME="$2"; shift 2 ;;
    --surface-key|-SurfaceKey) SURFACE_KEY="$2"; shift 2 ;;
    --target-repo|-TargetRepo) TARGET_REPO="$2"; shift 2 ;;
    --output-path|-OutputPath) OUTPUT_PATH="$2"; shift 2 ;;
    --ollama-base-url|-OllamaBaseUrl) OLLAMA_BASE_URL="$2"; shift 2 ;;
    --agent-command|-AgentCommand) AGENT_COMMAND="$2"; shift 2 ;;
    --agent-arguments-template|-AgentArgumentsTemplate) AGENT_ARGS_TEMPLATE="$2"; shift 2 ;;
    --model-argument-template|-ModelArgumentTemplate) MODEL_ARGS_TEMPLATE="$2"; shift 2 ;;
    --install-hint|-InstallHint) INSTALL_HINT="$2"; shift 2 ;;
    --timeout-seconds|-TimeoutSeconds) TIMEOUT_SECONDS="$2"; shift 2 ;;
    --include-write-smoke|-IncludeWriteSmoke) INCLUDE_WRITE_SMOKE=true; shift ;;
    --allow-non-generated-target|-AllowNonGeneratedTarget) ALLOW_NON_GENERATED_TARGET=true; shift ;;
    --dry-run|-DryRun) DRY_RUN=true; shift ;;
    --unload-after-each|-UnloadAfterEach) UNLOAD_AFTER_EACH=true; shift ;;
    --model|-Model) MODELS+=("$2"); shift 2 ;;
    --models|-Models)
      IFS=',' read -r -a split_models <<< "$2"
      for model in "${split_models[@]}"; do MODELS+=("$(printf '%s' "$model" | sed 's/^ *//;s/ *$//')"); done
      shift 2
      ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

load_surface_defaults() {
  defaults_path="$REPO_ROOT/config/agent-cli-surface-defaults.json"
  [ -f "$defaults_path" ] || return 0

  defaults_text=""
  for python_command in python3 python; do
    command -v "$python_command" >/dev/null 2>&1 || continue
    if defaults_text="$("$python_command" -c 'import json, sys
path, key = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as handle:
    data = json.load(handle)
surface = next((item for item in data.get("surfaces", []) if item.get("surfaceKey") == key), None)
if surface:
    fields = ("surfaceName", "agentCommand", "agentArgumentsTemplate", "modelArgumentTemplate", "installHint")
    print("\x1f".join(str(surface.get(field) or "") for field in fields))' "$defaults_path" "$SURFACE_KEY" 2>/dev/null)"; then
      [ -n "$defaults_text" ] && break
    fi
    defaults_text=""
  done

  if [ -z "$defaults_text" ]; then
    surface_block="$(awk -v key="\"surfaceKey\": \"$SURFACE_KEY\"" 'index($0, key) { found=1 } found { print; if ($0 ~ /^    },?$/) exit }' "$defaults_path")"
    if [ -n "$surface_block" ]; then
      default_surface_name="$(printf '%s\n' "$surface_block" | sed -n 's/^[[:space:]]*"surfaceName": "\(.*\)",\?$/\1/p' | head -n 1 | sed 's/\\"/"/g; s/\\\\/\\/g')"
      default_agent_command="$(printf '%s\n' "$surface_block" | sed -n 's/^[[:space:]]*"agentCommand": "\(.*\)",\?$/\1/p' | head -n 1 | sed 's/\\"/"/g; s/\\\\/\\/g')"
      default_agent_args_template="$(printf '%s\n' "$surface_block" | sed -n 's/^[[:space:]]*"agentArgumentsTemplate": "\(.*\)",\?$/\1/p' | head -n 1 | sed 's/\\"/"/g; s/\\\\/\\/g')"
      default_model_args_template="$(printf '%s\n' "$surface_block" | sed -n 's/^[[:space:]]*"modelArgumentTemplate": "\(.*\)",\?$/\1/p' | head -n 1 | sed 's/\\"/"/g; s/\\\\/\\/g')"
      default_install_hint="$(printf '%s\n' "$surface_block" | sed -n 's/^[[:space:]]*"installHint": "\(.*\)"$/\1/p' | head -n 1 | sed 's/\\"/"/g; s/\\\\/\\/g')"
      defaults_text="$default_surface_name"$'\037'"$default_agent_command"$'\037'"$default_agent_args_template"$'\037'"$default_model_args_template"$'\037'"$default_install_hint"
    fi
  fi

  [ -n "$defaults_text" ] || return 0
  IFS=$'\037' read -r default_surface_name default_agent_command default_agent_args_template default_model_args_template default_install_hint <<< "$defaults_text"

  [ -z "$SURFACE_NAME" ] && SURFACE_NAME="$default_surface_name"
  [ -z "$AGENT_COMMAND" ] && AGENT_COMMAND="$default_agent_command"
  [ -z "$AGENT_ARGS_TEMPLATE" ] && AGENT_ARGS_TEMPLATE="$default_agent_args_template"
  [ -z "$MODEL_ARGS_TEMPLATE" ] && MODEL_ARGS_TEMPLATE="$default_model_args_template"
  [ -z "$INSTALL_HINT" ] && INSTALL_HINT="$default_install_hint"
}

load_surface_defaults

[ -z "$SURFACE_NAME" ] && SURFACE_NAME="Aider CLI"
[ -z "$AGENT_COMMAND" ] && AGENT_COMMAND="aider"
[ -z "$AGENT_ARGS_TEMPLATE" ] && AGENT_ARGS_TEMPLATE='--message "{Prompt}" --yes-always --no-auto-commits'
[ -z "$MODEL_ARGS_TEMPLATE" ] && MODEL_ARGS_TEMPLATE='--model "ollama_chat/{Model}"'
[ -z "$INSTALL_HINT" ] && INSTALL_HINT="Install or configure the CLI, or pass --agent-command."

if [ -z "$OUTPUT_PATH" ]; then
  OUTPUT_PATH="$REPO_ROOT/runtime-validation-output/$SURFACE_KEY-model-tests-$(date '+%Y%m%d-%H%M%S').json"
fi

if [ ! -d "$TARGET_REPO" ]; then
  "$REPO_ROOT/scripts/generate-sample-repositories.shared.sh" --force >/dev/null
fi

if [ ! -d "$TARGET_REPO" ]; then
  printf 'TargetRepo does not exist: %s\n' "$TARGET_REPO" >&2
  exit 1
fi

if [ "$INCLUDE_WRITE_SMOKE" = true ] && [ "$ALLOW_NON_GENERATED_TARGET" != true ]; then
  case "$TARGET_REPO" in
    *runtime-validation-output/sample-repositories*) ;;
    *) printf 'Write smoke tests are allowed only for generated disposable samples unless --allow-non-generated-target is set.\n' >&2; exit 1 ;;
  esac
fi

if [ "$DRY_RUN" != true ] && ! command -v "$AGENT_COMMAND" >/dev/null 2>&1; then
  printf '%s command was not found: %s. %s\n' "$SURFACE_NAME" "$AGENT_COMMAND" "$INSTALL_HINT" >&2
  exit 1
fi

if [ "${#MODELS[@]}" -eq 0 ]; then
  if [ -f "$REPO_ROOT/config/evidence-catalog.tsv" ]; then
    while IFS=$'\t' read -r area subject surface os model status evidence notes; do
      [ "$area" = "area" ] && continue
      case "$surface" in
        *"$SURFACE_NAME"*) [ -n "$model" ] && [ "$model" != "N/A" ] && MODELS+=("$model") ;;
      esac
    done < "$REPO_ROOT/config/evidence-catalog.tsv"
  fi
fi

if [ "${#MODELS[@]}" -eq 0 ]; then MODELS+=("qwen3.5:9b"); fi

unload_model() {
  model_name="$1"
  base_url="${OLLAMA_BASE_URL%/}"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS -X POST "$base_url/api/chat" -H 'Content-Type: application/json' -d "{\"model\":\"$model_name\",\"messages\":[],\"keep_alive\":0,\"stream\":false}" >/dev/null
  else
    return 1
  fi
}

initialize_disposable_git_baseline() {
  run_dir="$1"
  case "$run_dir" in *runtime-validation-output/sample-repositories*) ;; *) return 0 ;; esac
  if [ ! -d "$run_dir/.git" ]; then git -C "$run_dir" init >/dev/null; fi
  git -C "$run_dir" config core.autocrlf false >/dev/null
  git -C "$run_dir" config core.eol lf >/dev/null
  if ! git -C "$run_dir" rev-parse --verify HEAD >/dev/null 2>&1; then
    git -C "$run_dir" add . >/dev/null
    git -C "$run_dir" -c user.name="Local Agent Validation" -c user.email="local-agent-validation@example.invalid" commit -m "Initial generated sample" >/dev/null
    return 0
  fi
  if [ -n "$(git -C "$run_dir" status --short)" ]; then
    git -C "$run_dir" restore . >/dev/null
    git -C "$run_dir" clean -fd >/dev/null
  fi
}

mkdir -p "$(dirname "$OUTPUT_PATH")"
initialize_disposable_git_baseline "$TARGET_REPO"

printf '[1/7] Preparing %s model test run...\n' "$SURFACE_NAME" >&2
printf '[2/7] Target repository: generated sample %s\n' "$(basename "$TARGET_REPO")" >&2
printf '[3/7] Candidate models: %s\n' "${MODELS[*]}" >&2
printf '[4/7] Agent command: %s\n' "$AGENT_COMMAND" >&2

read_prompt='Use tools to inspect the opened repository root. Do not modify files. Do not create files. Do not run package installation. Do not guess. Return only the actual top-level files and folders inspected, the project type, key source and test files inspected, risks or missing information, and a failure signal. If tools are unavailable, say TOOLS_UNAVAILABLE.'
write_line="$SURFACE_NAME approved-write smoke test passed."
write_prompt="Use approved write mode for this disposable smoke test only. Modify the existing README.md by adding exactly this final line: $write_line Do not modify any other files. Do not create new files. After editing, report the changed file and stop. Do not commit."

json_results=()
index=0
for model in "${MODELS[@]}"; do
  index=$((index + 1))
  printf '[5/7] Testing model %s/%s: %s\n' "$index" "${#MODELS[@]}" "$model" >&2
  read_status='failed'
  write_status='not-run'
  failures='none'

  prompt="$read_prompt"
  args="${AGENT_ARGS_TEMPLATE//\{Prompt\}/$prompt}"
  args="${args//\{Model\}/$model}"
  args="${args//\{TargetRepo\}/$TARGET_REPO}"
  model_args="${MODEL_ARGS_TEMPLATE//\{Model\}/$model}"

  if [ "$DRY_RUN" = true ]; then
    output='DRY_RUN README.md pyproject.toml app/main.py'
    exit_code=0
  else
    set +e
    output=$(cd "$TARGET_REPO" && timeout "$TIMEOUT_SECONDS" sh -c "$AGENT_COMMAND $model_args $args" 2>&1)
    exit_code=$?
    set -e
  fi

  if [ "$exit_code" -eq 0 ] && printf '%s' "$output" | grep -q 'README.md' && printf '%s' "$output" | grep -q 'pyproject.toml'; then
    read_status='read-only-tool-validated'
  else
    failures='READ_VALIDATION_FAILED'
  fi

  if [ "$INCLUDE_WRITE_SMOKE" = true ]; then
    prompt="$write_prompt"
    args="${AGENT_ARGS_TEMPLATE//\{Prompt\}/$prompt}"
    args="${args//\{Model\}/$model}"
    args="${args//\{TargetRepo\}/$TARGET_REPO}"
    model_args="${MODEL_ARGS_TEMPLATE//\{Model\}/$model}"
    if [ "$DRY_RUN" = true ]; then
      write_status='write-smoke-validated'
    else
      set +e
      (cd "$TARGET_REPO" && timeout "$TIMEOUT_SECONDS" sh -c "$AGENT_COMMAND $model_args $args" >/tmp/agent-cli-write.out 2>&1)
      write_exit=$?
      set -e
      changed_files="$(cd "$TARGET_REPO" && git diff --name-only)"
      if [ "$write_exit" -eq 0 ] && [ "$changed_files" = 'README.md' ] && (cd "$TARGET_REPO" && git diff --check >/dev/null) && tail -n 1 "$TARGET_REPO/README.md" | grep -qx "$write_line"; then
        write_status='write-smoke-validated'
      else
        failures='WRITE_VALIDATION_FAILED'
      fi
      (cd "$TARGET_REPO" && git restore README.md >/dev/null 2>&1 || true)
    fi
  fi

  if [ "$UNLOAD_AFTER_EACH" = true ] && [ "$DRY_RUN" != true ]; then
    printf '[6/7] Unloading %s from Ollama...\n' "$model" >&2
    unload_model "$model" || failures="${failures},UNLOAD_FAILED"
  fi
  json_results+=("{\"Model\":\"$model\",\"Surface\":\"$SURFACE_NAME\",\"Target\":\"generated-sample\",\"ReadStatus\":\"$read_status\",\"WriteStatus\":\"$write_status\",\"FailureSignal\":\"$failures\"}")
  printf '%s: read=%s, write=%s, failures=%s\n' "$model" "$read_status" "$write_status" "$failures" >&2
done

printf '[6/7] Writing sanitized report...\n' >&2
{
  printf '{\n'
  printf '  "Surface": "%s",\n' "$SURFACE_NAME"
  printf '  "SurfaceKey": "%s",\n' "$SURFACE_KEY"
  printf '  "Target": "generated-sample",\n'
  printf '  "IncludeWriteSmoke": %s,\n' "$INCLUDE_WRITE_SMOKE"
  printf '  "UnloadAfterEach": %s,\n' "$UNLOAD_AFTER_EACH"
  printf '  "DryRun": %s,\n' "$DRY_RUN"
  printf '  "Results": [\n'
  for i in "${!json_results[@]}"; do
    comma=','; [ "$i" -eq $((${#json_results[@]} - 1)) ] && comma=''
    printf '    %s%s\n' "${json_results[$i]}" "$comma"
  done
  printf '  ],\n'
  printf '  "Notes": "Report is sanitized: target paths, raw prompts, stdout, stderr, and private endpoints are intentionally omitted."\n'
  printf '}\n'
} > "$OUTPUT_PATH"
printf '[7/7] Report written to %s\n' "$OUTPUT_PATH" >&2
