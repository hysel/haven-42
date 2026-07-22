#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if command -v python3 >/dev/null 2>&1; then PYTHON_COMMAND="python3"; elif command -v python >/dev/null 2>&1; then PYTHON_COMMAND="python"; else printf 'Python 3 is required for native capability discovery.\n' >&2; exit 1; fi
exec "$PYTHON_COMMAND" "$SCRIPT_DIR/discover-capability-availability.py" --capability-registry "$REPO_ROOT/config/capabilities.json" --provider-registry "$REPO_ROOT/config/providers.json" --engine-registry "$REPO_ROOT/config/inference-engine-registry.json" "$@"
