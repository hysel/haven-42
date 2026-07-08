#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH=""
CONTEXT_PATH=""
WORKFLOW_NAME="unknown"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --context-path|-ContextPath)
      CONTEXT_PATH="$2"
      shift 2
      ;;
    --workflow-name|-WorkflowName)
      WORKFLOW_NAME="$2"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [ ! -f "$OUTPUT_PATH" ]; then
  printf 'Output path does not exist: %s\n' "$OUTPUT_PATH" >&2
  exit 1
fi

if [ ! -f "$CONTEXT_PATH" ]; then
  printf 'Runtime context path does not exist: %s\n' "$CONTEXT_PATH" >&2
  exit 1
fi

python3 - "$OUTPUT_PATH" "$CONTEXT_PATH" "$WORKFLOW_NAME" <<'PY'
import os
import re
import sys

output_path, context_path, workflow_name = sys.argv[1:4]

with open(output_path, "r", encoding="utf-8", errors="replace") as handle:
    output_text = handle.read()

with open(context_path, "r", encoding="utf-8", errors="replace") as handle:
    context_text = handle.read()

file_pattern = re.compile(r"(?<![\w.-])[\w.-]+(?:[\\/][\w.-]+)*\.(csproj|vbproj|fsproj|sln|config|props|targets|dna|xll|json|md|cs|sql|xml|yaml|yml|txt)(?![\w.-])", re.IGNORECASE)
context_files = set()

for match in file_pattern.finditer(context_text):
    value = match.group(0).strip("`'\"()[]{}:,;")
    if value:
        context_files.add(value.lower())
        context_files.add(os.path.basename(value).lower())

failures = []
output_file_mentions = []

for line in output_text.splitlines():
    for match in file_pattern.finditer(line):
        value = match.group(0).strip("`'\"()[]{}:,;")
        if value:
            output_file_mentions.append((value, line))

recommended_new_file_pattern = re.compile(r"recommended new file|missing file recommendation|new file recommendation|file to add|new documentation file|new config file", re.IGNORECASE)
seen_output_files = set()
for value, line in sorted(output_file_mentions, key=lambda item: item[0].lower()):
    key = value.lower()
    if key in seen_output_files:
        continue
    seen_output_files.add(key)
    leaf = os.path.basename(value)
    if value.lower() not in context_files and leaf.lower() not in context_files:
        if recommended_new_file_pattern.search(line):
            continue
        failures.append(f"FILENAME_NOT_IN_CONTEXT: {value}")

claim_patterns = [
    r"compatible with",
    r"actively maintained",
    r"supports \.NET",
    r"support(ed)? until",
    r"stable version",
    r"no evidence of dependencies requiring",
    r"no migration readiness issues are identified",
]
claim_qualifier = re.compile(r"current-source verification|requires verification|verify with current|unverified|not proven|source evidence", re.IGNORECASE)

if re.search(r"legacy|dependency|migration|repository-discovery", workflow_name, re.IGNORECASE):
    for line in output_text.splitlines():
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in claim_patterns) and not claim_qualifier.search(line):
            failures.append(f"UNSOURCED_COMPATIBILITY_CLAIM: {line.strip()}")

if re.search(r"legacy|dependency|migration", workflow_name, re.IGNORECASE):
    for pattern in [
        r"<PackageReference\s+Include=",
        r"Remove\s+packages\.config",
        r"Delete\s+packages\.config",
        r"Replace\s+the\s+entire\s+ItemGroup",
        r"dotnet\s+restore",
        r"dotnet\s+build",
    ]:
        if re.search(pattern, output_text, re.IGNORECASE):
            failures.append(f"UNSAFE_LEGACY_MIGRATION_PATTERN: {pattern}")

if failures:
    for failure in failures:
        print(f"FAIL {failure}")
    sys.exit(1)

print(f"PASS runtime output verification passed for {workflow_name}")
PY
