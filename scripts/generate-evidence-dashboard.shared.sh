#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EVIDENCE_CATALOG="$REPO_ROOT/config/evidence-catalog.tsv"
SURFACE_MATRIX="$REPO_ROOT/config/agent-surface-capabilities.json"
SURFACE_SOLUTIONS="$REPO_ROOT/config/agent-surface-solutions.json"
OUTPUT_PATH=""
MARKDOWN_OUTPUT_PATH=""
AS_JSON=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --evidence-catalog-path|-EvidenceCatalogPath)
      EVIDENCE_CATALOG="$2"
      shift 2
      ;;
    --surface-matrix-path|-SurfaceMatrixPath)
      SURFACE_MATRIX="$2"
      shift 2
      ;;
    --surface-solution-path|-SurfaceSolutionPath)
      SURFACE_SOLUTIONS="$2"
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
  args=(-EvidenceCatalogPath "$EVIDENCE_CATALOG" -SurfaceMatrixPath "$SURFACE_MATRIX" -SurfaceSolutionPath "$SURFACE_SOLUTIONS")
  [ -n "$OUTPUT_PATH" ] && args+=(-OutputPath "$OUTPUT_PATH")
  [ -n "$MARKDOWN_OUTPUT_PATH" ] && args+=(-MarkdownOutputPath "$MARKDOWN_OUTPUT_PATH")
  [ "$AS_JSON" -eq 1 ] && args+=(-AsJson)
  exec pwsh -NoProfile -ExecutionPolicy Bypass -File "$SCRIPT_DIR/generate-evidence-dashboard.ps1" "${args[@]}"
fi

printf '# Evidence Dashboard\n\n'
printf 'PowerShell is required for full dashboard generation on this platform.\n'
