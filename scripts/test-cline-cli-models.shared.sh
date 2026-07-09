#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_REPO="$REPO_ROOT/runtime-validation-output/sample-repositories/python-api"
OUTPUT_PATH=""
CLINE_COMMAND="cline"
CLINE_ARGS_TEMPLATE='--json "{Prompt}"'
MODEL_ARGS_TEMPLATE=""
TIMEOUT_SECONDS=600
INCLUDE_WRITE_SMOKE=false
ALLOW_NON_GENERATED_TARGET=false
DRY_RUN=false
MODELS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-repo|-TargetRepo)
      TARGET_REPO="$2"
      shift 2
      ;;
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --cline-command|-ClineCommand)
      CLINE_COMMAND="$2"
      shift 2
      ;;
    --cline-arguments-template|-ClineArgumentsTemplate)
      CLINE_ARGS_TEMPLATE="$2"
      shift 2
      ;;
    --model-argument-template|-ModelArgumentTemplate)
      MODEL_ARGS_TEMPLATE="$2"
      shift 2
      ;;
    --timeout-seconds|-TimeoutSeconds)
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --include-write-smoke|-IncludeWriteSmoke)
      INCLUDE_WRITE_SMOKE=true
      shift
      ;;
    --allow-non-generated-target|-AllowNonGeneratedTarget)
      ALLOW_NON_GENERATED_TARGET=true
      shift
      ;;
    --dry-run|-DryRun)
      DRY_RUN=true
      shift
      ;;
    --model|-Model)
      MODELS+=("$2")
      shift 2
      ;;
    --models|-Models)
      IFS=',' read -r -a split_models <<< "$2"
      for model in "${split_models[@]}"; do
        MODELS+=("$(printf '%s' "$model" | sed 's/^ *//;s/ *$//')")
      done
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [ -z "$OUTPUT_PATH" ]; then
  OUTPUT_PATH="$REPO_ROOT/runtime-validation-output/cline-cli-model-tests-$(date '+%Y%m%d-%H%M%S').json"
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
    *)
      printf 'Write smoke tests are allowed only for generated disposable samples unless --allow-non-generated-target is set.\n' >&2
      exit 1
      ;;
  esac
fi

if [ "$DRY_RUN" != true ] && ! command -v "$CLINE_COMMAND" >/dev/null 2>&1; then
  printf 'Cline command was not found: %s. Install with npm i -g cline or pass --cline-command.\n' "$CLINE_COMMAND" >&2
  exit 1
fi

if [ "${#MODELS[@]}" -eq 0 ]; then
  if [ -f "$REPO_ROOT/config/evidence-catalog.tsv" ]; then
    while IFS=$'\t' read -r area subject surface os model status evidence notes; do
      [ "$area" = "area" ] && continue
      case "$surface" in
        *Cline*) [ -n "$model" ] && [ "$model" != "N/A" ] && MODELS+=("$model") ;;
      esac
    done < "$REPO_ROOT/config/evidence-catalog.tsv"
  fi
fi

if [ "${#MODELS[@]}" -eq 0 ]; then
  MODELS+=("qwen3-coder:30b")
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"

printf '[1/7] Preparing Cline CLI model test run...\n' >&2
printf '[2/7] Target repository: generated sample %s\n' "$(basename "$TARGET_REPO")" >&2
printf '[3/7] Candidate models: %s\n' "${MODELS[*]}" >&2
printf '[4/7] Cline command: %s\n' "$CLINE_COMMAND" >&2

read_prompt='Use tools to inspect the opened repository root. Do not modify files. Do not create files. Do not run package installation. Do not guess. Return only the actual top-level files and folders inspected, the project type, key source and test files inspected, risks or missing information, and a failure signal. If tools are unavailable, say TOOLS_UNAVAILABLE.'
write_prompt='Use approved write mode for this disposable smoke test only. Modify the existing README.md by adding exactly this final line: Cline CLI approved-write smoke test passed. Do not modify any other files. Do not create new files. After editing, report the changed file and stop. Do not commit.'

json_results=()
index=0
for model in "${MODELS[@]}"; do
  index=$((index + 1))
  printf '[5/7] Testing model %s/%s: %s\n' "$index" "${#MODELS[@]}" "$model" >&2
  read_status='failed'
  write_status='not-run'
  failures='none'

  prompt="$read_prompt"
  args="${CLINE_ARGS_TEMPLATE//\{Prompt\}/$prompt}"
  args="${args//\{Model\}/$model}"
  args="${args//\{TargetRepo\}/$TARGET_REPO}"
  model_args="${MODEL_ARGS_TEMPLATE//\{Model\}/$model}"

  if [ "$DRY_RUN" = true ]; then
    output='DRY_RUN README.md pyproject.toml app/main.py'
    exit_code=0
  else
    set +e
    output=$(cd "$TARGET_REPO" && timeout "$TIMEOUT_SECONDS" sh -c "$CLINE_COMMAND $model_args $args" 2>&1)
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
    args="${CLINE_ARGS_TEMPLATE//\{Prompt\}/$prompt}"
    args="${args//\{Model\}/$model}"
    args="${args//\{TargetRepo\}/$TARGET_REPO}"
    model_args="${MODEL_ARGS_TEMPLATE//\{Model\}/$model}"
    if [ "$DRY_RUN" = true ]; then
      write_status='write-smoke-validated'
    else
      set +e
      (cd "$TARGET_REPO" && timeout "$TIMEOUT_SECONDS" sh -c "$CLINE_COMMAND $model_args $args" >/tmp/cline-cli-write.out 2>&1)
      write_exit=$?
      set -e
      changed_files="$(cd "$TARGET_REPO" && git diff --name-only)"
      if [ "$write_exit" -eq 0 ] && [ "$changed_files" = 'README.md' ] && (cd "$TARGET_REPO" && git diff --check >/dev/null) && tail -n 1 "$TARGET_REPO/README.md" | grep -qx 'Cline CLI approved-write smoke test passed.'; then
        write_status='write-smoke-validated'
      else
        failures='WRITE_VALIDATION_FAILED'
      fi
      (cd "$TARGET_REPO" && git restore README.md >/dev/null 2>&1 || true)
    fi
  fi

  json_results+=("{\"Model\":\"$model\",\"Surface\":\"Cline CLI\",\"Target\":\"generated-sample\",\"ReadStatus\":\"$read_status\",\"WriteStatus\":\"$write_status\",\"FailureSignal\":\"$failures\"}")
  printf '%s: read=%s, write=%s, failures=%s\n' "$model" "$read_status" "$write_status" "$failures" >&2
done

printf '[6/7] Writing sanitized report...\n' >&2
{
  printf '{\n'
  printf '  "Surface": "Cline CLI",\n'
  printf '  "Target": "generated-sample",\n'
  printf '  "IncludeWriteSmoke": %s,\n' "$INCLUDE_WRITE_SMOKE"
  printf '  "DryRun": %s,\n' "$DRY_RUN"
  printf '  "Results": [\n'
  for i in "${!json_results[@]}"; do
    comma=','
    [ "$i" -eq $((${#json_results[@]} - 1)) ] && comma=''
    printf '    %s%s\n' "${json_results[$i]}" "$comma"
  done
  printf '  ],\n'
  printf '  "Notes": "Report is sanitized: target paths, raw prompts, stdout, stderr, and private endpoints are intentionally omitted."\n'
  printf '}\n'
} > "$OUTPUT_PATH"
printf '[7/7] Report written to %s\n' "$OUTPUT_PATH" >&2
