#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; exec "$SCRIPT_DIR/invoke-local-text-capability.shared.sh" "$@"
