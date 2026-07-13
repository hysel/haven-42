#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKFLOW_ID=""
WORKFLOW_ARGUMENTS_JSON=""
PLATFORM="linux"
REGISTRY_PATH="$REPO_ROOT/config/workflows.json"
LIST=false
AS_JSON=false
DRY_RUN=false
WORKFLOW_ARGS=()

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

json_array_from_args() {
  first=true
  printf '['
  for arg in "$@"; do
    if [ "$first" = true ]; then first=false; else printf ','; fi
    printf '"%s"' "$(json_escape "$arg")"
  done
  printf ']'
}

try_python_dispatch() {
  python_command="$1"
  shift
  command -v "$python_command" >/dev/null 2>&1 || return 1
  "$python_command" - "$REGISTRY_PATH" "$PLATFORM" "$WORKFLOW_ID" "$LIST" "$AS_JSON" "$DRY_RUN" "$WORKFLOW_ARGUMENTS_JSON" "$@" 2>/dev/null <<'PY'
import json
import os
import subprocess
import sys

registry_path, platform, workflow_id, list_mode, as_json, dry_run, workflow_arguments_json, *workflow_args = sys.argv[1:]
list_mode = list_mode == "true"
as_json = as_json == "true"
dry_run = dry_run == "true"
repo_root = os.path.abspath(os.path.join(os.path.dirname(registry_path), ".."))

with open(registry_path, "r", encoding="utf-8") as handle:
    registry = json.load(handle)

if workflow_arguments_json:
    workflow_args.extend(str(item) for item in json.loads(workflow_arguments_json))

if list_mode:
    items = [
        {
            "Id": workflow["id"],
            "Name": workflow["name"],
            "Category": workflow["category"],
            "SafetyLevel": workflow["safetyLevel"],
            "UiReady": bool(workflow["uiReady"]),
        }
        for workflow in registry.get("workflows", [])
    ]
    if as_json:
        print(json.dumps(items, indent=2))
    else:
        for item in sorted(items, key=lambda value: value["Id"]):
            print(f'{item["Id"]}\t{item["Name"]}\t{item["Category"]}\t{item["SafetyLevel"]}\t{item["UiReady"]}')
    raise SystemExit(0)

if not workflow_id:
    print("WorkflowId is required unless --list is used.", file=sys.stderr)
    raise SystemExit(1)

matches = [workflow for workflow in registry.get("workflows", []) if workflow.get("id") == workflow_id]
if not matches:
    print(f"Workflow not found: {workflow_id}", file=sys.stderr)
    raise SystemExit(1)
if len(matches) > 1:
    print(f"Workflow id is not unique: {workflow_id}", file=sys.stderr)
    raise SystemExit(1)

workflow = matches[0]
entry_point = workflow.get("entryPoints", {}).get(platform, "")
if not entry_point or os.path.isabs(entry_point) or ".." in entry_point.replace("\\", "/").split("/"):
    print(f"Workflow entry point must be repository-relative: {entry_point}", file=sys.stderr)
    raise SystemExit(1)

entry_path = os.path.join(repo_root, entry_point)
if not os.path.exists(entry_path):
    print(f"Workflow entry point does not exist: {entry_point}", file=sys.stderr)
    raise SystemExit(1)

resolved = {
    "Id": workflow["id"],
    "Name": workflow["name"],
    "Category": workflow["category"],
    "SafetyLevel": workflow["safetyLevel"],
    "Platform": platform,
    "EntryPoint": entry_point,
    "ResolvedEntryPoint": entry_point,
    "Arguments": workflow_args,
}

if dry_run:
    if as_json:
        print(json.dumps(resolved, indent=2))
    else:
        print(f'Workflow: {resolved["Id"]}')
        print(f'Name: {resolved["Name"]}')
        print(f'Safety level: {resolved["SafetyLevel"]}')
        print(f'Platform: {resolved["Platform"]}')
        print(f'Entry point: {resolved["EntryPoint"]}')
        print("Arguments: " + (" ".join(workflow_args) if workflow_args else "none"))
        print("Dry run only; workflow was not invoked.")
    raise SystemExit(0)

if as_json:
    print(json.dumps(resolved, indent=2))

completed = subprocess.run([entry_path, *workflow_args], cwd=repo_root)
raise SystemExit(completed.returncode)
PY
}

extract_field() {
  field="$1"
  sed -n "s/^[[:space:]]*\"$field\": \"\\(.*\\)\",\\?$/\\1/p" | head -n 1
}

extract_bool() {
  field="$1"
  sed -n "s/^[[:space:]]*\"$field\": \\(true\\|false\\),\\?$/\\1/p" | head -n 1
}

get_workflow_block() {
  awk -v key="\"id\": \"$WORKFLOW_ID\"" 'index($0, key) { found=1 } found { print; if ($0 ~ /^    },?$/) exit }' "$REGISTRY_PATH"
}

append_json_arguments_fallback() {
  [ -n "$WORKFLOW_ARGUMENTS_JSON" ] || return 0
  normalized="$(printf '%s' "$WORKFLOW_ARGUMENTS_JSON" | sed 's/^[[:space:]]*\[//; s/\][[:space:]]*$//')"
  [ -n "$normalized" ] || return 0
  old_ifs="$IFS"
  IFS=,
  for item in $normalized; do
    value="$(printf '%s' "$item" | sed 's/^[[:space:]]*"//; s/"[[:space:]]*$//; s/\\"/"/g; s/\\\\/\\/g')"
    WORKFLOW_ARGS+=("$value")
  done
  IFS="$old_ifs"
}

fallback_list() {
  if [ "$AS_JSON" = true ]; then
    first=true
    printf '[\n'
  fi

  awk '
    /^[[:space:]]*"id": / { id=$0; sub(/^[[:space:]]*"id": "/, "", id); sub(/",?$/, "", id) }
    /^[[:space:]]*"name": / { name=$0; sub(/^[[:space:]]*"name": "/, "", name); sub(/",?$/, "", name) }
    /^[[:space:]]*"category": / { category=$0; sub(/^[[:space:]]*"category": "/, "", category); sub(/",?$/, "", category) }
    /^[[:space:]]*"safetyLevel": / { safety=$0; sub(/^[[:space:]]*"safetyLevel": "/, "", safety); sub(/",?$/, "", safety) }
    /^[[:space:]]*"uiReady": / {
      ui=$0; sub(/^[[:space:]]*"uiReady": /, "", ui); sub(/,?$/, "", ui);
      print id "\t" name "\t" category "\t" safety "\t" ui
    }
  ' "$REGISTRY_PATH" | while IFS=$'\t' read -r id name category safety ui_ready; do
    if [ "$AS_JSON" = true ]; then
      if [ "$first" = true ]; then first=false; else printf ',\n'; fi
      printf '  {"Id":"%s","Name":"%s","Category":"%s","SafetyLevel":"%s","UiReady":%s}' \
        "$(json_escape "$id")" "$(json_escape "$name")" "$(json_escape "$category")" "$(json_escape "$safety")" "$ui_ready"
    else
      printf '%s\t%s\t%s\t%s\t%s\n' "$id" "$name" "$category" "$safety" "$ui_ready"
    fi
  done

  if [ "$AS_JSON" = true ]; then
    printf '\n]\n'
  fi
}

fallback_dispatch() {
  append_json_arguments_fallback

  if [ "$LIST" = true ]; then
    fallback_list
    return 0
  fi

  if [ -z "$WORKFLOW_ID" ]; then
    printf 'WorkflowId is required unless --list is used.\n' >&2
    return 1
  fi

  block="$(get_workflow_block)"
  if [ -z "$block" ]; then
    printf 'Workflow not found: %s\n' "$WORKFLOW_ID" >&2
    return 1
  fi

  name="$(printf '%s\n' "$block" | extract_field name)"
  category="$(printf '%s\n' "$block" | extract_field category)"
  safety="$(printf '%s\n' "$block" | extract_field safetyLevel)"
  entry_point="$(printf '%s\n' "$block" | sed -n "s/^[[:space:]]*\"$PLATFORM\": \"\\(.*\\)\",\\?$/\\1/p" | head -n 1)"

  if [ -z "$entry_point" ] || printf '%s' "$entry_point" | grep -Eq '^/|^[A-Za-z]:|(^|/)\.\.(/|$)|\\'; then
    printf 'Workflow entry point must be repository-relative: %s\n' "$entry_point" >&2
    return 1
  fi

  entry_path="$REPO_ROOT/$entry_point"
  if [ ! -e "$entry_path" ]; then
    printf 'Workflow entry point does not exist: %s\n' "$entry_point" >&2
    return 1
  fi

  if [ "$DRY_RUN" = true ]; then
    if [ "$AS_JSON" = true ]; then
      printf '{\n'
      printf '  "Id": "%s",\n' "$(json_escape "$WORKFLOW_ID")"
      printf '  "Name": "%s",\n' "$(json_escape "$name")"
      printf '  "Category": "%s",\n' "$(json_escape "$category")"
      printf '  "SafetyLevel": "%s",\n' "$(json_escape "$safety")"
      printf '  "Platform": "%s",\n' "$(json_escape "$PLATFORM")"
      printf '  "EntryPoint": "%s",\n' "$(json_escape "$entry_point")"
      printf '  "ResolvedEntryPoint": "%s",\n' "$(json_escape "$entry_point")"
      printf '  "Arguments": '
      json_array_from_args "${WORKFLOW_ARGS[@]}"
      printf '\n}\n'
    else
      printf 'Workflow: %s\n' "$WORKFLOW_ID"
      printf 'Name: %s\n' "$name"
      printf 'Safety level: %s\n' "$safety"
      printf 'Platform: %s\n' "$PLATFORM"
      printf 'Entry point: %s\n' "$entry_point"
      if [ "${#WORKFLOW_ARGS[@]}" -gt 0 ]; then
        printf 'Arguments: %s\n' "${WORKFLOW_ARGS[*]}"
      else
        printf 'Arguments: none\n'
      fi
      printf 'Dry run only; workflow was not invoked.\n'
    fi
    return 0
  fi

  if [ "$AS_JSON" = true ]; then
    printf '{"Id":"%s","EntryPoint":"%s","Platform":"%s"}\n' "$(json_escape "$WORKFLOW_ID")" "$(json_escape "$entry_point")" "$(json_escape "$PLATFORM")"
  fi

  "$entry_path" "${WORKFLOW_ARGS[@]}"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --workflow-id|-WorkflowId) WORKFLOW_ID="$2"; shift 2 ;;
    --workflow-arguments-json|-WorkflowArgumentsJson) WORKFLOW_ARGUMENTS_JSON="$2"; shift 2 ;;
    --platform|-Platform) PLATFORM="$2"; shift 2 ;;
    --registry-path|-RegistryPath) REGISTRY_PATH="$2"; shift 2 ;;
    --list|-List) LIST=true; shift ;;
    --json|-Json) AS_JSON=true; shift ;;
    --dry-run|-DryRun) DRY_RUN=true; shift ;;
    --) shift; WORKFLOW_ARGS+=("$@"); break ;;
    *) WORKFLOW_ARGS+=("$1"); shift ;;
  esac
done

case "$PLATFORM" in
  linux|macos) ;;
  *) printf 'Unsupported platform: %s\n' "$PLATFORM" >&2; exit 1 ;;
esac

if [ ! -f "$REGISTRY_PATH" ]; then
  printf 'Workflow registry does not exist: %s\n' "$REGISTRY_PATH" >&2
  exit 1
fi

for python_command in python3 python; do
  if try_python_dispatch "$python_command" "${WORKFLOW_ARGS[@]}"; then
    exit 0
  fi
done

fallback_dispatch
