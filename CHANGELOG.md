# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple changelog format:

- `Added` for new capabilities
- `Changed` for updates to existing behavior or documentation
- `Fixed` for corrections
- `Removed` for deprecated or deleted behavior

## Unreleased

### Added

- Added Linux hardware profile platform notes for missing optional GPU detection tools and no-GPU detection fallbacks.
- Documented that CPU architecture is currently context for model selection, not a direct recommendation-tier input.
- Added a separate MLX model recommendation catalog and macOS MLX recommendation output for advanced Apple Silicon setups.
- Replaced Linux and macOS PowerShell-dependent wrappers with native Bash implementations for validation, tests, installation, runtime context generation, and runtime validation.

## 0.1.12 - 2026-07-03

### Added

- Added CPU architecture reporting to Windows, Linux, and macOS hardware profile scripts.
- Added a PowerShell install/update script with dry-run, backup, local-config exclusion, and install validation.
- Added tests for installer dry-run behavior, backup behavior, local-config exclusion, and self-target protection.
- Added Linux and macOS installer wrappers that call the canonical PowerShell installer.
- Added roadmap and TODO tracking for ARM, Apple Silicon, and MLX model support.
- Added VS Code and VSCodium compatibility guidance and roadmap tracking.
- Added a local-model tool-use validation checklist and roadmap tracking for model tool-use evidence.
- Added roadmap tracking for ARM architecture detection in hardware profile scripts.
- Added Linux distribution compatibility assumptions and optional GPU detection dependency guidance.
- Added enterprise and cloud Linux compatibility guidance for setup, install, validation, and hardware profiling.
- Added container, LXC, and LXD compatibility guidance for hardware visibility, GPU passthrough, and conservative model recommendations.
- Added ARM, Apple Silicon, Windows ARM, Linux ARM, MLX, unified-memory, and shared-memory model selection guidance.
- Added macOS hardware profile detection for MLX tooling as a separate signal from Ollama model recommendations.
- Added Linux hardware profile platform notes for ARM and NVIDIA Jetson/Tegra indicators.
- Added Linux and macOS CI smoke tests for native shell wrappers, hardware profile scripts, and installer wrappers.
- Added pack tests for validation/test wrapper coverage and runtime-validation missing-target handling.
- Added Linux and macOS CI smoke tests for runtime context generation.
- Added Linux and macOS shell wrappers for runtime context generation and runtime validation so users do not have to invoke PowerShell scripts directly.

### Changed

- Documented the current PowerShell install/update workflow in the README.
- Documented Windows, Linux, and macOS install/update commands in the README.

### Fixed

- Fixed Linux and macOS installer wrapper executable permissions so direct shell execution works in CI and user terminals.

## 0.1.11 - 2026-07-03

### Added

- Added documentation explaining how hardware profile scripts choose model recommendations from the local Ollama model list and catalog order.
- Added configuration-pack review guardrails and a prompt-quality fixture for non-application repositories.
- Added sanitized runtime validation notes from a private .NET Framework Excel-DNA add-in repository.
- Added practical MCP workflow examples for read-only repository review, approved write mode, and release-readiness context gathering.

### Changed

- Reworked the README quick start to cover Windows, Linux, and macOS setup and validation paths.
- Added a README quick-start note explaining that model helper scripts use `config/model-recommendations.tsv`.
- Added README path-selection, day-to-day usage, safe first prompt, and common-problem guidance.
- Added README hardware expectation and do-not-commit safety guidance.
- Clarified the README quick-start config step so users know to use the project-local `.continue/config.yaml`.

### Fixed

- Fixed runtime validation config/context path handling so relative paths are resolved before the runner changes into the target repository.

## 0.1.10 - 2026-07-02

### Added

- Added Linux and macOS validation/test wrapper scripts for contributors who prefer shell commands.
- Added CI coverage for Linux validation and test wrappers.
- Added sanitized runtime validation notes from pack repository self-validation.

## 0.1.9 - 2026-07-02

### Fixed

- Fixed validation path filtering so ignored local config files are handled correctly on Linux, macOS, and Windows.
- Fixed runtime context path filtering so build output directories are excluded correctly on Linux, macOS, and Windows.

## 0.1.8 - 2026-07-02

### Fixed

- Fixed Linux and macOS hardware profile output so numeric GPU memory prints as `GB VRAM`.
- Fixed Linux and macOS hardware profile JSON so RAM and VRAM values are emitted as numbers, with unknown or shared memory emitted as `null`.
- Fixed Windows AMD GPU profiling by using `dxdiag` as a dedicated VRAM fallback before unreliable WMI adapter memory values.

### Added

- Added automated pack tests for validation behavior, local config safety, model recommendation catalog structure, and Continue file reference integrity.
- Added model recommendations to hardware profile scripts based on detected resource tier and installed Ollama models.
- Added a version-controlled model recommendation catalog that scripts can use for future model updates without changing script logic.
- Added local configuration safety guidance for keeping private endpoints, local paths, hardware output, and model experiments out of committed config.

## 0.1.7 - 2026-07-02

### Added

- Added Milestone 6 roadmap and TODO items for tool-enabled project changes and hardware-aware local model selection.
- Added a beginner-friendly README quick start and safety section.
- Added tool-use mode guidance for read-only discovery, plan-only work, and approved write mode.
- Added approved tool-backed change guidance for safely moving from review to implementation.
- Added scoped edit guidance for converting approved plans into small, reviewable changes.
- Added hardware-aware local model selection guidance for Ollama-backed Continue workflows.
- Added a cross-platform PowerShell hardware profile helper for sanitized local model selection inputs.
- Improved the hardware profile helper with AMD-friendly GPU detection through `rocm-smi` and Windows display adapter registry data.
- Split hardware profiling into Windows PowerShell, Linux shell, and macOS shell helpers with Intel GPU detection guidance.
- Expanded README and local model selection documentation with detailed hardware profile script usage, prerequisites, output interpretation, and docs-folder guidance.
- Documented Windows local `file://C:/...` path behavior, duplicate-rule causes, raw JSON tool-call failures, and runtime-context fallback guidance from VSCodium/Ollama validation.
- Changed the default chat/edit/apply model to `qwen3-coder:30b` after validation showed it supports Continue Agent tool execution more reliably than `qwen2.5-coder:7b`.

## 0.1.6 - 2026-07-02

### Added

- Added Milestone 5 tracking for prompt quality hardening.
- Added prompt-quality documentation with legacy dependency migration, documentation review, release readiness, and implementation planning pass/fail expectations.
- Added an implementation-planning quality fixture for plan-only, layered-change validation.
- Added a documentation-review quality fixture for onboarding, operations, release, and support gap validation.
- Added a legacy dependency migration quality fixture.
- Added a release-readiness quality fixture for no-go evidence validation.
- Added local-model reliability guidance for Ollama-backed prompt validation and escalation.
- Added banned-output-pattern guidance for high-risk prompt workflows.
- Added static validation for prompt frontmatter, required metadata, filename style, and config coverage.
- Closed Milestone 4 using sanitized fixture-based validation coverage and moved broader real-repository validation to backlog.

## 0.1.5 - 2026-07-02

### Added

- Added runtime validation tracking documentation and security, performance, and release-readiness fixtures.
- Added README and troubleshooting guidance for using `npx @continuedev/cli` when `cn` is not installed.
- Added a runtime validation runner that captures prompt outputs to ignored local files.
- Added runtime context generation for local-model validation without CLI tool execution.
- Added a dedicated legacy .NET dependency migration prompt for safe `packages.config` to `PackageReference` planning.
- Added a fixed legacy .NET dependency migration template to reduce unsafe local-model migration recipes.

### Changed

- Tightened implementation planning guidance for legacy .NET project and dependency-management migrations.
- Strengthened legacy project migration guardrails after runtime validation showed unsafe project-file rewrite recommendations.
- Added explicit safeguards against mechanical `packages.config` migration recipes for custom MSBuild and add-in projects.
- Added forbidden response patterns and minimum acceptable plan requirements to the legacy .NET dependency migration workflow.
- Recorded local-model validation failure for legacy dependency migration despite explicit no-XML instructions.
- Recorded template-driven legacy dependency migration failure and documented the human-reviewed template fallback.

## 0.1.4 - 2026-07-02

### Added

- Added GitHub Actions validation workflow for the pack validation script.

## 0.1.3 - 2026-07-02

### Added

- Added validation checklists for prompts, rules, agents, templates, config, examples, documentation, and releases.
- Added troubleshooting guidance for config loading, local file references, Ollama connectivity, model availability, prompt visibility, rules, local endpoint overrides, and line-ending warnings.
- Added MCP options research with a local-first recommendation that keeps MCP optional and compatible with Ollama-backed systems.
- Added SonarQube integration options research with a manual-first, Web API automation recommendation and optional MCP guidance.
- Added optional GitHub MCP setup guidance and compatibility notes for Continue, Ollama, MCP, and SonarQube workflows.
- Added contributor guidance, release tagging guidance, validation automation, and sanitized review fixtures.

## 0.1.2

### Changed

- Selected the MIT License for repository reuse and redistribution.
- Verified that Continue CLI can load the pack configuration.
- Validated model-backed execution against a local-network Ollama endpoint used only as a test-time override.
- Added representative examples for major workflows.
- Added manual SonarQube review workflow documentation and example output.

## 0.1.1

### Added

- Project documentation foundation.
- Continue pack governance guidance.
- Architecture, roadmap, style, and task tracking documentation.
- Initial decision log.
- Continue `schema: v1` configuration with local-first Ollama defaults.
- Core agents, prompts, rules, and templates.
- Supplemental review prompts for AI framework self-review, refactoring planning, product-management review, and release readiness.

### Changed

- README now documents early implementation status, setup assumptions, and pending runtime validation.

## 0.1.0

### Added

- Initial repository structure for a Continue Enterprise Engineering Pack.
