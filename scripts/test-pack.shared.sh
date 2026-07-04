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
    END { exit 0 }
  ' "$REPO_ROOT/config/model-recommendations.tsv"
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
    "$REPO_ROOT/scripts/generate-runtime-context.linux.sh" \
    "$REPO_ROOT/scripts/generate-runtime-context.macos.sh" \
    "$REPO_ROOT/scripts/run-runtime-validation.linux.sh" \
    "$REPO_ROOT/scripts/run-runtime-validation.macos.sh"
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

test_runtime_validation_missing_target() {
  missing_repo="$(mktemp -d)"
  rmdir "$missing_repo"
  ! "$REPO_ROOT/scripts/run-runtime-validation.shared.sh" --target-repo "$missing_repo" >/tmp/continue-runtime.out 2>&1 &&
    grep -q "Target repository path does not exist" /tmp/continue-runtime.out
}

test_profile_script_markers() {
  grep -q "MlxRecommendation" "$REPO_ROOT/scripts/get-local-model-profile.macos.sh" &&
    grep -q "PlatformNotes" "$REPO_ROOT/scripts/get-local-model-profile.linux.sh"
}

run_test "validate-pack succeeds for repository" test_validate_succeeds
run_test "validate-pack fails for wrong expected version" test_validate_fails_for_wrong_version
run_test "model recommendation catalog has valid schema" test_catalog_schema
run_test "MLX model recommendation catalog has valid schema" test_mlx_catalog_schema
run_test "shell wrapper scripts are executable in git" test_shell_scripts_executable
run_test "Linux/macOS user-facing scripts do not require PowerShell" test_linux_macos_scripts_do_not_require_pwsh
run_test "runtime context generation captures useful files and excludes build output" test_runtime_context_generation
run_test "install script dry run does not modify target repository" test_install_dry_run
run_test "runtime validation fails before CLI execution for missing target repository" test_runtime_validation_missing_target
run_test "hardware profile scripts expose platform-specific markers" test_profile_script_markers

if [ "$FAILED" -eq 1 ]; then
  printf 'Test run failed. %s tests executed.\n' "$TEST_COUNT" >&2
  exit 1
fi

printf 'Test run passed. %s tests executed.\n' "$TEST_COUNT"
