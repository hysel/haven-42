# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple changelog format:

- `Added` for new capabilities
- `Changed` for updates to existing behavior or documentation
- `Fixed` for corrections
- `Removed` for deprecated or deleted behavior

## Unreleased

### Added

- Added optional Python and TypeScript rule packs under `.continue/rule-packs/` with evidence gates so they are not globally loaded by default.
- Added `docs/language-rule-packs.md` for optional language rule-pack selection, default config behavior, and validation expectations.
- Added `docs/project-detection.md` for evidence-based ecosystem, framework, build, package, and test-system classification before language-specific advice.
- Added focused Continue CLI repository-discovery validation evidence for generated Python and TypeScript samples after improving runtime context fidelity.
- Added sample repository factory documentation and scripts for disposable local validation repositories.
- Added sanitized sample repository factory validation evidence for generated Python and TypeScript samples.
- Added roadmap and TODO tracking for sample repository factory, agent-surface compatibility validation, language rule packs, installer profiles, evidence catalogs, and release packaging.

### Changed

- Updated core prompts, shared rules, and agents to evidence-gate language-specific recommendations and use `unconfirmed` when project metadata is missing.
- Improved runtime context generation so nested target folders do not inherit parent repository git status and common multi-language project metadata is included in context excerpts.

### Fixed

- Fixed PowerShell sample repository factory README generation so Markdown command examples do not leak factory script text into generated samples.
- Added regression checks that generated sample README and source files do not contain factory script or here-string markers.

## 0.2.0 - 2026-07-05

### Added

- Added Milestone 15 roadmap and TODO tracking for staged multi-language engineering support beyond the current .NET-centered guidance.
- Added `docs/language-support.md` to define current ecosystem maturity, planned language expansion, and guardrails against applying .NET-specific advice to non-.NET repositories.
- Added Milestone 14 roadmap and TODO tracking for agent-surface portability and broader non-enterprise adoption.
- Added deterministic runtime output verification for filename fidelity, unsafe migration patterns, and source-grounded compatibility/lifecycle/support claims.
- Added prompt-quality guardrails and tests for exact filename fidelity, mixed-filename synthesis prevention, and source-grounded lifecycle/support claims after the first legacy repository validation run.
- Added Linux hardware profile platform notes for missing optional GPU detection tools and no-GPU detection fallbacks.
- Documented that CPU architecture is currently context for model selection, not a direct recommendation-tier input.
- Added a separate MLX model recommendation catalog and macOS MLX recommendation output for advanced Apple Silicon setups.
- Replaced Linux and macOS PowerShell-dependent wrappers with native Bash implementations for validation, tests, installation, runtime context generation, and runtime validation.
- Renamed shared Linux and macOS Bash implementation files to the `*.shared.sh` suffix to avoid implying support beyond Linux and macOS.
- Added Linux profile warnings and smoke-test guidance for enterprise/cloud images and container or LXC-style environments.
- Added editor compatibility guidance for VS Code, VSCodium, project-local configs, duplicate rules, Agent mode, and CLI fallback testing.
- Changed the committed Ollama model to a smaller starter sample and added install-script support for generating a local-only config from hardware profile recommendations.
- Added roadmap tracking for optional online Ollama model discovery as candidate-only, local-validation-required future work.
- Added model tool-use validation guidance and a sanitized evidence template for recording candidate, read-only validated, plan-validated, and approved-write-ready model status.
- Added sanitized editor-surface preflight evidence for local VS Code-compatible and VSCodium Continue extension detection, plus terminal preflight guidance.
- Recorded sanitized VS Code-compatible read-only Agent validation evidence with `qwen3-coder:30b` on an application-style sample repository.
- Recorded sanitized VSCodium Agent tool validation results, including an initial tool-call markup failure and a controlled read-only Agent retest that successfully listed repository files.
- Recorded clean duplicate-rule status for the current VS Code-compatible and VSCodium validation setup and closed Milestone 11 for the current scope.
- Added installer support for explicitly updating the global Continue config with absolute references to a target repository's installed rules, prompts, and docs.
- Added platform-aware command guidance so Windows Agent workflows use PowerShell-native commands instead of Linux shell commands.
- Added an approved-write smoke test for validating Continue edit/apply tool behavior before trusting Agent mode to modify projects.
- Changed global Continue config generation to omit `rules:` by default so project-local `.continue/rules` do not produce duplicate rule warnings.
- Added read-content tool validation guidance so Agent mode cannot treat file-listing success as enough evidence for real code changes.
- Added post-edit diff verification guidance so Agent mode cannot claim a file changed when no changed content or diff exists.
- Added current-folder path resolution guidance so Agent mode does not create wrong-folder files for unqualified targets.
- Added workspace discovery guidance so Agent mode tries tools against the opened folder before asking users for explicit file paths.
- Added Apply target alignment guidance so users do not apply patches that target a different file than the one requested or read.
- Clarified that printed `edit_file` text without a real diff is `WRITE_NOT_APPLIED`.
- Clarified that validation status labels must not claim success when a failure signal is present.
- Added external shell and git verification requirements for approved-write validation so assistant-only readback cannot create false positive write passes.
- Added local Agent model pull and preflight scripts for Ollama API-level tool-call, load/unload, and exact-content validation before manual Continue Apply testing.
- Added a post-validation model installer for applying a selected validated model to local-only Continue profile config.
- Added duplicate approval and duplicate content guidance for existing-file Continue Agent write validation.
- Added installer-supported model profiles for separating WRITE SAFE, PLAN ONLY, and DEEP REVIEW Agent roles while keeping embeddings separate.
- Added optional online Ollama model discovery guardrails that keep discovery candidate-only, explicit, non-installing, and separate from local validation.
- Added broader multi-repository validation guidance and a sanitized evidence template for future real-repository validation runs.

### Changed

- Repositioned the project docs around the broader `Local Engineering Agent Pack` name while keeping Continue as the first supported and validated agent surface.
- Changed generated model profiles to use `qwen3.5:9b` for WRITE SAFE, PLAN ONLY, and DEEP REVIEW by default so simple-hardware setups do not require 24B or 30B models.
- Tuned the committed local model defaults to `contextLength: 16384` and `maxTokens: 2048` after VS Code and VSCodium Agent testing showed better responsiveness with smaller local output budgets.
- Clarified approved write mode so models must use edit/apply tools after explicit approval or report that write tools are unavailable.
- Added `-GlobalConfigIncludeRules` and `--global-config-include-rules` for explicit global-only rule loading when needed.
- Added `READ_TOOLS_UNAVAILABLE` guidance for cases where the model can list files but cannot read the source or config files it wants to change.
- Added `WRITE_NOT_APPLIED` guidance for cases where the model claims an edit but the file content or git diff does not show it.
- Clarified that claimed file readback is not enough for approved-write readiness unless `git status` and shell file checks can see the change.
- Documented that automated local model preflight is candidate screening only and does not replace editor Apply validation.
- Added `PATH_AMBIGUOUS` guidance for cases where the correct edit target cannot be proven from the opened repository folder.
- Added `WORKSPACE_UNAVAILABLE` guidance for cases where Continue cannot discover the opened workspace.
- Added `APPLY_TARGET_MISMATCH` guidance for cases where the Continue Apply panel targets an unrelated file.

## 0.1.12 - 2026-07-03

### Added

- Added CPU architecture reporting to Windows, Linux, and macOS hardware profile scripts.
- Added a PowerShell install/update script with dry-run, backup, local-config exclusion, and install validation.
- Added tests for installer dry-run behavior, backup behavior, local-config exclusion, and self-target protection.
- Added Linux and macOS installer wrappers.
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
- Changed the default chat/edit/apply model after validation showed the previous small coder model emitted raw tool-call text in the tested Continue setup.

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

- Initial repository structure for a Continue-based enterprise engineering pack.
