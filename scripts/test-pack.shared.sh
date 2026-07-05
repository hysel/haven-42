#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FAILED=0
TEST_COUNT=0

pass() {
  printf 'PASS %s\n' "$1"
}

fail() {
  printf 'FAIL %s - %s\n' "$1" "$2" >&2
  FAILED=1
}

run_test() {
  TEST_COUNT=$((TEST_COUNT + 1))
  name="$1"
  shift
  if "$@"; then
    pass "$name"
  else
    fail "$name" "test command failed"
  fi
}

assert_file() {
  [ -e "$1" ]
}

test_validate_succeeds() {
  "$REPO_ROOT/scripts/validate-pack.shared.sh" >/tmp/continue-pack-validate.out 2>&1 &&
    grep -q "Validation passed" /tmp/continue-pack-validate.out
}

test_validate_fails_for_wrong_version() {
  ! "$REPO_ROOT/scripts/validate-pack.shared.sh" --expected-version 0.0.0 >/tmp/continue-pack-validate-wrong.out 2>&1 &&
    grep -q "FAIL config version is 0.0.0" /tmp/continue-pack-validate-wrong.out
}

test_catalog_schema() {
  awk -F'|' '
    /^#/ || /^$/ { next }
    NF != 5 { exit 1 }
    $1 !~ /^(High|Medium|Low)$/ { exit 1 }
    $4 == "" || $5 == "" { exit 1 }
    $2 == "" && $3 ~ / or / { exit 1 }
    END { exit 0 }
  ' "$REPO_ROOT/config/model-recommendations.tsv" &&
    grep -q "simple-hardware default" "$REPO_ROOT/config/model-recommendations.tsv"
}

test_committed_config_uses_starter_model() {
  grep -q "model: qwen3.5:9b" "$REPO_ROOT/.continue/config.yaml" &&
  ! grep -q "model: qwen3-coder:30b" "$REPO_ROOT/.continue/config.yaml"
}

test_mlx_catalog_schema() {
  awk -F'|' '
    /^#/ || /^$/ { next }
    NF != 4 { exit 1 }
    $1 !~ /^(High|Medium|Low)$/ { exit 1 }
    $2 == "" || $3 == "" || $4 == "" { exit 1 }
    END { exit 0 }
  ' "$REPO_ROOT/config/model-recommendations.mlx.tsv"
}

test_shell_scripts_executable() {
  while IFS= read -r row; do
    mode="$(printf '%s' "$row" | awk '{ print $1 }')"
    [ "$mode" = "100755" ] || return 1
  done < <(git -C "$REPO_ROOT" ls-files -s 'scripts/*.sh')
}

test_linux_macos_scripts_do_not_require_pwsh() {
  ! grep -Eq 'pwsh|PowerShell 7' \
    "$REPO_ROOT/scripts/validate-pack.linux.sh" \
    "$REPO_ROOT/scripts/validate-pack.macos.sh" \
    "$REPO_ROOT/scripts/test-pack.linux.sh" \
    "$REPO_ROOT/scripts/test-pack.macos.sh" \
    "$REPO_ROOT/scripts/install-continue-pack.linux.sh" \
    "$REPO_ROOT/scripts/install-continue-pack.macos.sh" \
    "$REPO_ROOT/scripts/install-validated-model.linux.sh" \
    "$REPO_ROOT/scripts/install-validated-model.macos.sh" \
    "$REPO_ROOT/scripts/generate-runtime-context.linux.sh" \
    "$REPO_ROOT/scripts/generate-runtime-context.macos.sh" \
    "$REPO_ROOT/scripts/run-runtime-validation.linux.sh" \
    "$REPO_ROOT/scripts/run-runtime-validation.macos.sh" \
    "$REPO_ROOT/scripts/pull-local-agent-models.linux.sh" \
    "$REPO_ROOT/scripts/pull-local-agent-models.macos.sh" \
    "$REPO_ROOT/scripts/test-local-agent-models.linux.sh" \
    "$REPO_ROOT/scripts/test-local-agent-models.macos.sh"
}

test_runtime_context_generation() {
  temp_repo="$(mktemp -d)"
  mkdir -p "$temp_repo/src" "$temp_repo/bin"
  printf '# Sample\n' > "$temp_repo/README.md"
  printf 'public class App { }\n' > "$temp_repo/src/App.cs"
  printf 'public class BuildOutput { }\n' > "$temp_repo/bin/Ignored.cs"
  printf '<Project Sdk="Microsoft.NET.Sdk" />\n' > "$temp_repo/Sample.csproj"

  "$REPO_ROOT/scripts/generate-runtime-context.shared.sh" --target-repo "$temp_repo" --output-path "$temp_repo/runtime-context.md" >/tmp/continue-context.out 2>&1 || return 1
  grep -q '# Runtime Repository Context' "$temp_repo/runtime-context.md" || return 1
  grep -q 'src/App.cs' "$temp_repo/runtime-context.md" || return 1
  ! grep -q 'bin/Ignored.cs' "$temp_repo/runtime-context.md"
}

test_install_dry_run() {
  temp_repo="$(mktemp -d)"
  "$REPO_ROOT/scripts/install-continue-pack.shared.sh" --target-repo "$temp_repo" --dry-run >/tmp/continue-install.out 2>&1 || return 1
  grep -q "Dry run only" /tmp/continue-install.out || return 1
  [ ! -e "$temp_repo/.continue" ]
}

test_install_auto_model_dry_run() {
  temp_repo="$(mktemp -d)"
  "$REPO_ROOT/scripts/install-continue-pack.shared.sh" --target-repo "$temp_repo" --dry-run --auto-model-config >/tmp/continue-install-auto.out 2>&1 || return 1
  grep -q "Would generate .continue/config.local.yaml" /tmp/continue-install-auto.out || return 1
  [ ! -e "$temp_repo/.continue" ]
}

test_install_model_lanes() {
  temp_repo="$(mktemp -d)"
  global_config="$temp_repo/global-config.yaml"
  "$REPO_ROOT/scripts/install-continue-pack.shared.sh" --target-repo "$temp_repo" --model-lanes --global-config --global-config-path "$global_config" --global-config-api-base "http://127.0.0.1:11434" >/tmp/continue-install-model-lanes.out 2>&1 || return 1
  local_config="$temp_repo/.continue/config.local.yaml"
  [ -f "$local_config" ] || return 1
  [ -f "$global_config" ] || return 1
    grep -q "1 - WRITE SAFE - qwen3.5:9b" "$local_config" &&
    grep -q "2 - PLAN ONLY - qwen3.5:9b" "$local_config" &&
    grep -q "3 - DEEP REVIEW - qwen3.5:9b" "$local_config" &&
    grep -q "Ollama Nomic Embed" "$local_config" &&
    ! grep -q "4 - " "$local_config" &&
    ! grep -q "5 - " "$local_config" &&
    grep -q "apiBase: http://127.0.0.1:11434" "$global_config" &&
    awk '
      /^  - name: / {
        current = substr($0, 11)
      }
      current == "1 - WRITE SAFE - qwen3.5:9b" && /- edit/ { write_edit = 1 }
      current == "1 - WRITE SAFE - qwen3.5:9b" && /- apply/ { write_apply = 1 }
      current == "2 - PLAN ONLY - qwen3.5:9b" && /- edit|- apply/ { plan_bad = 1 }
      current == "3 - DEEP REVIEW - qwen3.5:9b" && /- edit|- apply/ { deep_bad = 1 }
      END {
        if (!write_edit || !write_apply || plan_bad || deep_bad) {
          exit 1
        }
      }
    ' "$local_config"
}

test_install_validated_model() {
  temp_repo="$(mktemp -d)"
  mkdir -p "$temp_repo/.continue"
  cp "$REPO_ROOT/.continue/config.yaml" "$temp_repo/.continue/config.yaml"
  "$REPO_ROOT/scripts/install-validated-model.shared.sh" --target-repo "$temp_repo" --model "devstral-small-2:24b" --profile plan-only --no-pull >/tmp/continue-install-validated-model.out 2>&1 || return 1
  local_config="$temp_repo/.continue/config.local.yaml"
  [ -f "$local_config" ] || return 1
  ! grep -q "devstral-small-2:24b" "$temp_repo/.continue/config.yaml" &&
    grep -q "2 - PLAN ONLY - devstral-small-2:24b" "$local_config" &&
    grep -q "1 - WRITE SAFE - qwen3.5:9b" "$local_config" &&
    grep -q "3 - DEEP REVIEW - qwen3.5:9b" "$local_config" &&
    grep -q "Ollama Nomic Embed" "$local_config"
}

test_install_validated_model_dry_run() {
  temp_repo="$(mktemp -d)"
  mkdir -p "$temp_repo/.continue"
  cp "$REPO_ROOT/.continue/config.yaml" "$temp_repo/.continue/config.yaml"
  "$REPO_ROOT/scripts/install-validated-model.shared.sh" --target-repo "$temp_repo" --model "qwen3-coder:30b" --profile deep-review --dry-run --no-pull >/tmp/continue-install-validated-model-dry-run.out 2>&1 || return 1
  grep -q "Would install validated model" /tmp/continue-install-validated-model-dry-run.out &&
    grep -q "Would write local-only config" /tmp/continue-install-validated-model-dry-run.out &&
    [ ! -e "$temp_repo/.continue/config.local.yaml" ]
}

test_install_global_config_dry_run() {
  temp_repo="$(mktemp -d)"
  global_config="$(mktemp)"
  rm -f "$global_config"
  "$REPO_ROOT/scripts/install-continue-pack.shared.sh" --target-repo "$temp_repo" --dry-run --global-config --global-config-path "$global_config" --global-config-api-base http://127.0.0.1:11434 >/tmp/continue-install-global.out 2>&1 || return 1
  grep -q "Would write global Continue config" /tmp/continue-install-global.out || return 1
  grep -q "Would omit rules from generated global config" /tmp/continue-install-global.out || return 1
  [ ! -e "$global_config" ] && [ ! -e "$temp_repo/.continue" ]
}

test_install_global_config_writes_refs() {
  temp_repo="$(mktemp -d)"
  global_config="$(mktemp)"
  rm -f "$global_config"
  "$REPO_ROOT/scripts/install-continue-pack.shared.sh" --target-repo "$temp_repo" --global-config --global-config-path "$global_config" --global-config-api-base http://127.0.0.1:11434 >/tmp/continue-install-global-write.out 2>&1 || return 1
  grep -q "Global Continue config generated" "$global_config" &&
    grep -q "apiBase: http://127.0.0.1:11434" "$global_config" &&
    grep -q "file:///" "$global_config" &&
    ! grep -q "rules/general.md" "$global_config" &&
    ! grep -q "^rules:" "$global_config" &&
    grep -q "prompts/repository-discovery.md" "$global_config" &&
    ! grep -q "file://./" "$global_config"
}

test_install_global_config_rules_opt_in() {
  temp_repo="$(mktemp -d)"
  global_config="$(mktemp)"
  rm -f "$global_config"
  "$REPO_ROOT/scripts/install-continue-pack.shared.sh" --target-repo "$temp_repo" --global-config --global-config-path "$global_config" --global-config-include-rules >/tmp/continue-install-global-rules.out 2>&1 || return 1
  grep -q "^rules:" "$global_config" &&
    grep -q "rules/general.md" "$global_config"
}

test_runtime_validation_missing_target() {
  missing_repo="$(mktemp -d)"
  rmdir "$missing_repo"
  ! "$REPO_ROOT/scripts/run-runtime-validation.shared.sh" --target-repo "$missing_repo" >/tmp/continue-runtime.out 2>&1 &&
    grep -q "Target repository path does not exist" /tmp/continue-runtime.out
}

test_profile_script_markers() {
  grep -q "MlxRecommendation" "$REPO_ROOT/scripts/get-local-model-profile.macos.sh" &&
    grep -q "PlatformNotes" "$REPO_ROOT/scripts/get-local-model-profile.linux.sh" &&
    grep -q "detect_container_context" "$REPO_ROOT/scripts/get-local-model-profile.linux.sh" &&
    grep -q "Container or LXC-style environment detected" "$REPO_ROOT/scripts/get-local-model-profile.linux.sh" &&
    grep -q "Recommended enterprise/cloud smoke test" "$REPO_ROOT/docs/compatibility.md" &&
    grep -q "Recommended container smoke test" "$REPO_ROOT/docs/compatibility.md"
}

test_editor_compatibility_doc() {
  grep -q "VS Code" "$REPO_ROOT/docs/editor-compatibility.md" &&
    grep -q "VSCodium" "$REPO_ROOT/docs/editor-compatibility.md" &&
    grep -q "project-local" "$REPO_ROOT/docs/editor-compatibility.md" &&
    grep -q "Duplicate rule" "$REPO_ROOT/docs/editor-compatibility.md" &&
    grep -q "Agent mode" "$REPO_ROOT/docs/editor-compatibility.md" &&
    grep -q "npx -y @continuedev/cli --config .continue/config.yaml" "$REPO_ROOT/docs/editor-compatibility.md" &&
    grep -q "Terminal Preflight Checks" "$REPO_ROOT/docs/editor-compatibility.md" &&
    grep -q "examples/editor-surface-validation.md" "$REPO_ROOT/docs/editor-compatibility.md" &&
    grep -q "Editor Surface Validation Evidence" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "VS Code-compatible build" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "VSCodium" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "Read-only tool validated" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "qwen3-coder:30b" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "Do not mark approved-write ready" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "VSCodium Agent Tool Test" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "<function=ls>" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "Controlled Retest" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "Ollama Qwen Coder" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "Continue listed files in ." "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "model connection error" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "Duplicate-Rule Warning Check" "$REPO_ROOT/examples/editor-surface-validation.md" &&
    grep -q "No duplicate-rule warnings observed" "$REPO_ROOT/examples/editor-surface-validation.md"
}

test_model_tool_use_validation_doc() {
  grep -q "Candidate" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "Read-only tool validated" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "read-only listing only" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "Approved-write ready" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "raw JSON" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "read file contents" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "READ_TOOLS_UNAVAILABLE" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "WRITE_NOT_APPLIED" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "PATH_AMBIGUOUS" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "WORKSPACE_UNAVAILABLE" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "APPLY_TARGET_MISMATCH" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "create_new_file" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "DUPLICATE_APPROVALS" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "DUPLICATE_CONTENT" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "edit_file" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "Validation labels must match the evidence" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "opened repository root or current folder" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "external shell or git check" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "Test-Path" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "test -f" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "active shell and operating system" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "continue-agent-write-test.md" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "I can't directly edit files" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "examples/model-tool-use-validation.md" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "Do not record" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "docs/local-agent-model-testing.md" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "pull candidate Ollama models" "$REPO_ROOT/docs/local-agent-model-testing.md" &&
    grep -q "load a model" "$REPO_ROOT/docs/local-agent-model-testing.md" &&
    grep -q "unload a model" "$REPO_ROOT/docs/local-agent-model-testing.md" &&
    grep -q "tool-call behavior" "$REPO_ROOT/docs/local-agent-model-testing.md" &&
    grep -q "exact-content output" "$REPO_ROOT/docs/local-agent-model-testing.md" &&
    grep -q "does not replace Continue UI Apply validation" "$REPO_ROOT/docs/local-agent-model-testing.md" &&
    grep -q "model lanes" "$REPO_ROOT/docs/model-tool-use-validation.md" &&
    grep -q "MODEL_DOES_NOT_SUPPORT_TOOLS" "$REPO_ROOT/docs/local-agent-model-testing.md" &&
    grep -q "THINK_TAG_LEAK" "$REPO_ROOT/docs/local-agent-model-testing.md" &&
    grep -q "runtime-validation-output" "$REPO_ROOT/docs/local-agent-model-testing.md" &&
    grep -q "Model Tool-Use Validation Evidence" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Read-only listing only" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Failure signal" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Provider: Ollama" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Editor surface" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "MCP state" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Read-content tool execution" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Path resolution and current-folder behavior" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Workspace discovery with no active file" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Apply target alignment" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Duplicate approval guard" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "DUPLICATE_APPROVALS" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "External write verification" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Platform-aware command use" "$REPO_ROOT/examples/model-tool-use-validation.md" &&
    grep -q "Sanitization Checklist" "$REPO_ROOT/examples/model-tool-use-validation.md"
}

test_tool_use_docs_define_platform_aware_write_behavior() {
  grep -q "Match commands to the user's active operating system and shell" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "READ_TOOLS_UNAVAILABLE" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "WRITE_NOT_APPLIED" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "PATH_AMBIGUOUS" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "WORKSPACE_UNAVAILABLE" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "APPLY_TARGET_MISMATCH" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "create_new_file" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "edit_file" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "Keep validation labels consistent with evidence" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "no file is open" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "src/main.py" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "current workspace root" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "src/README.md" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "git diff" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "external shell or git check" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "typical" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "Select-String" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "write tools are unavailable" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "I can't directly edit files" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "Platform-Aware Commands" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "READ_TOOLS_UNAVAILABLE" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "WRITE_TOOLS_UNAVAILABLE" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "WRITE_NOT_APPLIED" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "PATH_AMBIGUOUS" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "WORKSPACE_UNAVAILABLE" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "APPLY_TARGET_MISMATCH" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "create_new_file" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "DUPLICATE_APPROVALS" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "DUPLICATE_CONTENT" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "opened repository root or current folder" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "continue-agent-write-test.md" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "Assistant-only readback is not enough" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "Test-Path" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "test -f" "$REPO_ROOT/docs/tool-use-modes.md" &&
    grep -q "Safe write smoke-test prompt" "$REPO_ROOT/docs/approved-tool-backed-changes.md" &&
    grep -q "PATH_AMBIGUOUS" "$REPO_ROOT/docs/approved-tool-backed-changes.md" &&
    grep -q "git diff" "$REPO_ROOT/docs/approved-tool-backed-changes.md" &&
    grep -q "Assistant-only readback is not enough" "$REPO_ROOT/docs/approved-tool-backed-changes.md" &&
    grep -q "Test-Path" "$REPO_ROOT/docs/approved-tool-backed-changes.md" &&
    grep -q "test -f" "$REPO_ROOT/docs/approved-tool-backed-changes.md" &&
    grep -q "Remove-Item" "$REPO_ROOT/docs/approved-tool-backed-changes.md" &&
    grep -q "write tools are not validated yet" "$REPO_ROOT/README.md" &&
    grep -q "read file contents" "$REPO_ROOT/README.md" &&
    grep -q "git diff -- <file>" "$REPO_ROOT/README.md" &&
    grep -q "WORKSPACE_UNAVAILABLE" "$REPO_ROOT/README.md" &&
    grep -q "APPLY_TARGET_MISMATCH" "$REPO_ROOT/README.md" &&
    grep -q "create_new_file" "$REPO_ROOT/README.md" &&
    grep -q "Two approval prompts" "$REPO_ROOT/README.md" &&
    grep -q "edit_file" "$REPO_ROOT/README.md" &&
    grep -q "created and read back a file" "$REPO_ROOT/README.md" &&
    grep -q "READ_TOOLS_UNAVAILABLE.*read-only tool validated" "$REPO_ROOT/README.md" &&
    grep -q "ModelLanes" "$REPO_ROOT/README.md" &&
    grep -q "1 - WRITE SAFE" "$REPO_ROOT/README.md" &&
    grep -q "Agent Says It Cannot Edit Files" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "WRITE_TOOLS_UNAVAILABLE" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "Agent Lists Files But Cannot Read Or Edit Them" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "READ_TOOLS_UNAVAILABLE" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "Agent Claims A Change But Git Diff Is Empty" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "WRITE_NOT_APPLIED" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "Test-Path" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "Assistant-only readback is not enough" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "Agent Creates A File In The Wrong Folder" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "PATH_AMBIGUOUS" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "Agent Says No File Is Open And Asks For A Path" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "WORKSPACE_UNAVAILABLE" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "Apply Target Does Not Match The Requested File" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "APPLY_TARGET_MISMATCH" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "Duplicate Approval Prompts Or Duplicate Content" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "DUPLICATE_APPROVALS" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "DUPLICATE_CONTENT" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "edit_file" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "read-only listing only" "$REPO_ROOT/docs/troubleshooting.md" &&
    grep -q "Model Lanes" "$REPO_ROOT/docs/local-model-selection.md" &&
    grep -q "Why These Profiles" "$REPO_ROOT/docs/local-model-selection.md" &&
    grep -q "WRITE SAFE" "$REPO_ROOT/docs/local-model-selection.md" &&
    grep -q "PLAN ONLY" "$REPO_ROOT/docs/local-model-selection.md" &&
    grep -q "DEEP REVIEW" "$REPO_ROOT/docs/local-model-selection.md"
}

run_test "validate-pack succeeds for repository" test_validate_succeeds
run_test "validate-pack fails for wrong expected version" test_validate_fails_for_wrong_version
run_test "model recommendation catalog has valid schema" test_catalog_schema
run_test "committed config uses starter sample model" test_committed_config_uses_starter_model
run_test "MLX model recommendation catalog has valid schema" test_mlx_catalog_schema
run_test "shell wrapper scripts are executable in git" test_shell_scripts_executable
run_test "Linux/macOS user-facing scripts do not require PowerShell" test_linux_macos_scripts_do_not_require_pwsh
run_test "runtime context generation captures useful files and excludes build output" test_runtime_context_generation
run_test "install script dry run does not modify target repository" test_install_dry_run
run_test "install script auto model config dry run is explicit" test_install_auto_model_dry_run
run_test "install script model lanes generate scoped roles" test_install_model_lanes
run_test "validated model installer updates local-only config" test_install_validated_model
run_test "validated model installer dry run is local only" test_install_validated_model_dry_run
run_test "install script global config dry run is explicit" test_install_global_config_dry_run
run_test "install script writes global config with target references" test_install_global_config_writes_refs
run_test "install script can include rules in global config by explicit opt-in" test_install_global_config_rules_opt_in
run_test "runtime validation fails before CLI execution for missing target repository" test_runtime_validation_missing_target
run_test "hardware profile scripts expose platform-specific markers" test_profile_script_markers
run_test "editor compatibility docs cover config and tool validation" test_editor_compatibility_doc
run_test "model tool-use validation docs define evidence workflow" test_model_tool_use_validation_doc
run_test "tool-use docs define platform-aware approved write behavior" test_tool_use_docs_define_platform_aware_write_behavior

if [ "$FAILED" -eq 1 ]; then
  printf 'Test run failed. %s tests executed.\n' "$TEST_COUNT" >&2
  exit 1
fi

printf 'Test run passed. %s tests executed.\n' "$TEST_COUNT"
