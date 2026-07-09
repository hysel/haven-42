# Roadmap

## Status

The repository is in early implementation stage. Milestone 1, Milestone 2, Milestone 3, release hardening for version 0.1.3, CI validation for version 0.1.4, runtime validation tooling for version 0.1.5, Milestone 4 runtime validation and CI, Milestone 5 prompt quality hardening, Milestone 6 applied tooling and adaptive models, Milestone 7 cross-platform contributor experience, Milestone 8 real repository validation, Milestone 9 distribution and install experience, Milestone 10 ARM and Apple Silicon model support, Milestone 11 editor surface compatibility, and Milestone 12 model tool-use validation evidence are complete. Milestone 13 broader multi-repository validation is in progress. Milestone 14 broadens the project from a Continue-specific enterprise pack into a local-first engineering agent pack that can serve individual developers, small teams, and enterprise users. Milestone 15 tracks multi-language engineering support so the pack does not remain .NET-only over time. Milestone 16 starts the sample repository factory, with later roadmap tracks for language rule packs, installer profiles, evidence catalogs, release packaging, hardware-aware model/config automation, script consolidation, a stable workflow registry, and a future unified starter-toolkit web UI.

## Stage Status

| Stage | Status | Summary |
| --- | --- | --- |
| Milestone 1: Minimum Usable Pack | Complete | Core configuration, rules, prompts, agents, templates, setup docs, and Continue/Ollama validation are complete. |
| Milestone 2: Enterprise Review Depth | Complete | Architecture, performance, documentation, reviewer, product, SonarQube, examples, validation checklists, and decision records are complete. |
| Milestone 3: Tooling And Integration | Complete | Troubleshooting guidance, MCP options research, SonarQube integration research, MCP setup docs, and compatibility notes are complete. |
| Release Hardening: 0.1.3 | Complete | Contributor guidance, release tagging guidance, validation automation, sanitized fixtures, and version updates are complete. |
| Milestone 4: Runtime Validation And CI | Complete | GitHub Actions validation, runtime validation tracking docs, context generation, sanitized fixture-based validation, and legacy migration validation notes are complete. |
| Milestone 5: Prompt Quality Hardening | Complete | Prompt-specific fixtures, pass/fail checks, local-model reliability guardrails, banned-output guidance, and stronger static validation are complete. |
| Milestone 6: Applied Tooling And Adaptive Models | Complete | Tool-use modes, approved write guidance, scoped edit guidance, model selection strategy, hardware profiling, model tiers, and local override safety guidance are complete. |
| Milestone 7: Cross-Platform Contributor Experience | Complete | Linux and macOS validation/test wrappers are available, and Linux wrapper execution is covered in CI. |
| Milestone 8: Real Repository Validation | Complete | The pack repository and one private application-style repository have been validated with the runtime runner; practical MCP workflow examples are documented. |
| Milestone 9: Distribution And Install Experience | Complete | Install/update workflows are implemented with dry-run, backup, local-config exclusion, duplicate-rule-safe global config generation, install validation, and Windows/Linux/macOS commands. |
| Milestone 10: ARM And Apple Silicon Model Support | Complete | CPU architecture reporting, ARM model guidance, Linux compatibility assumptions, container caveats, cloud smoke-test guidance, and MLX guidance are documented. |
| Milestone 11: Editor Surface Compatibility | Complete | VS Code-compatible and VSCodium read-only Agent validation are recorded, duplicate-rule checks are clean, and CLI fallback guidance is documented. |
| Milestone 12: Model Tool-Use Validation Evidence | Complete | Starter model defaults, automatic local model config generation, model lanes, local Ollama Agent model preflight tooling, read-only and read-content tool validation guidance, approved-write smoke-test guidance, duplicate approval mitigation, external write verification, platform-aware command rules, sanitized evidence templates, post-validation install flow, and optional online discovery guardrails are in place. |
| Milestone 13: Broader Multi-Repository Validation | In Progress | Repository category coverage, sanitized evidence capture, validation workflow guidance, and first legacy .NET category evidence are defined; additional real repository categories remain pending. |
| Milestone 14: Agent Surface Portability And Broader Audience | In Progress | The project is repositioned as a local-first engineering agent pack, Continue remains the first supported surface, and an evidence-gated compatibility matrix now tracks other open-source agent surfaces. |
| Milestone 15: Multi-Language Engineering Support | Planned | Keep .NET as the first mature ecosystem while adding validated language guidance for Python, TypeScript, Java, Go, Rust, SQL, and infrastructure repositories. |
| Milestone 16: Sample Repository Factory | In Progress | Generate disposable local sample repositories for language, agent-surface, and runtime validation without needing private repositories; runtime context now includes non-.NET metadata from generated samples. |
| Milestone 17: Agent Surface Compatibility Validation | In Progress | Cline has read-only and disposable write-smoke validation evidence for `qwen3-coder:30b` at 16k context; real-project approved-write plus Aider, Roo Code, Kilo Code, and OpenCode live validation remain pending. |
| Milestone 18: Language Rule Packs | In Progress | Optional Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code rule packs are added as evidence-gated supplemental guidance with static generated-sample validation recorded; generated editor/model workflow evidence is recorded, prompt and runner filename-fidelity guardrails are in place, and runtime runners now write filename-fidelity fallback artifacts for deterministic filename failures. Remaining empty-output failures and any non-filename guardrail repeats require separate remediation before promotion. |
| Milestone 19: Installer Profiles, Evidence Catalog, And Release Packaging | In Progress | Installer profiles, the sanitized evidence catalog, and release packaging guidance are implemented for current scope; future surface-specific profiles remain after non-Continue validation. |
| Milestone 20: Hardware-Aware Model And Config Automation | In Progress | Offline hardware-aware recommendation output, local-only Continue config generation, and centralized shared asset config generation are implemented for current scope; future surface reuse, script consolidation, a shared command dispatcher, and a unified starter-toolkit web UI remain planned; the workflow registry foundation is implemented. |

## Milestone 1: Minimum Usable Pack

Goal: Make the pack loadable, understandable, and useful for common engineering workflows, from individual repositories to enterprise codebases.

Scope:

- Implement `.continue/config.yaml` for a basic Continue setup. Done.
- Define local-first model assumptions for Ollama. Done.
- Implement core rules. Done:
  - `general.md`
  - `git.md`
  - `dotnet.md`
  - `aspnetcore.md`
  - `clean-architecture.md`
  - `api.md`
  - `testing.md`
  - `logging.md`
  - `security.md`
  - `performance.md`
- Implement core prompts. Done:
  - `repository-discovery.md`
  - `implementation-plan.md`
  - `code-review.md`
  - `bug-investigation.md`
  - `security-review.md`
- Define primary agents. Done:
  - `senior-engineer.md`
  - `architect.md`
  - `security-engineer.md`
- Implement core templates. Done:
  - `Architecture.md`
  - `SecurityReview.md`
  - `PerformanceReview.md`
  - `AI.md`
- Update `README.md` with setup and usage instructions. Done.
- Statically validate local config file references. Done.
- Validate the pack in Continue CLI. Done.
- Validate model-backed prompt execution with Ollama. Done.
- Add example outputs for major workflows. Done.

Exit criteria:

- Continue can load the pack.
- A user can run repository discovery, implementation planning, code review, bug investigation, security review, architecture review, performance review, and documentation workflows.
- A user can run AI framework self-review, refactoring planning, product-management review, and release-readiness workflows.
- Rules and prompts are consistent with this repository's style guide.
- README instructions match tested behavior.

## Milestone 2: Enterprise Review Depth

Goal: Improve the quality and coverage of review workflows.

Scope:

- Add architecture review and performance review prompts. Done.
- Complete reviewer, performance, documentation, and product-manager agents. Done.
- Expand SonarQube guidance. Done.
- Add example review outputs. Done.
- Add validation checklists for prompt and rule changes. Done.
- Add decision records for major design choices. Done.

Exit criteria:

- Review outputs are consistent across architecture, security, code, and performance workflows.
- SonarQube findings can be incorporated manually in a documented way.
- The pack has examples that demonstrate expected usage.
- Prompt and rule changes have documented validation checklists.

## Milestone 3: Tooling And Integration

Goal: Connect the pack to richer repository and quality-system context.

Scope:

- Evaluate MCP servers for repository, filesystem, GitHub, issue tracking, and quality data. Done.
- Define a supported MCP integration path. Done.
- Explore SonarQube integration options. Done.
- Add troubleshooting documentation. Done.
- Add compatibility notes for Continue versions and local model choices. Done.

Exit criteria:

- Integration paths are documented and reproducible.
- MCP support has clear setup instructions.
- SonarQube usage is no longer only conceptual.

## Release Hardening: 0.1.3

Goal: Prepare the repository for repeatable release validation and external contribution.

Scope:

- Add `CONTRIBUTING.md`. Done.
- Add release tagging guidance. Done.
- Add sample review fixtures. Done.
- Add validation automation. Done.
- Update pack version to `0.1.3`. Done.
- Remove completed license work from the backlog. Done.

Exit criteria:

- Release process is documented.
- A validation script can check core repository invariants.
- Sample fixtures are sanitized and reusable.
- Changelog records version `0.1.3`.
- The pack configuration version is `0.1.3`.

## Backlog

## Milestone 5: Prompt Quality Hardening

Goal: Improve prompt reliability by converting runtime validation failures into focused fixtures, pass/fail checks, and stronger prompt-specific guardrails.

Scope:

- Add prompt-specific quality fixtures for implementation planning, legacy dependency migration, documentation review, and release readiness. Done.
- Define pass/fail expectations for sensitive workflows. Done.
- Add validation guidance for local-model reliability issues. Done.
- Extend static validation for prompt frontmatter and required prompt metadata. Done.
- Add checks or review guidance for banned output patterns in high-risk workflows. Done.

Exit criteria:

- Sensitive prompts have explicit pass/fail expectations.
- Legacy dependency migration has a human-reviewed fallback path and a model reliability warning.
- Documentation and release-readiness prompts discourage shallow summaries and unsupported go recommendations.
- Validation catches missing prompt metadata and obvious workflow drift.

## Milestone 4: Runtime Validation And CI

Goal: Validate the pack continuously and exercise it against realistic repositories and review inputs.

Scope:

- Add CI automation for `scripts/validate-pack.ps1`. Done.
- Validate the pack against additional realistic fixture inputs. Done.
- Add more sample fixtures for security, performance, and release-readiness workflows. Done.
- Add project-specific MCP examples after real-world validation.
- Record runtime validation results in repository documentation. Done.
- Add runtime context generation for local-model validation. Done.
- Add legacy .NET dependency migration prompt and template. Done.

Exit criteria:

- CI runs validation on pushes and pull requests.
- Runtime validation gaps are documented.
- Additional fixtures cover the highest-value review workflows.
- Local-model validation limitations are documented where workflows fail guardrails.
- Optional MCP examples remain deferred until validated usage is available.

## Milestone 6: Applied Tooling And Adaptive Models

Goal: Make the pack more useful in real repositories by supporting controlled tool-enabled changes and local hardware-aware model selection.

Scope:

- Define safe tool-use modes for reviewed repositories, including read-only discovery, plan-only review, and approved write mode. Done.
- Document how Continue users can enable tool-backed project changes without weakening approval, validation, rollback, or git safety rules. Done.
- Add prompts or guidance for converting an approved plan into scoped edits in the target project. Done.
- Define a model-selection strategy based on local hardware signals such as available RAM, GPU VRAM, model size, context needs, and workflow risk. Done.
- Add a hardware-profile helper or documented command sequence for collecting local model-selection inputs. Done.
- Define recommended Ollama model tiers for low, medium, and high resource machines. Done.
- Keep machine-specific endpoints, model experiments, and hardware details out of committed shared config. Done.

Exit criteria:

- Users understand when the pack may read, plan, or modify a reviewed repository.
- Tool-enabled changes require explicit approval and include validation and rollback expectations.
- Local model recommendations are tied to hardware capacity and workflow risk.
- The default committed config remains portable and safe for local Ollama users.
- Documentation includes examples for selecting models without committing private machine details.

## Backlog

- Validate the pack against additional real repositories when suitable repositories are available.

## Milestone 7: Cross-Platform Contributor Experience

Goal: Make validation and test commands easy for contributors on Windows, Linux, and macOS without requiring Linux or macOS users to run PowerShell.

Scope:

- Add Linux shell wrappers for validation and tests. Done.
- Add macOS shell wrappers for validation and tests. Done.
- Add shared Bash implementations for Linux and macOS validation, tests, installation, runtime context generation, and runtime validation. Done.
- Keep PowerShell validation and tests for Windows contributors. Done.
- Add CI coverage for Linux wrapper execution. Done.
- Document cross-platform validation commands in the README. Done.

Exit criteria:

- Windows contributors can run PowerShell validation and tests directly.
- Linux contributors can run Bash wrapper commands that call shared Bash implementations.
- macOS contributors can run Bash wrapper commands that call shared Bash implementations.
- Linux and macOS user-facing scripts do not require `pwsh`.
- CI verifies wrapper behavior on Ubuntu and macOS.

## Milestone 8: Real Repository Validation

Goal: Validate the pack against real repository contexts and convert runtime findings into prompt, fixture, documentation, and integration improvements.

Scope:

- Run runtime validation against the pack repository itself. Done.
- Record sanitized runtime validation results. Done.
- Identify prompt-quality gaps that only appear during runtime use. Done.
- Add prompt guidance for configuration-pack and documentation-heavy repositories. Done.
- Add a prompt-quality fixture for non-application repositories. Done.
- Validate against an application repository when a suitable target is available. Done.
- Add project-specific MCP examples only after validated real-world usage. Done.

Exit criteria:

- At least one public repository validation result is recorded.
- Runtime outputs are reviewed and sanitized before documentation updates.
- Follow-up work is tracked for generic or unsupported prompt findings.
- MCP examples are based on validated usage rather than speculation.

## Milestone 9: Distribution And Install Experience

Goal: Make the pack easier and safer to install, update, validate, and reuse across target repositories.

Scope:

- Add an install or update script for copying `.continue` assets into a target repository. Done for PowerShell.
- Back up an existing target `.continue` folder before replacement or merge. Done.
- Add a dry-run mode that shows what would change before copying files. Done.
- Add install validation that confirms copied config, prompts, rules, agents, and templates resolve correctly. Done.
- Document Windows, Linux, and macOS install/update commands. Done.
- Add an explicit global Continue config update mode for editor setups that ignore project-local config files. Done.
- Omit `rules:` from generated global config by default to avoid duplicate rule warnings when project-local `.continue/rules` are also loaded. Done.
- Design and implement centralized shared asset installation for users with multiple target repositories. Done for Continue global config generation with `-SharedAssets` / `--shared-assets`.
- Keep local overrides, private endpoints, tokens, and machine-specific config out of install outputs. Done for local config override exclusion.

Exit criteria:

- A user can install or update the pack in a target repository with one documented command. Done.
- Existing target `.continue` content is not overwritten without backup or explicit approval. Done.
- The installed pack can be validated after copy. Done.
- Install documentation stays beginner-friendly and cross-platform. Done.

## Milestone 10: ARM And Apple Silicon Model Support

Goal: Improve guidance for ARM-based machines whose local model behavior differs from traditional x64 workstations with dedicated GPU VRAM.

Scope:

- Detect and report CPU architecture in hardware profile outputs when available. Done.
- Add architecture fields to Windows, Linux, and macOS hardware profile text and JSON output. Done.
- Document Apple Silicon, Windows ARM, and Linux ARM as separate local-model scenarios.
- Document Linux distro assumptions and optional GPU detection dependencies.
- Document enterprise and cloud Linux assumptions for AWS, Azure, GCP, and RHEL-family style environments.
- Document container, LXC, and LXD hardware visibility and GPU passthrough caveats.
- Document the difference between Ollama/GGUF models and MLX models on Apple Silicon.
- Keep Ollama as the default beginner setup path.
- Add advanced Mac guidance for MLX model serving through an OpenAI-compatible local endpoint.
- Evaluate whether the macOS hardware profile script should detect `mlx-lm` or other MLX tooling.
- Evaluate whether Linux ARM profiles should identify NVIDIA Jetson or other ARM GPU acceleration paths.
- Evaluate fallback behavior on minimal Linux distributions where `lspci`, `nvidia-smi`, or `rocm-smi` are unavailable.
- Evaluate whether enterprise/cloud Linux images need additional validation fixtures or smoke-test guidance. Done.
- Evaluate whether containerized model servers need separate profile output warnings or detection. Done.
- Add conservative guidance for Windows ARM machines where local LLM acceleration may vary by hardware and tooling.
- Review whether ARM architecture should affect recommendation tiering before changing `config/model-recommendations.tsv`.
- Decide whether MLX recommendations belong in `config/model-recommendations.tsv` or a provider-specific catalog.
- Decide whether ARM-specific recommendations belong in the shared TSV catalog or a provider-specific catalog.
- Document how unified memory and shared memory change model-size recommendations compared with dedicated GPU VRAM.
- Keep ARM/MLX local endpoints, model experiments, private model names, and machine-specific paths out of committed shared config. Done.

Exit criteria:

- ARM users understand the differences between Apple Silicon, Windows ARM, and Linux ARM local-model options.
- Hardware profile scripts expose architecture consistently enough for future recommendation logic.
- Mac users understand when to use the default Ollama path versus an advanced MLX path.
- MLX guidance explains Continue compatibility through a local API server rather than assuming Ollama model discovery.
- Recommendation logic does not confuse Ollama-installed models with MLX-hosted models or other provider-specific ARM models.
- ARM and Apple Silicon memory guidance is conservative and clearly documented.

## Milestone 11: Editor Surface Compatibility

Goal: Make setup and troubleshooting clearer for users running Continue in VS Code, VSCodium, or the Continue CLI.

Scope:

- Document known VS Code and VSCodium differences for Continue extension availability, versioning, and command behavior. Done.
- Add sanitized terminal preflight evidence for locally installed VS Code-compatible and VSCodium Continue extensions. Done.
- Validate project-local `.continue/config.yaml` loading in VS Code-compatible builds when available. Done.
- Validate project-local `.continue/config.yaml` loading in VSCodium when available. Done for current scope.
- Validate Agent mode and tool execution in VS Code-compatible builds. Done for read-only tool use.
- Validate Agent mode and tool execution in VSCodium. Done for read-only tool use after controlled retest.
- Document how global Continue config can conflict with project-local rules. Done.
- Keep `npx @continuedev/cli --config .continue/config.yaml` as a fallback validation path. Done.
- Confirm duplicate-rule status in the current VS Code-compatible and VSCodium setup. Done.
- Add troubleshooting notes for duplicate rules, missing models, missing prompts, and raw JSON tool-call output. Done.

Exit criteria:

- Users can tell whether Continue is using the intended project-local config.
- Duplicate-rule troubleshooting is documented for both global and project-local config scenarios.
- Editor-specific behavior is documented without making the default config editor-specific.
- CLI fallback instructions remain available for confusing editor behavior.

## Milestone 12: Model Tool-Use Validation Evidence

Goal: Make model tool-use recommendations evidence-based instead of relying only on model names, hardware tier, or installed-model detection.

Scope:

- Keep committed model examples lightweight and treat larger models as validated candidates instead of setup requirements. Done.
- Add install-script support for local-only model config generation from hardware profile recommendations. Done.
- Define a repeatable read-only tool-use validation checklist. Done.
- Require read-content validation before using approved write mode for real code or configuration changes. Done.
- Define a repeatable approved-write smoke test for edit/apply tool validation. Done.
- Require post-edit content or diff verification before accepting claimed file changes. Done.
- Document duplicate approval mitigation for existing-file validation by excluding `create_new_file` and requiring one edit path. Done.
- Add installer-supported model lanes so only validated write models receive edit/apply roles. Done.
- Require current-folder path resolution before approved edits so models do not create wrong-folder files. Done.
- Require workspace discovery before asking users for file paths when no file is open. Done.
- Require Apply target alignment so read, apply, and reported changed files match. Done.
- Add platform-aware command guidance so Windows uses PowerShell and Linux/macOS use shell commands. Done.
- Record model, provider, editor surface, Continue version, operating system, and MCP state for validation runs. Done via sanitized evidence template.
- Distinguish candidate model recommendations from tool-validated model status. Done.
- Evaluate optional online model discovery for newer Ollama candidates while keeping the default workflow offline, local-first, and non-installing. Done.
- Add a post-validation model installer that can download the selected validated model automatically and update local-only Continue config without committing private endpoints. Done.
- Add a sanitized evidence template for model tool-use validation results. Done.
- Decide whether validated model evidence should live in docs, examples, or a separate catalog. Done for current scope: keep the reusable template in examples and defer larger evidence catalogs until records accumulate.
- Keep private endpoints, local paths, private repository names, and raw transcripts out of committed evidence.

Exit criteria:

- Users know that hardware/profile scripts recommend candidates, not proven tool-safe models.
- Online model discovery, if added, suggests candidates only and does not replace local validation or auto-install models. Done.
- Automatic model download, if added, runs only after a model is selected or validated and writes machine-specific settings only to local override config.
- A model is considered tool-validated only after a read-only tool test passes.
- Approved write mode for real code changes remains blocked until file listing, file-content reading, a scoped write smoke test, and post-edit diff verification pass in the intended editor/provider setup.
- Sanitized validation evidence can be recorded without exposing private machine or repository details.

## Milestone 13: Broader Multi-Repository Validation

Goal: Validate the pack across multiple repository categories and convert findings into reusable prompt, documentation, test, and setup improvements.

Scope:

- Define repository categories for validation coverage. Done.
- Add a sanitized multi-repository validation evidence template. Done.
- Document the minimum validation flow for each repository category. Done.
- Require clean-tree, config-source, model, editor, MCP, and tool-use status in evidence. Done.
- Add validation and test coverage so the guide and template stay linked. Done.
- Record first sanitized Milestone 13 validation evidence for a legacy .NET repository category. Done.
- Validate the pack against additional real repositories when suitable targets are available.
- Convert repeated validation failures into prompt, rule, documentation, or script updates. First legacy validation findings for filename fidelity and lifecycle/support claims have been converted into prompt and test guardrails.
- Add deterministic output verification or a stricter template fallback when local models continue to ignore filename-fidelity and lifecycle/support guardrails. Deterministic runtime output verification has been added; stricter template fallback remains available if verification shows repeated failures.
- Add generated local sample repositories for additional validation categories when real repositories are not available.
- Keep private repository names, local paths, endpoints, raw transcripts, customer names, and source code out of committed evidence.

Exit criteria:

- At least three distinct repository categories have sanitized validation evidence.
- Evidence records show setup, prompts tested, tool-use status, failure signals, and pack follow-up decisions.
- Repeated failures are tracked and converted into pack improvements.
- Additional repository-category coverage can use generated local samples when real repositories are not available.
- README, docs, roadmap, TODO, changelog, and wiki remain aligned with the validation workflow.

## Milestone 14: Agent Surface Portability And Broader Audience

Goal: Make the project useful beyond one editor extension or one enterprise-only audience while preserving the tested Continue path.

Scope:

- Reposition the project name and product language around a local-first engineering agent pack rather than a Continue-only enterprise pack.
- Keep Continue as the first supported and tested agent surface until another surface has equivalent validation evidence.
- Add an agent-surface compatibility matrix for Continue, Cline, Aider, Kilo Code, OpenCode, OpenHands, and other credible open-source options. Done.
- Define what each surface must prove before it can be called read-only validated, plan validated, or approved-write ready. Done.
- Keep beginner-friendly setup paths for simple local hardware while documenting enterprise-safe workflows for larger teams.
- Separate reusable prompts, rules, templates, validation scripts, and evidence formats from Continue-specific configuration details where practical.
- Decide whether future install scripts should generate surface-specific config bundles instead of only `.continue` assets.
- Update README, docs, roadmap, TODO, changelog, and wiki when the project identity or supported surfaces change.

Exit criteria:

- New users can understand that the project starts with Continue but is not limited to Continue forever.
- Non-enterprise users can follow the quick start without feeling the pack assumes a corporate environment.
- Enterprise users still see security, governance, validation, and auditability guidance.
- At least one non-Continue open-source agent surface is evaluated with a documented read-only validation result.
- Surface-specific limitations are documented before any surface is recommended for approved writes.

## Milestone 15: Multi-Language Engineering Support

Goal: Expand the pack beyond .NET while preserving the current .NET maturity and avoiding language-specific advice when the repository evidence does not support it.

Scope:

- Keep .NET and ASP.NET Core as the first mature and most validated ecosystem.
- Add language-specific rule packs or guidance for Python, JavaScript/TypeScript, Java/Spring, Go, Rust, SQL/database projects, and Infrastructure as Code.
- Add repository detection guidance so prompts identify project type before applying language-specific recommendations.
- Keep shared engineering standards reusable across languages: Git, testing, security, logging, performance, architecture, documentation, and rollback planning.
- Prevent .NET-specific recommendations from being applied to non-.NET repositories.
- Add generated local sample repositories for planned language ecosystems when real repositories are not available.
- Validate repository discovery, implementation planning, code review, and runtime output verification against at least Python and TypeScript samples before promoting language support. Generated-sample workflow validation now runs against Python and TypeScript, with filename-drift guardrail failures recorded for documentation and release-style workflows.
- Keep README, docs, roadmap, TODO, changelog, and wiki clear that language support is staged and evidence-based.

Exit criteria:

- Repository discovery can identify common project types without inventing unsupported framework details.
- Prompts select language-appropriate guidance or explicitly stay language-neutral when evidence is incomplete.
- At least Python and JavaScript/TypeScript sample repositories have sanitized validation evidence.
- README explains that .NET is currently the most mature path, not the only intended path.
- Language-specific guidance is not treated as approved until validation evidence exists.
## Milestone 16: Sample Repository Factory

Goal: Generate disposable local repositories that unblock validation when real repositories are unavailable.

Scope:

- Add Windows, Linux, and macOS sample repository factory scripts.
- Generate deterministic samples for Python API, TypeScript frontend, Node service, Java/Spring API, Go service, Rust CLI, Infrastructure as Code, and SQL migrations.
- Keep samples dependency-free and offline by default.
- Include metadata in each generated sample explaining that it is a validation fixture, not a production starter template.
- Document how to use generated samples for repository discovery, planning, code review, runtime output verification, and agent-surface testing.
- Keep generated sample output under `runtime-validation-output` by default so it is not committed accidentally.

Exit criteria:

- A contributor can generate all sample repositories with one documented command.
- Tests verify the factory creates expected language/project markers and runtime context captures non-.NET metadata.
- Generated samples are suitable for read-only and approved-write validation in disposable workspaces.

## Milestone 17: Agent Surface Compatibility Validation

Goal: Convert candidate agent surfaces from documentation into evidence-backed compatibility results.

Scope:

- Add a Cline read-only validation guide and sanitized evidence template. Done.
- Validate at least one generated sample repository with Cline in read-only mode. Done for generated Python sample with `qwen3-coder:30b` at 16k context.
- Validate at least one generated sample repository with Aider in plan or patch mode.
- Record surface, model, OS, tool permissions, failure signals, and changed-file verification.
- Keep Continue as the supported first path until another surface has equivalent validation evidence.
- Validate Cline approved-write smoke behavior against a disposable generated sample. Done for a README-only smoke test with `qwen3-coder:30b` at 16k context; realistic scoped edit validation remains pending.
- Add a Cline CLI automation harness for future read-only and disposable write-smoke model screening. Done for script and documentation scaffolding; model-specific Cline CLI evidence remains pending.
- Add a Continue CLI automation harness for focused read-only and disposable write-smoke model screening. Done for script and documentation scaffolding; model-specific Continue CLI evidence remains separate from editor Apply evidence.
- Add a shared agent CLI automation harness plus thin wrappers for Aider, Roo Code, Kilo Code, and OpenCode future read-only and disposable write-smoke model screening. Done for script, documentation, and evidence-template scaffolding; model-specific live evidence remains pending.

Exit criteria:

- At least one non-Continue surface has sanitized read-only validation evidence.
- Approved-write recommendations remain blocked until scoped-write and external verification pass.

## Milestone 18: Language Rule Packs

Goal: Add optional language-specific rules without making the default pack noisy or wrong for other ecosystems.

Scope:

- Add optional rule files for Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code. These optional rule packs are added for current scope and remain out of the default config.
- Define when each rule pack should apply based on repository evidence. Done for current optional language packs.
- Add prompt guidance that keeps recommendations language-neutral when evidence is incomplete.
- Validate each rule pack against generated samples before promoting it. Static generated-sample validation is recorded for Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code in `examples/language-rule-pack-validation.md`; model-backed workflow validation is recorded for generated Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure samples in `examples/multi-language-workflow-validation.md`. Prompt-level and runner-level filename-fidelity guardrails are now in place, but stricter fallback work remains because deterministic verification still catches model filename drift.

Exit criteria:

- Language-specific advice is evidence-gated.
- .NET guidance no longer leaks into non-.NET repositories during validation.

## Milestone 19: Installer Profiles, Evidence Catalog, And Release Packaging

Goal: Make adoption easier as the pack grows across surfaces, languages, and validation levels.

Scope:

- Add installer profiles for Continue, read-only review, approved-write workflows, and future validated agent surfaces. Default, read-only, and approved-write Continue profiles are implemented for current scope.
- Add language-focused install/profile options after language packs are validated.
- Create a sanitized evidence catalog for model, OS, editor, agent surface, language, and write-readiness results. Done for current scope in `config/evidence-catalog.tsv`.
- Improve release packaging with GitHub release notes, downloadable archives, checksums, and install command examples. Done for current scope with cross-platform packaging scripts and checksum guidance.

Exit criteria:

- Users can choose the right profile without manually assembling config files.
- Validation evidence is structured enough to compare models, surfaces, and languages over time.
- Release artifacts are easy to install and verify.
## Milestone 20: Hardware-Aware Model And Config Automation

Goal: Turn hardware/profile evidence into practical model and configuration recommendations that a local user can apply without hand-tuning every setting.

Scope:

- Add logic that evaluates detected GPU, VRAM, RAM, CPU, architecture, operating system, and model-host platform to decide which local models are reasonable candidates for the user's machine. Done for offline recommendation output.
- Rank candidate models by workflow fit, resource fit, tool-use validation status, and conservative defaults so the user receives a clear recommended model plus alternatives. Done for offline recommendation output.
- Generate best-fit local configuration for Continue first, including model lanes, roles, context length, max tokens, keep-alive settings, and local-only endpoint handling. Done for local-only Continue config output.
- Keep the configuration engine surface-neutral enough to support future plugins or agent surfaces after they have compatibility evidence.
- Ensure cloud tags, provider-specific tags, MLX tags, oversized models, and unsupported local pulls are filtered or explained before any model download is attempted.
- Keep all generated machine-specific settings in local-only config files and out of committed shared configuration.
- Add validation coverage that proves hardware-aware selection does not expose private paths, hostnames, usernames, endpoints, or raw hardware reports.
- Reduce the number of scripts by consolidating repeated command-line workflows behind shared engines, registries, or dispatchers before adding more surface-specific scripts.
- Keep thin wrapper scripts only where they improve beginner usability or platform ergonomics; avoid duplicating business logic across wrappers.
- Define a machine-readable workflow registry that describes available tasks, inputs, outputs, safety level, platform support, and script entry points. Done.
- Define a stable script/API boundary so future tools can call hardware profiling, model discovery, model testing, configuration generation, installation, and validation without knowing each script family. Workflow registry foundation is done; shared dispatcher remains pending.
- Design a unified starter-toolkit web UI for people who want to use local AI for coding, with guided flows for setup, hardware profiling, model choice, config generation, agent-surface testing, and validation.
- Keep the web UI evidence-first: show what was tested, what passed, what failed, and what is only a recommendation before applying changes.
- Generate a local evidence dashboard from validation JSON so users can compare models, agent surfaces, operating systems, write readiness, and risks before installing anything.
- Add a beginner setup mode that guides users through the common local-AI coding path with minimal questions and exact next commands.
- Add a health check workflow that verifies Ollama reachability, installed models, generated config, duplicate rules, repository detection, and read/write validation status.
- Add a safe cleanup workflow with dry-run support for failed or unused local models, stale runtime outputs, old generated samples, and obsolete backup folders.
- Add a release readiness gate that runs validation, tests, docs/wiki freshness checks, whitespace checks, and optionally remote workflow status before release or push.
- Add a model scorecard that tracks tested models by tool support, speed, output quality, write behavior, context size, hardware tier, and recommended use.
- Generate surface-specific plugin profiles only after each plugin has compatibility evidence, using the same recommendation and validation data model.
- Add sample scenario packs for common local-AI coding tasks such as legacy migration, config refactoring, bug fixing, security review, test generation, and documentation cleanup.

Exit criteria:

- A user can run one documented flow that profiles hardware, discovers or reads candidate models, tests eligible models, and receives a recommended model/config result.
- Continue local config generation uses the recommendation result without requiring manual YAML editing for common setups.
- Future agent/plugin support can reuse the same model/config recommendation data without being hard-coded to Continue-only assumptions.
- The final-stage UI is treated as an optional wrapper over tested shared engines, not a replacement for script-level validation.
- The UI can call a small number of stable script entry points, a workflow registry, or a shared command dispatcher rather than many plugin-specific scripts.
- A beginner can use the UI to complete the common local-AI coding setup path without manually choosing scripts or editing YAML.
- Evidence dashboard, health check, cleanup, release gate, and model scorecard workflows all read from sanitized local artifacts and avoid committing private machine details.
