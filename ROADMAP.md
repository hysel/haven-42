# Roadmap

## Status

The repository is in early implementation stage. Milestone 1, Milestone 2, Milestone 3, release hardening for version 0.1.3, CI validation for version 0.1.4, runtime validation tooling for version 0.1.5, Milestone 4 runtime validation and CI, Milestone 5 prompt quality hardening, Milestone 6 applied tooling and adaptive models, Milestone 7 cross-platform contributor experience, Milestone 8 real repository validation, Milestone 9 distribution and install experience, and Milestone 10 ARM and Apple Silicon model support are complete. Broader multi-repository validation remains in the backlog.

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
| Milestone 9: Distribution And Install Experience | Complete | Install/update workflows are implemented with dry-run, backup, local-config exclusion, install validation, and Windows/Linux/macOS commands. |
| Milestone 10: ARM And Apple Silicon Model Support | Complete | CPU architecture reporting, ARM model guidance, Linux compatibility assumptions, container caveats, cloud smoke-test guidance, and MLX guidance are documented. |
| Milestone 11: Editor Surface Compatibility | In Progress | VS Code and VSCodium setup guidance is documented; editor-specific config loading and Agent mode validation remain. |
| Milestone 12: Model Tool-Use Validation Evidence | In Progress | Starter model defaults, automatic local model config generation, read-only tool validation guidance, and sanitized evidence templates are in place; online discovery and broader evidence catalog decisions remain. |

## Milestone 1: Minimum Usable Pack

Goal: Make the pack loadable, understandable, and useful for common enterprise engineering workflows.

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

- Add project-specific MCP examples after real-world validation.
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
- Validate project-local `.continue/config.yaml` loading in both editor surfaces when available.
- Validate Agent mode and tool execution separately in VS Code and VSCodium.
- Document how global Continue config can conflict with project-local rules. Done.
- Keep `npx @continuedev/cli --config .continue/config.yaml` as a fallback validation path. Done.
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
- Record model, provider, editor surface, Continue version, operating system, and MCP state for validation runs. Done via sanitized evidence template.
- Distinguish candidate model recommendations from tool-validated model status. Done.
- Evaluate optional online model discovery for newer Ollama candidates while keeping the default workflow offline, local-first, and non-installing.
- Add a sanitized evidence template for model tool-use validation results. Done.
- Decide whether validated model evidence should live in docs, examples, or a separate catalog. Done for current scope: keep the reusable template in examples and defer larger evidence catalogs until records accumulate.
- Keep private endpoints, local paths, private repository names, and raw transcripts out of committed evidence.

Exit criteria:

- Users know that hardware/profile scripts recommend candidates, not proven tool-safe models.
- Online model discovery, if added, suggests candidates only and does not replace local validation or auto-install models.
- A model is considered tool-validated only after a read-only tool test passes.
- Approved write mode remains blocked until tool execution is proven in the intended editor/provider setup.
- Sanitized validation evidence can be recorded without exposing private machine or repository details.
