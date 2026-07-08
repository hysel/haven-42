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
- [x] Add explicit global Continue config generation for editor setups that ignore project-local config files.
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
- [x] Confirm duplicate-rule status in VSCodium.
- [x] Validate Agent mode and tool execution behavior in VS Code-compatible builds.
- [x] Validate Agent mode and tool execution behavior in VSCodium.
- [x] Document duplicate-rule troubleshooting for global plus project-local config conflicts.
- [x] Make global config generation omit rules by default to prevent duplicate rule warnings.
- [x] Keep Continue CLI `npx` fallback instructions available for editor-specific issues.

## Milestone 12: Model Tool-Use Validation Evidence

- [x] Keep committed model examples lightweight and treat larger models as validated candidates instead of setup requirements.
- [x] Add install-script support for local-only model config generation from hardware profile recommendations.
- [x] Define repeatable read-only tool-use validation steps.
- [x] Require file-content read validation before treating a setup as ready for real code changes.
- [x] Define a repeatable approved-write smoke test for validating edit/apply tools.
- [x] Require post-edit content or diff verification before accepting claimed file changes.
- [x] Require external shell or git verification before marking approved-write smoke tests as passed.
- [x] Document duplicate approval mitigation by excluding `create_new_file` during existing-file write validation.
- [x] Add installer-supported model lanes so only validated write models receive edit/apply roles.
- [x] Require current-folder path resolution before approved edits.
- [x] Require workspace discovery before asking users for file paths.
- [x] Require Apply target alignment before approved edits.
- [x] Add platform-aware command guidance for Windows PowerShell, Linux, and macOS shells.
- [x] Record model, provider, editor surface, Continue version, operating system, and MCP state for validation runs.
- [x] Distinguish candidate model recommendations from tool-validated model status.
- [x] Evaluate optional online Ollama model discovery for newer candidates without changing the offline default flow.
- [x] Add a post-validation model installer that can download the selected validated model automatically and update local-only Continue config without committing private endpoints.
- [x] Add a sanitized evidence template for model tool-use validation results.
- [x] Add local Ollama API preflight tooling for Agent model pull, load/unload, tool-call, and exact-output checks.
- [x] Decide where validated model evidence should live for current scope.
- [x] Keep private endpoints, local paths, private repository names, and raw transcripts out of committed evidence.

## Milestone 13: Broader Multi-Repository Validation

- [x] Define repository categories for broader validation coverage.
- [x] Add a sanitized multi-repository validation evidence template.
- [x] Document the minimum validation flow for each repository category.
- [x] Require clean-tree, config-source, model, editor, MCP, and tool-use status in evidence.
- [x] Add validation and test coverage for the guide and template.
- [x] Record first sanitized Milestone 13 validation evidence for a legacy .NET repository category.
- [x] Convert first legacy validation findings into filename-fidelity and lifecycle-claim prompt guardrails.
- [x] Add deterministic output verification for filename fidelity, unsafe migration patterns, and lifecycle/support claims.
- [ ] Add stricter template fallback for workflows that repeatedly fail deterministic output verification.
- [ ] Add generated local sample repositories for additional validation categories when real repositories are not available.
- [ ] Validate the pack against additional real repositories when suitable targets are available.
- [ ] Convert repeated validation failures into prompt, rule, documentation, or script updates.
- [x] Keep private repository names, local paths, endpoints, raw transcripts, customer names, and source code out of committed evidence.

## Milestone 14: Agent Surface Portability And Broader Audience

- [x] Reposition the project name and top-level purpose beyond Continue-only and enterprise-only language.
- [ ] Add an agent-surface compatibility matrix for Continue, Cline, Aider, Kilo Code, OpenCode, OpenHands, and other credible open-source options.
- [ ] Define validation levels for each agent surface: read-only, plan validated, approved-write ready.
- [ ] Evaluate at least one non-Continue open-source agent surface with sanitized evidence.
- [ ] Decide whether install scripts should generate surface-specific config bundles instead of only `.continue` assets.
- [ ] Keep beginner-friendly local setup guidance aligned with enterprise-safe review and audit guidance.

## Milestone 15: Multi-Language Engineering Support

- [x] Document current language-support maturity and staged expansion in `docs/language-support.md`.
- [x] Add project-detection guidance for Python, JavaScript/TypeScript, Java/Spring, Go, Rust, SQL, and Infrastructure as Code repositories.
- [x] Add generated local sample repositories for at least Python and JavaScript/TypeScript validation.
- [x] Update rules, prompts, and agents to evidence-gate language-specific advice.
- [x] Add language-specific rules or guidance without applying them globally by default for Python and TypeScript.
- [ ] Validate repository discovery, implementation planning, and code review against Python and JavaScript/TypeScript samples.
- [x] Record focused Continue CLI repository-discovery validation for generated Python and TypeScript samples.
- [x] Record generated multi-language workflow validation once local Ollama API is reachable.
- [x] Record sanitized multi-language validation evidence for implementation planning and code review.
- [ ] Strengthen filename-drift guardrails for documentation, AI framework self-review, and release-readiness workflows.

## Milestone 16: Sample Repository Factory

- [x] Add `docs/sample-repository-factory.md`.
- [x] Add Windows sample repository factory script.
- [x] Add Linux and macOS sample repository factory wrappers.
- [x] Generate deterministic samples for Python, TypeScript, Node, Java, Go, Rust, Infrastructure as Code, and SQL.
- [x] Add validation and test coverage for sample factory scripts.
- [x] Add regression coverage that generated sample files do not leak factory script text or here-string markers.
- [x] Record initial script-level validation evidence for generated Python and TypeScript samples.
- [x] Use generated samples for focused read-only Continue CLI repository-discovery validation evidence.
- [x] Use generated samples for model-backed multi-language validation evidence.
- [ ] Improve runtime context generation for non-.NET project metadata as new ecosystems are added.

## Milestone 17: Agent Surface Compatibility Validation

- [ ] Validate Cline against a generated sample repository in read-only mode.
- [ ] Validate Aider against a generated sample repository in plan or patch mode.
- [ ] Record sanitized evidence for each non-Continue agent surface.
- [ ] Keep approved-write status blocked until external changed-file verification passes.

## Milestone 20: Hardware-Aware Model And Config Automation

- [x] Add offline hardware-aware recommendation scripts for Windows, Linux, and macOS.
- [x] Read sanitized model profile JSON plus curated model and evidence catalogs.
- [x] Emit WRITE SAFE, PLAN ONLY, and DEEP REVIEW recommendation lanes without contacting external services.
- [x] Add validation coverage for recommendation scripts, docs, and sanitized output behavior.
- [x] Generate local-only Continue config directly from the recommendation output.
- [ ] Reuse the recommendation data model for future non-Continue agent surfaces.
- [ ] Add a guided UI wrapper after script-level workflows are stable.

## Milestone 18: Language Rule Packs

- [x] Add optional Python rule pack.
- [x] Add optional TypeScript rule pack.
- [ ] Add optional Java, Go, Rust, SQL, and Infrastructure as Code rule packs.
- [x] Add evidence-gated rule selection guidance for optional Python and TypeScript packs.
- [x] Validate Python and TypeScript rule packs against generated sample repositories with static evidence checks.
- [ ] Validate rule packs against editor/model repository-discovery, implementation-planning, and code-review workflows.

## Milestone 19: Installer Profiles, Evidence Catalog, And Release Packaging

- [x] Add installer profile options for read-only review and approved-write workflows.
- [ ] Add future surface-specific profile generation after non-Continue validation.
- [x] Add a sanitized evidence catalog for model, surface, OS, language, and write-readiness results.
- [x] Add release archive, checksum, and install-command guidance.
