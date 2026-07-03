#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if ! command -v pwsh >/dev/null 2>&1; then
  cat >&2 <<'EOF'
PowerShell 7+ is required to run pack tests.

Install it, then run this command again:
https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-linux

Direct command after installation:
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/test-pack.ps1
EOF
  exit 127
fi

pwsh -NoProfile -ExecutionPolicy Bypass -File "$REPO_ROOT/scripts/test-pack.ps1" "$@"
