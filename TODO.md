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
- [x] Document centralized shared asset installation design for teams or users with multiple target projects.
- [x] Implement centralized shared asset installation so global configs can point to one managed rules/prompts/docs folder instead of one project copy.

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
- [x] Validate a current MLX runtime and an Apple Silicon MLX candidate through local endpoint tool calls plus Continue CLI read, plan, review, and disposable scoped-write smoke checks.

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
- [x] Add deterministic filename-fidelity fallback artifacts for workflows that fail runtime output verification.
- [x] Add generated local sample repositories for additional validation categories when real repositories are not available.
- [x] Complete Milestone 13 coverage with legacy .NET real-category evidence plus generated Python, TypeScript, Node, Java, Go, Rust, Infrastructure as Code, and SQL sample-category evidence.
- [x] Keep private repository names, local paths, endpoints, raw transcripts, customer names, and source code out of committed evidence.

## Future Multi-Repository Evidence Expansion

- [ ] Add workflow-specific remediation templates for non-filename deterministic output verification failures if they recur.
- [ ] Validate the pack against additional real repositories when suitable targets are available.
- [ ] Convert repeated validation failures into prompt, rule, documentation, or script updates.

## Milestone 14: Agent Surface Portability And Broader Audience

- [x] Reposition the project name and top-level purpose beyond Continue-only and enterprise-only language.
- [x] Add an agent-surface compatibility matrix for maintained and documentation-only candidate open-source options.
- [x] Define validation levels for each agent surface: read-only, plan validated, approved-write ready.
- [x] Evaluate at least one non-Continue open-source agent surface with sanitized evidence.
- [x] Decide whether install scripts should generate surface-specific config bundles instead of only `.continue` assets.
- [x] Keep beginner-friendly local setup guidance aligned with enterprise-safe review and audit guidance.
- [x] Complete Milestone 14 positioning, support-boundary, and broader-audience exit criteria with evidence-gated surface docs.
- [x] Move full cross-agent validation and install/configure/test parity out of Milestone 14 and keep it tracked in Milestones 17 and 19.

## Milestone 15: Multi-Language Engineering Support

- [x] Document current language-support maturity and staged expansion in `docs/language-support.md`.
- [x] Add project-detection guidance for Python, JavaScript/TypeScript, Java/Spring, Go, Rust, SQL, and Infrastructure as Code repositories.
- [x] Add generated local sample repositories for at least Python and JavaScript/TypeScript validation.
- [x] Update rules, prompts, and agents to evidence-gate language-specific advice.
- [x] Add language-specific rules or guidance without applying them globally by default for Python and TypeScript.
- [x] Validate repository discovery, implementation planning, and code review against Python and JavaScript/TypeScript samples.
- [x] Record focused Continue CLI repository-discovery validation for generated Python and TypeScript samples.
- [x] Record generated multi-language workflow validation once local Ollama API is reachable.
- [x] Record sanitized multi-language validation evidence for implementation planning and code review.
- [x] Strengthen filename-drift guardrails for runtime prompts and runtime validation runners.
- [x] Add deterministic filename-fidelity fallback artifacts for workflows that repeatedly fail deterministic filename-fidelity verification.

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
- [x] Improve runtime context generation for non-.NET project metadata as new ecosystems are added.
- [x] Complete Milestone 16 sample repository factory exit criteria with evidence and regression tests.

## Milestone 17: Agent Surface Compatibility Validation

- [x] Add shared agent CLI automation scripts and thin wrappers for maintained Aider and OpenCode read-only and disposable write-smoke model screening.
- [x] Validate Aider against a generated sample repository in plan or patch mode.
- [x] Add Continue CLI automation scripts for future read-only and disposable write-smoke model screening.
- [x] Keep real-project approved-write status blocked until generated-sample scoped edit validation passes; continue blocking real-project approval until explicitly approved non-generated repository validation passes.
- [x] Complete Milestone 17 for the promoted supported-surface set: Continue, Aider, and OpenCode have explicit validation positions; documentation-only candidates do not count as supported parity.
- [x] Promote Aider as the first end-to-end non-Continue adapter by completing install, local-model configuration, health, and test automation with sanitized deterministic coverage; keep real-project approved write blocked.

## Future Agent Surface Evidence Expansion

- [x] Remove Roo Code wrappers and active metadata after upstream retirement; retain only a concise decision record under the agent admission policy.
- [x] Add a local-only OpenCode Ollama config generator and documented npm install plan to the unified setup adapter.
- [x] Validate OpenCode's installed CLI and `opencode run` wrapper against a generated sample with read-only and disposable write-smoke checks.
- [x] Add an opt-in generated Python scoped-edit gate to the shared CLI harness; record live evidence separately before any surface promotion.
- [x] Validate the OpenCode Devstral Small 2 generated Python scoped-edit gate with external changed-file, content, and whitespace verification.
- [x] Define a safe OpenHands validation boundary before adding platform-agent validation automation.
- [ ] Run explicitly approved non-generated repository validation before promoting any non-Continue surface to real-project approved-write ready.

## Milestone 18: Language Rule Packs

- [x] Add optional Python rule pack.
- [x] Add optional TypeScript rule pack.
- [x] Add optional Java, Go, Rust, SQL, and Infrastructure as Code rule packs.
- [x] Add evidence-gated rule selection guidance for optional Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code packs.
- [x] Validate optional language rule packs against generated sample repositories with static evidence checks.
- [x] Validate rule packs against Continue CLI repository-discovery, implementation-planning, code-review, and scoped-write workflows on generated medium fixtures. Composite Windows model lanes cover all 28 required cells, and Linux WSL2 evidence independently covers the same matrix.
- [x] Add a machine-readable project-profile classifier with ecosystem, evidence, confidence, and selected rule-pack IDs.
- [x] Activate matching optional language rule packs through project-local installer/config generation so installed projects do not require manual rule wiring.
- [x] Add medium-complexity language samples and a representative validation matrix covering discovery, planning, review, and scoped write; keep editor/model operation cells pending until executed.
- [x] Run the medium-fixture matrix through Continue CLI on Windows and record exact operation-to-model evidence; a Devstral Small 2 default plus Qwen 3.5 35B TypeScript-write override validates all 28 cells.
- [x] Add native Linux/macOS matrix-runner parity with shared Bash orchestration and dry-run validation.
- [x] Run the Linux matrix against live models in WSL2 Ubuntu 24.04. Devstral completed all 28 cells and Qwen completed the TypeScript scoped-write override with one-model-at-a-time unload safeguards.
- [x] Extend language-aware selector lookup to consume Linux validation evidence without inheriting Windows evidence.
- [x] Complete the native macOS matrix for all language packs. On 2026-07-17, Devstral Small 2 completed all 28 Continue CLI cells across separate bounded Apple Silicon runs with exact-file checks, external scoped-write verification, and confirmed model unload. The earlier Qwen 3.5 9B TypeScript reliability failure remains evidence against that weaker lane, not against the rule packs.
- [x] Generate a read-only language-aware model-lane recommendation from operation-level matrix evidence so a detected project and workflow select only a validated lane. Surface-specific runtime auto-switching remains a future adapter capability.

## Milestone 19: Installer Profiles, Evidence Catalog, And Release Packaging

- [x] Add installer profile options for read-only review and approved-write workflows.
- [x] Add a sanitized evidence catalog for model, surface, OS, language, and write-readiness results.
- [x] Add release archive, checksum, and install-command guidance.
- [x] Complete Milestone 19 Continue installer profile, evidence catalog, and release packaging exit criteria.
- [x] Define Capability Evidence Contract v2 keyed by surface, model, provider, OS, surface version, operation, and validation mode.
- [x] Migrate evidence lookup away from first-row-per-model behavior and aggregate duplicate evidence conservatively with provenance.
- [x] Prevent write-readiness evidence from one agent surface from being inherited by another surface.
- [x] Complete Milestone 19 install/configure/health parity for evidence-backed CLI adapters: Aider and OpenCode share dry-run-safe setup, local-only config, repository-local exclusion, health checks, and deterministic cross-platform contract tests. OpenHands remains separately evidence-blocked.
- [x] Add Aider install/configure automation with an explicit local-only config and supported isolated install methods.
- [x] Remove failed Cline and Kilo integrations from scripts, adapters, active catalogs, detailed evidence, and restoration backlog; require a fresh proposal and complete promotion-gate validation before either can return.
- [x] Adopt a repository-wide agent admission policy: evaluate candidates outside the tracked pack, ship assets only after all gates pass, and document failed evaluations without retaining implementation artifacts.
- [x] Keep OpenHands outside supported install/configure/test parity under the defined rootless workspace, sandbox, credential, mount, and deny-by-default network boundary until an implementation is explicitly approved and validated.

## Milestone 20: Hardware-Aware Model And Config Automation

- [x] Add offline hardware-aware recommendation scripts for Windows, Linux, and macOS.
- [x] Read sanitized model profile JSON plus curated model and evidence catalogs.
- [x] Emit WRITE SAFE, PLAN ONLY, and DEEP REVIEW recommendation lanes without contacting external services.
- [x] Add validation coverage for recommendation scripts, docs, and sanitized output behavior.
- [x] Generate local-only Continue config directly from the recommendation output.
- [x] Reuse the recommendation data model for future non-Continue agent surfaces.
- [x] Add a surface-neutral install/configure/test solution catalog for every tracked agent surface.
- [x] Add config-generation strategy that can choose between project-local assets and centralized shared assets for Continue and future agent plugins.
- [x] Add a script consolidation plan for shared engines, registries, dispatchers, thin wrappers, and no-consolidate-yet cases.
- [x] Consolidate PowerShell agent CLI wrapper defaults behind the shared agent CLI harness default catalog.
- [x] Consolidate Bash agent CLI wrapper defaults behind the shared agent CLI harness default catalog.
- [x] Add lane-specific model scoring that keeps WRITE SAFE reliability-first and can select larger validated PLAN ONLY or DEEP REVIEW models when hardware permits.
- [x] Replace parameter-name-only VRAM estimates for curated models with metadata for quantization assumptions, context target, backend overhead, model architecture or MoE behavior, and configurable memory reserve; retain a labeled low-confidence fallback for unknown tags.
- [x] Consolidate the onboarding/navigation script family behind a shared PowerShell module and native wrapper dispatcher before adding more plugin-specific wrappers.
- [x] Replace the no-PowerShell informational fallback for beginner plan, agent menu, and workflow chooser with a native Linux/macOS Python 3 renderer.
- [x] Define a versioned workflow request, progress, result, warning, and error envelope for dispatchers and the future UI.
- [x] Add a guided command/menu layer so end users choose from a small set of intents instead of individual scripts.
- [x] Keep individual script documentation as appendix/reference material for advanced users and maintainers.
- [x] Define a machine-readable workflow registry for tasks, inputs, outputs, safety level, platform support, and script entry points.
- [x] Define the stable script/API boundary that a future unified starter-toolkit web UI should call by adding a shared command dispatcher over the workflow registry.
- [x] Add cross-platform workflow dispatcher wrappers for Linux and macOS over the shared workflow registry.
- [x] Design a unified web UI for local-AI coding setup, hardware profiling, model choice, config generation, agent-surface testing, and validation.
- [x] Hand unified UI implementation to Milestone 22 after validating evidence v2, project-profile activation, lane scoring, one non-Continue adapter, and workflow envelopes.
- [x] Keep the UI evidence-first by showing tested, passed, failed, and recommended-only states before applying changes.
- [x] Generate a local evidence dashboard from committed evidence and surface readiness data.
- [x] Add beginner setup mode for the common local-AI coding setup path.
- [x] Add a health check workflow for Ollama, models, config, duplicate rules, repository detection, and validation status.
- [x] Add a safe cleanup workflow with dry-run support for failed models, stale runtime output, generated samples, and old backups.
- [x] Add a release readiness gate for validation, tests, docs/wiki freshness, whitespace checks, and optional remote workflow status.
- [x] Enforce exact-SHA hosted CI verification after every push, including required Windows/Linux/macOS jobs, failed-log retrieval, and explicit push/CI states.
- [x] Add a model scorecard for tool support, speed, quality, write behavior, context size, hardware tier, and recommended use.
- [x] Keep surface-specific plugin profiles outside Milestone 20 completion and admit each future profile only after compatibility evidence exists.
- [x] Add sample scenario packs for legacy migration, config refactoring, bug fixing, security review, test generation, and documentation cleanup.

## Milestone 21: General-Purpose AI Assistant And Intent Routing

- [x] Define a provider-neutral capability registry above the engineering workflow registry for chat, writing, summarization, image creation, software work, and local-AI setup.
- [x] Define typed result artifacts, capability availability states, privacy disclosures, and safety metadata for local and external providers.
- [x] Add deterministic registry routing with explicit-ID selection, phrase and keyword matching, ambiguity handling, unmatched fallback, and no automatic invocation.
- [x] Add a repository-optional, dry-run-first session workspace for general-purpose tasks.
- [x] Add a deterministic first-run "What would you like to do?" menu and rule-based intent fallback that does not require an LLM.
- [x] Add one dry-run-first local Ollama text adapter with bounded live chat, writing, summarization, typed-artifact, sanitization, cleanup, and cross-platform contract evidence.
- [x] Route software-work capabilities into deterministic, non-invoking plans over the existing workflow registry without weakening engineering evidence gates.
- [x] Add offline-first provider availability discovery with an explicit bounded Ollama health probe that never persists endpoint values or downloads models.
- [x] Add provider discovery and one evidence-gated image-generation adapter without assuming chat models support image generation.
- [x] Add an optional LLM intent router that can clarify and suggest capability IDs but cannot bypass availability, privacy, policy, or approval checks.
- [x] Add cross-platform contract tests for deterministic routing, unavailable capabilities, typed artifacts, repository-free operation, and safety enforcement.
- [x] Hand stable individual capabilities and artifact contracts to Milestone 22. Stop for UI design discussion before implementation.

## Milestone 22: Unified Product UI And Task Composition

- [x] Select and document Tauri 2 with bundled React/TypeScript/Vite assets, a packaged Haven 42 engine sidecar, private typed stdin/stdout IPC, and a separately promoted headless loopback mode.
- [x] Pin and review the direct Tauri, Rust, frontend, WebView, sidecar-packaging, installer, and license candidate set without scaffolding shippable runtime files.
- [x] Define a versioned desktop IPC schema and Tauri capability allowlist that reject arbitrary commands, unknown workflow/capability IDs, malformed envelopes, unauthorized paths, and remote UI navigation.
- [x] Resolve and audit the exact disposable Windows x64 npm, Cargo, and PyInstaller candidate graphs without admitting their manifests, locks, tools, or outputs.
- [ ] Resolve the five Windows-reachable unmaintained `rust-unic` advisories through an upstream update or a time-bounded reviewed exception, then repeat the audit with an attested or controlled source-built tool.
  - Upstream commit `dd725f4b13c3` removes the chain and passed the controlled disposable probe; keep this open until the fix ships in a reviewed Tauri release.
- [x] Run native `cargo check`, minimal Tauri build, SBOM, and package inspection on a disposable Windows runner with Microsoft C++ build tools before admitting runtime files.
- [ ] Resolve and lock the full npm, Cargo, Python, native-library, and packaging dependency graph; generate vulnerability, provenance, checksum, and third-party-license reports before runtime admission.
- [ ] Implement native bridge and sidecar negative tests for malformed/oversized messages, command injection, path/grant escape, approval replay, remote content, cancellation, lifecycle, and privilege boundaries.
  - The offline engine-side validator passes 46 hostile message/operation cases, and the native-authority policy model passes 55 path, link, approval, lifecycle, cancellation, environment, and privilege cases. Actual Rust/Tauri bridge, operating-system canonical path, WebView, process lifecycle, and privilege tests remain open until a runtime is admissible.
- [x] Define Windows, Linux, and macOS application, configuration, state, workspace, artifact, cache, update, and rollback locations without mixing immutable engine and user-owned data.
- [ ] Add platform package promotion gates for Windows x64/ARM64, Linux x64/ARM64 on a bounded distribution matrix, and macOS Apple Silicon/Intel, with a physical Mac reserved for the final public-release flow.
- [ ] Pursue Microsoft Store or SignPath Foundation Windows signing before paid Artifact Signing; defer Apple Developer enrollment until the first public macOS beta is otherwise ready.
- [x] Define a versioned core-engine update manifest for immutable Windows, macOS, and Linux assets published through GitHub Releases.
- [x] Add a cross-platform offline core-update policy that strictly validates manifest shape, immutable release identity, exact host asset, compatibility schemas, byte size, and SHA-256 while always denying download, staging, and activation.
- [x] Add a strict offline GitHub Release candidate contract and fixture check that validates official source, stable/immutable status, tag/manifest binding, approved HTTPS asset URLs, and exactly one manifest asset while denying network, download, writes, and activation.
- [ ] Add opt-in automatic stable-release checks, downloads, and installation without using unattended `git pull` or a moving branch.
- [ ] Verify downloaded engine assets with checksums and a release signature or attestation before staging or activation.
- [x] Keep engine binaries separate from user configuration, workspaces, models, provider data, generated artifacts, and evidence in the versioned storage and update contracts.
- [ ] Add compatibility preflight, atomic activation, post-update health checks, automatic rollback, retained-version cleanup, offline behavior, and a disabled-update mode.
  - [x] Add a cross-platform effect-free lifecycle simulator for healthy,
    failed-health, interrupted, rollback, retention, and disabled paths with 41
    hostile cases and every machine-effect flag denied.
  - [ ] Implement those lifecycle operations only after trusted cryptographic,
    native-path, packaging, privilege, and platform evidence permits real
    machine effects.
- [x] Implement Milestone 22A as a zero-new-dependency, loopback-only local web MVP over the Milestone 21 `general.chat` capability: sanitized system status, explicit Ollama endpoint validation, installed-model discovery, model selection, bounded chat, and verified unload after success, failure, and shutdown.
- [x] Expand Milestone 22A with repository-free `content.write` and `content.summarize` modes, typed chat/Markdown results, in-memory task reset, and the same bounded provider and unload policy.
- [x] Infer loopback versus private-LAN connection scope from the validated IP literal, remember separate chat/writing/summarization model choices, and replace response-by-response unload with a five-minute balanced idle policy plus advanced cleanup choices.
- [x] Make chat the primary local-web interaction, reduce the oversized hero, keep desktop navigation and provider/system setup visible while scrolling, and preserve responsive one-column behavior.
- [x] Add a security-first, memory-only first-run web wizard for provider connection, advanced timeout/residency settings, capability-specific readiness, and a working-chat handoff.
- [ ] Run the controlled writing-quality matrix for exact Qwen 3.5 9B, Gemma 3 12B, Mistral Small 3.2 24B, and Granite 4 7B-A1B-H artifacts before promoting a comparative writing-quality default over the validated adapter baseline.
  - [x] Run the initial exact-digest automated constraint matrix with synthetic
    inputs, provider token/timing metrics, no raw-output persistence, and
    verified per-case and final unloads. Blind human scoring and repeated
    quality samples remain open before comparative promotion.
- [x] Replace first-provider-result model defaults with capability-specific engine recommendations, non-downloading missing-model guidance, advanced per-capability overrides, reset-to-automatic, and visibly unverified handling for unknown installed models.
- [x] Bind local-web automatic recommendations to the exact tested Qwen
  provider digest and capability evidence; a matching model name with a
  different or missing digest remains an explicit unverified choice.
- [x] Expand the local web UI over the stable registries with exact-digest text
  selection, plan-only registered read-only software workflows, and the
  promoted Linux ComfyUI/SDXL image capability without duplicating provider
  or workflow admission logic.
- [ ] Keep Tauri as optional Milestone 22B native packaging after its published dependency, bridge, signing, package, and platform gates pass; the local web product must not wait on it.
- [x] Add unsigned PyInstaller one-folder development packages for Windows, Linux, and macOS using the shared browser UI, embedded resource-integrity verification, source/package parity, native smoke tests, least-privilege CI, checksums, dependency inventory, third-party notices, and CycloneDX SBOM evidence.
- [x] Harden portable development packaging with cross-platform wheel hashes, platform-allowlisted evidence, hostile resource/shutdown/archive tests, exact checksum coverage, full package inventory, and explicit unsigned build provenance.
- [ ] Promote packaging beyond development only after signing/notarization, installer/uninstall, provenance, platform lifecycle, and production release gates pass. Keep online updater activation and machine modification disabled until separately approved and validated.
- [x] Define the first product slice, first-run flow, Home/Chat/Software/Images/Models/System navigation, approval review, wireframes, and renderer-safe registry-backed view model without admitting a desktop runtime.
- [x] Define one product-wide progressive onboarding pattern with guided setup, existing-setup connection, not-now, advanced controls on both active paths, and engine-derived validated/customized/unverified/blocked states.
- [x] Define eight capability-specific advanced-setting schemas and an offline default-deny evaluator that rejects renderer authority, raw sensitive values, evidence forgery, and cross-domain admission without machine effects.
- [x] Add a versioned, read-only model catalog assembler that combines discovery, exact artifact identity, per-artifact license policy, hardware fit, and revision-bound evidence into one fail-closed beginner/advanced decision.
- [x] Add first-run intent navigation, capability availability, evidence states, and policy disclosures to the admitted local-web slice.
  - Chat, Writing, and Summarization become available only after provider validation; Software remains not admitted and Images remains provider-profile-required. Native renderer integration remains separately gated.
- [x] Render strict typed artifacts and ordered progress, warning, result, and
  error envelopes across admitted text, workflow-plan, and image operations.
- [x] Render local-web typed chat-message/Markdown artifacts with strict accepted/progress/warning/result/error ordering, visible unverified-model warnings, typed failure recovery, no automatic retry, and no file writes; broader workflow rendering remains open under the parent task.
- [ ] Connect setup, health, model choice, software workflows, validation, cleanup, and evidence views without duplicating business logic.
- [x] Connect local-web setup, provider health, model choice, cleanup status, evidence boundary, and disabled-update state; software workflow execution and broader validation evidence remain open under the parent task.
- [x] Add repository-free text flows only for evidence-gated Milestone 21 providers.
- [x] Add a repository-free browser-memory image flow only for the promoted
  Linux ComfyUI/SDXL profile, with loopback-only discovery, fixed checkpoint
  and workflow authority, bounded PNG validation, explicit retention
  disclosure, history cleanup, and user-triggered download.
- [ ] Add accessible cross-platform UI contract, failure, recovery, and packaging tests.
- [x] Add local-web keyboard/focus/ARIA/reduced-motion contracts, hostile catalog tests, and a dependency-free headless Chromium wizard/chat flow on Windows; native packaging and full cross-platform browser recovery coverage remain open under the parent task.
- [ ] Add bounded multi-step composition with explicit intermediate artifacts and approvals.

## Solution Architecture Review Backlog

- [x] Add a milestone solution completeness audit covering completed and active roadmap stages.
- [ ] Provide or approve suitable non-generated repositories for future real-repository validation.
- [ ] Confirm whether surface-specific install/configure profiles should be prioritized before more non-Continue evidence exists.
- [ ] Add future surface-specific profile generation after non-Continue validation.
- [x] Confirm the unified starter-toolkit UI follows general-purpose capability contracts as Milestone 22.
- [x] Require external wiki synchronization for mapped documentation and hosted CI.
- [x] Resolve the native macOS Milestone 18 workflow gap. Devstral Small 2 completed all required generated-fixture CLI cells; language rule packs remain evidence-gated for real repositories and editor surfaces.
- [x] Refresh `PROJECT.md`, `ARCHITECTURE.md`, README status text, and surface diagrams after the new contracts are implemented so documented maturity matches verified behavior.

## Milestone 23: Native Local Image Generation

- [x] Validate the pinned Linux ComfyUI/SDXL provider, typed PNG artifact, metadata exclusion, history cleanup, recovery, SSH tunnel, and visual result for its exact NVIDIA V100 scope.
- [x] Define hardware discovery and consent-driven local image-provider onboarding that does not require an external server.
- [ ] Validate a pinned Windows NVIDIA CUDA image-provider profile before shipping its local installer or runtime files.
- [ ] Validate a pinned Windows Intel GPU/XPU image-provider profile, including XPU acceleration, generation, metadata, recovery, cleanup, and typed-adapter evidence, before shipping its local installer or runtime files.
- [ ] Validate a pinned Windows AMD GPU image-provider profile before shipping its local installer or runtime files.
  - ComfyUI v0.28.0 AMD portable on an RX 7800 XT passed generation, typed artifact, visual, privacy, history, restart, active cancellation, invalid-workflow recovery, forced process recovery, repeated-run stability, retention cleanup, and uninstall checks. Update/rollback remains open because v0.28.0 is still the latest immutable AMD release, and consumer onboarding/installer behavior remains unadmitted.
- [ ] Validate a pinned Apple Silicon MPS image-provider profile on a physical Mac as the last native hardware gate before shipping its local installer or runtime files.
- [x] Keep custom nodes and external API nodes disabled unless each exact extension independently passes promotion.
- [ ] Add native installer and provider lifecycle files only after the exact profile passes; failed profiles leave documentation only.

## Milestone 24: Local Music And Audio Generation

- [x] Record exact ACE-Step 1.5 and accessible Stable Audio 3.0 candidate versions, model cards, download sizes, checksums, licenses, supported operations, and claimed hardware paths without adding executable integration assets; retain gated Small Music metadata as an explicit open evidence gap.
  - ACE-Step 1.5, Stable Audio Small SFX, and Stable Audio Medium are recorded from official immutable sources; gated Stable Audio Small Music did not expose exact anonymous revision/file metadata and remains open.
- [ ] Externally evaluate ACE-Step 1.5 on Linux CUDA for REST health, instrumental and vocal generation, typed WAV/FLAC artifact requirements, privacy, cancellation, recovery, cleanup, and uninstall behavior.
  - Commit `6d467e4b5081ccb0abf1ec1bf4fdf9051a2d34b0` passed a disposable deterministic instrumental REST/WAV structure and cleanup cell on a V100 32 GB profile. Vocal, signal/clipping, listening, cancellation, forced recovery, retention, and typed-adapter checks remain open.
- [ ] Externally evaluate Stable Audio 3.0 Small and Medium for sound effects, instrumental music, editing, duration, licensing, and consumer hardware fit.
- [ ] Validate Windows NVIDIA CUDA, Windows Intel XPU, Windows AMD ROCm, Apple Silicon MLX, and Linux CUDA independently; keep the physical Mac run last.
- [x] Add reference-audio, voice-cloning, identifiable-voice, lyrics, artist-style, attribution, and commercial-use consent policy before provider promotion.
- [ ] Define `audio.music.create`, typed audio artifacts, discovery, and a dry-run-first adapter only after an exact provider profile passes every external gate.
- [x] Ship no music scripts, adapters, harnesses, templates, workflows, configuration, or registry entries for a failed or documentation-only candidate.
- [ ] Expose music creation in the unified UI only after provider promotion, native evidence, cleanup, packaging, and exact-SHA hosted checks pass.

## Milestone 25: Local Video Generation

- [x] Record exact HunyuanVideo 1.5, Wan2.2 TI2V-5B, and LTX-2.3 candidate versions, model cards, licenses, sizes, supported operations, and claimed hardware without adding executable integration assets.
- [ ] Externally evaluate HunyuanVideo 1.5 and Wan2.2 separately on compatible Linux NVIDIA hardware for text-to-video, image-to-video, typed video artifacts, privacy, consent, cancellation, recovery, cleanup, and uninstall behavior.
- [ ] Evaluate LTX-2.3 only on hardware meeting its documented 32 GB VRAM, storage, CUDA, and license constraints.
- [x] Keep Windows Intel, Windows AMD, and Apple Silicon video profiles unavailable until an exact native provider path passes; test any Windows NVIDIA path independently from Linux.
- [x] Add reference-media, identity, face-animation, likeness, voice, deepfake, artist-style, disclosure, and commercial-use consent policy before promotion.
- [ ] Define `media.video.create`, typed MP4/WebM artifacts, discovery, and a dry-run-first adapter only after an exact provider profile passes every external gate.
- [x] Ship no video scripts, adapters, harnesses, templates, workflows, configuration, registry entries, runtime files, or installer automation for a failed or documentation-only candidate.
- [ ] Expose video generation in the unified UI only after provider promotion, native evidence, consent, cleanup, packaging, and exact-SHA hosted checks pass.

## Milestone 26: Hardware-Adaptive Model Quantization

- [x] Define versioned quantization-plan and artifact-manifest contracts with immutable source identity, license, hashes, pinned tools, recipe parameters, runtime compatibility, local storage, and cleanup state.
- [x] Extend sanitized hardware profiling with accelerator capabilities, usable memory, runtime and driver versions, instruction support, storage headroom, context target, concurrency, and workload lane.
- [x] Implement dry-run selection that prefers a trusted compatible pre-quantized artifact and explains when local conversion is unnecessary or unsafe.
- [x] Define explicit support matrices for GGUF/Ollama or llama.cpp, Apple Silicon MLX, and accelerator-specific AWQ, GPTQ, FP8, or INT4 paths without treating equal bit counts as interchangeable.
- [x] Add provenance, checksum, derivative-license, redistribution, calibration-data privacy, download-size, temporary-storage, compute-time, and cleanup disclosures before conversion.
- [x] Define comparative gates for load time, first-token latency, throughput, peak memory, disk use, context stability, accelerator use, general capability quality, tool calls, and engineering workflow reliability.
- [x] Validate one disposable Linux NVIDIA GGUF/Ollama path first; the exact Qwen 3.5 9B Q4_K_M versus Q8_0 evidence and cleanup record are complete.
- [x] Validate the exact Windows AMD/Ollama quantization comparison independently; the RX 7800 XT 16 GB profile passed and does not transfer to another platform or runtime.
- [ ] Validate Windows NVIDIA, Windows Intel, and Apple Silicon paths independently, keeping physical Mac testing last; Windows Intel remains parked until representative Intel GPU hardware is available.
- [ ] Add activation, previous-model rollback, cleanup, catalog admission, and UI integration only for exact model/recipe/runtime/hardware combinations that pass.
- [x] Ship no conversion scripts, harnesses, runtime configuration, model artifacts, or active catalog entries for failed or incomplete candidates.

## Security architecture remediation

- [x] Add SECURITY.md, CODEOWNERS, and a security-focused pull request checklist.
- [x] Pin GitHub Actions by immutable commit, disable persisted checkout credentials, and bound CI concurrency and duration.
- [x] Add pinned CodeQL Python analysis and remediate findings without suppressions.
- [x] Prevent quantization request metadata from being logged by requiring an exclusive local plan output file.
- [x] Block mutable third-party installation and macOS curl-to-shell bootstrap paths.
- [x] Enforce explicit provider endpoint trust scopes, redirect denial, bounded responses, private prompt channels, and exclusive no-follow artifact creation.
- [x] Require pull requests and successful checks on `main`, enable dependency security updates, and verify private vulnerability reporting in GitHub settings.
- [x] Align committed CI, staged-tree receipts, wiki retry, portable-package
  checks, merge methods, Actions SHA enforcement, and live GitHub settings
  under one verifiable repository policy.
- [ ] Add signed release tags and artifact provenance before admitting the automatic updater or native installers.
