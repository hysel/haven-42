#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MATRIX_PATH="$REPO_ROOT/config/language-workflow-validation-matrix.json"
READ_CONFIG_PATH="$REPO_ROOT/.continue/config.local.yaml"
WRITE_CONFIG_PATH=""
OUTPUT_PATH=""
ECOSYSTEMS=""
OPERATIONS=""
CONTINUE_COMMAND="npx"
TIMEOUT_SECONDS=900
UNLOAD_AFTER_RUN=false
REQUIRE_IDLE_SERVER=true
DRY_RUN=false

usage() {
  cat <<'EOF_USAGE'
Usage: run-language-workflow-matrix.shared.sh [options]

Runs selected language workflow matrix cells against Continue CLI and writes a
sanitized report. Raw model output stays under ignored runtime-validation-output.

Options:
  --matrix-path <path>
  --read-config <path>
  --write-config <path>
  --ecosystems <csv>
  --operations <csv>
  --output-path <path>
  --continue-command <command>
  --timeout-seconds <seconds>
  --unload-after-run
  --allow-loaded-models
  --dry-run
EOF_USAGE
}

require_value() {
  [ "$#" -ge 2 ] || { printf 'Missing value for %s\n' "$1" >&2; exit 1; }
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --matrix-path) require_value "$@"; MATRIX_PATH="$2"; shift 2 ;;
    --read-config) require_value "$@"; READ_CONFIG_PATH="$2"; shift 2 ;;
    --write-config) require_value "$@"; WRITE_CONFIG_PATH="$2"; shift 2 ;;
    --ecosystems) require_value "$@"; ECOSYSTEMS="$2"; shift 2 ;;
    --operations) require_value "$@"; OPERATIONS="$2"; shift 2 ;;
    --output-path) require_value "$@"; OUTPUT_PATH="$2"; shift 2 ;;
    --continue-command) require_value "$@"; CONTINUE_COMMAND="$2"; shift 2 ;;
    --timeout-seconds) require_value "$@"; TIMEOUT_SECONDS="$2"; shift 2 ;;
    --unload-after-run) UNLOAD_AFTER_RUN=true; shift ;;
    --allow-loaded-models) REQUIRE_IDLE_SERVER=false; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 1 ;;
  esac
done

[ -n "$WRITE_CONFIG_PATH" ] || WRITE_CONFIG_PATH="$READ_CONFIG_PATH"
if [ -z "$OUTPUT_PATH" ]; then
  OUTPUT_PATH="$REPO_ROOT/runtime-validation-output/language-workflow-matrix-$(date +%Y%m%d-%H%M%S).json"
fi

config_value() {
  awk -v key="$2" '$0 ~ "^[[:space:]]*" key ":[[:space:]]*" { sub("^[[:space:]]*" key ":[[:space:]]*", ""); print $1; exit }' "$1" | tr -d '"\047'
}

resolve_existing_path() {
  [ -e "$1" ] || { printf 'Required path does not exist: %s\n' "$1" >&2; exit 1; }
  local directory filename
  directory="$(cd "$(dirname "$1")" && pwd)"
  filename="$(basename "$1")"
  printf '%s/%s' "$directory" "$filename"
}

init_baseline() {
  local sample_path="$1"
  if [ ! -d "$sample_path/.git" ]; then
    git -C "$sample_path" init >/dev/null
    git -C "$sample_path" config core.autocrlf false
    git -C "$sample_path" config core.eol lf
    git -C "$sample_path" add .
    git -C "$sample_path" -c user.name="Local Agent Validation" -c user.email="local-agent-validation@example.invalid" commit -m "Initial generated sample" >/dev/null
  elif [ -n "$(git -C "$sample_path" status --short)" ]; then
    git -C "$sample_path" restore . >/dev/null
    git -C "$sample_path" clean -fd >/dev/null
  fi
}

READ_MODEL=""
WRITE_MODEL=""
READ_BASE_URL=""
WRITE_BASE_URL=""
unload_models() {
  [ "$UNLOAD_AFTER_RUN" = true ] && [ "$DRY_RUN" = false ] || return 0
  printf '[7/8] Unloading tested models...\n' >&2
  local pair base model
  for pair in "$READ_BASE_URL|$READ_MODEL" "$WRITE_BASE_URL|$WRITE_MODEL"; do
    base="${pair%%|*}"; model="${pair#*|}"
    [ -n "$base" ] && [ -n "$model" ] || continue
    local unloaded=false attempt loaded
    for attempt in 1 2 3; do
      curl -fsS --max-time 60 -H 'Content-Type: application/json' \
        -d "{\"model\":\"$model\",\"prompt\":\"\",\"keep_alive\":0,\"stream\":false}" \
        "${base%/}/api/generate" >/dev/null || break
      sleep 2
      loaded="$(curl -fsS --max-time 15 "${base%/}/api/ps" 2>/dev/null || true)"
      if ! printf '%s' "$loaded" | grep -Fq "\"name\":\"$model\""; then
        unloaded=true
        break
      fi
    done
    if [ "$unloaded" = true ]; then
      printf '[7/8] Unloaded %s.\n' "$model" >&2
    else
      printf 'Warning: model %s is still loaded after three unload attempts.\n' "$model" >&2
    fi
  done
}

handle_interruption() {
  printf 'Interrupted; releasing tested model(s) before exit.\n' >&2
  trap - EXIT HUP INT TERM
  unload_models
  exit 130
}

trap handle_interruption HUP INT TERM
trap unload_models EXIT

run_continue() {
  local sample_path="$1" config_path="$2" mode="$3" prompt="$4" stdout_path="$5" stderr_path="$6"
  if [ "$DRY_RUN" = true ]; then
    printf 'DRY_RUN %s\n' "$prompt" > "$stdout_path"
    : > "$stderr_path"
    return 0
  fi
  (
    cd "$sample_path"
    if [ "$CONTINUE_COMMAND" = "npx" ]; then
      npx -y @continuedev/cli --config "$config_path" "$mode" --format json --silent -p "$prompt"
    else
      "$CONTINUE_COMMAND" --config "$config_path" "$mode" --format json --silent -p "$prompt"
    fi
  ) > "$stdout_path" 2> "$stderr_path" &
  local pid=$! elapsed=0
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$elapsed" -ge "$TIMEOUT_SECONDS" ]; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      return 124
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  wait "$pid"
}

operation_prompt() {
  local ecosystem="$1" operation="$2" expected="$3" target="$4" marker="$5"
  case "$operation" in
    repository-discovery)
      printf 'Inspect this repository in read-only mode for the %s component. Do not modify or create files. Begin the final answer with "Evidence files inspected:" and list each of these exact repository paths on its own bullet before the analysis: %s. Then identify the project structure, architecture, source, tests, configuration, risks, and next steps. Copy paths exactly; do not invent or shorten filenames.' "$ecosystem" "$expected" ;;
    implementation-plan)
      printf 'Create a read-only implementation plan for the scenario in SCENARIO.md, scoped to the %s component. Do not modify or create files. Begin the final answer with "Evidence files inspected:" and list each of these exact repository paths on its own bullet before the plan: %s. Include affected components, ordered steps, tests, risks, and rollback. Copy paths exactly; do not invent or shorten filenames.' "$ecosystem" "$expected" ;;
    code-review)
      printf 'Review the %s component in read-only mode. Do not modify or create files. Begin the final answer with "Evidence files inspected:" and list each of these exact repository paths on its own bullet before the findings: %s. Then lead with correctness, security, regression, maintainability, and missing-test findings. Copy paths exactly; do not invent or shorten filenames.' "$ecosystem" "$expected" ;;
    scoped-write)
      printf 'Use approved write mode for this disposable validation fixture. Modify only the existing file %s. Add one new line if needed. Append exactly this one final line, with no other text on that line:\n%s\nDo not modify or create any other file. Do not reformat existing content. Before responding, read the target and verify that its final line exactly matches the marker above. Then respond exactly: Changed file: %s Do not commit.' "$target" "$marker" "$target" ;;
  esac
}

append_result() {
  local ecosystem="$1" rule_pack="$2" sample="$3" operation="$4" status="$5" model="$6" external_diff="$7" signals="$8" stdout_path="$9" sample_path="${10}"
  python3 - "$RESULTS_PATH" "$stdout_path" "$REPO_ROOT" "$sample_path" "$ecosystem" "$rule_pack" "$sample" "$operation" "$status" "$SURFACE_VERSION" "$model" "$external_diff" "$signals" <<'PY'
import json, pathlib, re, sys
result_path, stdout_path, root, sample_path, ecosystem, rule_pack, sample, operation, status, version, model, external_diff, signals = sys.argv[1:]
text = pathlib.Path(stdout_path).read_text(encoding="utf-8", errors="replace")
for value in (root, sample_path):
    text = text.replace(value, "<local-value>")
text = re.sub(r"https?://[^\s)\]}>]+", "<endpoint>", text)
text = re.sub(r"(?i)[A-Z]:\\\\Users\\\\[^\\\\\s]+", "<user-home>", text)
if len(text) > 6000:
    text = text[:6000] + "\n[truncated]"
result = {
    "Ecosystem": ecosystem,
    "RulePackId": rule_pack,
    "Sample": sample,
    "Operation": operation,
    "Status": status,
    "Surface": "Continue CLI",
    "SurfaceVersion": version,
    "Provider": "Ollama",
    "Model": model,
    "OperatingSystem": sys.platform,
    "SanitizedOutput": text.strip(),
    "ExternalDiffVerification": external_diff,
    "FailureSignals": [signal for signal in signals.split("|") if signal],
}
with open(result_path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(result) + "\n")
PY
}

printf '[1/8] Validating matrix, configs, and Continue CLI...\n' >&2
command -v python3 >/dev/null 2>&1 || { printf 'python3 is required for matrix JSON processing.\n' >&2; exit 1; }
[ -f "$MATRIX_PATH" ] && [ -f "$READ_CONFIG_PATH" ] && [ -f "$WRITE_CONFIG_PATH" ] || { printf 'Matrix or config path is missing.\n' >&2; exit 1; }
MATRIX_PATH="$(resolve_existing_path "$MATRIX_PATH")"
READ_CONFIG_PATH="$(resolve_existing_path "$READ_CONFIG_PATH")"
WRITE_CONFIG_PATH="$(resolve_existing_path "$WRITE_CONFIG_PATH")"
OUTPUT_DIRECTORY="$(dirname "$OUTPUT_PATH")"
mkdir -p "$OUTPUT_DIRECTORY"
OUTPUT_PATH="$(cd "$OUTPUT_DIRECTORY" && pwd)/$(basename "$OUTPUT_PATH")"
if [ "$DRY_RUN" = false ]; then
  command -v "$CONTINUE_COMMAND" >/dev/null 2>&1 || { printf 'Continue command not found: %s\n' "$CONTINUE_COMMAND" >&2; exit 1; }
fi

READ_MODEL="$(config_value "$READ_CONFIG_PATH" model)"
WRITE_MODEL="$(config_value "$WRITE_CONFIG_PATH" model)"
READ_BASE_URL="$(config_value "$READ_CONFIG_PATH" apiBase)"
WRITE_BASE_URL="$(config_value "$WRITE_CONFIG_PATH" apiBase)"
# A portable Continue config intentionally omits apiBase. Ollama uses this
# local default when no endpoint override is configured.
[ -n "$READ_BASE_URL" ] || READ_BASE_URL="http://127.0.0.1:11434"
[ -n "$WRITE_BASE_URL" ] || WRITE_BASE_URL="$READ_BASE_URL"
if [ "$DRY_RUN" = true ]; then
  SURFACE_VERSION="dry-run"
elif [ "$CONTINUE_COMMAND" = "npx" ]; then
  SURFACE_VERSION="$(npx -y @continuedev/cli --version 2>/dev/null || true)"
else
  SURFACE_VERSION="$("$CONTINUE_COMMAND" --version 2>/dev/null || true)"
fi
[ -n "$SURFACE_VERSION" ] || SURFACE_VERSION="unconfirmed"
if [ "$DRY_RUN" = false ]; then
  curl -fsS --max-time 15 "${READ_BASE_URL%/}/api/version" >/dev/null
  [ "$WRITE_BASE_URL" = "$READ_BASE_URL" ] || curl -fsS --max-time 15 "${WRITE_BASE_URL%/}/api/version" >/dev/null
  if [ "$REQUIRE_IDLE_SERVER" = true ]; then
    loaded_models="$(curl -fsS --max-time 15 "${READ_BASE_URL%/}/api/ps" | python3 -c 'import json,sys; print(",".join(sorted(str(x.get("name","")) for x in json.load(sys.stdin).get("models",[]))))')"
    if [ -n "$loaded_models" ]; then
      printf 'Refusing to start: Ollama already has loaded model(s): %s. Unload them first, or explicitly use --allow-loaded-models.\n' "$loaded_models" >&2
      exit 1
    fi
  fi
fi

printf '[2/8] Generating clean medium-complexity fixtures...\n' >&2
generator_script="$SCRIPT_DIR/generate-sample-repositories.shared.sh"
if grep -q $'\r' "$generator_script"; then
  normalized_generator="$SCRIPT_DIR/.generate-sample-repositories-normalized-$$.sh"
  tr -d '\r' < "$generator_script" > "$normalized_generator"
  set +e
  bash "$normalized_generator" --force >/dev/null
  generator_status=$?
  set -e
  rm -f "$normalized_generator"
  [ "$generator_status" -eq 0 ] || exit "$generator_status"
else
  bash "$generator_script" --force >/dev/null
fi
SAMPLE_ROOT="$REPO_ROOT/runtime-validation-output/sample-repositories"
RAW_ROOT="$(dirname "$OUTPUT_PATH")/language-workflow-matrix-raw-$(date +%s)-$$"
mkdir -p "$RAW_ROOT"
RESULTS_PATH="$RAW_ROOT/results.ndjson"
: > "$RESULTS_PATH"

printf '[3/8] Read model: %s\n' "$READ_MODEL" >&2
printf '[3/8] Write model: %s\n' "$WRITE_MODEL" >&2

MATRIX_ROWS=()
while IFS= read -r matrix_row; do
  MATRIX_ROWS+=("$matrix_row")
done < <(python3 - "$MATRIX_PATH" "$ECOSYSTEMS" "$OPERATIONS" <<'PY'
import json, sys
matrix = json.load(open(sys.argv[1], encoding="utf-8"))
ecosystems = set(filter(None, sys.argv[2].split(",")))
operations = [item for item in sys.argv[3].split(",") if item] or matrix["requiredOperations"]
for entry in matrix["entries"]:
    if ecosystems and entry["ecosystem"] not in ecosystems:
        continue
    for operation in operations:
        evidence = entry["operationEvidence"][operation]
        if operation == "scoped-write":
            expected = ""
            target = evidence["targetFile"]
            marker = evidence["marker"]
        else:
            expected = "\x1f".join(evidence)
            target = ""
            marker = ""
        print("\x1e".join([entry["ecosystem"], entry["rulePackId"], entry["sample"], operation, expected, target, marker]))
PY
)
[ "${#MATRIX_ROWS[@]}" -gt 0 ] || { printf 'No matrix entries matched the requested filters.\n' >&2; exit 1; }
DISPLAY_OPERATIONS="$OPERATIONS"
[ -n "$DISPLAY_OPERATIONS" ] || DISPLAY_OPERATIONS="repository-discovery,implementation-plan,code-review,scoped-write"
printf '[4/8] Operations: %s\n' "$DISPLAY_OPERATIONS" >&2

index=0 total="${#MATRIX_ROWS[@]}"
for row in "${MATRIX_ROWS[@]}"; do
  IFS=$'\036' read -r ecosystem rule_pack sample operation expected_raw target marker <<< "$row"
  index=$((index + 1))
  sample_path="$SAMPLE_ROOT/$sample"
  init_baseline "$sample_path"
  expected_csv="${expected_raw//$'\037'/, }"
  prompt="$(operation_prompt "$ecosystem" "$operation" "$expected_csv" "$target" "$marker")"
  stdout_path="$RAW_ROOT/${ecosystem//[^a-zA-Z0-9._-]/-}-${operation}.stdout.txt"
  stderr_path="$RAW_ROOT/${ecosystem//[^a-zA-Z0-9._-]/-}-${operation}.stderr.txt"
  config="$READ_CONFIG_PATH"; mode="--readonly"; model="$READ_MODEL"
  [ "$operation" = "scoped-write" ] && { config="$WRITE_CONFIG_PATH"; mode="--auto"; model="$WRITE_MODEL"; }
  printf '[5/8] Running %s/%s: %s / %s\n' "$index" "$total" "$ecosystem" "$operation" >&2
  started="$(date +%s)"
  set +e
  run_continue "$sample_path" "$config" "$mode" "$prompt" "$stdout_path" "$stderr_path"
  exit_code=$?
  set -e
  signals=()
  [ "$exit_code" -eq 124 ] && signals+=("TIMEOUT")
  [ "$exit_code" -ne 0 ] && [ "$exit_code" -ne 124 ] && signals+=("CLI_EXIT_$exit_code")
  [ -s "$stdout_path" ] || signals+=("EMPTY_OUTPUT")
  if grep -Eqi 'TOOLS_UNAVAILABLE|WRITE_NOT_APPLIED|RAW_TOOL_CALL_OUTPUT' "$stdout_path"; then signals+=("MODEL_FAILURE_SIGNAL"); fi
  if grep -Eq '^<function=|^[[:space:]]*\{[[:space:]]*"name"[[:space:]]*:' "$stdout_path"; then signals+=("RAW_TOOL_CALL_ONLY"); fi
  external_diff="not-applicable"
  if [ "$operation" = "scoped-write" ]; then
    if [ "$DRY_RUN" = true ]; then
      external_diff="dry-run"
    else
      write_failed=false
      changed="$(git -C "$sample_path" diff --name-only)"
      diff_check="$(git -C "$sample_path" diff --check 2>&1 || true)"
      target_path="$sample_path/$target"
      marker_count="$(grep -Fxc -- "$marker" "$target_path" 2>/dev/null || true)"
      [ "$changed" = "$target" ] || { signals+=("WRITE_SCOPE_MISMATCH"); write_failed=true; }
      [ -z "$diff_check" ] || { signals+=("GIT_DIFF_CHECK_FAILED"); write_failed=true; }
      [ "$marker_count" = "1" ] || { signals+=("WRITE_MARKER_MISMATCH"); write_failed=true; }
      tail -n 1 "$target_path" | grep -Fqx -- "$marker" || { signals+=("WRITE_FINAL_LINE_MISMATCH"); write_failed=true; }
      [ "$write_failed" = true ] && external_diff="failed" || external_diff="passed"
      git -C "$sample_path" restore . >/dev/null
      git -C "$sample_path" clean -fd >/dev/null
    fi
  else
    IFS=$'\037' read -ra expected_files <<< "$expected_raw"
    for expected_file in "${expected_files[@]}"; do grep -Fq -- "$expected_file" "$stdout_path" || signals+=("EXPECTED_FILE_MISSING:$expected_file"); done
    [ -z "$(git -C "$sample_path" status --short)" ] || signals+=("UNEXPECTED_READ_WRITE")
  fi
  [ "${#signals[@]}" -eq 0 ] && { status="validated"; signals=("none"); } || status="failed"
  append_result "$ecosystem" "$rule_pack" "$sample" "$operation" "$status" "$model" "$external_diff" "$(IFS='|'; echo "${signals[*]}")" "$stdout_path" "$sample_path"
  elapsed=$(( $(date +%s) - started ))
  printf '[5/8] Completed %s / %s: %s in %ss\n' "$ecosystem" "$operation" "$status" "$elapsed" >&2
done

printf '[6/8] Writing sanitized matrix report...\n' >&2
python3 - "$RESULTS_PATH" "$OUTPUT_PATH" "$SURFACE_VERSION" "$READ_MODEL" "$WRITE_MODEL" <<'PY'
import json, pathlib, sys
results = [json.loads(line) for line in pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if line]
report = {
    "SchemaVersion": 1,
    "Surface": "Continue CLI",
    "SurfaceVersion": sys.argv[3],
    "Provider": "Ollama",
    "OperatingSystem": "native-shell",
    "ReadModel": sys.argv[4],
    "WriteModel": sys.argv[5],
    "Results": results,
    "Notes": "Raw output remains under ignored runtime output. The report omits endpoints, local paths, prompts, stdout, and stderr.",
}
pathlib.Path(sys.argv[2]).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
PY
printf '[8/8] Sanitized report written to %s\n' "$OUTPUT_PATH" >&2
