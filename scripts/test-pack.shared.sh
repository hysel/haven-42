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


test_release_packaging_scripts() {
  output="$($REPO_ROOT/scripts/build-release-package.shared.sh --version 0.2.0 --dry-run --allow-dirty 2>&1)" || return 1
  printf '%s\n' "$output" | grep -q "Release package plan" || return 1
  printf '%s\n' "$output" | grep -q "local-engineering-agent-pack-0.2.0.tar.gz" || return 1
  printf '%s\n' "$output" | grep -q "\.sha256" || return 1
  printf '%s\n' "$output" | grep -q "Excluded: .git, .vscode, runtime-validation-output, dist, local configs" || return 1
  grep -q "tar -C" "$REPO_ROOT/scripts/build-release-package.shared.sh" &&
    grep -q "sha256sum" "$REPO_ROOT/scripts/build-release-package.shared.sh" &&
    grep -q "shasum -a 256" "$REPO_ROOT/scripts/build-release-package.shared.sh" &&
    ! grep -q "mapfile" "$REPO_ROOT/scripts/build-release-package.shared.sh" &&
    grep -q "config" "$REPO_ROOT/scripts/build-release-package.shared.sh" &&
    grep -q "local" "$REPO_ROOT/scripts/build-release-package.shared.sh" &&
    grep -q "runtime-validation-output" "$REPO_ROOT/scripts/build-release-package.shared.sh" &&
    grep -q "Build Release Artifacts" "$REPO_ROOT/docs/release.md" &&
    grep -q "Verify Checksums" "$REPO_ROOT/docs/release.md" &&
    grep -q "GitHub Release" "$REPO_ROOT/docs/release.md" &&
    grep -Fxq "dist/" "$REPO_ROOT/.gitignore"
}
test_evidence_catalog_schema() {
  catalog="$REPO_ROOT/config/evidence-catalog.tsv"
  doc="$REPO_ROOT/docs/evidence-catalog.md"
  [ -f "$catalog" ] || return 1
  [ -f "$doc" ] || return 1
  head -n 1 "$catalog" | grep -q $'area\tsubject\tsurface\tos\tmodel\tstatus\tevidence\tnotes' || return 1
  awk -F'\t' '
    NR == 1 { next }
    NF != 8 { exit 1 }
    $1 == "" || $2 == "" || $3 == "" || $4 == "" || $5 == "" || $6 == "" || $7 == "" || $8 == "" { exit 1 }
    $6 !~ /^(candidate-only|plan-review-candidate|read-only-tool-validated|read-only-cli-validated|approved-write-ready|static-validated|validated-by-tests|partial-pass)$/ { exit 1 }
    $7 ~ /^[A-Za-z]:|^\/|\\|\.\./ { exit 1 }
    $0 ~ /192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|localhost|itama|Users\\|OneDrive|customer|token|secret/ { exit 1 }
    $6 == "approved-write-ready" { approved = 1 }
    $6 == "candidate-only" { candidate = 1 }
    $6 == "read-only-tool-validated" { readonly = 1 }
    END { if (!approved || !candidate || !readonly) exit 1 }
  ' "$catalog" || return 1
  while IFS=$'\t' read -r area subject surface os model status evidence notes; do
    [ "$area" = "area" ] && continue
    [ -e "$REPO_ROOT/$evidence" ] || return 1
  done < "$catalog"
  grep -q "config/evidence-catalog.tsv" "$doc" && grep -q "approved-write-ready" "$doc"
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
  done < <(git -C "$REPO_ROOT" ls-files -s 'scripts/*.sh' '.githooks/pre-push')
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
    "$REPO_ROOT/scripts/verify-runtime-output.linux.sh" \
    "$REPO_ROOT/scripts/verify-runtime-output.macos.sh" \
    "$REPO_ROOT/scripts/pull-local-agent-models.linux.sh" \
    "$REPO_ROOT/scripts/pull-local-agent-models.macos.sh" \
    "$REPO_ROOT/scripts/test-local-agent-models.linux.sh" \
    "$REPO_ROOT/scripts/test-local-agent-models.macos.sh" \
    "$REPO_ROOT/scripts/generate-sample-repositories.linux.sh" \
    "$REPO_ROOT/scripts/generate-sample-repositories.macos.sh"
}

test_runtime_context_generation() {
  temp_repo="$REPO_ROOT/runtime-validation-output/context-parent-git-test-$$"
  rm -rf "$temp_repo"
  mkdir -p "$temp_repo/src" "$temp_repo/bin"
  printf '# Sample\n' > "$temp_repo/README.md"
  printf 'public class App { }\n' > "$temp_repo/src/App.cs"
  printf 'public class BuildOutput { }\n' > "$temp_repo/bin/Ignored.cs"
  printf '<Project Sdk="Microsoft.NET.Sdk" />\n' > "$temp_repo/Sample.csproj"
  printf '{"scripts":{"test":"vitest run"}}\n' > "$temp_repo/package.json"

  "$REPO_ROOT/scripts/generate-runtime-context.shared.sh" --target-repo "$temp_repo" --output-path "$temp_repo/runtime-context.md" >/tmp/continue-context.out 2>&1 || return 1
  grep -q '# Runtime Repository Context' "$temp_repo/runtime-context.md" || return 1
  grep -q 'src/App.cs' "$temp_repo/runtime-context.md" || return 1
  grep -q 'package.json' "$temp_repo/runtime-context.md" || return 1
  grep -q 'vitest run' "$temp_repo/runtime-context.md" || return 1
  ! grep -q 'scripts/test-pack.shared.sh' "$temp_repo/runtime-context.md" || return 1
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

test_install_read_only_profile() {
  temp_repo="$(mktemp -d)"
  global_config="$temp_repo/global-config.yaml"
  "$REPO_ROOT/scripts/install-continue-pack.shared.sh" --target-repo "$temp_repo" --install-profile read-only --global-config --global-config-path "$global_config" >/tmp/continue-install-read-only-profile.out 2>&1 || return 1
  local_config="$temp_repo/.continue/config.local.yaml"
  [ -f "$local_config" ] || return 1
  [ -f "$global_config" ] || return 1
  grep -q "READ ONLY - qwen3.5:9b" "$local_config" &&
    grep -q "Ollama Nomic Embed" "$local_config" &&
    ! grep -q -- "- edit" "$local_config" &&
    ! grep -q -- "- apply" "$local_config" &&
    grep -q "READ ONLY - qwen3.5:9b" "$global_config" &&
    ! grep -q -- "- edit" "$global_config"
}

test_install_approved_write_profile() {
  temp_repo="$(mktemp -d)"
  "$REPO_ROOT/scripts/install-continue-pack.shared.sh" --target-repo "$temp_repo" --install-profile approved-write >/tmp/continue-install-approved-write-profile.out 2>&1 || return 1
  local_config="$temp_repo/.continue/config.local.yaml"
  [ -f "$local_config" ] || return 1
  grep -q "1 - WRITE SAFE - qwen3.5:9b" "$local_config" &&
    grep -q "2 - PLAN ONLY - qwen3.5:9b" "$local_config" &&
    awk '
      /^  - name: / {
        current = substr($0, 11)
      }
      current == "1 - WRITE SAFE - qwen3.5:9b" && /- edit/ { write_edit = 1 }
      current == "1 - WRITE SAFE - qwen3.5:9b" && /- apply/ { write_apply = 1 }
      current == "2 - PLAN ONLY - qwen3.5:9b" && /- edit|- apply/ { plan_bad = 1 }
      END {
        if (!write_edit || !write_apply || plan_bad) {
          exit 1
        }
      }
    ' "$local_config"
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

test_runtime_output_verifier_catches_bad_output() {
  temp_dir="$(mktemp -d)"
  trap 'rm -rf "$temp_dir"' RETURN

  cat > "$temp_dir/runtime-context.md" <<'EOF_CONTEXT'
## Project Files

- BrickLinkBrickSet.csproj
- packages.config
- Properties/ExcelDna.Build.props
EOF_CONTEXT

  printf '%s\n' 'Use BrickLinkBrickSet.csproj and packages.config. Compatibility requires current-source verification.' > "$temp_dir/good.md"
  printf '%s\n' 'BrickLinkBrickSet-AddIn.csproj is compatible with .NET Framework 4.8.' > "$temp_dir/bad.md"

  "$REPO_ROOT/scripts/verify-runtime-output.shared.sh" \
    --output-path "$temp_dir/good.md" \
    --context-path "$temp_dir/runtime-context.md" \
    --workflow-name legacy-dotnet-dependency-migration >/tmp/continue-verify-good.out 2>&1 || return 1

  ! "$REPO_ROOT/scripts/verify-runtime-output.shared.sh" \
    --output-path "$temp_dir/bad.md" \
    --context-path "$temp_dir/runtime-context.md" \
    --workflow-name legacy-dotnet-dependency-migration >/tmp/continue-verify-bad.out 2>&1 &&
    grep -q "FILENAME_NOT_IN_CONTEXT" /tmp/continue-verify-bad.out &&
    grep -q "UNSOURCED_COMPATIBILITY_CLAIM" /tmp/continue-verify-bad.out
}

test_runtime_validation_runner_writes_verification_outputs() {
  grep -q "verify-runtime-output.ps1" "$REPO_ROOT/scripts/run-runtime-validation.ps1" &&
    grep -q "Local Ollama API preflight failed" "$REPO_ROOT/scripts/run-runtime-validation.ps1" &&
    grep -q "/api/tags" "$REPO_ROOT/scripts/run-runtime-validation.ps1" &&
    grep -q "Failed guardrail verification" "$REPO_ROOT/scripts/run-runtime-validation.ps1" &&
    grep -q "verify-runtime-output.shared.sh" "$REPO_ROOT/scripts/run-runtime-validation.shared.sh" &&
    grep -q "Local Ollama API preflight failed" "$REPO_ROOT/scripts/run-runtime-validation.shared.sh" &&
    grep -q "/api/tags" "$REPO_ROOT/scripts/run-runtime-validation.shared.sh" &&
    grep -q ".verification.txt" "$REPO_ROOT/scripts/run-runtime-validation.shared.sh"
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

test_online_model_discovery_doc() {
  [ -f "$REPO_ROOT/docs/online-model-discovery.md" ] &&
    grep -q "candidate model names only" "$REPO_ROOT/docs/online-model-discovery.md" &&
    grep -q "default workflow stays offline" "$REPO_ROOT/docs/online-model-discovery.md" &&
    grep -q "must not" "$REPO_ROOT/docs/online-model-discovery.md" &&
    grep -q "Pull models automatically" "$REPO_ROOT/docs/online-model-discovery.md" &&
    grep -q "Mark a model as tool-safe" "$REPO_ROOT/docs/online-model-discovery.md" &&
    grep -q "private repository content" "$REPO_ROOT/docs/online-model-discovery.md" &&
    grep -q "Approved-write ready" "$REPO_ROOT/docs/online-model-discovery.md" &&
    grep -q "docs/online-model-discovery.md" "$REPO_ROOT/README.md" &&
    grep -q "docs/online-model-discovery.md" "$REPO_ROOT/docs/local-model-selection.md" &&
    grep -q "do not discover newer" "$REPO_ROOT/docs/local-agent-model-testing.md"
}

test_multi_repository_validation_doc() {
  [ -f "$REPO_ROOT/docs/multi-repository-validation.md" ] &&
    [ -f "$REPO_ROOT/docs/runtime-output-verification.md" ] &&
    [ -f "$REPO_ROOT/examples/multi-repository-validation.md" ] &&
    grep -q "Repository Categories" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "Legacy .NET" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "Modern .NET" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "Documentation or configuration pack" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "Frontend application" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "Script or tooling repository" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "clean git working tree" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "deterministic output verification" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "local sample repositories" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "examples/multi-repository-validation.md" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "docs/runtime-output-verification.md" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "Do not record" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "private repository names" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "Multi-Repository Validation Evidence" "$REPO_ROOT/examples/multi-repository-validation.md" &&
    grep -q "Repository category" "$REPO_ROOT/examples/multi-repository-validation.md" &&
    grep -q "Clean git tree before validation" "$REPO_ROOT/examples/multi-repository-validation.md" &&
    grep -q "Failure signals" "$REPO_ROOT/examples/multi-repository-validation.md" &&
    grep -q "Sanitization Checklist" "$REPO_ROOT/examples/multi-repository-validation.md" &&
    grep -q "No private repository names" "$REPO_ROOT/examples/multi-repository-validation.md" &&
    grep -q "docs/multi-repository-validation.md" "$REPO_ROOT/README.md" &&
    grep -q "docs/runtime-output-verification.md" "$REPO_ROOT/README.md" &&
    grep -q "examples/multi-repository-validation.md" "$REPO_ROOT/README.md" &&
    grep -q "filename" "$REPO_ROOT/docs/runtime-output-verification.md" &&
    grep -q "unsafe mechanical migration patterns" "$REPO_ROOT/docs/runtime-output-verification.md" &&
    grep -q "current-source verification" "$REPO_ROOT/docs/runtime-output-verification.md"
}



test_sample_repository_factory_validation_evidence() {
  [ -f "$REPO_ROOT/examples/sample-repository-factory-validation.md" ] &&
    grep -q "Sample Repository Factory Validation Evidence" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "python-api" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "typescript-frontend" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "Runtime context generation" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "does not prove model or editor Agent behavior" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "No private local paths" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "examples/sample-repository-factory-validation.md" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "examples/sample-repository-factory-validation.md" "$REPO_ROOT/README.md"
}

test_sample_repository_factory_doc() {
  [ -f "$REPO_ROOT/docs/sample-repository-factory.md" ] &&
    grep -q "python-api" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "typescript-frontend" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "generate-sample-repositories.ps1" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "generate-sample-repositories.linux.sh" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "generate-sample-repositories.macos.sh" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "production starter projects" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "docs/sample-repository-factory.md" "$REPO_ROOT/README.md" &&
    grep -q "Milestone 16: Sample Repository Factory" "$REPO_ROOT/ROADMAP.md"
}

test_agent_surface_options_doc() {
  [ -f "$REPO_ROOT/docs/agent-surface-options.md" ] &&
    grep -q "Continue is the first supported surface" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Candidate means" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Approved-write ready" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Cline" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Aider" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Non-Enterprise Use" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "docs/agent-surface-options.md" "$REPO_ROOT/README.md" &&
    grep -q "Milestone 14: Agent Surface Portability And Broader Audience" "$REPO_ROOT/ROADMAP.md"
}


test_language_support_doc() {
  [ -f "$REPO_ROOT/docs/language-support.md" ] &&
    grep -q ".NET.*most mature" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Python" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "JavaScript / TypeScript" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Infrastructure as Code" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Do not apply .NET-specific advice" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "docs/language-support.md" "$REPO_ROOT/README.md" &&
    grep -q "Milestone 15: Multi-Language Engineering Support" "$REPO_ROOT/ROADMAP.md"
}


test_optional_language_rule_packs() {
  [ -f "$REPO_ROOT/.continue/rule-packs/python.md" ] &&
    [ -f "$REPO_ROOT/.continue/rule-packs/typescript.md" ] &&
    [ -f "$REPO_ROOT/docs/language-rule-packs.md" ] &&
    [ -f "$REPO_ROOT/examples/language-rule-pack-validation.md" ] &&
    [ -f "$REPO_ROOT/examples/multi-language-workflow-validation.md" ] &&
    grep -q "optional: true" "$REPO_ROOT/.continue/rule-packs/python.md" &&
    grep -q "pyproject.toml" "$REPO_ROOT/.continue/rule-packs/python.md" &&
    grep -q "unconfirmed" "$REPO_ROOT/.continue/rule-packs/python.md" &&
    grep -q "optional: true" "$REPO_ROOT/.continue/rule-packs/typescript.md" &&
    grep -q "package.json" "$REPO_ROOT/.continue/rule-packs/typescript.md" &&
    grep -q "unconfirmed" "$REPO_ROOT/.continue/rule-packs/typescript.md" &&
    grep -q "not referenced from" "$REPO_ROOT/docs/language-rule-packs.md" &&
    grep -q "docs/project-detection.md" "$REPO_ROOT/docs/language-rule-packs.md" &&
    grep -q "examples/language-rule-pack-validation.md" "$REPO_ROOT/docs/language-rule-packs.md" &&
    grep -q "docs/language-rule-packs.md" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "examples/language-rule-pack-validation.md" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Optional Language Rule Packs" "$REPO_ROOT/docs/project-detection.md" &&
    grep -q "docs/language-rule-packs.md" "$REPO_ROOT/README.md" &&
    grep -q "examples/language-rule-pack-validation.md" "$REPO_ROOT/README.md" &&
    grep -q "Optional Python and TypeScript rule packs" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Language Rule Pack Validation Evidence" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "python-api" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "typescript-frontend" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "pyproject.toml" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "package.json" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "does not prove editor/model behavior" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "Multi-Language Workflow Validation Evidence" "$REPO_ROOT/examples/multi-language-workflow-validation.md" &&
    grep -q "Local Ollama API preflight | Passed" "$REPO_ROOT/examples/multi-language-workflow-validation.md" &&
    grep -q "Repository discovery | Passed verification" "$REPO_ROOT/examples/multi-language-workflow-validation.md" &&
    grep -q "FILENAME_NOT_IN_CONTEXT" "$REPO_ROOT/examples/multi-language-workflow-validation.md" &&
    ! grep -q "rule-packs" "$REPO_ROOT/.continue/config.yaml"
}
test_project_detection_doc() {
  [ -f "$REPO_ROOT/docs/project-detection.md" ] &&
    grep -q "Evidence Strength" "$REPO_ROOT/docs/project-detection.md" &&
    grep -q "Ecosystem Signals" "$REPO_ROOT/docs/project-detection.md" &&
    grep -q "Python" "$REPO_ROOT/docs/project-detection.md" &&
    grep -q "JavaScript / TypeScript" "$REPO_ROOT/docs/project-detection.md" &&
    grep -q "Do not apply .NET-specific guidance" "$REPO_ROOT/docs/project-detection.md" &&
    grep -q "package metadata is present" "$REPO_ROOT/docs/project-detection.md" &&
    grep -q "docs/project-detection.md" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "docs/project-detection.md" "$REPO_ROOT/README.md" &&
    grep -q "Run project classification" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "Evidence Gate" "$REPO_ROOT/.continue/rules/dotnet.md" &&
    grep -q "Evidence Gate" "$REPO_ROOT/.continue/rules/aspnetcore.md" &&
    grep -q "Project Classification" "$REPO_ROOT/.continue/prompts/repository-discovery.md" &&
    grep -q "docs/project-detection.md" "$REPO_ROOT/.continue/prompts/implementation-plan.md" &&
    grep -q "Do not apply language-specific recommendations" "$REPO_ROOT/.continue/prompts/code-review.md" &&
    grep -q "Project Detection" "$REPO_ROOT/.continue/agents/senior-engineer.md"
}
test_sample_repository_factory() {
  temp_root="$(mktemp -d)"
  "$REPO_ROOT/scripts/generate-sample-repositories.shared.sh" --output-root "$temp_root" >/tmp/sample-factory.out 2>&1 || return 1
  grep -q "Generated sample repositories" /tmp/sample-factory.out || return 1
  [ -f "$temp_root/python-api/SAMPLE-METADATA.md" ] || return 1
  [ -f "$temp_root/python-api/pyproject.toml" ] || return 1
  [ -f "$temp_root/python-api/app/main.py" ] || return 1
  [ -f "$temp_root/python-api/tests/test_main.py" ] || return 1
  [ -f "$temp_root/typescript-frontend/package.json" ] || return 1
  [ -f "$temp_root/node-service/Dockerfile" ] || return 1
  [ -f "$temp_root/java-spring-api/pom.xml" ] || return 1
  [ -f "$temp_root/go-service/go.mod" ] || return 1
  [ -f "$temp_root/rust-cli/Cargo.toml" ] || return 1
  [ -f "$temp_root/iac-terraform-kubernetes/terraform/main.tf" ] || return 1
  [ -f "$temp_root/sql-migrations/schema/001_create_items.sql" ] || return 1

  grep -q "# Python API Sample" "$temp_root/python-api/README.md" || return 1
  grep -q "python -m pytest" "$temp_root/python-api/README.md" || return 1
  grep -q "\[project\]" "$temp_root/python-api/pyproject.toml" || return 1
  grep -q "\[tool.pytest.ini_options\]" "$temp_root/python-api/pyproject.toml" || return 1
  ! grep -q "Write-SampleFile" "$temp_root/python-api/README.md" || return 1
  ! grep -Eq "@['\"]|['\"]@" "$temp_root/python-api/README.md" || return 1
  ! grep -q "Write-SampleFile" "$temp_root/python-api/app/main.py" || return 1

  "$REPO_ROOT/scripts/generate-runtime-context.shared.sh" --target-repo "$temp_root/typescript-frontend" --output-path "$temp_root/typescript-context.md" >/tmp/sample-typescript-context.out 2>&1 || return 1
  grep -q "SAMPLE-METADATA.md" "$temp_root/typescript-context.md" || return 1
  grep -q "tsconfig.json" "$temp_root/typescript-context.md" || return 1
  grep -q "src/App.tsx" "$temp_root/typescript-context.md" || return 1

  "$REPO_ROOT/scripts/generate-runtime-context.shared.sh" --target-repo "$temp_root/node-service" --output-path "$temp_root/node-context.md" >/tmp/sample-node-context.out 2>&1 || return 1
  grep -q "Dockerfile" "$temp_root/node-context.md" || return 1
  grep -q "src/server.js" "$temp_root/node-context.md" || return 1

  "$REPO_ROOT/scripts/generate-runtime-context.shared.sh" --target-repo "$temp_root/iac-terraform-kubernetes" --output-path "$temp_root/iac-context.md" >/tmp/sample-iac-context.out 2>&1 || return 1
  grep -q "terraform/main.tf" "$temp_root/iac-context.md" || return 1
  grep -q "k8s/deployment.yaml" "$temp_root/iac-context.md" || return 1
  grep -q ".github/workflows/validate.yml" "$temp_root/iac-context.md" || return 1

  "$REPO_ROOT/scripts/generate-runtime-context.shared.sh" --target-repo "$temp_root/sql-migrations" --output-path "$temp_root/sql-context.md" >/tmp/sample-sql-context.out 2>&1 || return 1
  grep -q "schema/001_create_items.sql" "$temp_root/sql-context.md" || return 1
  grep -q "migrations/002_add_item_status.sql" "$temp_root/sql-context.md" || return 1
  ! "$REPO_ROOT/scripts/generate-sample-repositories.shared.sh" --output-root "$temp_root" >/tmp/sample-factory-rerun.out 2>&1 || return 1
  grep -q "Use --force" /tmp/sample-factory-rerun.out || return 1
  "$REPO_ROOT/scripts/generate-sample-repositories.shared.sh" --output-root "$temp_root" --force >/tmp/sample-factory-force.out 2>&1 || return 1
  "$REPO_ROOT/scripts/generate-sample-repositories.shared.sh" --list >/tmp/sample-factory-list.out 2>&1 || return 1
  grep -q "python-api" /tmp/sample-factory-list.out && grep -q "sql-migrations" /tmp/sample-factory-list.out
}

test_prompt_quality_guardrails_require_filename_fidelity() {
  grep -q "exact filenames" "$REPO_ROOT/.continue/prompts/legacy-dotnet-dependency-migration.md" &&
    grep -q "Do not invent or normalize filenames" "$REPO_ROOT/.continue/prompts/legacy-dotnet-dependency-migration.md" &&
    grep -q "Do not combine a basename" "$REPO_ROOT/.continue/prompts/legacy-dotnet-dependency-migration.md" &&
    grep -q "Evidence Files" "$REPO_ROOT/.continue/prompts/legacy-dotnet-dependency-migration.md" &&
    grep -q "requires current-source verification" "$REPO_ROOT/.continue/prompts/legacy-dotnet-dependency-migration.md" &&
    grep -q "lifecycle/support claims" "$REPO_ROOT/.continue/prompts/legacy-dotnet-dependency-migration.md" &&
    grep -q "verify with current vendor documentation" "$REPO_ROOT/.continue/prompts/legacy-dotnet-dependency-migration.md" &&
    grep -q "Use exact filenames" "$REPO_ROOT/.continue/prompts/repository-discovery.md" &&
    grep -q "filename-fidelity gate" "$REPO_ROOT/.continue/prompts/repository-discovery.md" &&
    grep -q "Do not combine a basename" "$REPO_ROOT/.continue/prompts/repository-discovery.md" &&
    grep -q "label it as unconfirmed" "$REPO_ROOT/.continue/prompts/repository-discovery.md" &&
    grep -q "Use exact filenames" "$REPO_ROOT/docs/prompt-quality.md" &&
    grep -q "lifecycle/support claims" "$REPO_ROOT/docs/prompt-quality.md" &&
    grep -q "Do not combine a basename" "$REPO_ROOT/docs/prompt-quality.md" &&
    grep -q "Invents, normalizes, or alters" "$REPO_ROOT/docs/banned-output-patterns.md" &&
    grep -q "Combines a basename" "$REPO_ROOT/docs/banned-output-patterns.md" &&
    grep -q "support-lifecycle claims" "$REPO_ROOT/docs/banned-output-patterns.md"
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


test_hardware_aware_recommendation_scripts() {
  temp_root="$(mktemp -d)"
  trap 'rm -rf "$temp_root"' RETURN
  profile_path="$temp_root/model-profile.json"
  output_path="$temp_root/recommendation.json"

  cat > "$profile_path" <<'JSON'
{
  "Platform": "Linux",
  "CpuArchitecture": "x64",
  "SystemRamGb": 32,
  "Gpus": [
    {"Name":"fixture gpu","VramGb":16,"MemoryType":"dedicated"}
  ],
  "OllamaModels": ["qwen3.5:9b", "qwen3-coder:30b"]
}
JSON

  "$REPO_ROOT/scripts/recommend-local-agent-config.shared.sh" \
    --model-profile-path "$profile_path" \
    --output-path "$output_path" \
    --vram-selection-mode MaxDedicated >/tmp/hardware-aware-recommendation.out 2>&1 || return 1

  [ -f "$output_path" ] || return 1
  python3 - "$output_path" <<'PY'
import json
import re
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    report = json.load(handle)
text = json.dumps(report, sort_keys=True)
assert report["Recommendation"]["Status"] == "recommended"
assert report["Recommendation"]["WriteSafeModel"] == "qwen3.5:9b"
assert "edit" in report["ContinueProfiles"]["WriteSafe"]["Roles"]
assert "edit" not in report["ContinueProfiles"]["PlanOnly"]["Roles"]
assert report["ModelProfilePath"] == "redacted"
assert report["Privacy"]["RepositoryContentSent"] is False
assert report["Privacy"]["HardwareProfileSentOnline"] is False
assert not re.search(r"Users|OneDrive|192\.168\.|localhost", text)
PY
  grep -q "VramSelectionMode" "$REPO_ROOT/scripts/recommend-local-agent-config.ps1" &&
    grep -q "config/evidence-catalog.tsv" "$REPO_ROOT/scripts/recommend-local-agent-config.ps1" &&
    grep -q "python3 is required" "$REPO_ROOT/scripts/recommend-local-agent-config.shared.sh" &&
    grep -q "HardwareProfileSentOnline" "$REPO_ROOT/scripts/recommend-local-agent-config.shared.sh" &&
    grep -q "WRITE SAFE" "$REPO_ROOT/docs/hardware-aware-recommendations.md" &&
    grep -q "does not read repository source code" "$REPO_ROOT/docs/hardware-aware-recommendations.md" &&
    grep -q "hardware-aware model/config recommendation" "$REPO_ROOT/README.md"
}

test_recommended_agent_config_generation() {
  temp_root="$(mktemp -d)"
  target_root="$(mktemp -d)"
  trap 'rm -rf "$temp_root" "$target_root"' RETURN
  mkdir -p "$target_root/.continue"
  cp "$REPO_ROOT/.continue/config.yaml" "$target_root/.continue/config.yaml"
  recommendation_path="$temp_root/recommendation.json"
  cat > "$recommendation_path" <<'JSON'
{
  "Recommendation": {
    "Status": "recommended",
    "WriteSafeModel": "qwen3.5:9b",
    "PlanOnlyModel": "devstral-small-2:24b",
    "DeepReviewModel": "qwen3-coder:30b"
  },
  "ContinueProfiles": {
    "WriteSafe": {"Model":"qwen3.5:9b","Roles":["chat","edit","apply"],"ContextLength":16384,"MaxTokens":2048,"KeepAlive":1800},
    "PlanOnly": {"Model":"devstral-small-2:24b","Roles":["chat"],"ContextLength":16384,"MaxTokens":2048,"KeepAlive":1800},
    "DeepReview": {"Model":"qwen3-coder:30b","Roles":["chat"],"ContextLength":32768,"MaxTokens":4096,"KeepAlive":1800}
  }
}
JSON

  "$REPO_ROOT/scripts/apply-recommended-agent-config.shared.sh" \
    --target-repo "$target_root" \
    --recommendation-path "$recommendation_path" \
    --dry-run >/tmp/apply-recommended-config-dry-run.out 2>&1 || return 1
  grep -q "Would apply hardware-aware recommendation" /tmp/apply-recommended-config-dry-run.out || return 1

  "$REPO_ROOT/scripts/apply-recommended-agent-config.shared.sh" \
    --target-repo "$target_root" \
    --recommendation-path "$recommendation_path" \
    --ollama-base-url "http://example.local:11434" >/tmp/apply-recommended-config.out 2>&1 || return 1

  local_config="$target_root/.continue/config.local.yaml"
  [ -f "$local_config" ] || return 1
  grep -q "1 - WRITE SAFE - qwen3.5:9b" "$local_config" || return 1
  grep -q "2 - PLAN ONLY - devstral-small-2:24b" "$local_config" || return 1
  grep -q "3 - DEEP REVIEW - qwen3-coder:30b" "$local_config" || return 1
  grep -q "apiBase: http://example.local:11434" "$local_config" || return 1
  ! grep -q "$recommendation_path" "$local_config" || return 1

  global_config="$temp_root/global-config.yaml"
  "$REPO_ROOT/scripts/apply-recommended-agent-config.shared.sh" \
    --target-repo "$target_root" \
    --recommendation-path "$recommendation_path" \
    --ollama-base-url "http://example.local:11434" \
    --global-config \
    --global-config-path "$global_config" >/tmp/apply-recommended-global-config.out 2>&1 || return 1

  [ -f "$global_config" ] || return 1
  grep -q "1 - WRITE SAFE - qwen3.5:9b" "$global_config" || return 1
  grep -q "prompts/repository-discovery.md" "$global_config" || return 1
  ! grep -q "file://./" "$global_config" || return 1
  ! grep -q "^rules:" "$global_config" || return 1
  ! grep -q "$recommendation_path" "$global_config" || return 1

  grep -q "GlobalConfig" "$REPO_ROOT/scripts/apply-recommended-agent-config.ps1" &&
    grep -q -- "--global-config" "$REPO_ROOT/scripts/apply-recommended-agent-config.shared.sh" &&
    grep -q "global Continue config" "$REPO_ROOT/docs/hardware-aware-recommendations.md" &&
    grep -q "Do not commit this file" "$REPO_ROOT/docs/hardware-aware-recommendations.md"
}

test_shared_asset_installation_doc() {
  grep -q "Project-Local Mode" "$REPO_ROOT/docs/shared-asset-installation.md" &&
    grep -q "Shared-Assets Mode" "$REPO_ROOT/docs/shared-asset-installation.md" &&
    grep -q "SharedAssetsPath" "$REPO_ROOT/docs/shared-asset-installation.md" &&
    grep -q "file://\./" "$REPO_ROOT/docs/shared-asset-installation.md" &&
    grep -q "duplicate rule" "$REPO_ROOT/docs/shared-asset-installation.md" &&
    grep -q "Rollback" "$REPO_ROOT/docs/shared-asset-installation.md" &&
    grep -q "docs/shared-asset-installation.md" "$REPO_ROOT/README.md" &&
    grep -q "docs/shared-asset-installation.md" "$REPO_ROOT/docs/hardware-aware-recommendations.md" &&
    grep -q "centralized shared asset" "$REPO_ROOT/TODO.md" &&
    grep -q "centralized shared asset" "$REPO_ROOT/ROADMAP.md"
}
run_test "validate-pack succeeds for repository" test_validate_succeeds
run_test "validate-pack fails for wrong expected version" test_validate_fails_for_wrong_version
run_test "release packaging scripts define archives, checksums, and sanitized dry runs" test_release_packaging_scripts
run_test "evidence catalog has valid schema and sanitized links" test_evidence_catalog_schema
run_test "model recommendation catalog has valid schema" test_catalog_schema
run_test "committed config uses starter sample model" test_committed_config_uses_starter_model
run_test "MLX model recommendation catalog has valid schema" test_mlx_catalog_schema
run_test "shell wrapper scripts and hooks are executable in git" test_shell_scripts_executable
run_test "Linux/macOS user-facing scripts do not require PowerShell" test_linux_macos_scripts_do_not_require_pwsh
run_test "runtime context generation captures useful files and excludes build output" test_runtime_context_generation
run_test "install script dry run does not modify target repository" test_install_dry_run
run_test "install script auto model config dry run is explicit" test_install_auto_model_dry_run
run_test "install script read-only profile omits edit roles" test_install_read_only_profile
run_test "install script approved-write profile maps to model lanes" test_install_approved_write_profile
run_test "install script model lanes generate scoped roles" test_install_model_lanes
run_test "validated model installer updates local-only config" test_install_validated_model
run_test "validated model installer dry run is local only" test_install_validated_model_dry_run
run_test "install script global config dry run is explicit" test_install_global_config_dry_run
run_test "install script writes global config with target references" test_install_global_config_writes_refs
run_test "install script can include rules in global config by explicit opt-in" test_install_global_config_rules_opt_in
run_test "runtime validation fails before CLI execution for missing target repository" test_runtime_validation_missing_target
run_test "runtime output verifier catches invented filenames and unsupported claims" test_runtime_output_verifier_catches_bad_output
run_test "runtime validation runner writes verification outputs" test_runtime_validation_runner_writes_verification_outputs
run_test "hardware profile scripts expose platform-specific markers" test_profile_script_markers
run_test "editor compatibility docs cover config and tool validation" test_editor_compatibility_doc
run_test "model tool-use validation docs define evidence workflow" test_model_tool_use_validation_doc
run_test "online model discovery docs preserve offline local-first defaults" test_online_model_discovery_doc
run_test "multi-repository validation docs define sanitized evidence workflow" test_multi_repository_validation_doc
run_test "sample repository factory validation evidence is sanitized" test_sample_repository_factory_validation_evidence
run_test "sample repository factory docs define generated fixtures" test_sample_repository_factory_doc
run_test "agent surface docs define portability boundary" test_agent_surface_options_doc
run_test "language support docs define staged multi-language boundary" test_language_support_doc
run_test "optional language rule packs are evidence-gated and not globally loaded" test_optional_language_rule_packs
run_test "project detection docs and guidance are evidence-gated" test_project_detection_doc
run_test "sample repository factory creates expected fixtures" test_sample_repository_factory
run_test "prompt quality guardrails require filename fidelity and sourced lifecycle claims" test_prompt_quality_guardrails_require_filename_fidelity
run_test "tool-use docs define platform-aware approved write behavior" test_tool_use_docs_define_platform_aware_write_behavior
run_test "hardware-aware recommendation scripts emit sanitized model lanes" test_hardware_aware_recommendation_scripts
run_test "shared asset installation docs define centralized config strategy" test_shared_asset_installation_doc
run_test "recommended agent config generation writes local-only config" test_recommended_agent_config_generation

if [ "$FAILED" -eq 1 ]; then
  printf 'Test run failed. %s tests executed.\n' "$TEST_COUNT" >&2
  exit 1
fi

printf 'Test run passed. %s tests executed.\n' "$TEST_COUNT"
