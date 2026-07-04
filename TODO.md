# TODO

## Milestone 1: Minimum Usable Pack

### Project Documentation

- [x] Create initial README.
- [x] Define project purpose in `PROJECT.md`.
- [x] Define architecture boundaries in `ARCHITECTURE.md`.
- [x] Define staged roadmap in `ROADMAP.md`.
- [x] Define documentation and prompt style in `STYLEGUIDE.md`.
- [x] Define AI contributor guidance in `AI.md`.
- [x] Define decision log structure in `DECISIONS.md`.
- [x] Define changelog structure in `CHANGELOG.md`.
- [x] Add temporary license status.
- [x] Choose final license terms.

### Continue Configuration

- [x] Identify target Continue configuration schema.
- [x] Define local Ollama model assumptions.
- [x] Implement `.continue/config.yaml`.
- [x] Statically verify configured local file references exist.
- [x] Verify Continue can load the pack.
- [x] Verify model-backed prompt execution with Ollama.
- [x] Document setup and usage in `README.md`.

### Core Rules

- [x] Implement `.continue/rules/general.md`.
- [x] Implement `.continue/rules/git.md`.
- [x] Implement `.continue/rules/dotnet.md`.
- [x] Implement `.continue/rules/aspnetcore.md`.
- [x] Implement `.continue/rules/clean-architecture.md`.
- [x] Implement `.continue/rules/api.md`.
- [x] Implement `.continue/rules/testing.md`.
- [x] Implement `.continue/rules/logging.md`.
- [x] Implement `.continue/rules/security.md`.
- [x] Implement `.continue/rules/performance.md`.
- [x] Implement `.continue/rules/sonarqube.md`.

### Core Prompts

- [x] Implement `.continue/prompts/repository-discovery.md`.
- [x] Implement `.continue/prompts/implementation-plan.md`.
- [x] Implement `.continue/prompts/code-review.md`.
- [x] Implement `.continue/prompts/bug-investigation.md`.
- [x] Implement `.continue/prompts/security-review.md`.
- [x] Implement `.continue/prompts/architecture-review.md`.
- [x] Implement `.continue/prompts/performance-review.md`.
- [x] Implement `.continue/prompts/documentation.md`.
- [x] Implement `.continue/prompts/ai-framework-self-review.md`.
- [x] Implement `.continue/prompts/refactoring-planner.md`.
- [x] Implement `.continue/prompts/product-manager.md`.
- [x] Implement `.continue/prompts/release-readiness.md`.

### Primary Agents

- [x] Implement `.continue/agents/senior-engineer.md`.
- [x] Implement `.continue/agents/architect.md`.
- [x] Implement `.continue/agents/security-engineer.md`.
- [x] Implement `.continue/agents/reviewer.md`.
- [x] Implement `.continue/agents/performance.md`.
- [x] Implement `.continue/agents/documentation.md`.
- [x] Implement `.continue/agents/product-manager.md`.

### Core Templates

- [x] Implement `.continue/templates/Architecture.md`.
- [x] Implement `.continue/templates/SecurityReview.md`.
- [x] Implement `.continue/templates/PerformanceReview.md`.
- [x] Implement `.continue/templates/AI.md`.

## Milestone 2: Review Depth

- [x] Implement architecture review prompt.
- [x] Implement performance review prompt.
- [x] Implement documentation prompt.
- [x] Implement reviewer agent.
- [x] Implement performance agent.
- [x] Implement documentation agent.
- [x] Implement product manager agent.
- [x] Add example outputs for major workflows.
- [x] Expand SonarQube guidance.
- [x] Add validation checklists for prompt and rule changes.
- [x] Add decision records for major design choices.

## Milestone 3: Integrations

- [x] Research MCP options for repository and GitHub context.
- [x] Research SonarQube integration options.
- [x] Document manual SonarQube review workflow.
- [x] Add MCP setup documentation when implementation path is selected.
- [x] Add troubleshooting guidance.

## Release Hardening: 0.1.3

- [x] Add `CONTRIBUTING.md`.
- [x] Add release tagging guidance.
- [x] Add sample review fixtures.
- [x] Add validation automation.
- [x] Update pack version to `0.1.3`.
- [x] Update changelog for `0.1.3`.

## Milestone 4: Runtime Validation And CI

- [x] Add CI automation for `scripts/validate-pack.ps1`.
- [x] Update pack version to `0.1.4`.
- [x] Update changelog for `0.1.4`.
- [x] Validate the pack against additional realistic fixture inputs.
- [x] Add security review fixture.
- [x] Add performance review fixture.
- [x] Add release-readiness fixture.
- [x] Add runtime validation documentation.
- [x] Add runtime context generation.
- [x] Add legacy .NET dependency migration prompt.
- [x] Add legacy .NET dependency migration template.
- [x] Update pack version to `0.1.5`.
- [x] Update changelog for `0.1.5`.

## Milestone 5: Prompt Quality Hardening

- [x] Add implementation-planning quality fixture.
- [x] Add legacy dependency migration quality fixture.
- [x] Add documentation-review quality fixture.
- [x] Add release-readiness quality fixture.
- [x] Define pass/fail expectations for sensitive prompts.
- [x] Add local-model reliability guidance.
- [x] Extend static validation for prompt frontmatter and required metadata.
- [x] Add banned-output-pattern guidance for high-risk workflows.

## Milestone 6: Applied Tooling And Adaptive Models

- [x] Define safe tool-use modes for reviewed repositories.
- [x] Document how to enable approved tool-backed project changes.
- [x] Add guidance for converting approved plans into scoped edits.
- [x] Define hardware-aware local model selection strategy.
- [x] Add hardware-profile helper or documented collection commands.
- [x] Define recommended Ollama model tiers by RAM, VRAM, context size, and workflow risk.
- [x] Document how to keep machine-specific model and endpoint details out of committed config.

## Milestone 7: Cross-Platform Contributor Experience

- [x] Add Linux validation wrapper.
- [x] Add Linux test wrapper.
- [x] Add macOS validation wrapper.
- [x] Add macOS test wrapper.
- [x] Add CI coverage for Linux wrappers.
- [x] Document cross-platform validation commands.

## Milestone 8: Real Repository Validation

- [x] Run runtime validation against the pack repository itself.
- [x] Record sanitized self-validation results.
- [x] Add prompt guidance for configuration-pack repositories.
- [x] Add a prompt-quality fixture for non-application repositories.
- [x] Validate against an application repository when a suitable target is available.
- [x] Add project-specific MCP examples after validated real-world usage.

## Milestone 9: Distribution And Install Experience

- [x] Add an install or update script for copying `.continue` assets into a target repository.
- [x] Add backup behavior for existing target `.continue` folders.
- [x] Add dry-run output before copying files.
- [x] Add install validation for copied config, prompts, rules, agents, and templates.
- [x] Document Windows, Linux, and macOS install/update commands.
- [x] Ensure install outputs exclude local overrides, private endpoints, tokens, and machine-specific config.

## Milestone 10: ARM And Apple Silicon Model Support

- [x] Detect and report CPU architecture in hardware profile outputs when available.
- [x] Add architecture fields to Windows, Linux, and macOS hardware profile text and JSON output.
- [x] Document Apple Silicon, Windows ARM, and Linux ARM local-model differences.
- [x] Document Linux distro assumptions and optional GPU detection dependencies.
- [x] Document enterprise and cloud Linux assumptions for AWS, Azure, GCP, and RHEL-family style environments.
- [x] Document container, LXC, and LXD hardware visibility and GPU passthrough caveats.
- [x] Document Ollama/GGUF versus MLX model differences for Apple Silicon.
- [x] Add advanced Mac guidance for MLX models served through an OpenAI-compatible local endpoint.
- [x] Evaluate `mlx-lm` detection in the macOS hardware profile script.
- [x] Evaluate Linux ARM detection for NVIDIA Jetson or other ARM GPU acceleration paths.
- [x] Evaluate fallback behavior on minimal Linux distributions where optional GPU tools are unavailable.
- [x] Evaluate whether enterprise/cloud Linux images need additional validation fixtures or smoke-test guidance.
- [x] Evaluate whether containerized model servers need separate profile output warnings or detection.
- [x] Add conservative Windows ARM local-model guidance.
- [x] Review whether ARM architecture should affect recommendation tiering before changing `config/model-recommendations.tsv`.
- [x] Decide whether MLX or ARM recommendations belong in the shared TSV catalog or provider-specific catalogs.
- [x] Document unified-memory and shared-memory guidance for model sizing.
- [x] Keep ARM/MLX endpoints, private model names, and machine-specific paths out of committed config.

## Milestone 11: Editor Surface Compatibility

- [x] Document VS Code and VSCodium Continue extension differences.
- [x] Add sanitized terminal preflight evidence for locally installed VS Code-compatible and VSCodium Continue extensions.
- [x] Validate project-local `.continue/config.yaml` loading in VS Code-compatible builds when available.
- [ ] Confirm duplicate-rule status and exact project-local config loading in VSCodium.
- [x] Validate Agent mode and tool execution behavior in VS Code-compatible builds.
- [x] Validate Agent mode and tool execution behavior in VSCodium.
- [x] Document duplicate-rule troubleshooting for global plus project-local config conflicts.
- [x] Keep Continue CLI `npx` fallback instructions available for editor-specific issues.

## Milestone 12: Model Tool-Use Validation Evidence

- [x] Keep committed model examples lightweight and treat larger models as validated candidates instead of setup requirements.
- [x] Add install-script support for local-only model config generation from hardware profile recommendations.
- [x] Define repeatable read-only tool-use validation steps.
- [x] Record model, provider, editor surface, Continue version, operating system, and MCP state for validation runs.
- [x] Distinguish candidate model recommendations from tool-validated model status.
- [ ] Evaluate optional online Ollama model discovery for newer candidates without changing the offline default flow.
- [x] Add a sanitized evidence template for model tool-use validation results.
- [x] Decide where validated model evidence should live for current scope.
- [ ] Keep private endpoints, local paths, private repository names, and raw transcripts out of committed evidence.
