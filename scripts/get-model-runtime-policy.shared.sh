#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
POLICY_PATH="${1:-}"

if [ -z "$POLICY_PATH" ]; then
  if [ -f "$REPO_ROOT/config/model-runtime-policy.local.json" ]; then
    POLICY_PATH="$REPO_ROOT/config/model-runtime-policy.local.json"
  else
    POLICY_PATH="$REPO_ROOT/config/model-runtime-policy.sample.json"
  fi
fi

[ -f "$POLICY_PATH" ] || { printf 'Model runtime policy does not exist: %s\n' "$POLICY_PATH" >&2; exit 1; }

POLICY_PYTHON=""
for candidate in python3 python py py.exe; do
  if command -v "$candidate" >/dev/null 2>&1; then
    POLICY_PYTHON="$candidate"
    break
  fi
done
[ -n "$POLICY_PYTHON" ] || { printf 'python3 or python is required to read the model runtime policy.\n' >&2; exit 1; }

"$POLICY_PYTHON" - "$POLICY_PATH" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
if policy.get("schemaVersion") != 1:
    raise SystemExit("Unsupported model runtime policy schema.")
if policy.get("residencyMode") not in {"unload-after-run", "keep-loaded"}:
    raise SystemExit("residencyMode must be unload-after-run or keep-loaded.")
try:
    max_resident = int(policy["maxResidentModels"])
    keep_alive = int(policy["preloadKeepAliveMinutes"])
except (KeyError, TypeError, ValueError) as exc:
    raise SystemExit("maxResidentModels and preloadKeepAliveMinutes must be positive integers.") from exc
if max_resident < 1 or keep_alive < 1:
    raise SystemExit("maxResidentModels and preloadKeepAliveMinutes must be positive integers.")
print(f'{policy["residencyMode"]}\t{max_resident}\t{keep_alive}')
PY
