#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_REPO="$PWD"
CONFIG_PATH=""
CONTEXT_PATH=""
APPEND_SUMMARY=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-repo|-TargetRepo)
      TARGET_REPO="$2"
      shift 2
      ;;
    --config-path|-ConfigPath)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --context-path|-ContextPath)
      CONTEXT_PATH="$2"
      shift 2
      ;;
    --append-summary|-AppendSummary)
      APPEND_SUMMARY=true
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [ ! -d "$TARGET_REPO" ]; then
  printf 'Target repository path does not exist: %s\n' "$TARGET_REPO" >&2
  exit 1
fi

if [ -z "$CONFIG_PATH" ]; then
  if [ -f "$PACK_ROOT/.continue/config.local.yaml" ]; then
    CONFIG_PATH="$PACK_ROOT/.continue/config.local.yaml"
  else
    CONFIG_PATH="$PACK_ROOT/.continue/config.yaml"
  fi
fi

if [ ! -f "$CONFIG_PATH" ]; then
  printf 'Continue config path does not exist: %s\n' "$CONFIG_PATH" >&2
  exit 1
fi

preflight_local_ollama_config() {
  config_path="$1"
  grep -q "provider:[[:space:]]*ollama" "$config_path" || return 0
  api_base="$(awk '/apiBase:[[:space:]]*/ { print $2; exit }' "$config_path")"
  [ -n "$api_base" ] || return 0
  api_base="${api_base%/}"
  if ! command -v curl >/dev/null 2>&1; then
    printf 'Local Ollama API preflight failed. curl is required to check local model server reachability.\n' >&2
    exit 1
  fi
  if ! curl --fail --silent --show-error --max-time 15 "$api_base/api/tags" >/dev/null 2>&1; then
    printf 'Local Ollama API preflight failed. Confirm the local model server is reachable before running runtime validation.\n' >&2
    exit 1
  fi
}

preflight_local_ollama_config "$CONFIG_PATH"

RUN_ROOT="$PACK_ROOT/runtime-validation-output/$(date '+%Y%m%d-%H%M%S')"
mkdir -p "$RUN_ROOT"

if [ -z "$CONTEXT_PATH" ]; then
  CONTEXT_PATH="$RUN_ROOT/runtime-context.md"
  "$PACK_ROOT/scripts/generate-runtime-context.shared.sh" --target-repo "$TARGET_REPO" --output-path "$CONTEXT_PATH"
fi

if [ ! -f "$CONTEXT_PATH" ]; then
  printf 'Runtime context path does not exist: %s\n' "$CONTEXT_PATH" >&2
  exit 1
fi

SUMMARY_PATH="$RUN_ROOT/runtime-validation-summary-draft.md"
{
  printf '## Runtime Validation Run - %s\n\n' "$(date '+%Y-%m-%d %H:%M')"
  printf 'Repository type: TODO sanitize repository type\n'
  printf 'Model setup: TODO record model setup\n'
  printf 'Continue surface: Continue CLI through npx @continuedev/cli\n'
  printf 'Config used: TODO confirm sanitized config path\n\n'
  printf 'Raw outputs were written to an ignored local folder:\n\n%s\n\n' "$RUN_ROOT"
  printf 'Runtime context used:\n\n%s\n\n' "$CONTEXT_PATH"
  printf 'Do not commit raw outputs until they have been reviewed and sanitized.\n\n'
} > "$SUMMARY_PATH"

if ! command -v npx >/dev/null 2>&1; then
  printf 'npx was not found. Runtime validation summary template was created at %s\n' "$SUMMARY_PATH" >&2
  exit 0
fi

PROMPTS=(
  "repository-discovery"
  "architecture-review"
  "code-review"
  "implementation-plan"
  "bug-investigation"
  "security-review"
  "performance-review"
  "documentation"
  "ai-framework-self-review"
  "refactoring-planner"
  "product-manager"
  "release-readiness"
)

for workflow in "${PROMPTS[@]}"; do
  prompt_path="$PACK_ROOT/.continue/prompts/$workflow.md"
  output_path="$RUN_ROOT/$workflow.md"
  verification_path="$RUN_ROOT/$workflow.verification.txt"
  [ -f "$prompt_path" ] || continue
  (
    cd "$TARGET_REPO"
    npx @continuedev/cli \
      --config "$CONFIG_PATH" \
      --prompt "$prompt_path" \
      --prompt "$CONTEXT_PATH" \
      --readonly \
      -p "Use the supplied runtime repository context. Do not call tools. Produce final review text only."
  ) > "$output_path" 2>&1 || true

  "$PACK_ROOT/scripts/verify-runtime-output.shared.sh" \
    --output-path "$output_path" \
    --context-path "$CONTEXT_PATH" \
    --workflow-name "$workflow" > "$verification_path" 2>&1 || true
done

if [ "$APPEND_SUMMARY" = true ]; then
  cat "$SUMMARY_PATH" >> "$PACK_ROOT/docs/runtime-validation.md"
  printf 'Appended sanitized summary template to %s\n' "$PACK_ROOT/docs/runtime-validation.md"
fi

printf 'Runtime validation outputs written to %s\n' "$RUN_ROOT"
printf 'Review and sanitize %s before committing runtime validation notes.\n' "$SUMMARY_PATH"
