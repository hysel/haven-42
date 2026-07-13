#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/test-agent-cli-surface-models.shared.sh" \
  --surface-key "aider-cli" \
  "$@"
