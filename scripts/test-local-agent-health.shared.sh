#!/usr/bin/env bash
set -uo pipefail

TARGET_REPO=""
OUTPUT_PATH=""
SKIP_OLLAMA=0
AS_JSON=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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
    --skip-ollama|-SkipOllama)
      SKIP_OLLAMA=1
      shift
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

[ -n "$TARGET_REPO" ] || TARGET_REPO="$REPO_ROOT"

STATUS="pass"
CHECKS=""

add_check() {
  id="$1"
  name="$2"
  status="$3"
  message="$4"

  [ "$status" = "fail" ] && STATUS="fail"
  if [ "$status" = "warn" ] && [ "$STATUS" = "pass" ]; then
    STATUS="warn"
  fi

  CHECKS="${CHECKS}${id}|${name}|${status}|${message}
"
}

if [ -d "$TARGET_REPO" ]; then
  add_check "target.exists" "Target Repository" "pass" "Target repository path exists."
else
  add_check "target.exists" "Target Repository" "fail" "Target repository path does not exist."
fi

CONFIG_PATH="$TARGET_REPO/.continue/config.yaml"
if [ -f "$CONFIG_PATH" ]; then
  add_check "config.exists" "Continue Config" "pass" ".continue/config.yaml exists."
  if grep -Eq '^version:[[:space:]]+\S+' "$CONFIG_PATH"; then
    add_check "config.version" "Config Version" "pass" "Config declares a version."
  else
    add_check "config.version" "Config Version" "warn" "Config does not declare a version."
  fi
else
  add_check "config.exists" "Continue Config" "warn" ".continue/config.yaml was not found."
fi

if [ -d "$TARGET_REPO/runtime-validation-output" ]; then
  add_check "runtime.output" "Runtime Output" "warn" "Runtime validation output exists."
else
  add_check "runtime.output" "Runtime Output" "pass" "No runtime validation output folder found."
fi

if [ "$SKIP_OLLAMA" -eq 1 ]; then
  add_check "ollama.reachable" "Ollama Reachability" "skip" "Ollama check skipped by request."
else
  add_check "ollama.reachable" "Ollama Reachability" "warn" "Ollama reachability check is available in the PowerShell implementation."
fi

json_report() {
  printf '{\n'
  printf '  "SchemaVersion": 1,\n'
  printf '  "TargetRepoChecked": %s,\n' "$([ -d "$TARGET_REPO" ] && printf true || printf false)"
  printf '  "OllamaCheckSkipped": %s,\n' "$([ "$SKIP_OLLAMA" -eq 1 ] && printf true || printf false)"
  printf '  "OverallStatus": "%s",\n' "$STATUS"
  printf '  "Checks": [\n'
  first=1
  while IFS='|' read -r id name status message; do
    [ -n "$id" ] || continue
    [ "$first" -eq 0 ] && printf ',\n'
    first=0
    printf '    {"Id":"%s","Name":"%s","Status":"%s","Message":"%s"}' "$id" "$name" "$status" "$message"
  done <<EOF
$CHECKS
EOF
  printf '\n  ]\n'
  printf '}\n'
}

if [ -n "$OUTPUT_PATH" ]; then
  mkdir -p "$(dirname "$OUTPUT_PATH")"
  json_report > "$OUTPUT_PATH"
fi

if [ "$AS_JSON" -eq 1 ] || [ -n "$OUTPUT_PATH" ]; then
  json_report
else
  printf 'Overall: %s\n' "$STATUS"
  printf '%s' "$CHECKS" | while IFS='|' read -r id name status message; do
    [ -n "$id" ] || continue
    printf '%s %s: %s\n' "$status" "$name" "$message"
  done
fi

[ "$STATUS" != "fail" ]
