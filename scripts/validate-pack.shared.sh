#!/usr/bin/env bash
set -uo pipefail

EXPECTED_VERSION="0.3.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FAILED=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --expected-version|-ExpectedVersion)
      EXPECTED_VERSION="$2"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

pass() {
  printf 'PASS %s\n' "$1"
}

fail() {
  printf 'FAIL %s\n' "$1" >&2
  FAILED=1
}

matches_text() {
  local content="$1"
  local pattern="$2"
  grep -Eq "$pattern" <<<"$content"
}

matches_text_i() {
  local content="$1"
  local pattern="$2"
  grep -Eiq "$pattern" <<<"$content"
}

require_file() {
  if [ -e "$REPO_ROOT/$1" ]; then
    pass "required file exists: $1"
  else
    fail "required file exists: $1"
  fi
}

CONFIG_PATH="$REPO_ROOT/.continue/config.yaml"

if [ -f "$CONFIG_PATH" ]; then
  pass ".continue/config.yaml exists"
else
  fail ".continue/config.yaml exists"
fi

CONFIG_CONTENT="$(cat "$CONFIG_PATH" 2>/dev/null || true)"

if matches_text "$CONFIG_CONTENT" "^version:[[:space:]]+$EXPECTED_VERSION[[:space:]]*$"; then
  pass "config version is $EXPECTED_VERSION"
else
  fail "config version is $EXPECTED_VERSION"
fi

if matches_text "$CONFIG_CONTENT" '^schema:[[:space:]]+v1[[:space:]]*$'; then
  pass "config schema is v1"
else
  fail "config schema is v1"
fi

if matches_text "$CONFIG_CONTENT" '^mcpServers:[[:space:]]+\[\][[:space:]]*$'; then
  pass "default MCP server list is empty"
else
  fail "default MCP server list is empty"
fi

FILE_REFS="$(grep -Eo 'file://\./[^[:space:]]+' <<<"$CONFIG_CONTENT" | sed 's#file://./##' || true)"

while IFS= read -r ref; do
  [ -z "$ref" ] && continue
  if [ -e "$REPO_ROOT/.continue/$ref" ]; then
    pass "referenced file exists: .continue/$ref"
  else
    fail "referenced file exists: .continue/$ref"
  fi
done <<EOF
$FILE_REFS
EOF

for prompt_path in "$REPO_ROOT"/.continue/prompts/*.md; do
  [ -e "$prompt_path" ] || continue
  prompt_file="$(basename "$prompt_path")"
  prompt_name="${prompt_file%.md}"
  relative_prompt_path="prompts/$prompt_file"
  prompt_content="$(cat "$prompt_path")"

  if printf '%s' "$prompt_file" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*\.md$'; then
    pass "prompt filename is kebab-case: .continue/$relative_prompt_path"
  else
    fail "prompt filename is kebab-case: .continue/$relative_prompt_path"
  fi

  if grep -Fxq "$relative_prompt_path" <<< "$FILE_REFS"; then
    pass "prompt is referenced in config: .continue/$relative_prompt_path"
  else
    fail "prompt is referenced in config: .continue/$relative_prompt_path"
  fi

  if grep -Eq '^---' <<< "$prompt_content"; then
    pass "prompt frontmatter starts on first line: .continue/$relative_prompt_path"
  else
    fail "prompt frontmatter starts on first line: .continue/$relative_prompt_path"
  fi

  if grep -Eq "^name:[[:space:]]+['\"]?$prompt_name['\"]?[[:space:]]*$" <<< "$prompt_content"; then
    pass "prompt name matches filename: .continue/$relative_prompt_path"
  else
    fail "prompt name matches filename: .continue/$relative_prompt_path"
  fi

  if grep -Eq '^description:[[:space:]]+.+$' <<< "$prompt_content"; then
    pass "prompt description is present: .continue/$relative_prompt_path"
  else
    fail "prompt description is present: .continue/$relative_prompt_path"
  fi

  if grep -Eq '^invokable:[[:space:]]+true[[:space:]]*$' <<< "$prompt_content"; then
    pass "prompt is invokable: .continue/$relative_prompt_path"
  else
    fail "prompt is invokable: .continue/$relative_prompt_path"
  fi
done

REQUIRED_FILES=(
  "README.md"
  "BRANDING.md"
  "PROJECT.md"
  "ARCHITECTURE.md"
  "STYLEGUIDE.md"
  "ROADMAP.md"
  "TODO.md"
  "AI.md"
  "DECISIONS.md"
  "CHANGELOG.md"
  "LICENSE"
  "CONTRIBUTING.md"
  "SECURITY.md"
  ".github/CODEOWNERS"
  ".github/pull_request_template.md"
  "config/model-recommendations.tsv"
  "config/model-recommendations.mlx.tsv"
  "config/model-discovery-contract.json"
  "config/model-discovery-sources.json"
  "config/agent-surface-capabilities.json"
  "config/agent-surface-solutions.json"
  "config/agent-cli-surface-defaults.json"
  "config/sample-scenario-packs.json"
  "config/wiki-sync.tsv"
  "config/wiki-retired-pages.txt"
  "config/capabilities.json"
  "config/typed-artifact-contract.json"
  "config/desktop-ipc-contract.json"
  "config/ui-navigation-contract.json"
  "config/progressive-onboarding-contract.json"
  "config/onboarding-setting-schemas.json"
  "config/desktop-capability-policy.json"
  "config/native-bridge-boundary-contract.json"
  "config/desktop-storage-contract.json"
  "config/core-update-manifest-contract.json"
  ".github/workflows/codeql.yml"
  "docs/provider-endpoint-security.md"
  "scripts/provider_security.py"
  "config/providers.json"
  "config/engineering-routes.json"
  "docs/release.md"
  "docs/test-tiers.md"
  "docs/wiki-home.md"
  "docs/wiki-maintenance.md"
  "docs/capability-evidence-contract.md"
  "docs/capability-registry.md"
  "docs/capability-availability-and-engineering-routing.md"
  "docs/optional-llm-intent-routing.md"
  "docs/local-image-capability.md"
  "docs/comfyui-image-provider-setup.md"
  "docs/typed-artifact-contract.md"
  "docs/deterministic-intent-routing.md"
  "docs/general-ai-session-workspace.md"
  "docs/local-text-capabilities.md"
  "docs/setup-paths.md"
  "docs/config-generation-strategy.md"
  "docs/compatibility.md"
  "docs/workflow-chooser.md"
  "docs/desktop-runtime-dependency-evaluation.md"
  "docs/desktop-dependency-resolution-evidence.md"
  "docs/desktop-ipc-contract.md"
  "docs/native-bridge-boundary-evidence.md"
  "docs/product-ui-first-slice.md"
  "docs/progressive-onboarding.md"
  "docs/onboarding-setting-security.md"
  "docs/desktop-storage-and-updates.md"
  "docs/script-consolidation-plan.md"
  "docs/autonomous-maintainer-queue.md"
  "docs/runtime-validation.md"
  "docs/agent-surface-solutions.md"
  "docs/surface-specific-config-bundles.md"
  "docs/shared-asset-installation.md"
  "docs/editor-compatibility.md"
  "docs/prompt-quality.md"
  "docs/validation-checklists.md"
  "docs/troubleshooting.md"
  "docs/tool-use-modes.md"
  "docs/approved-tool-backed-changes.md"
  "docs/scoped-edits.md"
  "docs/local-config-safety.md"
  "docs/local-model-selection.md"
  "docs/online-model-discovery.md"
  "docs/multi-repository-validation.md"
  "docs/runtime-output-verification.md"
  "docs/agent-surface-options.md"
  "docs/agent-surface-promotion-gates.md"
  "docs/agent-integration-admission-policy.md"
  "docs/agent-surface-capability-parity.md"
  "docs/continue-cli-model-testing.md"
  "docs/language-support.md"
  "docs/project-detection.md"
  "docs/language-rule-packs.md"
  "docs/language-workflow-validation-matrix.md"
  "docs/sample-repository-factory.md"
  "docs/local-agent-model-testing.md"
  "docs/model-scorecard.md"
  "docs/evidence-dashboard.md"
  "docs/beginner-setup-mode.md"
  "docs/haven-42-menu.md"
  "docs/sample-scenario-packs.md"
  "docs/model-tool-use-validation.md"
  "docs/local-model-reliability.md"
  "docs/banned-output-patterns.md"
  "docs/mcp-options.md"
  "docs/mcp-setup.md"
  "docs/mcp-examples.md"
  "docs/sonarqube-review.md"
  "docs/sonarqube-integration-options.md"
  "scripts/generate-sample-repositories.ps1"
  "scripts/run-language-workflow-matrix.ps1"
  "scripts/run-language-workflow-matrix.shared.sh"
  "scripts/run-language-workflow-matrix.linux.sh"
  "scripts/run-language-workflow-matrix.macos.sh"
  "scripts/generate-sample-repositories.linux.sh"
  "scripts/generate-sample-repositories.macos.sh"
  "scripts/generate-sample-repositories.shared.sh"
  "scripts/build-release-package.ps1"
  "scripts/sync-wiki.ps1"
  "scripts/sync-wiki.shared.sh"
  "scripts/sync-wiki.linux.sh"
  "scripts/sync-wiki.macos.sh"
  "scripts/resolve-capability.ps1"
  "scripts/resolve-capability.py"
  "scripts/resolve-capability.shared.sh"
  "scripts/resolve-capability.linux.sh"
  "scripts/resolve-capability.macos.sh"
  "scripts/start-ai-session.ps1"
  "scripts/start-ai-session.py"
  "scripts/start-ai-session.shared.sh"
  "scripts/start-ai-session.linux.sh"
  "scripts/start-ai-session.macos.sh"
  "scripts/invoke-local-text-capability.ps1"
  "scripts/invoke-local-text-capability.py"
  "scripts/invoke-local-text-capability.shared.sh"
  "scripts/invoke-local-text-capability.linux.sh"
  "scripts/invoke-local-text-capability.macos.sh"
  "scripts/discover-capability-availability.ps1"
  "scripts/discover-capability-availability.py"
  "scripts/discover-capability-availability.shared.sh"
  "scripts/discover-capability-availability.linux.sh"
  "scripts/discover-capability-availability.macos.sh"
  "scripts/resolve-engineering-route.ps1"
  "scripts/resolve-engineering-route.py"
  "scripts/resolve-engineering-route.shared.sh"
  "scripts/resolve-engineering-route.linux.sh"
  "scripts/resolve-engineering-route.macos.sh"
  "scripts/suggest-capability-route.ps1"
  "scripts/suggest-capability-route.py"
  "scripts/suggest-capability-route.shared.sh"
  "scripts/suggest-capability-route.linux.sh"
  "scripts/suggest-capability-route.macos.sh"
  "scripts/invoke-local-image-capability.ps1"
  "scripts/invoke-local-image-capability.py"
  "scripts/invoke-local-image-capability.shared.sh"
  "scripts/invoke-local-image-capability.linux.sh"
  "scripts/invoke-local-image-capability.macos.sh"
  "scripts/invoke-workflow.linux.sh"
  "scripts/invoke-workflow.macos.sh"
  "scripts/invoke-workflow.shared.sh"
  "scripts/build-release-package.linux.sh"
  "scripts/build-release-package.macos.sh"
  "scripts/recommend-local-agent-config.ps1"
  "scripts/apply-recommended-agent-config.ps1"
  "scripts/recommend-local-agent-config.linux.sh"
  "scripts/apply-recommended-agent-config.linux.sh"
  "scripts/recommend-local-agent-config.macos.sh"
  "scripts/apply-recommended-agent-config.macos.sh"
  "scripts/recommend-local-agent-config.shared.sh"
  "scripts/apply-recommended-agent-config.shared.sh"
  "scripts/build-release-package.shared.sh"
  "scripts/generate-runtime-context.ps1"
  "scripts/generate-runtime-context.linux.sh"
  "scripts/generate-runtime-context.macos.sh"
  "scripts/generate-runtime-context.shared.sh"
  "scripts/install-continue-pack.ps1"
  "scripts/install-git-hooks.ps1"
  "scripts/install-continue-pack.linux.sh"
  "scripts/install-continue-pack.macos.sh"
  "scripts/install-continue-pack.shared.sh"
  "scripts/install-validated-model.ps1"
  "scripts/install-validated-model.linux.sh"
  "scripts/install-validated-model.macos.sh"
  "scripts/install-validated-model.shared.sh"
  "scripts/run-runtime-validation.ps1"
  "scripts/run-runtime-validation.linux.sh"
  "scripts/run-runtime-validation.macos.sh"
  "scripts/run-runtime-validation.shared.sh"
  "scripts/verify-runtime-output.ps1"
  "scripts/verify-runtime-output.linux.sh"
  "scripts/verify-runtime-output.macos.sh"
  "scripts/verify-runtime-output.shared.sh"
  "scripts/test-local-agent-health.ps1"
  "scripts/test-local-agent-health.linux.sh"
  "scripts/test-local-agent-health.macos.sh"
  "scripts/test-local-agent-health.shared.sh"
  "scripts/cleanup-local-agent-artifacts.ps1"
  "scripts/cleanup-local-agent-artifacts.linux.sh"
  "scripts/cleanup-local-agent-artifacts.macos.sh"
  "scripts/cleanup-local-agent-artifacts.shared.sh"
  "scripts/test-pack.ps1"
  "scripts/test-release-readiness.ps1"
  "scripts/test-release-readiness.linux.sh"
  "scripts/test-release-readiness.macos.sh"
  "scripts/test-release-readiness.shared.sh"
  "scripts/test-pack.linux.sh"
  "scripts/test-pack.macos.sh"
  "scripts/test-pack.shared.sh"
  "scripts/validate-pack.ps1"
  "scripts/validate-pack.linux.sh"
  "scripts/validate-pack.macos.sh"
  "scripts/validate-pack.shared.sh"
  "scripts/get-local-model-profile.windows.ps1"
  "scripts/get-local-model-profile.linux.sh"
  "scripts/get-local-model-profile.macos.sh"
  "scripts/discover-online-model-candidates.ps1"
  "scripts/discover-online-model-candidates.py"
  "scripts/desktop-ipc-policy.py"
  "scripts/native-bridge-boundary-policy.py"
  "scripts/build-ui-view-model.py"
  "scripts/evaluate-onboarding-configuration.py"
  "scripts/discover-online-model-candidates.linux.sh"
  "scripts/discover-online-model-candidates.macos.sh"
  "scripts/discover-online-model-candidates.shared.sh"
  "examples/fixtures/ollama-model-library.html"
  "examples/fixtures/huggingface-model-search-response.json"
  "scripts/generate-model-scorecard.ps1"
  "scripts/generate-model-scorecard.linux.sh"
  "scripts/generate-model-scorecard.macos.sh"
  "scripts/generate-model-scorecard.shared.sh"
  "scripts/generate-evidence-dashboard.ps1"
  "scripts/generate-evidence-dashboard.linux.sh"
  "scripts/generate-evidence-dashboard.macos.sh"
  "scripts/generate-evidence-dashboard.shared.sh"
  "scripts/get-beginner-setup-plan.ps1"
  "scripts/get-beginner-setup-plan.linux.sh"
  "scripts/get-beginner-setup-plan.macos.sh"
  "scripts/get-beginner-setup-plan.shared.sh"
  "scripts/show-haven-42-menu.ps1"
  "scripts/show-haven-42-menu.linux.sh"
  "scripts/show-haven-42-menu.macos.sh"
  "scripts/show-haven-42-menu.shared.sh"
  "scripts/show-workflow-chooser.ps1"
  "scripts/show-workflow-chooser.linux.sh"
  "scripts/show-workflow-chooser.macos.sh"
  "scripts/show-workflow-chooser.shared.sh"
  "scripts/pull-local-agent-models.ps1"
  "scripts/pull-local-agent-models.linux.sh"
  "scripts/pull-local-agent-models.macos.sh"
  "scripts/pull-local-agent-models.shared.sh"
  "scripts/test-local-agent-models.ps1"
  "scripts/test-local-agent-models.linux.sh"
  "scripts/test-local-agent-models.macos.sh"
  "scripts/test-local-agent-models.shared.sh"
  "scripts/test-continue-cli-models.ps1"
  "scripts/test-continue-cli-models.linux.sh"
  "scripts/test-continue-cli-models.macos.sh"
  "scripts/test-continue-cli-models.shared.sh"
  ".continue/prompts/legacy-dotnet-dependency-migration.md"
  ".continue/templates/LegacyDotNetDependencyMigration.md"
  ".continue/rule-packs/python.md"
  ".continue/rule-packs/typescript.md"
  "examples/fixtures/implementation-planning-quality-input.md"
  "examples/fixtures/config-pack-review-input.md"
  "examples/fixtures/documentation-review-quality-input.md"
  "examples/fixtures/legacy-dependency-migration-input.md"
  "examples/fixtures/sonarqube-findings.md"
  "examples/fixtures/repository-context.md"
  "examples/fixtures/security-review-input.md"
  "examples/fixtures/performance-review-input.md"
  "examples/fixtures/release-readiness-input.md"
  "examples/fixtures/release-readiness-quality-input.md"
  "examples/fixtures/ollama-chat-response.json"
  "examples/fixtures/onboarding-settings-request.json"
  "examples/fixtures/onboarding-trusted-admission.json"
  "examples/editor-surface-validation.md"
  "examples/local-text-capability-validation.md"
  "examples/capability-availability-validation.md"
  "examples/optional-llm-routing-validation.md"
  "examples/local-image-capability-validation.md"
  "examples/fixtures/ollama-tags-response.json"
  "examples/fixtures/ollama-capability-route-response.json"
  "examples/fixtures/ollama-invalid-capability-route-response.json"
  "examples/fixtures/comfyui-image-response.json"
  "examples/model-tool-use-validation.md"
  "examples/multi-repository-validation.md"
  "examples/sample-repository-factory-validation.md"
  "examples/language-rule-pack-validation.md"
  "examples/multi-language-workflow-validation.md"
  "config/language-workflow-validation-matrix.json"
  ".github/workflows/validate-pack.yml"
  ".github/CODEOWNERS"
  ".github/pull_request_template.md"
  ".githooks/pre-push"
)

for required in "${REQUIRED_FILES[@]}"; do
  require_file "$required"
done

PRIVATE_IP_PATTERN='(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})'
SECRET_PATTERN='(api[_-]?key|access[_-]?token|personal[_-]?access[_-]?token|password|secret)[[:space:]]*[:=][[:space:]]*["'\'']?[A-Za-z0-9_-]{16,}'

while IFS= read -r file; do
  rel="${file#$REPO_ROOT/}"
  case "$rel" in
    .git/*|runtime-validation-output/*|.continue/config.local*.yaml) continue ;;
  esac

  case "$file" in
    *.md|*.yaml|*.yml|*.ps1|*.sh|*.tsv|*.txt)
      content="$(cat "$file" 2>/dev/null || true)"
      if matches_text_i "$content" "$PRIVATE_IP_PATTERN"; then
        fail "no private IP address committed: $rel"
      fi
      if matches_text_i "$content" "$SECRET_PATTERN"; then
        fail "no likely secret committed: $rel"
      fi
      ;;
  esac
done < <(find "$REPO_ROOT" -type f)

if [ "$FAILED" -eq 0 ]; then
  printf 'Validation passed.\n'
  exit 0
fi

printf 'Validation failed.\n' >&2
exit 1
