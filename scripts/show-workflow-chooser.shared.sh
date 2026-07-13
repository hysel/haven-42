#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM="linux"
OUTPUT_PATH=""
MARKDOWN_OUTPUT_PATH=""
AS_JSON=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --platform|-Platform)
      PLATFORM="$2"
      shift 2
      ;;
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --markdown-output-path|-MarkdownOutputPath)
      MARKDOWN_OUTPUT_PATH="$2"
      shift 2
      ;;
    --as-json|-AsJson)
      AS_JSON=1
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if command -v pwsh >/dev/null 2>&1; then
  args=(-Platform "$PLATFORM")
  [ -n "$OUTPUT_PATH" ] && args+=(-OutputPath "$OUTPUT_PATH")
  [ -n "$MARKDOWN_OUTPUT_PATH" ] && args+=(-MarkdownOutputPath "$MARKDOWN_OUTPUT_PATH")
  [ "$AS_JSON" -eq 1 ] && args+=(-AsJson)
  exec pwsh -NoProfile -ExecutionPolicy Bypass -File "$SCRIPT_DIR/show-workflow-chooser.ps1" "${args[@]}"
fi

printf '# Workflow Chooser\n\n'
printf 'PowerShell is required for full chooser generation on this platform.\n'
