#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FAILED=0
TEST_COUNT=0
SKIPPED_COUNT=0
TEST_TIER="full"
NO_RECEIPT=false
RUN_STARTED_SECONDS=$SECONDS

while [ "$#" -gt 0 ]; do
  case "$1" in
    --tier|-Tier)
      TEST_TIER="$(printf '%s' "$2" | tr '[:upper:]' '[:lower:]')"
      shift 2
      ;;
    --no-receipt|-NoReceipt)
      NO_RECEIPT=true
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

case "$TEST_TIER" in
  fast|integration|full) ;;
  *) printf 'Tier must be fast, integration, or full.\n' >&2; exit 1 ;;
esac

pass() {
  printf 'PASS %s\n' "$1"
}

fail() {
  printf 'FAIL %s - %s\n' "$1" "$2" >&2
  FAILED=1
}

run_test() {
  name="$1"
  shift
  category="fast"
  case "$name" in
    "release packaging scripts define archives, checksums, and sanitized dry runs"|\
    "runtime context generation captures useful files and excludes build output"|\
    "install script dry run does not modify target repository"|\
    "project classifier emits a sanitized evidence-backed profile"|\
    "install script activates evidence-backed project rule packs"|\
    "install script auto model config dry run is explicit"|\
    "install script read-only profile omits edit roles"|\
    "install script approved-write profile maps to model lanes"|\
    "install script model lanes generate scoped roles"|\
    "validated model installer updates local-only config"|\
    "validated model installer dry run is local only"|\
    "install script global config dry run is explicit"|\
    "install script writes global config with target references"|\
    "install script can include rules in global config by explicit opt-in"|\
    "runtime validation fails before CLI execution for missing target repository"|\
    "runtime output verifier catches invented filenames and unsupported claims"|\
    "runtime validation runner writes verification outputs"|\
    "sample repository factory creates expected fixtures"|\
    "medium language workflow matrix is complete and evidence-gated"|\
    "hardware-aware recommendation scripts emit sanitized model lanes"|\
    "capability registry and deterministic routing enforce policy boundaries"|\
    "general AI sessions are repository optional and dry-run first"|\
    "local text capabilities are session bound and typed"|\
    "provider discovery and engineering routing preserve policy boundaries"|\
    "optional LLM routing is advisory and registry gated"|\
    "local image capability is session bound typed and evidence gated"|\
    "recommended agent config generation writes local-only config"|\
    "agent surface adapters plan installs configure and report health safely"|\
    "workflow envelope contract is versioned private by default and cross-platform"|\
    "wiki synchronization is deterministic and hosted"|\
    "online model discovery normalizes Ollama and Hugging Face fixtures") category="integration" ;;
  esac
  if { [ "$TEST_TIER" = "fast" ] && [ "$category" = "integration" ]; } ||
     { [ "$TEST_TIER" = "integration" ] && [ "$category" != "integration" ]; }; then
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    return
  fi
  TEST_COUNT=$((TEST_COUNT + 1))
  started_seconds=$SECONDS
  if "$@"; then
    pass "$name [$((SECONDS - started_seconds)) s]"
  else
    fail "$name" "test command failed"
  fi
}

write_test_receipt() {
  [ "$NO_RECEIPT" = false ] || return 0
  [ "$TEST_TIER" = "full" ] || return 0
  [ -z "$(git -C "$REPO_ROOT" status --porcelain=v1 2>/dev/null)" ] || {
    printf 'Receipt not written: the working tree is not clean.\n'
    return 0
  }
  commit="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null)" || return 0
  tree="$(git -C "$REPO_ROOT" rev-parse 'HEAD^{tree}' 2>/dev/null)" || return 0
  git_dir="$(git -C "$REPO_ROOT" rev-parse --git-dir 2>/dev/null)" || return 0
  case "$git_dir" in
    /*|[A-Za-z]:*) ;;
    *) git_dir="$REPO_ROOT/$git_dir" ;;
  esac
  {
    printf 'schema=1\n'
    printf 'commit=%s\n' "$commit"
    printf 'tree=%s\n' "$tree"
    printf 'tier=full\n'
    printf 'runner=native-shell\n'
  } > "$git_dir/haven-42-test-receipt-v1"
  printf 'Wrote exact-tree full-test receipt for %s.\n' "$commit"
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
  output="$($REPO_ROOT/scripts/build-release-package.shared.sh --version 0.3.0 --dry-run --allow-dirty 2>&1)" || return 1
  printf '%s\n' "$output" | grep -q "Release package plan" || return 1
  printf '%s\n' "$output" | grep -q "haven-42-0.3.0.tar.gz" || return 1
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
    grep -q "Milestone 19 Completion Basis" "$REPO_ROOT/docs/release.md" &&
    grep -q "config/evidence-catalog.tsv" "$REPO_ROOT/docs/release.md" &&
    grep -q "complete for the promoted supported-surface set" "$REPO_ROOT/docs/release.md" &&
    grep -q "Verify Checksums" "$REPO_ROOT/docs/release.md" &&
    grep -q "GitHub Release" "$REPO_ROOT/docs/release.md" &&
    grep -q "| Milestone 19: Installer Profiles, Evidence Catalog, And Release Packaging | Complete |" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Future candidate expansion" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "\\[x\\] Complete Milestone 19 Continue installer profile, evidence catalog, and release packaging exit criteria" "$REPO_ROOT/TODO.md" &&
    grep -q "\\[x\\] Complete Milestone 19 install/configure/health parity for evidence-backed CLI adapters" "$REPO_ROOT/TODO.md" &&
    grep -q "Solution Architecture Review Backlog" "$REPO_ROOT/TODO.md" &&
    grep -q "\\[ \\] Add future surface-specific profile generation after non-Continue validation" "$REPO_ROOT/TODO.md" &&
    grep -Fxq "dist/" "$REPO_ROOT/.gitignore"
}
test_evidence_catalog_schema() {
  catalog="$REPO_ROOT/config/evidence-catalog.tsv"
  doc="$REPO_ROOT/docs/evidence-catalog.md"
  [ -f "$catalog" ] || return 1
  [ -f "$doc" ] || return 1
  head -n 1 "$catalog" | grep -q $'schema_version\tarea\tsubject\tsurface\tsurface_version\tprovider\tos\tmodel\toperation\tvalidation_mode\tstatus\tevidence\tnotes' || return 1
  awk -F'\t' '
    NR == 1 { next }
    NF != 13 { exit 1 }
    $1 != "2" { exit 1 }
    $1 == "" || $2 == "" || $3 == "" || $4 == "" || $5 == "" || $6 == "" || $7 == "" || $8 == "" || $9 == "" || $10 == "" || $11 == "" || $12 == "" || $13 == "" { exit 1 }
    $11 !~ /^(candidate-only|plan-review-candidate|plan-validated|review-validated|read-only-tool-validated|read-only-cli-validated|write-smoke-validated|approved-write-ready|static-validated|validated-by-tests|partial-pass)$/ { exit 1 }
    $12 ~ /^[A-Za-z]:|^\/|\\|\.\./ { exit 1 }
    $0 ~ /192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|localhost|itama|Users\\|OneDrive|customer|token|secret/ { exit 1 }
    $11 == "approved-write-ready" { approved = 1 }
    $11 == "candidate-only" { candidate = 1 }
    $11 == "read-only-tool-validated" { readonly = 1 }
    $11 == "write-smoke-validated" { writesmoke = 1 }
    END { if (!approved || !candidate || !readonly || !writesmoke) exit 1 }
  ' "$catalog" || return 1
  while IFS=$'\t' read -r schema_version area subject surface surface_version provider os model operation validation_mode status evidence notes; do
    [ "$schema_version" = "schema_version" ] && continue
    [ -e "$REPO_ROOT/$evidence" ] || return 1
  done < "$catalog"
  python3 - "$REPO_ROOT/config/capability-evidence-contract.json" <<'PY' &&
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    contract = json.load(handle)
assert contract["schemaVersion"] == 2
assert contract["aggregation"]["allowCrossSurfaceInheritance"] is False
assert contract["aggregation"]["allowCrossOperationInheritance"] is False
assert contract["aggregation"]["retainAllEvidencePaths"] is True
PY
  grep -q "config/evidence-catalog.tsv" "$doc" && grep -q "approved-write-ready" "$doc" && grep -q "Capability Evidence Contract v2" "$doc"
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
    grep -q "simple-hardware default" "$REPO_ROOT/config/model-recommendations.tsv" &&
    python3 - "$REPO_ROOT/config/model-fit-profiles.json" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    catalog = json.load(handle)
assert catalog["schemaVersion"] == 1
assert catalog["defaults"]["contextTargetTokens"] >= 1024
assert catalog["defaults"]["memoryReserveGb"] > 0
assert catalog["profiles"]
for profile in catalog["profiles"]:
    assert profile["matchPattern"]
    assert profile["estimatedWeightsGb"] > 0
    assert profile["kvCacheGbAtBaseline"] > 0
    assert profile["baselineContextTokens"] > 0
    assert profile["runtimeOverheadGb"] > 0
    assert profile["quantizationAssumption"]
    assert profile["architecture"] in {"dense", "mixture-of-experts"}
PY
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

test_github_actions_dependencies() {
  action_sources="$(cat \
    "$REPO_ROOT/.github/workflows/validate-pack.yml" \
    "$REPO_ROOT/scripts/generate-sample-repositories.ps1" \
    "$REPO_ROOT/scripts/generate-sample-repositories.shared.sh")"
  checkout_sha='d23441a48e516b6c34aea4fa41551a30e30af803'
  checkout_count="$(printf '%s' "$action_sources" | grep -Ec "actions/checkout@${checkout_sha}([^0-9a-f]|$)")"
  credential_count="$(printf '%s' "$action_sources" | grep -Ec 'persist-credentials:[[:space:]]*false')"

  ! printf '%s' "$action_sources" | grep -Eq 'actions/checkout@(v[0-9]+|main|master)([^0-9]|$)' &&
    [ "$checkout_count" -eq 6 ] &&
    [ "$credential_count" -eq 6 ] &&
    grep -Eq '^concurrency:' "$REPO_ROOT/.github/workflows/validate-pack.yml" &&
    grep -q 'timeout-minutes:' "$REPO_ROOT/.github/workflows/validate-pack.yml" &&
    grep -Eq 'package-ecosystem:[[:space:]]*github-actions' "$REPO_ROOT/.github/dependabot.yml" &&
    grep -Eq 'interval:[[:space:]]*weekly' "$REPO_ROOT/.github/dependabot.yml"
}

test_test_tier_contract() {
  grep -q 'ValidateSet("Fast", "Integration", "Full")' "$REPO_ROOT/scripts/test-pack.ps1" &&
    grep -q 'RUN_STARTED_SECONDS' "$REPO_ROOT/scripts/test-pack.shared.sh" &&
    grep -q 'haven-42-test-receipt-v1' "$REPO_ROOT/scripts/test-pack.ps1" &&
    grep -q 'haven-42-test-receipt-v1' "$REPO_ROOT/scripts/test-pack.shared.sh" &&
    grep -q 'Exact-tree full-test receipt found' "$REPO_ROOT/.githooks/pre-push" &&
    grep -q -- '-Tier Full -NoReceipt' "$REPO_ROOT/.github/workflows/validate-pack.yml" &&
    grep -q -- '--tier full --no-receipt' "$REPO_ROOT/.github/workflows/validate-pack.yml" &&
    ! grep -q 'Run pack validation' "$REPO_ROOT/.github/workflows/validate-pack.yml" &&
    grep -q 'GitHub Actions always runs Full independently' "$REPO_ROOT/docs/test-tiers.md"
}

test_os_aware_command_contract() {
  [ -f "$REPO_ROOT/scripts/CommandResolution.psm1" ] &&
    grep -q 'windows-cmd-shim' "$REPO_ROOT/scripts/CommandResolution.psm1" &&
    grep -q 'powershell-script' "$REPO_ROOT/scripts/CommandResolution.psm1" &&
    grep -q 'Resolve-ExternalCommand' "$REPO_ROOT/scripts/test-agent-cli-surface-models.ps1" &&
    ! grep -q '{TempDir}\\' "$REPO_ROOT/config/agent-cli-surface-defaults.json" &&
    python3 - "$REPO_ROOT" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
registry = json.loads((root / "config/workflows.json").read_text(encoding="utf-8"))
suffixes = {"windows": ".ps1", "linux": ".linux.sh", "macos": ".macos.sh"}
for workflow in registry["workflows"]:
    for platform, suffix in suffixes.items():
        entry = workflow["entryPoints"][platform]
        assert entry.endswith(suffix), (workflow["id"], platform, entry)
        assert (root / entry).is_file(), (workflow["id"], platform, entry)
PY
}

test_macos_wrapper_help_surface() {
  [ -x "$REPO_ROOT/scripts/run-macos-wrapper.sh" ] || return 1
  [ -x "$REPO_ROOT/scripts/test-macos-script-surface.macos.sh" ] || return 1
  grep -q 'Automated macOS installation is blocked' "$REPO_ROOT/scripts/bootstrap-macos-agent-host.sh" || return 1
  ! grep -Eq 'curl[^|]*\|[[:space:]]*(bash|sh)' "$REPO_ROOT/scripts/bootstrap-macos-agent-host.sh" || return 1
  ! grep -Eq '(^|[[:space:]])(brew|pip3?|python3? -m pip)[[:space:]]+install' "$REPO_ROOT/scripts/bootstrap-macos-agent-host.sh" || return 1
  grep -q 'pack virtual environment: mlx_lm.server' "$REPO_ROOT/scripts/get-local-model-profile.macos.sh" || return 1
  grep -q 'MLX_TIER="Low"' "$REPO_ROOT/scripts/get-local-model-profile.macos.sh" || return 1
  grep -q '\[ "$RAM_INT" -ge 24 \]' "$REPO_ROOT/scripts/get-local-model-profile.macos.sh" || return 1
  grep -q -- '--mlx-config' "$REPO_ROOT/scripts/install-continue-pack.shared.sh" || return 1
  grep -q 'provider: openai' "$REPO_ROOT/scripts/install-continue-pack.shared.sh" || return 1
  grep -q 'MlxStatus.*\[\[:space:\]\]\*' "$REPO_ROOT/scripts/install-continue-pack.shared.sh" || return 1
  grep -q 'MlxRecommendation.*\[\[:space:\]\]\*' "$REPO_ROOT/scripts/install-continue-pack.shared.sh" || return 1
  for script in "$REPO_ROOT/scripts"/*.macos.sh; do
    bash -n "$script" || return 1
    bash "$script" --help >/dev/null || return 1
  done
}

test_linux_macos_scripts_do_not_require_pwsh() {
  ! grep -Eq 'pwsh|PowerShell 7' \
    "$REPO_ROOT/scripts/validate-pack.linux.sh" \
    "$REPO_ROOT/scripts/validate-pack.macos.sh" \
    "$REPO_ROOT/scripts/invoke-workflow.linux.sh" \
    "$REPO_ROOT/scripts/invoke-workflow.macos.sh" \
    "$REPO_ROOT/scripts/invoke-workflow.shared.sh" \
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
  grep -q "Detected project ecosystem" /tmp/continue-install.out || return 1
  grep -q "Would write .continue/project-profile.json" /tmp/continue-install.out || return 1
  [ ! -e "$temp_repo/.continue" ]
}

test_project_profile_classifier() {
  temp_repo="$(mktemp -d)"
  printf '[project]\n' > "$temp_repo/pyproject.toml"
  profile_path="$temp_repo/profile.json"
  "$REPO_ROOT/scripts/get-project-profile.shared.sh" --target-repo "$temp_repo" --output-path "$profile_path" >/tmp/project-profile.out 2>&1 || return 1
  python3 - "$profile_path" "$temp_repo" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    profile = json.load(handle)
assert profile["SchemaVersion"] == 1
assert profile["ActivationMinimumConfidence"] == "medium"
assert "python" in profile["SelectedRulePackIds"]
assert sys.argv[2] not in json.dumps(profile)
assert profile["Privacy"]["TargetPathRecorded"] is False
assert profile["Privacy"]["FileContentsRead"] is False
PY
}

test_install_project_profile_activation() {
  temp_repo="$(mktemp -d)"
  printf '[project]\n' > "$temp_repo/pyproject.toml"
  "$REPO_ROOT/scripts/install-continue-pack.shared.sh" --target-repo "$temp_repo" --model-lanes >/tmp/project-profile-install.out 2>&1 || return 1
  [ -f "$temp_repo/.continue/project-profile.json" ] &&
    [ -f "$temp_repo/.continue/rules/active-language-python.md" ] &&
    [ ! -e "$temp_repo/.continue/rules/active-language-java.md" ] &&
    [ -f "$temp_repo/.continue/config.local.yaml" ] &&
    grep -q '"python"' "$temp_repo/.continue/project-profile.json"
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
    grep -q "New-FilenameFidelityFallback" "$REPO_ROOT/scripts/run-runtime-validation.ps1" &&
    grep -q "filename-fidelity-fallback.md" "$REPO_ROOT/scripts/run-runtime-validation.ps1" &&
    grep -q "FILENAME_NOT_IN_CONTEXT" "$REPO_ROOT/scripts/run-runtime-validation.ps1" &&
    grep -q "write_filename_fidelity_fallback" "$REPO_ROOT/scripts/run-runtime-validation.shared.sh" &&
    grep -q "filename-fidelity-fallback.md" "$REPO_ROOT/scripts/run-runtime-validation.shared.sh" &&
    grep -q "FILENAME_NOT_IN_CONTEXT" "$REPO_ROOT/scripts/run-runtime-validation.shared.sh" &&
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
    grep -q "npx -y @continuedev/cli@1.5.47 --config .continue/config.yaml" "$REPO_ROOT/docs/editor-compatibility.md" &&
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
    grep -q "candidate metadata only" "$REPO_ROOT/docs/online-model-discovery.md" &&
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

test_multi_source_model_discovery() {
  temp_root="$(mktemp -d)"
  output_path="$temp_root/candidates.json"
  "$REPO_ROOT/scripts/discover-online-model-candidates.shared.sh" \
    --sources ollama,huggingface \
    --families qwen3.5 \
    --source-html-path "$REPO_ROOT/examples/fixtures/ollama-model-library.html" \
    --hugging-face-json-path "$REPO_ROOT/examples/fixtures/huggingface-model-search-response.json" \
    --output-path "$output_path" >/tmp/multi-source-model-discovery.out 2>&1 || { rm -rf "$temp_root"; return 1; }
  python3 - "$output_path" "$REPO_ROOT/config/model-discovery-contract.json" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
contract = json.load(open(sys.argv[2], encoding="utf-8"))
assert report["SchemaVersion"] == 2
assert set(report["Sources"]) == {"ollama", "huggingface"}
assert report["PullsModels"] is False and report["RewritesContinueConfig"] is False
hub = [item for item in report["Candidates"] if item["SourceId"] == "huggingface"]
assert len(hub) == 2
assert all(item["ValidationStatus"] == "candidate-only" for item in report["Candidates"])
assert any("gguf" in item["Formats"] and "ollama-import" in item["RuntimeCandidates"] and item["DirectOllamaPull"] is False for item in hub)
assert {"Revision", "License", "QuantizationSignals"}.issubset(contract["candidateRequiredFields"])
PY
  result=$?
  rm -rf "$temp_root"
  return "$result"
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
    grep -q "Milestone 13 Completion Basis" "$REPO_ROOT/docs/multi-repository-validation.md" &&
    grep -q "Generated samples are acceptable for the milestone coverage target" "$REPO_ROOT/docs/multi-repository-validation.md" &&
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
    grep -q "node-service" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "java-spring-api" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "iac-terraform-kubernetes" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "Milestone 13: Broader Multi-Repository Validation | Complete" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "future real-repository runs continue as evidence expansion" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Complete Milestone 13 coverage" "$REPO_ROOT/TODO.md" &&
    grep -q "Future Multi-Repository Evidence Expansion" "$REPO_ROOT/TODO.md" &&
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
    grep -q "Generated Category Expansion Validation" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "node-service" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "java-spring-api" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "go-service" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "rust-cli" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "iac-terraform-kubernetes" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "sql-migrations" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "Runtime context generation" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "does not prove model or editor Agent behavior" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "No private local paths" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "Expanded generated-category evidence" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "examples/sample-repository-factory-validation.md" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "examples/sample-repository-factory-validation.md" "$REPO_ROOT/README.md"
}

test_sample_repository_factory_doc() {
  [ -f "$REPO_ROOT/docs/sample-repository-factory.md" ] &&
    grep -q "Milestone 16 Completion Basis" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "examples/sample-repository-factory-validation.md" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "python-api" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "typescript-frontend" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "node-service" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "java-spring-api" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "go-service" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "rust-cli" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "iac-terraform-kubernetes" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "sql-migrations" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "generate-sample-repositories.ps1" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "generate-sample-repositories.linux.sh" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "generate-sample-repositories.macos.sh" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "production starter projects" "$REPO_ROOT/docs/sample-repository-factory.md" &&
    grep -q "Generated Category Expansion Validation" "$REPO_ROOT/examples/sample-repository-factory-validation.md" &&
    grep -q "docs/sample-repository-factory.md" "$REPO_ROOT/README.md" &&
    grep -q "| Milestone 16: Sample Repository Factory | Complete |" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "\\[x\\] Complete Milestone 16 sample repository factory exit criteria" "$REPO_ROOT/TODO.md"
}

test_agent_surface_options_doc() {
  [ -f "$REPO_ROOT/docs/agent-surface-options.md" ] &&
    grep -q "Continue is the first supported surface" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Milestone 14 Positioning Completion Basis" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Full live validation parity belongs to Milestone 17" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Aider and OpenCode generated-sample evidence" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "docs/surface-specific-config-bundles.md" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "docs/setup-paths.md" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Candidate means" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Approved-write ready" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Cline" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Aider" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Non-Enterprise Use" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Milestone 17 Supported-Surface Completion Basis" "$REPO_ROOT/docs/agent-surface-promotion-gates.md" &&
    grep -q "fresh external evaluation" "$REPO_ROOT/docs/agent-surface-options.md" &&
    [ -f "$REPO_ROOT/docs/openhands-validation-boundary.md" ] &&
    grep -q "OpenHands Validation Boundary" "$REPO_ROOT/docs/openhands-validation-boundary.md" &&
    grep -q "disposable generated repository" "$REPO_ROOT/docs/openhands-validation-boundary.md" &&
    grep -q "SSH keys" "$REPO_ROOT/docs/openhands-validation-boundary.md" &&
    grep -q "Docker socket" "$REPO_ROOT/docs/openhands-validation-boundary.md" &&
    grep -q "unrestricted network access" "$REPO_ROOT/docs/openhands-validation-boundary.md" &&
    grep -q "docs/openhands-validation-boundary.md" "$REPO_ROOT/docs/agent-surface-promotion-gates.md" &&
    grep -q "docs/agent-surface-options.md" "$REPO_ROOT/README.md" &&
    grep -q "| Milestone 14: Agent Surface Portability And Broader Audience | Complete |" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "| Milestone 17: Agent Surface Compatibility Validation | Complete |" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "\\[x\\] Complete Milestone 14 positioning, support-boundary, and broader-audience exit criteria" "$REPO_ROOT/TODO.md" &&
    grep -q "\[x\] Move full cross-agent validation and install/configure/test parity out of Milestone 14 and keep it tracked in Milestones 17 and 19" "$REPO_ROOT/TODO.md" &&
    grep -q "\\[x\\] Complete Milestone 17 for the promoted supported-surface set" "$REPO_ROOT/TODO.md" &&
    grep -q "Future Agent Surface Evidence Expansion" "$REPO_ROOT/TODO.md" &&
    grep -q "\[x\] Add a local-only OpenCode Ollama config generator" "$REPO_ROOT/TODO.md" &&
    grep -q "\[x\] Validate OpenCode's installed CLI" "$REPO_ROOT/TODO.md" &&
    [ -f "$REPO_ROOT/docs/opencode-cli-model-testing.md" ] &&
    grep -q "Confirmed Command Boundaries" "$REPO_ROOT/docs/agent-cli-surface-model-testing.md" &&
    grep -q "opencode run" "$REPO_ROOT/docs/agent-cli-surface-model-testing.md" &&
    grep -q "hasValidationFailure" "$REPO_ROOT/scripts/test-agent-cli-surface-models.ps1" &&
    grep -q 'ScopedEditStatus.*failed' "$REPO_ROOT/scripts/test-agent-cli-surface-models.shared.sh" &&
    grep -q "\\[x\\] Define a safe OpenHands validation boundary before adding platform-agent validation automation" "$REPO_ROOT/TODO.md"
}



test_removed_agent_integrations() {
  for path in \
    docs/cline-readonly-validation.md \
    docs/cline-cli-model-testing.md \
    examples/cline-readonly-validation.md \
    examples/kilo-validation.md \
    scripts/run-kilo-code-validation.ps1 \
    scripts/test-cline-cli-models.ps1 \
    scripts/test-cline-cli-models.shared.sh \
    scripts/test-kilo-code-cli-models.ps1 \
    scripts/test-kilo-code-cli-models.shared.sh \
    scripts/test-roo-code-cli-models.ps1 \
    scripts/test-roo-code-cli-models.shared.sh; do
    [ ! -e "$REPO_ROOT/$path" ] || return 1
  done
  ! grep -Eqi 'cline|kilo|roo([ -]?code)' "$REPO_ROOT/config/agent-surface-solutions.json" &&
    ! grep -Eqi 'cline|kilo|roo([ -]?code)' "$REPO_ROOT/config/agent-surface-capabilities.json" &&
    ! grep -Eqi 'cline|kilo|roo([ -]?code)' "$REPO_ROOT/config/agent-cli-surface-defaults.json" &&
    ! grep -Eqi 'cline|kilo|roo([ -]?code)' "$REPO_ROOT/scripts/setup-agent-surface.shared.sh" &&
    grep -q "Removed Integrations" "$REPO_ROOT/docs/agent-surface-options.md" &&
    grep -q "Pass-To-Ship Gate" "$REPO_ROOT/docs/agent-integration-admission-policy.md" &&
    grep -q "If an evaluation fails, commit only a concise sanitized decision record" "$REPO_ROOT/docs/agent-integration-admission-policy.md" &&
    python3 - "$REPO_ROOT" <<'PY'
import json, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
solutions = json.loads((root / "config/agent-surface-solutions.json").read_text(encoding="utf-8"))
defaults = json.loads((root / "config/agent-cli-surface-defaults.json").read_text(encoding="utf-8"))
supported = {surface["id"] for surface in solutions["surfaces"] if surface["supportTier"] == "supported"}
for default in defaults["surfaces"]:
    assert re.sub(r"-cli$", "", default["surfaceKey"]) in supported
for wrapper in (root / "scripts").glob("test-*-cli-models.ps1"):
    match = re.fullmatch(r"test-(.+)-cli-models\.ps1", wrapper.name)
    if match:
        assert match.group(1) in supported, wrapper.name
PY
}
test_continue_cli_model_testing_doc() {
  [ -f "$REPO_ROOT/docs/continue-cli-model-testing.md" ] &&
    [ -f "$REPO_ROOT/scripts/test-continue-cli-models.ps1" ] &&
    [ -f "$REPO_ROOT/scripts/test-continue-cli-models.shared.sh" ] &&
    grep -q "Continue CLI Model Testing" "$REPO_ROOT/docs/continue-cli-model-testing.md" &&
    grep -q "test-continue-cli-models" "$REPO_ROOT/docs/continue-cli-model-testing.md" &&
    grep -q "command-template" "$REPO_ROOT/docs/continue-cli-model-testing.md" &&
    grep -q "Write Smoke Test" "$REPO_ROOT/docs/continue-cli-model-testing.md" &&
    grep -q "Editor Apply" "$REPO_ROOT/docs/continue-cli-model-testing.md" &&
    grep -q "ContinueArgumentsTemplate" "$REPO_ROOT/scripts/test-continue-cli-models.ps1" &&
    grep -q "ConfigPath" "$REPO_ROOT/scripts/test-continue-cli-models.ps1" &&
    grep -q "IncludeWriteSmoke" "$REPO_ROOT/scripts/test-continue-cli-models.ps1" &&
    grep -q "Initialize-DisposableGitBaseline" "$REPO_ROOT/scripts/test-continue-cli-models.ps1" &&
    grep -q "CONTINUE_ARGS_TEMPLATE" "$REPO_ROOT/scripts/test-continue-cli-models.shared.sh" &&
    grep -q "INCLUDE_WRITE_SMOKE" "$REPO_ROOT/scripts/test-continue-cli-models.shared.sh" &&
    grep -q "UNLOAD_AFTER_EACH" "$REPO_ROOT/scripts/test-continue-cli-models.shared.sh" &&
    grep -q "UNLOAD_AFTER_EACH" "$REPO_ROOT/scripts/test-continue-cli-models.shared.sh" &&
    grep -q "Continue CLI model test harness" "$REPO_ROOT/config/evidence-catalog.tsv" &&
    grep -q "docs/continue-cli-model-testing.md" "$REPO_ROOT/README.md" &&
    grep -q "docs/continue-cli-model-testing.md" "$REPO_ROOT/docs/agent-surface-options.md"
}
test_language_support_doc() {
  [ -f "$REPO_ROOT/docs/language-support.md" ] &&
    [ -f "$REPO_ROOT/examples/multi-language-workflow-validation.md" ] &&
    grep -q ".NET.*most mature" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Milestone 15 Completion Basis" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "examples/multi-language-workflow-validation.md" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Python" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "JavaScript / TypeScript" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Infrastructure as Code" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Do not apply .NET-specific advice" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Python API Sample" "$REPO_ROOT/examples/multi-language-workflow-validation.md" &&
    grep -q "TypeScript Frontend Sample" "$REPO_ROOT/examples/multi-language-workflow-validation.md" &&
    grep -q "Repository discovery | Passed verification | Passed verification" "$REPO_ROOT/examples/multi-language-workflow-validation.md" &&
    grep -q "Implementation planning | Passed verification | Passed verification" "$REPO_ROOT/examples/multi-language-workflow-validation.md" &&
    grep -q "Code review | Passed verification | Passed verification" "$REPO_ROOT/examples/multi-language-workflow-validation.md" &&
    grep -q "docs/language-support.md" "$REPO_ROOT/README.md" &&
    grep -q "| Milestone 15: Multi-Language Engineering Support | Complete |" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "\\[x\\] Validate repository discovery, implementation planning, and code review against Python and JavaScript/TypeScript samples" "$REPO_ROOT/TODO.md"
}


test_optional_language_rule_packs() {
  [ -f "$REPO_ROOT/.continue/rule-packs/python.md" ] &&
    [ -f "$REPO_ROOT/.continue/rule-packs/typescript.md" ] &&
    [ -f "$REPO_ROOT/.continue/rule-packs/java.md" ] &&
    [ -f "$REPO_ROOT/.continue/rule-packs/go.md" ] &&
    [ -f "$REPO_ROOT/.continue/rule-packs/rust.md" ] &&
    [ -f "$REPO_ROOT/.continue/rule-packs/sql.md" ] &&
    [ -f "$REPO_ROOT/.continue/rule-packs/infrastructure-as-code.md" ] &&
    [ -f "$REPO_ROOT/docs/language-rule-packs.md" ] &&
    [ -f "$REPO_ROOT/examples/language-rule-pack-validation.md" ] &&
    [ -f "$REPO_ROOT/examples/multi-language-workflow-validation.md" ] &&
    grep -q "optional: true" "$REPO_ROOT/.continue/rule-packs/python.md" &&
    grep -q "pyproject.toml" "$REPO_ROOT/.continue/rule-packs/python.md" &&
    grep -q "unconfirmed" "$REPO_ROOT/.continue/rule-packs/python.md" &&
    grep -q "optional: true" "$REPO_ROOT/.continue/rule-packs/typescript.md" &&
    grep -q "package.json" "$REPO_ROOT/.continue/rule-packs/typescript.md" &&
    grep -q "unconfirmed" "$REPO_ROOT/.continue/rule-packs/typescript.md" &&
    grep -q "optional: true" "$REPO_ROOT/.continue/rule-packs/java.md" &&
    grep -q "pom.xml" "$REPO_ROOT/.continue/rule-packs/java.md" &&
    grep -q "unconfirmed" "$REPO_ROOT/.continue/rule-packs/java.md" &&
    grep -q "optional: true" "$REPO_ROOT/.continue/rule-packs/go.md" &&
    grep -q "go.mod" "$REPO_ROOT/.continue/rule-packs/go.md" &&
    grep -q "unconfirmed" "$REPO_ROOT/.continue/rule-packs/go.md" &&
    grep -q "optional: true" "$REPO_ROOT/.continue/rule-packs/rust.md" &&
    grep -q "Cargo.toml" "$REPO_ROOT/.continue/rule-packs/rust.md" &&
    grep -q "unconfirmed" "$REPO_ROOT/.continue/rule-packs/rust.md" &&
    grep -q "optional: true" "$REPO_ROOT/.continue/rule-packs/sql.md" &&
    grep -q ".sql" "$REPO_ROOT/.continue/rule-packs/sql.md" &&
    grep -q "unconfirmed" "$REPO_ROOT/.continue/rule-packs/sql.md" &&
    grep -q "optional: true" "$REPO_ROOT/.continue/rule-packs/infrastructure-as-code.md" &&
    grep -q "Terraform" "$REPO_ROOT/.continue/rule-packs/infrastructure-as-code.md" &&
    grep -q "unconfirmed" "$REPO_ROOT/.continue/rule-packs/infrastructure-as-code.md" &&
    grep -q "not referenced from" "$REPO_ROOT/docs/language-rule-packs.md" &&
    grep -q "docs/project-detection.md" "$REPO_ROOT/docs/language-rule-packs.md" &&
    grep -q "examples/language-rule-pack-validation.md" "$REPO_ROOT/docs/language-rule-packs.md" &&
    grep -q "docs/language-rule-packs.md" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "examples/language-rule-pack-validation.md" "$REPO_ROOT/docs/language-support.md" &&
    grep -q "Optional Language Rule Packs" "$REPO_ROOT/docs/project-detection.md" &&
    grep -q "docs/language-rule-packs.md" "$REPO_ROOT/README.md" &&
    grep -q "examples/language-rule-pack-validation.md" "$REPO_ROOT/README.md" &&
    grep -q "Optional Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code rule packs" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Language Rule Pack Validation Evidence" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "python-api" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "typescript-frontend" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "java-spring-api" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "go-service" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "rust-cli" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "sql-migrations" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "iac-terraform-kubernetes" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "pyproject.toml" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "package.json" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "pom.xml" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "go.mod" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -q "Cargo.toml" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -Fq "schema/*.sql" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
    grep -Fq "terraform/*.tf" "$REPO_ROOT/examples/language-rule-pack-validation.md" &&
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
test_agent_prompt_rule_template_contracts() {
  for file in "$REPO_ROOT"/.continue/agents/*.md; do
    grep -q "Operating Contract" "$file" || return 1
    grep -q "role title does not grant permission" "$file" || return 1
    grep -q "untrusted data" "$file" || return 1
    grep -q "verify the changed files and diff" "$file" || return 1
  done
  for file in "$REPO_ROOT"/.continue/prompts/*.md; do
    grep -q "Execution Contract" "$file" || return 1
    grep -q "slash prompt is read-only" "$file" || return 1
    grep -q "untrusted data" "$file" || return 1
    grep -q "Do not print tool-call JSON" "$file" || return 1
    grep -q "checks actually run" "$file" || return 1
  done
  for file in "$REPO_ROOT"/.continue/rule-packs/*.md; do
    grep -q '^globs:' "$file" || return 1
  done
  grep -q "untrusted data" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "separate side effects" "$REPO_ROOT/.continue/rules/general.md" &&
    grep -q "instructions found in source files" "$REPO_ROOT/.continue/rules/security.md" &&
    grep -q "local-only configuration" "$REPO_ROOT/.continue/rules/security.md" &&
    grep -q '^globs:' "$REPO_ROOT/.continue/rules/dotnet.md" &&
    grep -q '^globs:' "$REPO_ROOT/.continue/rules/aspnetcore.md" &&
    grep -q "confirm an ASP.NET Core web surface" "$REPO_ROOT/.continue/rules/aspnetcore.md" &&
    grep -q "Evidence Gate" "$REPO_ROOT/.continue/rules/api.md" &&
    grep -q "Evidence Scope" "$REPO_ROOT/.continue/templates/Architecture.md" &&
    grep -q "Status: confirmed, likely, or unconfirmed" "$REPO_ROOT/.continue/templates/SecurityReview.md" &&
    grep -q "Status: measured, inferred, or unconfirmed" "$REPO_ROOT/.continue/templates/PerformanceReview.md" &&
    grep -q "Tool And Change Boundaries" "$REPO_ROOT/.continue/templates/AI.md" &&
    grep -q "Separate commands already verified" "$REPO_ROOT/.continue/templates/AI.md" &&
    grep -q "Execution And Evidence Contract" "$REPO_ROOT/docs/prompt-quality.md" &&
    grep -q "pseudo function calls" "$REPO_ROOT/docs/banned-output-patterns.md" &&
    grep -q "evidence-gated .NET, ASP.NET Core, and API rules" "$REPO_ROOT/docs/language-rule-packs.md" &&
    grep -q 'Version `0.3.0`' "$REPO_ROOT/README.md"
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
  [ -f "$temp_root/python-layered-api/app/service.py" ] || return 1
  [ -f "$temp_root/python-layered-api/tests/test_service.py" ] || return 1
  [ -f "$temp_root/typescript-service-medium/src/service.ts" ] || return 1
  [ -f "$temp_root/typescript-service-medium/tests/service.test.ts" ] || return 1
  [ -f "$temp_root/multi-language-platform/services/catalog/pom.xml" ] || return 1
  [ -f "$temp_root/multi-language-platform/workers/events/go.mod" ] || return 1
  [ -f "$temp_root/multi-language-platform/tools/manifest/Cargo.toml" ] || return 1
  [ -f "$temp_root/multi-language-platform/database/schema/001_catalog.sql" ] || return 1
  [ -f "$temp_root/multi-language-platform/infrastructure/terraform/main.tf" ] || return 1

  grep -q "# Python API Sample" "$temp_root/python-api/README.md" || return 1
  grep -q "python3 -m venv .venv" "$temp_root/python-api/README.md" || return 1
  grep -q "python -m pytest" "$temp_root/python-api/README.md" || return 1
  [ -f "$temp_root/python-api/.gitignore" ] || return 1
  grep -Fxq ".venv/" "$temp_root/python-api/.gitignore" || return 1
  grep -Fxq "__pycache__/" "$temp_root/python-api/.gitignore" || return 1
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
  grep -q "python-api" /tmp/sample-factory-list.out &&
    grep -q "sql-migrations" /tmp/sample-factory-list.out &&
    grep -q "python-layered-api" /tmp/sample-factory-list.out &&
    grep -q "typescript-service-medium" /tmp/sample-factory-list.out &&
    grep -q "multi-language-platform" /tmp/sample-factory-list.out
}

test_language_workflow_validation_matrix() {
  command -v python3 >/dev/null 2>&1 || return 1
  matrix="$REPO_ROOT/config/language-workflow-validation-matrix.json"
  doc="$REPO_ROOT/docs/language-workflow-validation-matrix.md"
  runner="$REPO_ROOT/scripts/run-language-workflow-matrix.ps1"
  shared_runner="$REPO_ROOT/scripts/run-language-workflow-matrix.shared.sh"
  linux_runner="$REPO_ROOT/scripts/run-language-workflow-matrix.linux.sh"
  macos_runner="$REPO_ROOT/scripts/run-language-workflow-matrix.macos.sh"
  [ -f "$matrix" ] && [ -f "$doc" ] && [ -f "$runner" ] && [ -f "$shared_runner" ] && [ -f "$linux_runner" ] && [ -f "$macos_runner" ] || return 1
  python3 - "$matrix" <<'PY'
import json
import pathlib
import sys

matrix = json.loads(pathlib.Path(sys.argv[1]).read_text())
expected_packs = {"python", "typescript", "java", "go", "rust", "sql", "infrastructure-as-code"}
expected_operations = {"repository-discovery", "implementation-plan", "code-review", "scoped-write"}
assert matrix["schemaVersion"] == 1
assert set(matrix["requiredOperations"]) == expected_operations
assert {entry["rulePackId"] for entry in matrix["entries"]} == expected_packs
for entry in matrix["entries"]:
    assert entry["fixtureComplexity"] == "medium"
    assert entry["fixtureStatus"] == "static-validated"
    assert set(entry["operations"]) == expected_operations
    assert set(entry["operations"].values()) <= {"validated", "failed-model-validation"}
    assert set(entry["operationEvidence"]) == expected_operations
    assert set(entry["operationModels"]) == expected_operations
validated = sum(value == "validated" for entry in matrix["entries"] for value in entry["operations"].values())
failed = sum(value == "failed-model-validation" for entry in matrix["entries"] for value in entry["operations"].values())
assert validated == 28
assert failed == 0
assert matrix["latestValidation"]["surfaceVersion"] == "1.5.47"
assert "devstral-small-2:24b" in matrix["latestValidation"]["models"]
assert "qwen3.5:35b" in matrix["latestValidation"]["models"]
native = matrix["nativeOperatingSystemEvidence"]
assert len(native) == 4
linux = [item for item in native if item["operatingSystem"].startswith("Linux ")]
macos = [item for item in native if item["operatingSystem"] == "macOS (Apple Silicon)"]
assert len(linux) == 2
assert len(macos) == 2
assert sum(item["model"] == "qwen3.5:9b" and item["validatedCells"] == 4 and item["failedCells"] == 0 for item in macos) == 1
assert sum(item["model"] == "devstral-small-2:24b" and item["validatedCells"] == 28 and item["failedCells"] == 0 for item in macos) == 1
assert all(item["evidenceDocument"] for item in native)
PY
  grep -q "Static fixture success alone never promotes" "$doc" &&
    grep -q "external Git diff" "$doc" &&
    grep -q "28 of 28" "$doc" &&
    grep -q "Native Linux and macOS runners are available" "$doc" &&
    grep -q "Native Linux Evidence" "$doc" &&
    grep -q "language-workflow-validation-matrix.json" "$doc" &&
    grep -q -- "--readonly" "$runner" &&
    grep -q -- "--auto" "$runner" &&
    grep -q "ConvertTo-SanitizedOutput" "$runner" &&
    grep -q "UnloadAfterRun" "$runner" &&
    grep -q "AllowLoadedModels" "$runner" &&
    grep -q -- "--readonly" "$shared_runner" &&
    grep -q -- "--auto" "$shared_runner" &&
    grep -q "trap handle_interruption HUP INT TERM" "$shared_runner" &&
    grep -q -- "--format json" "$shared_runner" &&
    grep -q "unload_models" "$shared_runner" &&
    grep -q "UNREAD_SOURCE_CLAIM" "$shared_runner" &&
    grep -q "Use the available read tools to open every named evidence file" "$shared_runner" &&
    grep -q 'http://127.0.0.1:11434' "$shared_runner" &&
    grep -q 'openai) curl -fsS' "$shared_runner" &&
    grep -q 'Skipping unload for' "$shared_runner" &&
    grep -q 'OpenAI-compatible endpoint' "$doc" &&
    grep -q 'resolve_existing_path' "$shared_runner" &&
    grep -q 'resolve_continue_command' "$shared_runner" &&
    grep -q '/opt/homebrew/bin/npx' "$shared_runner" &&
    ! grep -q 'mapfile' "$shared_runner" &&
    grep -q 'with no other text on that line' "$shared_runner" &&
    grep -q -- "--allow-loaded-models" "$shared_runner" &&
    grep -q "run-language-workflow-matrix.shared.sh" "$linux_runner" &&
    grep -q "run-language-workflow-matrix.shared.sh" "$macos_runner" &&
    grep -q 'bootstrap-macos-agent-host.sh' "$REPO_ROOT/docs/macos-agent-host-bootstrap.md" &&
    grep -q 'Native macOS Evidence' "$doc" &&
    grep -q 'Native macOS Python Smoke' "$REPO_ROOT/examples/language-rule-pack-validation.md"
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
  lane_profile_path="$temp_root/lane-model-profile.json"
  lane_catalog_path="$temp_root/lane-evidence.tsv"
  lane_output_path="$temp_root/lane-recommendation.json"

  cat > "$profile_path" <<'JSON'
{
  "Platform": "Windows",
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
assert report["ModelLanes"]["Contract"] == "surface-neutral"
assert report["ModelLanes"]["WriteSafe"]["ToolUse"] == "approved-write"
assert "edit" in report["ModelLanes"]["WriteSafe"]["RecommendedRoles"]
assert "edit" in report["ContinueProfiles"]["WriteSafe"]["Roles"]
assert "edit" not in report["ContinueProfiles"]["PlanOnly"]["Roles"]
assert report["ModelProfilePath"] == "redacted"
assert report["Privacy"]["RepositoryContentSent"] is False
assert report["Privacy"]["HardwareProfileSentOnline"] is False
assert not re.search(r"Users|OneDrive|192\.168\.|localhost", text)
PY

  cat > "$lane_profile_path" <<'JSON'
{
  "Platform": "Linux",
  "CpuArchitecture": "x64",
  "SystemRamGb": 128,
  "Gpus": [{"Name":"fixture gpu","VramGb":64,"MemoryType":"dedicated"}],
  "OllamaModels": ["qwen3.5:9b", "qwen3-coder:30b"]
}
JSON

  printf '%s\n' \
    $'schema_version\tarea\tsubject\tsurface\tsurface_version\tprovider\tos\tmodel\toperation\tvalidation_mode\tstatus\tevidence\tnotes' \
    $'2\tmodel-tool-use\tsmall write\tContinue Agent\tnot-recorded\tOllama\tLinux\tqwen3.5:9b\tscoped-write\teditor-agent\tapproved-write-ready\texamples/model-tool-use-validation.md\tSmall validated writer.' \
    $'2\tmodel-tool-use\tsmall plan\tContinue Agent\tnot-recorded\tOllama\tLinux\tqwen3.5:9b\tplan\teditor-agent\tplan-validated\texamples/model-tool-use-validation.md\tSmall validated planner.' \
    $'2\tmodel-tool-use\tsmall review\tContinue Agent\tnot-recorded\tOllama\tLinux\tqwen3.5:9b\treview\teditor-agent\treview-validated\texamples/model-tool-use-validation.md\tSmall validated reviewer.' \
    $'2\tmodel-tool-use\tlarge plan\tContinue Agent\tnot-recorded\tOllama\tLinux\tqwen3-coder:30b\tplan\teditor-agent\tplan-validated\texamples/model-tool-use-validation.md\tLarge validated planner.' \
    $'2\tmodel-tool-use\tlarge review\tContinue Agent\tnot-recorded\tOllama\tLinux\tqwen3-coder:30b\treview\teditor-agent\treview-validated\texamples/model-tool-use-validation.md\tLarge validated reviewer.' \
    > "$lane_catalog_path"

  "$REPO_ROOT/scripts/recommend-local-agent-config.shared.sh" \
    --model-profile-path "$lane_profile_path" \
    --evidence-catalog-path "$lane_catalog_path" \
    --output-path "$lane_output_path" \
    --context-target-tokens 32768 \
    --memory-reserve-gb 6 \
    --vram-selection-mode MaxDedicated >/tmp/lane-scoring-recommendation.out 2>&1 || return 1

  python3 - "$lane_output_path" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    report = json.load(handle)
assert report["SelectionPolicy"]["Version"] == 1
assert report["FitPolicy"]["Version"] == 1
assert report["FitPolicy"]["ContextTargetTokens"] == 32768
assert report["Recommendation"]["WriteSafeModel"] == "qwen3.5:9b"
assert report["Recommendation"]["PlanOnlyModel"] == "qwen3-coder:30b"
assert report["Recommendation"]["DeepReviewModel"] == "qwen3-coder:30b"
candidates = {item["Model"]: item for item in report["Candidates"]}
assert candidates["qwen3.5:9b"]["LaneScores"]["WriteSafe"]["Eligible"] is True
assert candidates["qwen3.5:9b"]["ModelFit"]["Source"] == "model-fit-catalog"
assert candidates["qwen3.5:9b"]["ModelFit"]["MemoryReserveGb"] == 6
assert candidates["qwen3.5:9b"]["RecommendedMinVramGb"] == 16.5
assert candidates["qwen3-coder:30b"]["LaneScores"]["WriteSafe"]["Eligible"] is False
assert candidates["qwen3-coder:30b"]["LaneScores"]["PlanOnly"]["Score"] > candidates["qwen3.5:9b"]["LaneScores"]["PlanOnly"]["Score"]
assert candidates["qwen3-coder:30b"]["LaneScores"]["DeepReview"]["Score"] > candidates["qwen3.5:9b"]["LaneScores"]["DeepReview"]["Score"]
PY
  grep -q "VramSelectionMode" "$REPO_ROOT/scripts/recommend-local-agent-config.ps1" &&
    grep -q "config/evidence-catalog.tsv" "$REPO_ROOT/scripts/recommend-local-agent-config.ps1" &&
    grep -q "python3 is required" "$REPO_ROOT/scripts/recommend-local-agent-config.shared.sh" &&
    grep -q '"ModelLanes"' "$REPO_ROOT/scripts/recommend-local-agent-config.shared.sh" &&
    grep -q '"SelectionPolicy"' "$REPO_ROOT/scripts/recommend-local-agent-config.shared.sh" &&
    grep -q "HardwareProfileSentOnline" "$REPO_ROOT/scripts/recommend-local-agent-config.shared.sh" &&
    grep -q "ModelLanes" "$REPO_ROOT/docs/hardware-aware-recommendations.md" &&
    grep -q "WRITE SAFE" "$REPO_ROOT/docs/hardware-aware-recommendations.md" &&
    grep -q "Selection policy version 1" "$REPO_ROOT/docs/hardware-aware-recommendations.md" &&
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

test_agent_surface_adapters() {
  temp_root="$(mktemp -d)"
  trap 'rm -rf "$temp_root"' RETURN
  mkdir -p "$temp_root/.git/info"
  : > "$temp_root/.git/info/exclude"
  recommendation_path="$temp_root/recommendation.json"
  cat > "$recommendation_path" <<'JSON'
{
  "Recommendation": {
    "WriteSafeModel": "qwen3.5:9b",
    "PlanOnlyModel": "devstral-small-2:24b",
    "DeepReviewModel": "qwen3-coder:30b"
  }
}
JSON

  "$REPO_ROOT/scripts/setup-agent-surface.shared.sh" --action Plan >/tmp/aider-adapter-plan.out 2>&1 || return 1
  grep -q "aider-chat==0.86.2" /tmp/aider-adapter-plan.out || return 1
  grep -q "local-only" /tmp/aider-adapter-plan.out || return 1
  ! "$REPO_ROOT/scripts/setup-agent-surface.shared.sh" --action Install --install-method pipx --dry-run >/tmp/aider-adapter-install.out 2>&1 || return 1
  grep -q "aider-chat==0.86.2" /tmp/aider-adapter-install.out || return 1
  grep -q "Automated third-party installation is blocked" /tmp/aider-adapter-install.out || return 1

  "$REPO_ROOT/scripts/setup-agent-surface.shared.sh" \
    --action Configure \
    --target-repo "$temp_root" \
    --recommendation-path "$recommendation_path" \
    --lane PlanOnly \
    --ollama-base-url "http://example.invalid:11434" >/tmp/aider-adapter-configure.out 2>&1 || return 1

  config_path="$temp_root/.aider.conf.local.yml"
  [ -f "$config_path" ] || return 1
  grep -q '^model: ollama_chat/devstral-small-2:24b$' "$config_path" || return 1
  grep -q '^auto-commits: false$' "$config_path" || return 1
  grep -q '^dirty-commits: false$' "$config_path" || return 1
  grep -Fxq '.aider.conf.local.yml' "$temp_root/.git/info/exclude" || return 1

  "$REPO_ROOT/scripts/setup-agent-surface.shared.sh" --action Health --target-repo "$temp_root" --aider-command sh >/tmp/aider-adapter-health.out 2>&1 || return 1
  grep -q 'Aider adapter health: healthy' /tmp/aider-adapter-health.out || return 1

  "$REPO_ROOT/scripts/setup-agent-surface.shared.sh" --surface opencode --action Plan >/tmp/opencode-adapter-plan.out 2>&1 || return 1
  grep -q 'opencode-ai' /tmp/opencode-adapter-plan.out || return 1
  ! "$REPO_ROOT/scripts/setup-agent-surface.shared.sh" --surface opencode --action Install --dry-run >/tmp/opencode-adapter-install.out 2>&1 || return 1
  grep -q 'opencode-ai@1.18.2' /tmp/opencode-adapter-install.out || return 1
  grep -q 'Automated third-party installation is blocked' /tmp/opencode-adapter-install.out || return 1
  "$REPO_ROOT/scripts/setup-agent-surface.shared.sh" --surface opencode --action Configure --target-repo "$temp_root" --recommendation-path "$recommendation_path" --lane PlanOnly --ollama-base-url 'http://example.invalid:11434' >/tmp/opencode-adapter-configure.out 2>&1 || return 1
  python3 - "$temp_root/.opencode.local.json" <<'PY' || return 1
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle: config = json.load(handle)
assert config["model"] == "ollama/devstral-small-2:24b"
assert config["provider"]["ollama"]["options"]["baseURL"] == "http://example.invalid:11434/v1"
PY
  grep -Fxq '.opencode.local.json' "$temp_root/.git/info/exclude" || return 1
  "$REPO_ROOT/scripts/setup-agent-surface.shared.sh" --surface opencode --action Health --target-repo "$temp_root" --opencode-command sh >/tmp/opencode-adapter-health.out 2>&1 || return 1
  grep -q 'OpenCode adapter health: healthy' /tmp/opencode-adapter-health.out || return 1
  ! grep -q 'pwsh' "$REPO_ROOT/scripts/setup-agent-surface.shared.sh"
}

test_workflow_envelope_contract() {
  command -v python3 >/dev/null 2>&1 || return 1
  [ -f "$REPO_ROOT/config/workflow-envelope-contract.json" ] || return 1
  [ -f "$REPO_ROOT/docs/workflow-envelope-contract.md" ] || return 1
  request='{"schemaVersion":1,"requestId":"shell-pack-test","workflowId":"validate-pack","platform":"linux","dryRun":true,"arguments":["--expected-version","0.3.0"]}'
  output="$("$REPO_ROOT/scripts/invoke-workflow.linux.sh" --request-json "$request")" || return 1
  printf '%s' "$output" | python3 -c 'import json,sys; value=json.load(sys.stdin); assert value["schemaVersion"] == 1; assert value["status"] == "planned"; assert value["workflow"]["argumentCount"] == 2; assert not value["result"]["invoked"]; assert any(event["type"] == "warning" for event in value["events"])' || return 1
  ! printf '%s' "$output" | grep -q 'expected-version'
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

test_capability_registry_and_routing() {
  registry="$REPO_ROOT/config/capabilities.json"
  artifacts="$REPO_ROOT/config/typed-artifact-contract.json"
  resolver="$REPO_ROOT/scripts/resolve-capability.shared.sh"
  python3 - "$registry" "$artifacts" <<'PY'
import json, sys
registry = json.load(open(sys.argv[1], encoding="utf-8"))
artifacts = json.load(open(sys.argv[2], encoding="utf-8"))
assert registry["schemaVersion"] == 1
assert artifacts["schemaVersion"] == 1
assert len(registry["capabilities"]) == 6
assert len({item["id"] for item in registry["capabilities"]}) == 6
artifact_ids = {item["id"] for item in artifacts["artifactTypes"]}
states = set(registry["availabilityStates"])
for capability in registry["capabilities"]:
    assert capability["availability"]["state"] in states
    assert set(capability["outputArtifactTypes"]) <= artifact_ids
    assert {"readsRepository", "writesFiles", "networkAccess", "downloadsModels", "externalProvider", "requiresApproval"} <= set(capability["policy"])
PY
  chat="$($resolver --text 'I want to chat with AI' --json)" || return 1
  software="$($resolver --text 'please review code' --json)" || return 1
  ambiguous="$($resolver --text 'write code' --json)" || return 1
  unmatched="$($resolver --text 'do something unusual' --json)" || return 1
  python3 - "$chat" "$software" "$ambiguous" "$unmatched" <<'PY'
import json, sys
chat, software, ambiguous, unmatched = [json.loads(value) for value in sys.argv[1:]]
assert chat["Status"] == "selected" and chat["Selected"]["Id"] == "general.chat"
assert chat["InvocationAllowed"] is False
assert software["Selected"]["Id"] == "engineering.software-work"
assert software["Selected"]["Availability"]["state"] == "available"
assert ambiguous["Status"] == "needs-clarification" and len(ambiguous["Candidates"]) == 2
assert unmatched["Status"] == "unmatched" and unmatched["InvocationAllowed"] is False
PY
}

test_general_ai_session_workspace() {
  session_root="$(mktemp -d)"
  session_script="$REPO_ROOT/scripts/start-ai-session.shared.sh"
  menu="$($session_script --list --json)" || { rm -rf "$session_root"; return 1; }
  plan="$($session_script --capability-id general.chat --workspace-root "$session_root" --session-id dry-run-session --json)" || { rm -rf "$session_root"; return 1; }
  created="$($session_script --text 'summarize a document' --workspace-root "$session_root" --session-id created-session --apply --json)" || { rm -rf "$session_root"; return 1; }
  ambiguous="$($session_script --text 'write code' --workspace-root "$session_root" --session-id ambiguous-session --apply --json)" || { rm -rf "$session_root"; return 1; }
  python3 - "$menu" "$plan" "$created" "$ambiguous" "$session_root" <<'PY'
import json, pathlib, sys
menu, plan, created, ambiguous = [json.loads(value) for value in sys.argv[1:5]]
root = pathlib.Path(sys.argv[5])
assert menu["Kind"] == "capability-menu" and len(menu["Items"]) == 6
assert plan["Status"] == "planned" and plan["WorkspaceCreated"] is False and plan["CapabilityInvoked"] is False
assert not pathlib.Path(plan["SessionPath"]).exists()
assert created["Status"] == "created" and pathlib.Path(created["SessionPath"], "session.json").is_file()
assert pathlib.Path(created["SessionPath"], "artifacts").is_dir()
metadata_text = pathlib.Path(created["SessionPath"], "session.json").read_text(encoding="utf-8")
assert json.loads(metadata_text)["capabilityId"] == "content.summarize"
assert "summarize a document" not in metadata_text
assert ambiguous["Status"] == "needs-clarification" and ambiguous["WorkspaceCreated"] is False
assert not (root / "ambiguous-session").exists()
PY
  result=$?
  rm -rf "$session_root"
  return "$result"
}

test_local_text_capability_adapter() {
  root="$(mktemp -d)"
  session="$REPO_ROOT/scripts/start-ai-session.shared.sh"
  provider="$REPO_ROOT/scripts/invoke-local-text-capability.shared.sh"
  fixture="$REPO_ROOT/examples/fixtures/ollama-chat-response.json"
  openai_fixture="$REPO_ROOT/examples/fixtures/openai-chat-response.json"
  $session --capability-id content.summarize --workspace-root "$root" --session-id summary --apply --json >/dev/null || { rm -rf "$root"; return 1; }
  plan="$($provider --capability-id content.summarize --prompt 'private prompt marker' --model fixture-model --session-path "$root/summary" --artifact-name summary.json --json)" || { rm -rf "$root"; return 1; }
  result="$($provider --capability-id content.summarize --prompt 'private prompt marker' --model fixture-model --session-path "$root/summary" --artifact-name summary.json --response-fixture-path "$fixture" --execute --apply --json)" || { rm -rf "$root"; return 1; }
  llama="$($provider --capability-id content.summarize --prompt 'private prompt marker' --model example-text-model --session-path "$root/summary" --provider-id llamacpp.local-text --engine-id llama.cpp --backend-id cuda --hardware-profile linux-x64-nvidia-rtx5000-16gb --response-fixture-path "$openai_fixture" --execute --json)" || { rm -rf "$root"; return 1; }
  ! $provider --capability-id content.summarize --prompt blocked --model example-text-model --session-path "$root/summary" --provider-id llamacpp.local-text --engine-id llama.cpp --backend-id sycl --hardware-profile linux-x64-intel --response-fixture-path "$openai_fixture" --execute --json >/dev/null 2>&1 || { rm -rf "$root"; return 1; }
  python3 - "$plan" "$result" "$llama" "$root/summary/artifacts/summary.json" <<'PY'
import json, pathlib, sys
plan, result = json.loads(sys.argv[1]), json.loads(sys.argv[2])
llama = json.loads(sys.argv[3])
artifact_path = pathlib.Path(sys.argv[4])
assert plan["Status"] == "planned" and plan["NetworkUsed"] is False and plan["ArtifactWritten"] is False
assert result["Status"] == "succeeded" and result["Artifact"]["artifactType"] == "markdown-document"
assert result["NetworkUsed"] is False and result["RepositoryRead"] is False and result["PromptPersisted"] is False
assert llama["ProviderId"] == "llamacpp.local-text" and llama["Protocol"] == "openai-chat-completions"
assert llama["RuntimeSelection"]["admission"] == "validated-exact-profile"
text = artifact_path.read_text(encoding="utf-8")
assert "private prompt marker" not in text and "127.0.0.1" not in text and "11434" not in text
PY
  result_code=$?
  rm -rf "$root"
  return "$result_code"
}

test_provider_discovery_and_engineering_routes() {
  discovery="$REPO_ROOT/scripts/discover-capability-availability.shared.sh"
  router="$REPO_ROOT/scripts/resolve-engineering-route.shared.sh"
  fixture="$REPO_ROOT/examples/fixtures/ollama-tags-response.json"
  openai_fixture="$REPO_ROOT/examples/fixtures/openai-models-response.json"
  offline="$($discovery --capability-id general.chat --json)" || return 1
  probe="$($discovery --capability-id general.chat --probe --model example-text-model:latest --ollama-base-url http://private-runtime.invalid:11434 --response-fixture-path "$fixture" --json)" || return 1
  llama_probe="$($discovery --capability-id general.chat --provider-id llamacpp.local-text --probe --model example-text-model --engine-id llama.cpp --backend-id cuda --hardware-profile linux-x64-nvidia-rtx5000-16gb --runtime-base-url http://private-runtime.invalid:8080 --response-fixture-path "$openai_fixture" --json)" || return 1
  ! $discovery --capability-id general.chat --provider-id llamacpp.local-text --probe --model example-text-model --engine-id llama.cpp --backend-id sycl --hardware-profile linux-x64-intel --response-fixture-path "$openai_fixture" --json >/dev/null 2>&1 || return 1
  route="$($router --text 'please review code' --json)" || return 1
  python3 - "$REPO_ROOT/config/engineering-routes.json" "$REPO_ROOT/config/workflows.json" "$offline" "$probe" "$llama_probe" "$route" <<'PY'
import json, pathlib, sys
routes = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["routes"]
workflows = {item["id"] for item in json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))["workflows"]}
offline, probe, llama_probe, route = map(json.loads, sys.argv[3:])
assert all(workflow_id in workflows for item in routes for workflow_id in item["workflowIds"])
assert offline["ProbeUsed"] is False and offline["CapabilityInvoked"] is False
assert offline["Items"][0]["EffectiveAvailability"] == "configuration-required"
assert probe["Probe"]["status"] == "available" and probe["Probe"]["source"] == "validation-fixture"
assert probe["EndpointPersisted"] is False and "private-runtime" not in sys.argv[4] and "11434" not in sys.argv[4]
assert llama_probe["Probe"]["status"] == "available"
assert llama_probe["Probe"]["runtimeSelection"]["admission"] == "validated-exact-profile"
assert route["Status"] == "selected" and route["SelectedRouteId"] == "engineering.review"
assert route["InvocationAllowed"] is False and any(step["WorkflowId"] == "verify-runtime-output" for step in route["Steps"])
PY
}

test_optional_llm_routing_boundary() {
  router="$REPO_ROOT/scripts/suggest-capability-route.shared.sh"
  fixture="$REPO_ROOT/examples/fixtures/ollama-capability-route-response.json"
  invalid_fixture="$REPO_ROOT/examples/fixtures/ollama-invalid-capability-route-response.json"
  plan="$($router --text 'private routing text' --model fixture-model --json)" || return 1
  valid="$($router --text 'private routing text' --model fixture-model --ollama-base-url http://private-runtime.invalid:11434 --response-fixture-path "$fixture" --execute --json)" || return 1
  invalid="$($router --text 'do something' --model fixture-model --response-fixture-path "$invalid_fixture" --execute --json)" || return 1
  python3 - "$plan" "$valid" "$invalid" <<'PY'
import json, sys
plan, valid, invalid = map(json.loads, sys.argv[1:])
assert plan["Status"] == "planned" and plan["InvocationAllowed"] is False
assert valid["Status"] == "suggested" and valid["Selected"]["Id"] == "content.summarize"
assert valid["RegistryValidated"] is True and valid["ExecutionEligible"] is False
assert valid["InvocationAllowed"] is False and valid["PromptPersisted"] is False and valid["EndpointPersisted"] is False
assert "private routing text" not in sys.argv[2] and "private-runtime" not in sys.argv[2] and "11434" not in sys.argv[2]
assert invalid["Status"] == "rejected" and invalid["RegistryValidated"] is False and invalid["InvocationAllowed"] is False
PY
}

test_local_image_capability_adapter() {
  root="$(mktemp -d)"
  session="$REPO_ROOT/scripts/start-ai-session.shared.sh"
  provider="$REPO_ROOT/scripts/invoke-local-image-capability.shared.sh"
  fixture="$REPO_ROOT/examples/fixtures/comfyui-image-response.json"
  $session --capability-id media.image.create --workspace-root "$root" --session-id image --apply --json >/dev/null || { rm -rf "$root"; return 1; }
  plan="$($provider --prompt 'private image marker' --model fixture.safetensors --session-path "$root/image" --json)" || { rm -rf "$root"; return 1; }
  result="$($provider --prompt 'private image marker' --model fixture.safetensors --session-path "$root/image" --comfyui-base-url http://private-runtime.invalid:8188 --response-fixture-path "$fixture" --image-name fixture.png --artifact-name fixture.json --execute --apply --json)" || { rm -rf "$root"; return 1; }
  python3 - "$REPO_ROOT/config/providers.json" "$plan" "$result" "$root/image/artifacts/fixture.json" <<'PY'
import json, pathlib, sys
providers = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["providers"]
plan, result = json.loads(sys.argv[2]), json.loads(sys.argv[3])
artifact_text = pathlib.Path(sys.argv[4]).read_text(encoding="utf-8")
assert any(p["id"] == "comfyui.local-image" and p["validationStatus"] == "live-validated" for p in providers)
assert plan["Status"] == "planned" and plan["NetworkUsed"] is False and plan["ImageWritten"] is False
assert result["Status"] == "succeeded" and result["Artifact"]["artifactType"] == "image"
assert result["Artifact"]["content"]["width"] == 1 and result["Artifact"]["content"]["height"] == 1
assert result["PromptPersisted"] is False and result["EndpointPersisted"] is False and result["RepositoryRead"] is False
assert "private image marker" not in sys.argv[3] and "private-runtime" not in sys.argv[3] and "8188" not in sys.argv[3]
assert "private image marker" not in artifact_text and "private-runtime" not in artifact_text and "8188" not in artifact_text
PY
  result_code=$?
  rm -rf "$root"
  return "$result_code"
}

test_solution_architecture_review_doc() {
  [ -f "$REPO_ROOT/docs/solution-architecture-review.md" ] &&
    [ -f "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" ] &&
    [ -f "$REPO_ROOT/BRANDING.md" ] &&
    [ -f "$REPO_ROOT/docs/haven-42-menu.md" ] &&
    [ -f "$REPO_ROOT/scripts/show-haven-42-menu.ps1" ] &&
    [ ! -e "$REPO_ROOT/docs/agent-pack-menu.md" ] &&
    [ ! -e "$REPO_ROOT/scripts/show-agent-pack-menu.ps1" ] &&
    grep -q '^# Haven 42$' "$REPO_ROOT/README.md" &&
    grep -q 'Your private, local AI station' "$REPO_ROOT/README.md" &&
    grep -q '^name: Haven 42$' "$REPO_ROOT/.continue/config.yaml" &&
    grep -q 'Canonical repository: `hysel/haven-42`' "$REPO_ROOT/BRANDING.md" &&
    grep -q 'Product Identity Policy' "$REPO_ROOT/BRANDING.md" &&
    grep -q 'PACKAGE_NAME="haven-42-$PACK_VERSION"' "$REPO_ROOT/scripts/build-release-package.shared.sh" &&
    grep -q 'haven-42/assets' "$REPO_ROOT/scripts/install-continue-pack.shared.sh" &&
    grep -q '\.haven-42-mlx' "$REPO_ROOT/scripts/bootstrap-macos-agent-host.sh" &&
    ! git -C "$REPO_ROOT" grep -n -I -i -E 'engineering[ -]+agent[ -]+pack|local[ _-]+engineering[ _-]+agent[ _-]+pack' -- . >/dev/null 2>&1 &&
    grep -q "Review Standard" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "Milestone Audit" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "1: Minimum Usable Pack" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "17: Agent Surface Compatibility Validation" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "18: Language Rule Packs" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "19: Installer Profiles" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "20: Hardware-Aware Model" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "21: General-Purpose AI Assistant" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "22: Unified Product UI" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "23: Native Local Image Generation" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "24: Local Music And Audio Generation" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "25: Local Video Generation" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "26: Hardware-Adaptive Model Quantization" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "21: General-Purpose AI Assistant And Intent Routing | Complete | Complete for the promoted provider set" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "22: Unified Product UI And Task Composition | In progress | First slice and policy boundary complete; native runtime dependency-gated" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    ! grep -q "21: General-Purpose AI Assistant And Intent Routing | Planned" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    ! grep -q "22: Unified Product UI And Task Composition | Planned" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "automated status-consistency checks" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "Complete for the workflow-foundation scope" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "Input-Dependent Decisions" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "new integration proposal" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "Complete for positioning and support-tier governance" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "Complete for the promoted supported-surface set" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "OpenHands is a candidate with a defined isolation boundary" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "Candidate surfaces are excluded from supported parity" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "EMPTY_MODEL_OUTPUT" "$REPO_ROOT/docs/solution-architecture-review.md" &&
    grep -q "Evidence States" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "tested-passed" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "tested-partial" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "recommended-only" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "blocked" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "config/workflows.json" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "scripts/invoke-workflow" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "local-first" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "Tauri 2" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "typed JSON over private stdin/stdout IPC" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "must not expose arbitrary shell execution" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "headless Linux" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "Microsoft Store MSIX signing or the SignPath Foundation" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "Defer Apple Developer Program enrollment" "$REPO_ROOT/docs/unified-starter-toolkit-ui.md" &&
    grep -q "Milestone 22: Unified Product UI And Task Composition | In progress" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Milestone 21: General-Purpose AI Assistant And Intent Routing | Complete" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Milestone 21: General-Purpose AI Assistant And Intent Routing | Complete" "$REPO_ROOT/README.md" &&
    grep -q "Milestone 22: Unified Product UI And Task Composition | In progress" "$REPO_ROOT/README.md" &&
    grep -q "\[x\] Select and document Tauri 2" "$REPO_ROOT/TODO.md" &&
    grep -q "docs/solution-architecture-review.md" "$REPO_ROOT/README.md" &&
    grep -q "docs/unified-starter-toolkit-ui.md" "$REPO_ROOT/README.md" &&
    grep -q "local-first AI workbench" "$REPO_ROOT/README.md" &&
    grep -q "Continue, Aider, and OpenCode" "$REPO_ROOT/README.md" &&
    grep -q "general.chat" "$REPO_ROOT/README.md" &&
    grep -q "content.write" "$REPO_ROOT/README.md" &&
    grep -q "content.summarize" "$REPO_ROOT/README.md" &&
    grep -q "media.image.create" "$REPO_ROOT/README.md" &&
    grep -q "pass-before-ship" "$REPO_ROOT/README.md" &&
    grep -q "Milestone 22: Unified Product UI And Task Composition" "$REPO_ROOT/README.md" &&
    grep -q "Milestone 23: Native Local Image Generation" "$REPO_ROOT/README.md" &&
    grep -q "Milestone 24: Local Music And Audio Generation" "$REPO_ROOT/README.md" &&
    grep -q "Milestone 25: Local Video Generation" "$REPO_ROOT/README.md" &&
    grep -q "Linux ComfyUI/SDXL.*validated" "$REPO_ROOT/README.md" &&
    grep -q "documentation-only candidate inventories" "$REPO_ROOT/README.md" &&
    ! grep -Eq '(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})' "$REPO_ROOT/README.md" &&
    grep -q "Solution Architecture Review Backlog" "$REPO_ROOT/TODO.md" &&
    grep -q "\\[x\\] Add a milestone solution completeness audit" "$REPO_ROOT/TODO.md" &&
    grep -q "\\[x\\] Reuse the recommendation data model for future non-Continue agent surfaces" "$REPO_ROOT/TODO.md" &&
    grep -q "\\[ \\] Provide or approve suitable non-generated repositories" "$REPO_ROOT/TODO.md" &&
    grep -q "\\[x\\] Design a unified web UI" "$REPO_ROOT/TODO.md" &&
    grep -q "\\[x\\] Keep the UI evidence-first" "$REPO_ROOT/TODO.md" &&
    grep -q "\\[x\\] Hand unified UI implementation to Milestone 22" "$REPO_ROOT/TODO.md" &&
    grep -q "## Milestone 22: Unified Product UI And Task Composition" "$REPO_ROOT/TODO.md" &&
    grep -q "Windows Intel GPU/XPU" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Intel GPU support must pass installation, XPU acceleration, generation, metadata, recovery, cleanup, and typed-adapter gates" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "shared Linux provider as an optional advanced deployment" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "\[ \] Validate a pinned Windows Intel GPU/XPU image-provider profile" "$REPO_ROOT/TODO.md" &&
    grep -q "## Milestone 23: Native Local Image Generation" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Linux ComfyUI/SDXL profile is live-validated" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Cross-platform fixture contracts do not promote native Windows or macOS execution" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "## Milestone 23: Native Local Image Generation" "$REPO_ROOT/TODO.md" &&
    grep -q "## Milestone 24: Local Music And Audio Generation" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "ACE-Step 1.5" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Stable Audio 3.0" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "YuE" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "MusicGen" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Windows Intel XPU" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Apple Silicon MLX" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Candidate status alone must not add registry entries, scripts, adapters, templates, workflows, installer files, or model configuration" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "silent CPU fallback" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "## Milestone 24: Local Music And Audio Generation" "$REPO_ROOT/TODO.md" &&
    grep -q "\[x\] Ship no music scripts, adapters, harnesses, templates, workflows, configuration, or registry entries" "$REPO_ROOT/TODO.md" &&
    grep -q "## Milestone 25: Local Video Generation" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "HunyuanVideo 1.5" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Wan2.2 TI2V-5B" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "LTX-2.3" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Windows Intel, Windows AMD, and Apple Silicon local video generation unavailable" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "Candidate status must not add registry entries, scripts, adapters, harnesses, templates, workflows, configuration, runtime files, or installer automation" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "generated-content disclosure" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "## Milestone 25: Local Video Generation" "$REPO_ROOT/TODO.md" &&
    grep -q "\[x\] Ship no video scripts, adapters, harnesses, templates, workflows, configuration, registry entries, runtime files, or installer automation" "$REPO_ROOT/TODO.md" &&
    grep -q "cross-platform core-engine updater" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "stable releases published by the official GitHub repository" "$REPO_ROOT/ROADMAP.md" &&
    grep -q 'Never update a production installation with an unattended `git pull` or from a moving branch' "$REPO_ROOT/ROADMAP.md" &&
    grep -q "signature or attestation" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "previous known-good engine" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "local configuration, models, provider data, generated artifacts, and evidence" "$REPO_ROOT/ROADMAP.md" &&
    grep -q "\[ \] Add opt-in automatic stable-release checks, downloads, and installation" "$REPO_ROOT/TODO.md" &&
    grep -q "\[ \] Add compatibility preflight, atomic activation, post-update health checks, automatic rollback" "$REPO_ROOT/TODO.md"
}
test_hosted_ci_verifier_contract() {
  windows="$REPO_ROOT/scripts/verify-hosted-ci.ps1"
  shared="$REPO_ROOT/scripts/verify-hosted-ci.shared.sh"
  linux="$REPO_ROOT/scripts/verify-hosted-ci.linux.sh"
  macos="$REPO_ROOT/scripts/verify-hosted-ci.macos.sh"
  doc="$REPO_ROOT/docs/hosted-ci-verification.md"

  [ -f "$windows" ] &&
    [ -f "$shared" ] &&
    [ -f "$linux" ] &&
    [ -f "$macos" ] &&
    [ -f "$doc" ] &&
    grep -q -- '--commit' "$shared" &&
    grep -q 'headSha' "$shared" &&
    grep -q 'run watch' "$shared" &&
    grep -q -- '--exit-status' "$shared" &&
    grep -q -- '--log-failed' "$shared" &&
    grep -q 'Wiki synchronization' "$shared" &&
    grep -q 'Windows PowerShell validation' "$shared" &&
    grep -q 'Linux script smoke tests' "$shared" &&
    grep -q 'macOS script smoke tests' "$shared" &&
    grep -q 'State: %s' "$shared" &&
    grep -q 'exact run API request is authoritative' "$shared" &&
    grep -q 'exact 40-character commit SHA' "$doc" &&
    grep -q 'Never reuse a successful run' "$doc" &&
    grep -q 'preflight as advisory' "$doc"
}

test_wiki_synchronization() {
  wiki_temp="$(mktemp -d)"
  sync="$REPO_ROOT/scripts/sync-wiki.shared.sh"
  "$sync" --wiki-path "$wiki_temp" >/dev/null 2>&1 || { rm -rf "$wiki_temp"; return 1; }
  "$sync" --wiki-path "$wiki_temp" --check >/dev/null 2>&1 || { rm -rf "$wiki_temp"; return 1; }
  printf 'stale' > "$wiki_temp/Home.md"
  if "$sync" --wiki-path "$wiki_temp" --check >/dev/null 2>&1; then
    rm -rf "$wiki_temp"
    return 1
  fi
  rm -rf "$wiki_temp"
  grep -q 'Cline-CLI-Model-Testing.md' "$REPO_ROOT/config/wiki-retired-pages.txt" &&
    grep -q 'name: Wiki synchronization' "$REPO_ROOT/.github/workflows/validate-pack.yml" &&
    grep -Eq 'sync-wiki\.linux\.sh.+--check' "$REPO_ROOT/.github/workflows/validate-pack.yml" &&
    grep -q 'commit the wiki before pushing the main repository' "$REPO_ROOT/docs/wiki-maintenance.md"
}

test_model_residency_policy_contract() {
  [ -f "$REPO_ROOT/config/model-runtime-policy.sample.json" ] &&
    grep -q '"residencyMode": "unload-after-run"' "$REPO_ROOT/config/model-runtime-policy.sample.json" &&
    grep -q '"maxResidentModels": 1' "$REPO_ROOT/config/model-runtime-policy.sample.json" &&
    [ -f "$REPO_ROOT/scripts/get-model-runtime-policy.ps1" ] &&
    [ -f "$REPO_ROOT/scripts/get-model-runtime-policy.shared.sh" ] &&
    grep -q 'runtimePolicy' "$REPO_ROOT/scripts/run-language-workflow-matrix.ps1" &&
    grep -q 'RUNTIME_RESIDENCY_MODE' "$REPO_ROOT/scripts/run-language-workflow-matrix.shared.sh" &&
    grep -q 'runtimePolicy' "$REPO_ROOT/scripts/test-local-agent-models.ps1" &&
    grep -q 'RUNTIME_RESIDENCY_MODE' "$REPO_ROOT/scripts/test-local-agent-models.shared.sh" &&
    grep -q 'continueKeepAliveSeconds' "$REPO_ROOT/scripts/apply-recommended-agent-config.ps1" &&
    grep -q 'CONTINUE_KEEP_ALIVE_SECONDS' "$REPO_ROOT/scripts/apply-recommended-agent-config.shared.sh" &&
    grep -q 'continueKeepAliveSeconds' "$REPO_ROOT/scripts/install-continue-pack.ps1" &&
    grep -q 'CONTINUE_KEEP_ALIVE_SECONDS' "$REPO_ROOT/scripts/install-continue-pack.shared.sh" &&
    [ -f "$REPO_ROOT/scripts/run-continue-with-runtime-policy.ps1" ] &&
    [ -f "$REPO_ROOT/scripts/run-continue-with-runtime-policy.shared.sh" ] &&
    grep -q 'Invoke-OllamaUnload' "$REPO_ROOT/scripts/run-continue-with-runtime-policy.ps1" &&
    grep -q 'trap' "$REPO_ROOT/scripts/run-continue-with-runtime-policy.shared.sh"
}

test_comfyui_setup_guide_contract() {
  guide="$REPO_ROOT/docs/comfyui-image-provider-setup.md"
  [ -f "$guide" ] || return 1
  grep -Fq 'v0.28.2' "$guide" &&
    grep -Fq '306af3a8771a8232d26bd20acbfc6b07f862ad2b' "$guide" &&
    grep -Fq '2.11.0+cu126' "$guide" &&
    grep -Fq '31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b' "$guide" &&
    grep -Fq '127.0.0.1:8188' "$guide" &&
    grep -Fq -- '--disable-metadata' "$guide" &&
    grep -Fq -- '--disable-all-custom-nodes' "$guide" &&
    grep -Fq -- '--disable-api-nodes' "$guide" &&
    grep -Fq 'NoNewPrivileges=true' "$guide" &&
    grep -Fq 'ProtectSystem=strict' "$guide" &&
    grep -Fq 'sha256sum --check' "$guide" &&
    grep -Fq 'SSH tunneling' "$guide" &&
    grep -Fq 'ProviderRetainedOutput' "$guide" &&
    grep -Fq 'moving branch' "$guide" &&
    grep -Fq 'scripts, templates, workflows, or configuration' "$guide" &&
    grep -Eiq 'dedicated Ed25519 key' "$guide" &&
    grep -Eiq 'Never copy or transmit the private key' "$guide" &&
    ! grep -Eq '(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})' "$guide" &&
    ! grep -Eq 'ssh-ed25519[[:space:]]+AAAA[A-Za-z0-9+/]+' "$guide"
}

run_test "validate-pack succeeds for repository" test_validate_succeeds
run_test "validate-pack fails for wrong expected version" test_validate_fails_for_wrong_version
run_test "release packaging scripts define archives, checksums, and sanitized dry runs" test_release_packaging_scripts
run_test "evidence catalog has valid schema and sanitized links" test_evidence_catalog_schema
test_desktop_runtime_and_ipc_contracts() {
  dependency="$REPO_ROOT/docs/desktop-runtime-dependency-evaluation.md"
  resolution="$REPO_ROOT/docs/desktop-dependency-resolution-evidence.md"
  contract_doc="$REPO_ROOT/docs/desktop-ipc-contract.md"
  storage_doc="$REPO_ROOT/docs/desktop-storage-and-updates.md"
  ipc="$REPO_ROOT/config/desktop-ipc-contract.json"
  policy="$REPO_ROOT/config/desktop-capability-policy.json"
  storage="$REPO_ROOT/config/desktop-storage-contract.json"
  update="$REPO_ROOT/config/core-update-manifest-contract.json"

  python3 - "$ipc" "$policy" "$storage" "$update" <<'PY' || return 1
import json
import pathlib
import sys

ipc = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
policy = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
storage = json.loads(pathlib.Path(sys.argv[3]).read_text(encoding="utf-8"))
update = json.loads(pathlib.Path(sys.argv[4]).read_text(encoding="utf-8"))
assert ipc["schemaVersion"] == 1
assert ipc["transport"]["kind"] == "stdio-json-lines"
assert ipc["transport"]["listeningSocket"] is False
assert ipc["transport"]["remoteContentAllowed"] is False
assert ipc["transport"]["maxMessageBytes"] == 1048576
assert ipc["request"]["additionalProperties"] is False
for field in ("command", "shell", "executable", "program", "argv", "cwd", "rawPath", "url", "endpoint"):
    assert field in ipc["request"]["forbiddenProperties"]
assert ipc["operationResolution"]["unknownIdsRejected"] is True
assert ipc["operationResolution"]["workflowMustBeUiReady"] is True
assert ipc["pathGrants"]["rawCanonicalRootReturnedToRendererByDefault"] is False
assert ipc["approvals"]["defaultDeny"] is True
assert ipc["privacy"]["persistMessagesByDefault"] is False
assert policy["defaultDecision"] == "deny"
assert policy["contentPolicy"]["bundledLocalAssetsOnly"] is True
for field in ("remoteCapabilities", "genericShellPermission", "genericProcessPermission", "genericFilesystemPermission", "genericUrlOpenPermission", "listeningSocket"):
    assert policy["tauriAuthority"][field] is False
assert len(policy["tauriAuthority"]["allowedRendererCommands"]) == 7
assert policy["networkPolicy"]["telemetry"] is False
assert policy["networkPolicy"]["crashUpload"] is False
assert policy["headlessSeparation"]["inheritsDesktopEvidence"] is False
assert storage["schemaVersion"] == 1
assert storage["resolutionRules"]["resolveWithNativePlatformApis"] is True
assert storage["resolutionRules"]["persistUnexpandedEnvironmentPaths"] is False
for platform in ("windows", "linux", "macos"):
    values = storage["platforms"][platform]
    for field in ("immutableApplication", "configuration", "state", "cache", "managedModels", "defaultArtifacts", "updateDownloads", "stagedVersions", "activationJournal", "credentials"):
        assert values[field]
assert "user-content" in storage["lifecycleRules"]["updateMustPreserve"]
assert "provider-data" in storage["lifecycleRules"]["updateMustPreserve"]
assert storage["lifecycleRules"]["rollbackMustNotDowngradeUserDataWithoutCompatibleMigration"] is True
assert update["schemaVersion"] == 1
assert update["transport"]["movingBranchAllowed"] is False
assert update["transport"]["gitPullAllowed"] is False
assert update["transport"]["defaultUpdateMode"] == "disabled"
assert update["manifest"]["releaseTagMustBeImmutable"] is True
assert update["manifest"]["releaseCommitMustBeFullSha"] is True
for field in ("sizeBytes", "sha256", "signatureOrAttestation", "sbomUrl", "thirdPartyNoticesUrl"):
    assert field in update["asset"]["required"]
assert update["activation"]["atomic"] is True
assert update["activation"]["inPlaceOverwriteAllowed"] is False
assert update["activation"]["automaticRollbackOnHealthFailure"] is True
assert update["activation"]["userDataIncludedInEnginePackage"] is False
assert update["activation"]["modelsIncludedInEnginePackage"] is False
assert update["privacy"]["telemetry"] is False
assert update["privacy"]["updateCheckSendsHardwareProfile"] is False
PY

  grep -q "architecture-approved but not admitted for shipment" "$dependency" &&
    grep -q "2.11.5" "$dependency" &&
    grep -q "19.2.8" "$dependency" &&
    grep -q "8.1.5" "$dependency" &&
    grep -q "7.0.2" "$dependency" &&
    grep -q "24.18.0" "$dependency" &&
    grep -q "1.97.1" "$dependency" &&
    grep -q "6.21.0" "$dependency" &&
    grep -q "not a cross-compiler" "$dependency" &&
    grep -q "Electron" "$dependency" &&
    grep -q "remote JavaScript" "$dependency" &&
    grep -q "generic filesystem plugin" "$dependency" &&
    grep -q "updater plugin" "$dependency" &&
    grep -q "blocked; do not admit desktop runtime manifests or scaffolding" "$resolution" &&
    grep -q "24.18.0" "$resolution" &&
    grep -q "11.16.0" "$resolution" &&
    grep -q "89" "$resolution" &&
    grep -q "443 third-party packages" "$resolution" &&
    grep -q "247" "$resolution" &&
    grep -q "RUSTSEC-2025-0081" "$resolution" &&
    grep -q "RUSTSEC-2024-0429" "$resolution" &&
    grep -q "6.21.0" "$resolution" &&
    grep -q "zero known vulnerabilities" "$resolution" &&
    grep -q "GitHub reported no build attestation" "$resolution" &&
    ! grep -Eq '(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})' "$resolution" &&
    [ ! -e "$REPO_ROOT/package.json" ] &&
    [ ! -e "$REPO_ROOT/Cargo.toml" ] &&
    [ ! -e "$REPO_ROOT/Cargo.lock" ] &&
    grep -q "renderer is untrusted input" "$contract_doc" &&
    grep -q "raw paths" "$contract_doc" &&
    grep -q "single-use" "$contract_doc" &&
    grep -q "Required Negative Tests" "$contract_doc" &&
    grep -q "headless-loopback" "$contract_doc" &&
    grep -q "Immutable engine" "$storage_doc" &&
    grep -q "user-owned" "$storage_doc" &&
    grep -q "Windows Credential Manager" "$storage_doc" &&
    grep -q "Secret Service" "$storage_doc" &&
    grep -q "macOS Keychain" "$storage_doc" &&
    grep -q 'unattended `git pull`' "$storage_doc" &&
    grep -q "Atomically" "$storage_doc" &&
    grep -q "docs/desktop-runtime-dependency-evaluation.md" "$REPO_ROOT/config/wiki-sync.tsv" &&
    grep -q "docs/desktop-dependency-resolution-evidence.md" "$REPO_ROOT/config/wiki-sync.tsv" &&
    grep -q "docs/desktop-ipc-contract.md" "$REPO_ROOT/config/wiki-sync.tsv" &&
    grep -q "docs/desktop-storage-and-updates.md" "$REPO_ROOT/config/wiki-sync.tsv"
}

test_desktop_sidecar_ipc_policy() {
  output="$(python3 "$REPO_ROOT/scripts/desktop-ipc-policy.py" --self-test 2>&1)" || return 1
  printf '%s\n' "$output" | grep -q "passed: 46 cases"
}

test_native_bridge_boundary_policy() {
  output="$(python3 "$REPO_ROOT/scripts/native-bridge-boundary-policy.py" --self-test 2>&1)" || return 1
  printf '%s\n' "$output" | grep -q "passed: 55 cases" || return 1
  python3 - "$REPO_ROOT" <<'PY' || return 1
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
contract = json.loads((root / "config/native-bridge-boundary-contract.json").read_text(encoding="utf-8"))
assert contract["schemaVersion"] == 1
assert contract["runtimeAdmitted"] is False and contract["defaultDecision"] == "deny"
assert contract["pathGrants"]["rawRendererPathAccepted"] is False
assert contract["pathGrants"]["networkPathAllowed"] is False
assert contract["pathGrants"]["symlinkOrReparseEscapeAllowed"] is False
assert contract["approvalTokens"]["rememberApprovalAllowed"] is False
assert contract["approvalTokens"]["singleUse"] is True
assert contract["approvalTokens"]["nativeMemoryOnly"] is True
assert contract["sidecarLifecycle"]["rendererMaySelectBinary"] is False
assert contract["sidecarLifecycle"]["rendererMaySupplyArguments"] is False
assert contract["sidecarLifecycle"]["elevationAllowed"] is False
assert contract["sidecarLifecycle"]["listeningSocketAllowed"] is False
assert contract["sidecarLifecycle"]["unrelatedProcessTerminationAllowed"] is False
assert contract["privilegeBoundary"]["installService"] is False
assert contract["privilegeBoundary"]["modifyFirewall"] is False
assert contract["privilegeBoundary"]["modifyDrivers"] is False
assert contract["promotion"]["policyModelPassesAsNativeEvidence"] is False
assert contract["promotion"]["requiresActualNativeBridgeTests"] is True
evidence = (root / "docs/native-bridge-boundary-evidence.md").read_text(encoding="utf-8")
assert "policy model passed; native runtime remains blocked and unadmitted" in evidence
assert "does not prove Tauri command registration" in evidence
assert "docs/native-bridge-boundary-evidence.md" in (root / "config/wiki-sync.tsv").read_text(encoding="utf-8")
for runtime_file in ("package.json", "package-lock.json", "Cargo.toml", "Cargo.lock", "tauri.conf.json"):
    assert not (root / runtime_file).exists()
PY
}

test_core_update_policy() {
  policy="$REPO_ROOT/scripts/core-update-policy.shared.sh"
  manifest="$REPO_ROOT/examples/fixtures/core-update-manifest.json"
  package="$REPO_ROOT/examples/fixtures/core-update-package.bin"
  output="$($policy --manifest-path "$manifest" --package-path "$package" --host-os windows --host-architecture x64 --target-triple x86_64-pc-windows-msvc --current-version 0.3.0 --updater-version 0.3.0 --json)" || return 1
  python3 - "$output" <<'PY' || return 1
import json, sys
value = json.loads(sys.argv[1])
assert value["Status"] == "verified-bytes-awaiting-cryptographic-attestation"
assert value["BytesVerified"] is True
assert value["ManifestSignatureVerified"] is False and value["AssetAttestationVerified"] is False
assert value["CompatibilityPreflightComplete"] is False
assert value["OperatingSystemCompatibilityVerified"] is False
assert value["ActivationAllowed"] is False and value["NetworkUsed"] is False
assert value["FilesWritten"] is False and value["UserDataTouched"] is False
PY
  ! "$policy" --manifest-path "$manifest" --host-os linux --host-architecture x64 --target-triple x86_64-unknown-linux-gnu --current-version 0.3.0 --updater-version 0.3.0 --json >/dev/null 2>&1 || return 1
  hostile_output="$(python3 "$REPO_ROOT/scripts/core-update-policy.py" --self-test 2>&1)" || return 1
  printf ''%s\n'' "$hostile_output" | grep -q "passed: 17 cases"
}

test_workflow_reliability_and_data_lifecycle() {
  python3 - "$REPO_ROOT" <<''PY'' || return 1
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
workflow = json.loads((root / "config/workflow-reliability-contract.json").read_text(encoding="utf-8"))
lifecycle = json.loads((root / "config/local-data-lifecycle-contract.json").read_text(encoding="utf-8"))
envelope = json.loads((root / "config/workflow-envelope-contract.json").read_text(encoding="utf-8"))
assert workflow["timeouts"]["requiredForExecution"] is True
assert workflow["cancellation"]["unrelatedProcessTerminationAllowed"] is False
assert workflow["retries"]["writeOperationsRetryByDefault"] is False
assert workflow["idempotency"]["keyRequiredForRetriedEffects"] is True
assert workflow["events"]["exactlyOneTerminalEvent"] is True
assert workflow["events"]["eventsAfterTerminalAllowed"] is False
assert workflow["resumability"]["default"] is False
assert workflow["resumability"]["resumeRequiresSameWorkflowVersionAndApprovalScope"] is True
assert lifecycle["deletion"]["preexistingModelsNeverDeletedByCleanup"] is True
assert lifecycle["deletion"]["failedOperationCleanupLimitedToRunOwnedData"] is True
assert lifecycle["defaults"]["telemetry"] is False
assert lifecycle["defaults"]["rawPromptPersistence"] is False
assert lifecycle["export"]["secretsExcluded"] is True
assert envelope["reliabilityExtension"]["contract"] == "config/workflow-reliability-contract.json"
for relative in ("docs/workflow-reliability.md", "docs/security-threat-model.md", "docs/local-data-lifecycle.md"):
    assert len((root / relative).read_text(encoding="utf-8")) > 500
wiki = (root / "config/wiki-sync.tsv").read_text(encoding="utf-8")
for relative in ("docs/workflow-reliability.md", "docs/security-threat-model.md", "docs/local-data-lifecycle.md", "examples/laguna-xs-2.1-validation.md"):
    assert relative in wiki
PY
}

test_provider_evidence_and_capacity() {
  python3 "$REPO_ROOT/scripts/validate-model-performance-evidence.py" --evidence-path "$REPO_ROOT/examples/fixtures/model-performance-evidence.json" >/dev/null || return 1
  output="$("$REPO_ROOT/scripts/runtime-capacity-preflight.shared.sh" --profile-path "$REPO_ROOT/examples/fixtures/runtime-capacity-profile.json" --required-accelerator-mib 8000 --required-system-mib 8000 --required-disk-mib 8000 --reserve-mib 1000 --json)" || return 1
  python3 - "$output" <<'PY' || return 1
import json, sys
value = json.loads(sys.argv[1])
assert value["Decision"] == "ready"
assert value["NetworkUsed"] is False and value["FilesWritten"] is False
assert value["ProcessesTerminated"] is False and value["DriverOrServiceChanged"] is False
PY
  ! "$REPO_ROOT/scripts/runtime-capacity-preflight.shared.sh" --profile-path "$REPO_ROOT/examples/fixtures/runtime-capacity-profile.json" --required-accelerator-mib 16000 --required-system-mib 8000 --required-disk-mib 8000 --reserve-mib 1000 --json >/dev/null 2>&1
}

test_media_onboarding_and_quantization_foundations() {
  python3 - "$REPO_ROOT" <<'PY' || return 1
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
image = json.loads((root / "config/local-image-onboarding-contract.json").read_text(encoding="utf-8"))
plan = json.loads((root / "config/quantization-plan-contract.json").read_text(encoding="utf-8"))
artifact = json.loads((root / "config/quantized-artifact-manifest-contract.json").read_text(encoding="utf-8"))
matrix = json.loads((root / "config/quantization-support-matrix.json").read_text(encoding="utf-8"))
engines = json.loads((root / "config/inference-engine-registry.json").read_text(encoding="utf-8"))
assert image["schemaVersion"] == 1
assert image["externalServerRequired"] is False
assert image["executionDefault"] == "dry-run"
assert image["discovery"]["silentCpuFallbackAllowed"] is False
assert image["selection"]["evidenceInheritanceAcrossProfilesAllowed"] is False
assert image["promotion"]["failedProfileLeavesDocumentationOnly"] is True
assert plan["selection"]["trustedExistingArtifactPreferred"] is True
assert plan["selection"]["silentCpuFallbackAllowed"] is False
assert artifact["output"]["storageOutsideEngineAndRepository"] is True
assert artifact["activation"]["previousKnownGoodRetained"] is True
assert matrix["defaultDecision"] == "no-safe-recommendation"
assert {item["format"] for item in matrix["formats"]} == {"gguf", "mlx", "awq", "gptq", "fp8", "int4"}
assert engines["schemaVersion"] == 1
assert engines["layers"] == ["capability", "provider-contract", "inference-engine", "hardware-backend", "model-artifact"]
assert engines["selection"]["silentCpuFallbackAllowed"] is False
assert engines["selection"]["evidenceInheritanceAcrossEnginesBackendsOrHardwareAllowed"] is False
by_id = {item["id"]: item for item in engines["engines"]}
llama_backends = {item["id"]: item for item in by_id["llama.cpp"]["backends"]}
assert llama_backends["cuda"]["status"] == "validated-exact-profile"
assert llama_backends["cuda"]["profiles"] == ["linux-x64-nvidia-rtx5000-16gb"]
assert llama_backends["hip"]["status"] == "validated-exact-profile"
assert "vulkan" not in llama_backends
assert llama_backends["sycl"]["status"] == "parked-hardware-required"
assert by_id["openvino-genai"]["status"] == "parked-hardware-required"
assert by_id["ipex-llm"]["status"] == "retired"
assert by_id["lm-studio"]["status"] == "optional-external-api"
assert by_id["lm-studio"]["redistributionAllowedByHaven42"] is False
assert by_id["lm-studio"]["embeddingAllowedByHaven42"] is False
script_names = "\n".join(path.name for path in (root / "scripts").rglob("*") if path.is_file())
assert not re.search(r"(?:ipex|openvino|sycl|lm-studio|vulkan)", script_names, re.I)
engine_doc = (root / "docs/inference-engine-architecture.md").read_text(encoding="utf-8")
for marker in ("provider contract", "failed candidates leave documentation only", "Parked", "Optional external API", "Retired"):
    assert marker in engine_doc
for registry in ("config/capabilities.json", "config/workflows.json"):
    text = (root / registry).read_text(encoding="utf-8")
    assert "audio.music.create" not in text
    assert "media.video.create" not in text
wiki = (root / "config/wiki-sync.tsv").read_text(encoding="utf-8")
private_ip = re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b")
for doc in (
    "docs/local-image-provider-onboarding.md",
    "docs/local-audio-provider-candidates.md",
    "docs/local-video-provider-candidates.md",
    "docs/generative-media-consent-policy.md",
    "docs/hardware-adaptive-quantization.md",
    "docs/inference-engine-architecture.md",
    "examples/inference-engine-validation.md",
):
    assert doc in wiki
    assert not private_ip.search((root / doc).read_text(encoding="utf-8"))
PY
  grep -q 'plan_parser.add_argument("--output", required=True' "$REPO_ROOT/scripts/quantization-planner.py" || return 1
  grep -q 'write_new_file(output_path' "$REPO_ROOT/scripts/quantization-planner.py" || return 1
  ! grep -q 'print(json.dumps(create_plan' "$REPO_ROOT/scripts/quantization-planner.py" || return 1
  python3 "$REPO_ROOT/scripts/quantization-planner.py" --self-test | grep -q "3 cases" || return 1
  profile="$(python3 "$REPO_ROOT/scripts/quantization-planner.py" profile --storage-root "$REPO_ROOT" --context-tokens 16384 --concurrency 1 --workload-lane tool-use)" || return 1
  python3 - "$profile" <<'PY'
import json
import sys
profile = json.loads(sys.argv[1])
assert profile["schemaVersion"] == 1
assert profile["privacy"]["localOnlyHardwareValuesIncluded"] is True
assert profile["privacy"]["persistentIdentityValuesIncluded"] is False
assert profile["target"]["workloadLane"] == "tool-use"
PY
}

test_product_ui_first_slice() {
  python3 "$REPO_ROOT/scripts/build-ui-view-model.py" --self-test | grep -q "5 cases" || return 1
  python3 "$REPO_ROOT/scripts/evaluate-onboarding-configuration.py" --self-test | grep -q "11 cases" || return 1
  ui_temp="$(mktemp -d)" || return 1
  decision_file="$ui_temp/decision.json"
  model_file="$ui_temp/model.json"
  python3 "$REPO_ROOT/scripts/evaluate-onboarding-configuration.py" --request-path "$REPO_ROOT/examples/fixtures/onboarding-settings-request.json" --admission-path "$REPO_ROOT/examples/fixtures/onboarding-trusted-admission.json" --json >"$decision_file" || { rm -rf "$ui_temp"; return 1; }
  python3 "$REPO_ROOT/scripts/build-ui-view-model.py" --platform linux >"$model_file" || { rm -rf "$ui_temp"; return 1; }
  python3 - "$REPO_ROOT" "$model_file" "$decision_file" <<'PY' || { rm -rf "$ui_temp"; return 1; }
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
model = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
decision = json.loads(pathlib.Path(sys.argv[3]).read_text(encoding="utf-8"))
ui = json.loads((root / "config/ui-navigation-contract.json").read_text(encoding="utf-8"))
onboarding = json.loads((root / "config/progressive-onboarding-contract.json").read_text(encoding="utf-8"))
setting_schemas = json.loads((root / "config/onboarding-setting-schemas.json").read_text(encoding="utf-8"))
capabilities = json.loads((root / "config/capabilities.json").read_text(encoding="utf-8"))
workflows = json.loads((root / "config/workflows.json").read_text(encoding="utf-8"))
assert ui["schemaVersion"] == 1 and ui["runtimeAdmitted"] is False
assert ui["principles"]["rendererIsExecutionAuthority"] is False
assert ui["principles"]["remoteContentAllowed"] is False
assert ui["firstRun"]["networkProbeByDefault"] is False
assert ui["firstRun"]["installsSoftwareByDefault"] is False
assert ui["firstRun"]["downloadsModelsByDefault"] is False
assert onboarding["schemaVersion"] == 1 and onboarding["runtimeAdmitted"] is False
assert [item["id"] for item in onboarding["choices"]] == ["guided-setup", "existing-setup", "not-now"]
assert onboarding["choices"][0]["advancedSettingsAvailable"] is True
assert onboarding["choices"][1]["advancedSettingsAvailable"] is True
assert onboarding["choices"][2]["advancedSettingsAvailable"] is False
assert [item["id"] for item in onboarding["configurationStates"]] == ["validated", "customized", "unverified", "blocked"]
assert onboarding["stateDerivation"]["rendererMaySelectState"] is False
assert onboarding["advancedSettings"]["rawArbitraryCommandOrFlagEntryAllowed"] is False
assert setting_schemas["runtimeAdmitted"] is False and setting_schemas["defaultDecision"] == "blocked"
assert [item["id"] for item in setting_schemas["domains"]] == ["text-providers", "engineering-agent-surfaces", "image-generation", "audio-generation", "video-generation", "model-management", "inference-engines", "storage-updates"]
for key in ("unknownFieldsAllowed", "rawEndpointsAllowed", "rawFilesystemPathsAllowed", "plaintextCredentialsAllowed", "commandsExecutablesArgumentsOrEnvironmentAllowed", "rendererSuppliedEvidenceOrApprovalAllowed"):
    assert setting_schemas["rendererInputPolicy"][key] is False
assert ui["approvalReview"]["rememberApprovalAllowed"] is False
assert ui["approvalReview"]["approvalTokenVisibleToRenderer"] is False
capability_ids = {item["id"] for item in capabilities["capabilities"]}
workflow_by_id = {item["id"]: item for item in workflows["workflows"]}
for action in ui["homeActions"]:
    if action["operationKind"] == "capability":
        assert action["operationId"] in capability_ids
    else:
        assert workflow_by_id[action["operationId"]]["uiReady"] is True
assert model["initialRouteId"] == "welcome"
assert model["executionEnabled"] is False and model["runtimeAdmitted"] is False
assert [item["id"] for item in model["onboarding"]["choices"]] == ["guided-setup", "existing-setup", "not-now"]
assert len(model["onboarding"]["settingDomains"]) == 8
assert decision["configurationState"] == "customized" and decision["executionAllowed"] is True
assert not any(decision["effects"].values())
for forbidden in ("fixture-exact-image-profile", "ref:", "grant:", "secret:"):
    assert forbidden not in json.dumps(decision)
rendered = json.dumps(model)
for forbidden in ("entryPoints", "127.0.0.1", "192.168.", "approvalTokenId"):
    assert forbidden not in rendered
assert "What do you want to do?" in (root / "docs/product-ui-first-slice.md").read_text(encoding="utf-8")
assert "docs/product-ui-first-slice.md" in (root / "config/wiki-sync.tsv").read_text(encoding="utf-8")
assert "Advanced mode is control, not a bypass" in (root / "docs/progressive-onboarding.md").read_text(encoding="utf-8")
PY
  rm -rf "$ui_temp"
}

run_test "model recommendation catalog has valid schema" test_catalog_schema
run_test "committed config uses starter sample model" test_committed_config_uses_starter_model
run_test "MLX model recommendation catalog has valid schema" test_mlx_catalog_schema
run_test "shell wrapper scripts and hooks are executable in git" test_shell_scripts_executable
run_test "GitHub Actions dependencies are current and monitored" test_github_actions_dependencies
run_test "test tiers are timed and exact-tree receipt gated" test_test_tier_contract
run_test "commands and workflows are OS aware" test_os_aware_command_contract
run_test "native macOS wrappers have a validated help surface and MLX bootstrap contract" test_macos_wrapper_help_surface
run_test "Linux/macOS user-facing scripts do not require PowerShell" test_linux_macos_scripts_do_not_require_pwsh
run_test "runtime context generation captures useful files and excludes build output" test_runtime_context_generation
run_test "install script dry run does not modify target repository" test_install_dry_run
run_test "project classifier emits a sanitized evidence-backed profile" test_project_profile_classifier
run_test "install script activates evidence-backed project rule packs" test_install_project_profile_activation
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
run_test "online model discovery normalizes Ollama and Hugging Face fixtures" test_multi_source_model_discovery
run_test "multi-repository validation docs define sanitized evidence workflow" test_multi_repository_validation_doc
run_test "sample repository factory validation evidence is sanitized" test_sample_repository_factory_validation_evidence
run_test "sample repository factory docs define generated fixtures" test_sample_repository_factory_doc
run_test "agent surface docs define portability boundary" test_agent_surface_options_doc
run_test "failed agent integrations have no executable surface" test_removed_agent_integrations
run_test "Continue CLI model testing docs define automation workflow" test_continue_cli_model_testing_doc
run_test "language support docs define staged multi-language boundary" test_language_support_doc
run_test "optional language rule packs are evidence-gated and not globally loaded" test_optional_language_rule_packs
run_test "project detection docs and guidance are evidence-gated" test_project_detection_doc
run_test "agent prompt rule and template contracts are enforced" test_agent_prompt_rule_template_contracts
run_test "sample repository factory creates expected fixtures" test_sample_repository_factory
run_test "medium language workflow matrix is complete and evidence-gated" test_language_workflow_validation_matrix
run_test "prompt quality guardrails require filename fidelity and sourced lifecycle claims" test_prompt_quality_guardrails_require_filename_fidelity
run_test "tool-use docs define platform-aware approved write behavior" test_tool_use_docs_define_platform_aware_write_behavior
run_test "hardware-aware recommendation scripts emit sanitized model lanes" test_hardware_aware_recommendation_scripts
run_test "shared asset installation docs define centralized config strategy" test_shared_asset_installation_doc
run_test "solution architecture review tracks milestone gaps" test_solution_architecture_review_doc
run_test "capability registry and deterministic routing enforce policy boundaries" test_capability_registry_and_routing
run_test "general AI sessions are repository optional and dry-run first" test_general_ai_session_workspace
run_test "local text capabilities are session bound and typed" test_local_text_capability_adapter
run_test "provider discovery and engineering routing preserve policy boundaries" test_provider_discovery_and_engineering_routes
run_test "optional LLM routing is advisory and registry gated" test_optional_llm_routing_boundary
run_test "local image capability is session bound typed and evidence gated" test_local_image_capability_adapter
run_test "recommended agent config generation writes local-only config" test_recommended_agent_config_generation
run_test "agent surface adapters plan installs configure and report health safely" test_agent_surface_adapters
run_test "workflow envelope contract is versioned private by default and cross-platform" test_workflow_envelope_contract
run_test "hosted CI verifier enforces exact-SHA cross-platform completion" test_hosted_ci_verifier_contract
run_test "wiki synchronization is deterministic and hosted" test_wiki_synchronization
run_test "model residency policy is applied across runtime and config paths" test_model_residency_policy_contract
run_test "ComfyUI setup guide preserves the validated secure provider profile" test_comfyui_setup_guide_contract
run_test "desktop runtime and IPC contracts are pinned and fail closed" test_desktop_runtime_and_ipc_contracts
run_test "desktop sidecar IPC policy rejects hostile messages" test_desktop_sidecar_ipc_policy
run_test "native bridge authority model rejects hostile boundaries" test_native_bridge_boundary_policy
run_test "core update policy fails closed before cryptographic admission" test_core_update_policy
run_test "workflow reliability threat model and data lifecycle fail closed" test_workflow_reliability_and_data_lifecycle
run_test "provider performance evidence and capacity preflight fail closed" test_provider_evidence_and_capacity
run_test "product UI first slice is registry-backed and fail closed" test_product_ui_first_slice
run_test "media onboarding and quantization foundations fail closed" test_media_onboarding_and_quantization_foundations

if [ "$FAILED" -eq 1 ]; then
  printf 'Test run failed. Tier=%s; %s tests executed; %s skipped; %s seconds.\n' "$TEST_TIER" "$TEST_COUNT" "$SKIPPED_COUNT" "$((SECONDS - RUN_STARTED_SECONDS))" >&2
  exit 1
fi

write_test_receipt
printf 'Test run passed. Tier=%s; %s tests executed; %s skipped; %s seconds.\n' "$TEST_TIER" "$TEST_COUNT" "$SKIPPED_COUNT" "$((SECONDS - RUN_STARTED_SECONDS))"
