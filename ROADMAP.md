# Roadmap

## Status

The repository has entered user-visible product implementation. Milestones 1 through 21 are complete for their defined scopes. Milestone 22A now ships a runnable local-web application for sanitized system status, explicit Ollama connection, installed-model discovery, private chat, writing, summarization, and verified unload on Windows, Linux, and macOS. Milestone 22B retains broader UI composition and optional native Tauri packaging behind separate dependency, security, packaging, and cross-platform gates. Milestone 23 has a promoted Linux image profile and partial Windows AMD evidence. Milestone 24 has partial Linux CUDA ACE-Step evidence, while Milestone 25 remains documentation-only. Milestone 26 has its foundation plus exact Linux/NVIDIA and Windows/AMD evidence.

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
| Milestone 10: ARM And Apple Silicon Model Support | Complete | CPU architecture reporting, ARM model guidance, Linux compatibility assumptions, container caveats, cloud smoke-test guidance, and MLX guidance are documented. A bounded Apple Silicon MLX/Continue CLI validation now records endpoint tool calls plus generated-sample read, plan, review, and scoped-write smoke evidence. |
| Milestone 11: Editor Surface Compatibility | Complete | VS Code-compatible and VSCodium read-only Agent validation are recorded, duplicate-rule checks are clean, and CLI fallback guidance is documented. |
| Milestone 12: Model Tool-Use Validation Evidence | Complete | Starter model defaults, automatic local model config generation, model lanes, local Ollama Agent model preflight tooling, read-only and read-content tool validation guidance, approved-write smoke-test guidance, duplicate approval mitigation, external write verification, platform-aware command rules, sanitized evidence templates, post-validation install flow, and optional online discovery guardrails are in place. |
| Milestone 13: Broader Multi-Repository Validation | Complete | Sanitized legacy .NET evidence plus generated Python, TypeScript, Node, Java, Go, Rust, Infrastructure as Code, and SQL category evidence satisfy the milestone coverage target; future real-repository runs continue as evidence expansion. |
| Milestone 14: Agent Surface Portability And Broader Audience | Complete | Haven 42 supports individual, team, and enterprise users through a local-first AI workbench, and non-Continue surfaces are tracked through evidence-gated validation levels, promotion gates, config-bundle limits, and parity catalogs. Full cross-agent validation and install/configure/test implementation remain tracked in Milestones 17 and 19. |
| Milestone 15: Multi-Language Engineering Support | Complete | .NET remains the most mature path, optional multi-language guidance is evidence-gated, and generated Python plus TypeScript samples have repository-discovery, implementation-planning, and code-review validation evidence. |
| Milestone 16: Sample Repository Factory | Complete | Disposable sample repositories can be generated on Windows, Linux, and macOS for Python, TypeScript, Node, Java, Go, Rust, Infrastructure as Code, and SQL validation; evidence and tests cover fixture shape, runtime context, and sanitization. |
| Milestone 17: Agent Surface Compatibility Validation | Complete | Continue, Aider, and OpenCode have explicit evidence-backed validation positions for the supported-surface scope. Failed or retired integrations were removed, OpenHands remains a documentation-only candidate, and real-project approved write stays separately evidence-gated. |
| Milestone 18: Language Rule Packs | Complete | Optional Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code rule packs are evidence-gated; deterministic project profiles, project-local activation, medium fixtures, and a 28-cell Continue CLI matrix are implemented. Windows, Linux, and native Apple Silicon macOS evidence is recorded separately, and the language-aware selector consumes each platform's evidence. The macOS matrix completed with Devstral Small 2 in bounded single-model runs with external scoped-write verification. |
| Milestone 19: Installer Profiles, Evidence Catalog, And Release Packaging | Complete | Continue profiles plus Aider and OpenCode install/configure/health/test paths satisfy supported-surface parity with deterministic cross-platform contracts. Failed or retired integrations are absent from active catalogs and scripts; OpenHands is documentation-only. |
| Milestone 20: Hardware-Aware Model And Config Automation | Complete | Hardware-aware recommendations, local-only config generation, surface-neutral model lanes, workflow dispatch and envelopes, setup health, cleanup, release readiness, evidence views, cross-platform onboarding, and the stable UI-facing foundation are implemented. Future surface profiles remain separately evidence-gated. |
| Milestone 21: General-Purpose AI Assistant And Intent Routing | Complete | Repository-optional sessions, deterministic and optional bounded LLM routing, provider-neutral local text, live-validated ComfyUI images, runtime discovery, typed artifacts, and engineering workflow route plans are implemented with cross-platform contracts. Ollama text includes an exact Linux Laguna XS 2.1 conformance cell; llama.cpp transport has a direct exact-profile Linux NVIDIA/CUDA live run. |
| Milestone 22: Unified Product UI And Task Composition | In progress; 22A text tools runnable | The zero-dependency local-web application provides system status, inferred local/LAN Ollama scope, per-capability model selection, chat, writing, summarization, and bounded idle cleanup. Software, images, composition, persistence, updates, remote access, and optional Tauri packaging remain gated. |
| Milestone 23: Native Local Image Generation | In progress | The Linux ComfyUI/SDXL profile is live-validated and promoted; Windows AMD/RX 7800 XT now passes cancellation, forced recovery, repeated generation, retention cleanup, and uninstall, while a real update/rollback candidate plus consumer onboarding/installer behavior remain gated. |
| Milestone 24: Local Music And Audio Generation | Live feasibility in progress | ACE-Step has a partial Linux CUDA instrumental pass; vocal, signal-quality, cancellation, recovery, and adapter gates remain open. |
| Milestone 25: Local Video Generation | Research in progress | Exact HunyuanVideo, Wan2.2, and LTX-2.3 candidate records plus identity/media consent policy are complete; no live provider is promoted. |
| Milestone 26: Hardware-Adaptive Model Quantization | Engine evidence expanded | Exact Ollama comparisons passed on Linux NVIDIA and Windows AMD; llama.cpp CUDA passed on Linux NVIDIA and HIP passed on Windows AMD, while Vulkan failed the patch gate and Intel remains parked. |

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
- Validate the pack against additional real repositories when suitable targets are available. Future evidence expansion, not a Milestone 13 completion blocker.
- Convert repeated validation failures into prompt, rule, documentation, or script updates. First legacy validation findings for filename fidelity and lifecycle/support claims have been converted into prompt and test guardrails.
- Add deterministic output verification or a stricter template fallback when local models continue to ignore filename-fidelity and lifecycle/support guardrails. Deterministic runtime output verification has been added; stricter template fallback remains available if verification shows repeated failures.
- Add generated local sample repositories for additional validation categories when real repositories are not available. Done for Node, Java, Go, Rust, Infrastructure as Code, and SQL generated categories with sanitized script-level evidence.
- Keep private repository names, local paths, endpoints, raw transcripts, customer names, and source code out of committed evidence.

Exit criteria:

- At least three distinct repository categories have sanitized validation evidence. Done through legacy .NET real-category evidence plus generated Python, TypeScript, Node, Java, Go, Rust, Infrastructure as Code, and SQL sample-category evidence.
- Evidence records show setup, prompts tested, tool-use status, failure signals, and pack follow-up decisions.
- Repeated failures are tracked and converted into pack improvements.
- Additional repository-category coverage can use generated local samples when real repositories are not available.
- README, docs, roadmap, TODO, changelog, and wiki remain aligned with the validation workflow.

## Milestone 14: Agent Surface Portability And Broader Audience

Goal: Make the project useful beyond one editor extension or one enterprise-only audience while preserving the tested Continue path.

Scope:

- Position Haven 42 as a local-first AI workbench rather than a Continue-only enterprise bundle. Done.
- Keep Continue as the first supported and tested agent surface until another surface has equivalent validation evidence. Done as the support boundary.
- Add an agent-surface compatibility matrix for maintained and documentation-only candidate open-source options. Done for status visibility; failed and retired integrations are recorded only as concise decisions.
- Define what each surface must prove before it can be called read-only validated, plan validated, or approved-write ready. Done.
- Keep beginner-friendly setup paths for simple local hardware while documenting enterprise-safe workflows for larger teams. Done with a shared setup-paths guide.
- Separate reusable prompts, rules, templates, validation scripts, and evidence formats from Continue-specific configuration details where practical. Done for the current docs, shared assets, validation harnesses, and evidence catalogs.
- Decide whether future install scripts should generate surface-specific config bundles instead of only `.continue` assets. Done: surface-specific bundles are allowed only after compatibility evidence exists; Continue and Aider now have supported local config generation paths.
- Update README, docs, roadmap, TODO, changelog, and wiki when the project identity or supported surfaces change. Done for the repository docs and roadmap; external wiki updates remain release-process work when publishing.

Exit criteria:

- New users can understand that the project starts with Continue but is not limited to Continue forever. Done in the README and agent surface docs.
- Non-enterprise users can follow the quick start without feeling the pack assumes a corporate environment. Done through beginner setup paths and non-enterprise guidance.
- Enterprise users still see security, governance, validation, and auditability guidance. Done through the governance, validation, and evidence docs.
- At least one non-Continue open-source agent surface is evaluated with a documented read-only validation result. Done with Aider and OpenCode generated-sample evidence.
- Surface-specific limitations are documented before any surface is recommended for approved writes. Done through promotion gates, compatibility status, and config-bundle policy docs.
- Every tracked agent surface has comparable install, configure, and test status visibility. Done through the compatibility matrix, promotion gates, surface solution catalog, and capability parity catalog. Actual validation and install/configure/test implementation parity remains tracked in Milestones 17 and 19.

## Milestone 15: Multi-Language Engineering Support

Goal: Expand the pack beyond .NET while preserving the current .NET maturity and avoiding language-specific advice when the repository evidence does not support it.

Scope:

- Keep .NET and ASP.NET Core as the first mature and most validated ecosystem. Done.
- Add language-specific rule packs or guidance for Python, JavaScript/TypeScript, Java/Spring, Go, Rust, SQL/database projects, and Infrastructure as Code. Done as optional rule packs and staged guidance.
- Add repository detection guidance so prompts identify project type before applying language-specific recommendations. Done.
- Keep shared engineering standards reusable across languages: Git, testing, security, logging, performance, architecture, documentation, and rollback planning. Done.
- Prevent .NET-specific recommendations from being applied to non-.NET repositories. Done through project-detection guidance and evidence gates.
- Add generated local sample repositories for planned language ecosystems when real repositories are not available. Done.
- Validate repository discovery, implementation planning, code review, and runtime output verification against at least Python and TypeScript samples before promoting language support. Generated-sample workflow validation now runs against Python and TypeScript, with filename-drift guardrail failures recorded for documentation and release-style workflows.
- Keep README, docs, roadmap, TODO, changelog, and wiki clear that language support is staged and evidence-based. Done for repository docs and roadmap; external wiki updates remain release-process work when publishing.

Exit criteria:

- Repository discovery can identify common project types without inventing unsupported framework details. Done through project-detection docs and generated-sample validation.
- Prompts select language-appropriate guidance or explicitly stay language-neutral when evidence is incomplete. Done through optional rule packs, project-detection references, and filename-fidelity guardrails.
- At least Python and JavaScript/TypeScript sample repositories have sanitized validation evidence. Done in `examples/multi-language-workflow-validation.md`.
- README explains that .NET is currently the most mature path, not the only intended path. Done.
- Language-specific guidance is not treated as approved until validation evidence exists. Done through optional rule-pack gating and staged support docs.
## Milestone 16: Sample Repository Factory

Goal: Generate disposable local repositories that unblock validation when real repositories are unavailable.

Scope:

- Add Windows, Linux, and macOS sample repository factory scripts. Done.
- Generate deterministic samples for Python API, TypeScript frontend, Node service, Java/Spring API, Go service, Rust CLI, Infrastructure as Code, and SQL migrations. Done.
- Keep samples dependency-free and offline by default. Done.
- Include metadata in each generated sample explaining that it is a validation fixture, not a production starter template. Done.
- Document how to use generated samples for repository discovery, planning, code review, runtime output verification, and agent-surface testing. Done.
- Keep generated sample output under `runtime-validation-output` by default so it is not committed accidentally. Done.

Exit criteria:

- A contributor can generate all sample repositories with one documented command. Done.
- Tests verify the factory creates expected language/project markers and runtime context captures non-.NET metadata. Done.
- Generated samples are suitable for read-only and approved-write validation in disposable workspaces. Done for disposable validation setup; any surface or language promotion still needs separate evidence.

## Milestone 17: Agent Surface Compatibility Validation

Goal: Convert candidate agent surfaces from documentation into evidence-backed compatibility results.

Scope:

- Validate at least one generated sample repository with Aider in plan or patch mode. Done for generated Python read-only, write-smoke, and scoped-edit validation, plus richer disposable Node service scoped-edit validation with `qwen3-coder:30b`.
- Record surface, model, OS, tool permissions, failure signals, and changed-file verification. Done for current Aider generated-sample scope.
- Keep Continue as the supported first path until another surface has equivalent validation evidence. Done; no non-Continue surface is promoted to equivalent approved-write support.
- Add a Continue CLI automation harness for focused read-only and disposable write-smoke model screening. Done for script and documentation scaffolding; model-specific Continue CLI evidence remains separate from editor Apply evidence.
- Add a shared agent CLI automation harness plus thin wrappers for maintained CLI surfaces. Done for Aider and OpenCode; retired surfaces have no shipped wrapper.

Exit criteria:

- At least one non-Continue surface has sanitized read-only validation evidence. Done with Aider and OpenCode generated-sample evidence.
- Approved-write recommendations remain blocked until scoped-write and external verification pass. Done through promotion gates and evidence catalog status.
- Every promoted supported surface has install/configure/test validation status. Done for Continue, Aider, and OpenCode. Documentation-only candidates do not count as supported parity; failed and retired integrations are removed.

Future evidence expansion:

- Evaluate any future agent successor externally under the admission policy before adding it to the tracked surface list.
- Define a safe OpenHands validation boundary before adding platform-agent validation automation. Done with an isolated generated-sample, sandbox, credential, mount, and network policy.
- Run explicitly approved non-generated repository validation before any non-Continue surface is promoted to real-project approved-write ready.
- Promote one non-Continue surface end to end before widening adapter support. Done for the Aider install, local-model configuration, health, and test adapter; real-project approved write remains blocked pending explicitly approved validation.

## Milestone 18: Language Rule Packs

Goal: Add optional language-specific rules without making the default pack noisy or wrong for other ecosystems.

Scope:

- Add optional rule files for Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code. These optional rule packs are added for current scope and remain out of the default config.
- Define when each rule pack should apply based on repository evidence. Done for current optional language packs.
- Add prompt guidance that keeps recommendations language-neutral when evidence is incomplete.
- Validate each rule pack against generated samples before promoting it. Static generated-sample validation is recorded for Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code in `examples/language-rule-pack-validation.md`; model-backed workflow validation is recorded for generated Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure samples in `examples/multi-language-workflow-validation.md`. Prompt-level and runner-level filename-fidelity guardrails are now in place, but stricter fallback work remains because deterministic verification still catches model filename drift.
- Add a machine-readable project-profile classifier that emits detected ecosystems, evidence files, confidence, and selected language-rule-pack IDs. Done with a sanitized, filename-only cross-platform classifier and `config/project-profile-rules.json`.
- Make installers and config generators activate only the rule packs selected by the project profile. Done for project-local installation by materializing selected packs under `.continue/rules/`; shared-assets mode remains project-neutral pending a per-project overlay design.
- Add medium-complexity generated samples and a representative language/workflow validation matrix so promotion is not based only on static checks or minimal fixtures. Done with layered Python and TypeScript fixtures plus a component-scoped Java/Go/Rust/SQL/IaC platform fixture and a machine-readable four-operation matrix; editor/model cells remain pending until executed.
- Execute the representative matrix with deterministic filename and external-write gates. Done for Continue CLI `1.5.47` on Windows: `devstral-small-2:24b` and `qwen3.5:35b` each passed 27 of 28 cells, and their operation-specific combination validates all 28.
- Generate language-aware agent configuration from exact matrix evidence so a project profile and workflow select the validated model lane. Done for a read-only cross-platform selector that emits Continue-ready model profile metadata; surface-specific runtime auto-switching remains a future adapter capability.
- Add native Linux/macOS matrix-runner parity and validate the evidence-backed language-aware lanes. Linux Continue CLI live evidence is complete through WSL2 Ubuntu 24.04 with one-model-at-a-time safeguards, and the selector consumes that Linux evidence separately. Native Apple Silicon macOS now has a complete 28-cell matrix with Devstral Small 2, including external scoped-write verification and model unload after every bounded run.

Exit criteria:

- Language-specific advice is evidence-gated.
- .NET guidance no longer leaks into non-.NET repositories during validation.
- An installed project can prove which optional language rules are active and why, without manual config editing.
- Each promoted language has repository-discovery, planning, review, and scoped-write evidence against a representative sample.

## Milestone 19: Installer Profiles, Evidence Catalog, And Release Packaging

Goal: Make adoption easier as the pack grows across surfaces, languages, and validation levels.

Scope:

- Add installer profiles for Continue, read-only review, approved-write workflows, and future validated agent surfaces. Done for Continue profiles plus evidence-backed Aider and OpenCode setup adapters; candidate surfaces are excluded from supported setup.
- Add language-focused install/profile options after language packs are validated. Future evidence-gated expansion; not a current completion blocker.
- Create a sanitized evidence catalog for model, OS, editor, agent surface, language, and write-readiness results. Done for current scope in `config/evidence-catalog.tsv`.
- Evolve the catalog to Capability Evidence Contract v2, keyed by surface, model, provider, operating system, surface version, operation, and validation mode. Done with a machine-readable v2 contract and migrated catalog; a model validated for one surface does not inherit write readiness on another surface.
- Aggregate duplicate evidence conservatively and retain provenance instead of selecting the first row for a model. Done in the PowerShell and cross-platform recommendation engines and capability-keyed scorecard.
- Improve release packaging with GitHub release notes, downloadable archives, checksums, and install command examples. Done for current scope with cross-platform packaging scripts and checksum guidance.

Exit criteria:

- Users can choose the right profile without manually assembling config files. Done for the supported Continue, Aider, and OpenCode set. Documentation-only candidates are excluded from default choices.
- Validation evidence is structured enough to compare models, surfaces, and languages over time. Done for the v2 catalog and current recommendation and scorecard consumers; new surface adapters must still add exact evidence before promotion.
- Release artifacts are easy to install and verify. Done with cross-platform package scripts and checksum guidance.

Future candidate expansion:

- Continue, Aider, and OpenCode have supported install, configure, health, and test paths within their documented evidence limits; real-project approved write remains blocked for non-Continue surfaces.
- Failed integrations are removed from scripts, adapters, active catalogs, and detailed evidence; reintroduction requires a fresh proposal and full promotion-gate validation.
- New agent software is evaluated in disposable untracked workspaces. Only fully passing integrations may add repository or release-package assets; failed evaluations receive a concise sanitized decision record only.
- OpenHands has a defined rootless workspace, credential, sandbox, and network boundary, but remains a candidate until an explicitly approved implementation passes generated-sample validation.
## Milestone 20: Hardware-Aware Model And Config Automation

Goal: Turn hardware/profile evidence into practical model and configuration recommendations that a local user can apply without hand-tuning every setting.

Scope:

- Add logic that evaluates detected GPU, VRAM, RAM, CPU, architecture, operating system, and model-host platform to decide which local models are reasonable candidates for the user's machine. Done for offline recommendation output.
- Rank candidate models by workflow fit, resource fit, tool-use validation status, and conservative defaults so the user receives a clear recommended model plus alternatives. Done with lane-specific policy version 1 and per-candidate score rationale.
- Add lane-specific scoring: prioritize reliability and VRAM headroom for WRITE SAFE, while allowing larger validated models for PLAN ONLY and DEEP REVIEW when hardware permits. Done for exact evidence matches on Windows, Linux, and macOS recommendation paths.
- Include quantization, context target, backend overhead, model architecture or MoE behavior, and a configurable memory reserve rather than estimating fit only from parameter count in the model name. Done for curated model-fit profiles with a labeled low-confidence fallback for unknown tags; runtime-measured metadata remains a future refinement.
- Generate best-fit local configuration for Continue first, including model lanes, roles, context length, max tokens, keep-alive settings, and local-only endpoint handling. Done for local-only Continue config output.
- Keep the configuration engine surface-neutral enough to support future plugins or agent surfaces after they have compatibility evidence. Done with a reusable `ModelLanes` recommendation contract; generated config remains evidence-gated per surface.
- Ensure cloud tags, provider-specific tags, MLX tags, oversized models, and unsupported local pulls are filtered or explained before any model download is attempted.
- Keep all generated machine-specific settings in local-only config files and out of committed shared configuration.
- Add validation coverage that proves hardware-aware selection does not expose private paths, hostnames, usernames, endpoints, or raw hardware reports.
- Reduce the number of scripts by consolidating repeated command-line workflows behind shared engines, registries, or dispatchers before adding more surface-specific scripts.
- Script consolidation planning is documented, and the onboarding/navigation family now shares workflow lookup, command rendering, report output, and native argument dispatch while preserving its public commands.
- Implementation slices are complete for PowerShell and Bash agent CLI wrapper defaults plus onboarding/navigation plumbing; further consolidation remains evidence-driven.
- Keep thin wrapper scripts only where they improve beginner usability or platform ergonomics; avoid duplicating business logic across wrappers.
- Define a machine-readable workflow registry that describes available tasks, inputs, outputs, safety level, platform support, and script entry points. Done.
- Define a stable script/API boundary so future tools can call hardware profiling, model discovery, model testing, configuration generation, installation, and validation without knowing each script family. Workflow registry foundation and PowerShell/Linux/macOS dispatchers are done; deeper workflow execution reuse remains pending.
- Standardize a versioned workflow request, progress, result, warning, and error envelope before the web UI calls the dispatcher. Done with schema v1, privacy-safe defaults, structured failures, and PowerShell/native-shell parity.
- Add a guided command/menu layer that presents a small set of user intents such as first-time setup, health check, model choice, install/configure an agent, validation, cleanup, and release readiness while calling existing workflows underneath. Done for registry-backed menu generation; future interactive command execution can build on it.
- Keep per-script documentation available as appendix/reference material for advanced users, maintainers, and automation authors rather than presenting every script as a primary user choice. Done for registry-backed appendix coverage.
- Design a unified starter-toolkit web UI for people who want to use local AI for coding, with guided flows for setup, hardware profiling, model choice, config generation, agent-surface testing, and validation. Done as an evidence-first architecture spec.
- Keep the web UI evidence-first: show what was tested, what passed, what failed, and what is only a recommendation before applying changes. Done in the UI design spec; implementation remains future work.
- Generate a local evidence dashboard from validation JSON so users can compare models, agent surfaces, operating systems, write readiness, and risks before installing anything. Done for committed evidence catalog and surface readiness data; deeper runtime JSON ingestion remains future work.
- Add a beginner setup mode that guides users through the common local-AI coding path with minimal questions and exact next commands. Done for a registry-backed command plan; future UI can turn the plan into guided controls.
- Add a health check workflow that verifies Ollama reachability, generated config, duplicate local references, repository detection, and runtime validation output status. Done for current PowerShell and shell-wrapper scope.
- Add a safe cleanup workflow with dry-run support for stale runtime outputs, generated samples, failed diagnostic artifacts, and obsolete backup folders. Done for local artifact cleanup; model deletion remains explicit in model-testing workflows.
- Add a release readiness gate that runs validation, tests, release package dry-run, git state, workflow registry checks, and agent-surface parity checks before release or push. Done for local gate scope, with a separate exact-SHA hosted verifier that waits for GitHub Actions and checks every required Windows, Linux, and macOS job after push.
- Add a model scorecard that tracks tested models by surface, evidence status, write readiness, and recommended use. Done for evidence-backed readiness; speed, quality, context size, and hardware tier remain future structured evidence fields.
- Keep surface-specific plugin profiles outside the supported pack until each plugin has compatibility evidence. The reusable data model and gating policy are complete; individual future profiles are new evidence-gated integration work rather than a Milestone 20 blocker.
- Add a surface-neutral install/configure/test solution catalog for every tracked agent surface. Done for current evidence-gated status and blocked-reason tracking.
- Add sample scenario packs for common local-AI coding tasks such as legacy migration, config refactoring, bug fixing, security review, test generation, and documentation cleanup. Done for registry-backed scenario catalog and docs; future UI can expose these as guided lanes.

Exit criteria:

- A user can run one documented flow that profiles hardware, discovers or reads candidate models, tests eligible models, and receives a recommended model/config result.
- Continue local config generation uses the recommendation result without requiring manual YAML editing for common setups.
- Future agent/plugin support can reuse the same model/config recommendation data without being hard-coded to Continue-only assumptions.
- The final-stage UI is treated as an optional wrapper over tested shared engines, not a replacement for script-level validation.
- The UI can call a small number of stable script entry points, a workflow registry, or a shared command dispatcher rather than many plugin-specific scripts.
- Users can start from a guided menu or beginner flow, while individual script docs remain available in an appendix for detailed reference and troubleshooting.
- The future UI can call the completed stable entry points without requiring plugin-specific business logic. UI implementation belongs to Milestone 22 after Milestone 21 defines general-purpose capability and artifact contracts.
- Evidence dashboard, health check, cleanup, release gate, and model scorecard workflows all read from sanitized local artifacts and avoid committing private machine details.

### Recommended Implementation Order

1. Define Capability Evidence Contract v2 and migrate recommendation lookups to surface-specific, operation-specific evidence. Done.
2. Add machine-readable project classification and runtime activation of matching language rule packs. Done for deterministic project-local installation.
3. Implement lane-specific model scoring and richer hardware/model-fit metadata. Done for scoring policy version 1 and curated fit policy version 1; runtime-measured artifact metadata remains a future refinement.
4. Complete Aider as the first end-to-end non-Continue install, configure, health, and test adapter. Done with local-only config and deterministic cross-platform coverage.
5. Standardize versioned workflow request/result/progress/error envelopes and consolidate repeated script-family business logic. Envelope contract and the first onboarding/navigation consolidation are done; additional families remain evidence-driven.
6. Expand medium-complexity samples and define a representative surface/language/mode validation matrix. Done for fixtures and static coverage; execute and record the model-backed operation cells next.
7. Hand the stable workflow, evidence, and onboarding foundation to Milestone 21 capability work and Milestone 22 UI implementation. Done.
8. Refresh `PROJECT.md`, `ARCHITECTURE.md`, README status text, and surface diagrams so documented maturity and runtime wiring match verified behavior. Done.

## Milestone 21: General-Purpose AI Assistant And Intent Routing

Goal: Let new AI users describe an ordinary task without first understanding repositories, coding agents, model hosts, or individual scripts, while preserving the engineering pack as the most mature evidence-gated capability domain.

Scope:

- Add a first-run "What would you like to do?" experience with top-level choices for chat, writing or summarization, image creation, software work, and local-AI setup or troubleshooting. Done for the deterministic cross-platform command/menu foundation.
- Define a provider-neutral capability registry above the engineering workflow registry. Capabilities describe user intent and typed outputs; providers describe how text, images, or engineering workflows are executed. Done for schema version 1 and the initial six capability families.
- Allow general-purpose capabilities to run without a repository by using an explicit session or user-selected artifact workspace. Done for dry-run-first repository-optional session planning and creation; provider artifact writes remain separately gated.
- Implement a deterministic menu and rule-based intent fallback that remains usable when no model is installed, the model server is unavailable, or LLM routing confidence is low. Done for registry-driven resolution, first-run menu output, ambiguity handling, and unmatched fallback.
- Optionally use an LLM to ask follow-up questions and propose capability IDs. Treat its output as an untrusted routing suggestion that must pass capability availability, policy, privacy, and approval checks. Done with a dry-run-first cross-platform advisory router that rejects unknown IDs and never invokes capabilities.
- Add provider adapters for general text/chat, writing and summarization, image generation, and the existing engineering workflow dispatcher without assuming one model or provider supports every modality. Done with one local-text contract supporting live-validated Ollama and exact-profile-gated, live-validated llama.cpp OpenAI transport on Linux NVIDIA/CUDA; the ComfyUI SDXL image adapter is live-validated, and deterministic engineering route plans preserve workflow safety levels.
- Represent results as typed artifacts such as chat messages, Markdown documents, images, reports, configuration plans, or reviewed repository changes. Done for typed artifact contract version 1 and the local text adapter; image artifacts remain gated on image-provider admission.
- Show whether each capability is local or external and whether it reads a repository, writes files, downloads models, calls a network service, or requires approval. Done in capability, provider-discovery, session, and route result contracts.
- Keep file, network, and repository safety enforcement in application policy rather than relying on model prompts. Done for deterministic routing, provider discovery, local text execution, and advisory LLM routing boundaries.
- Keep engineering write readiness tied to existing surface-, model-, provider-, OS-, operation-, and validation-specific evidence; general chat success must not promote a model for source-code edits.

Exit criteria:

- A new user can start with an ordinary-language goal or deterministic menu without selecting a script, agent surface, or repository.
- General chat and writing tasks can run without repository context and produce clearly identified typed results.
- Image generation appears only when a compatible configured provider is available and identifies its output location before writing.
- The deterministic fallback produces testable capability selections without an LLM.
- An optional LLM router can ask clarifying questions and recommend capabilities but cannot invoke unavailable or disallowed actions or bypass approval requirements.
- The existing workflow registry and dispatcher remain the source of truth for engineering operations.
- Local versus external execution and all material read, write, download, and network effects are disclosed before execution.

### Recommended Implementation Order

1. Define the capability registry, typed artifact contract, availability states, and policy metadata. Done.
2. Add the deterministic first-run intent experience and repository-optional session workspace. Done.
3. Implement one local text/chat adapter plus writing and summarization capabilities. Done with a dry-run-first, session-bound adapter shared by `ollama.local-text` and `llamacpp.local-text`. Ollama has live Windows evidence; llama.cpp has portable contract evidence plus a direct Linux NVIDIA/CUDA discovery and invocation pass. Windows AMD/HIP remains engine-evidence-only until its adapter is run directly.
4. Add runtime provider availability discovery and deterministic engineering route plans without provider or workflow auto-invocation. Done with offline-first Windows, Linux, and macOS entry points, bounded Ollama `/api/tags` and OpenAI-compatible `/v1/models` probes, exact engine-profile admission, and workflow-ID integrity checks.
5. Add the optional LLM routing layer as an untrusted suggestion boundary. Done with structured output, committed-registry validation, explicit clarification/rejection states, no persistence, and no automatic invocation.
6. Add provider discovery and one evidence-gated image-generation adapter. Done for a pinned, hardened, localhost-only ComfyUI service and session-bound SDXL adapter with live Linux evidence and cross-platform fixture contracts.
7. Hand stable individual capabilities and artifact contracts to Milestone 22 for UI integration and tested multi-step composition. Done; the UI design checkpoint completed with the first product slice recorded in `docs/product-ui-first-slice.md`.

## Milestone 22: Unified Product UI And Task Composition

Goal: Provide one local-first product surface over the completed engineering workflows and general-purpose capability platform without reimplementing their business logic or weakening their safety boundaries.

Scope:

- Use Tauri 2 with a React and TypeScript UI built by Vite for ordinary desktop operation. Load bundled local assets only and communicate with a packaged Haven 42 engine sidecar through versioned typed stdin/stdout IPC.
- Permit only registered capability and workflow IDs through narrowly scoped Tauri permissions; ship no arbitrary shell bridge, unrestricted filesystem API, remote UI code, or default listening port.
- Keep hardened loopback/browser operation as a separately tested option for headless Linux, SSH-tunneled use, development, and diagnostics.
- Implement the unified web UI over stable workflow IDs, capability IDs, typed artifacts, and versioned request/result envelopes.
- Keep chat as the primary interaction surface with compact sticky navigation and provider/system configuration. Done for the local web slice; responsive contract and visual regression coverage remain part of each UI change.
- Evaluate text models independently for chat, writing, and summarization before automatic defaults. The first writing matrix tracks Qwen 3.5 9B as the adapter control plus Gemma 3 12B, Mistral Small 3.2 24B, and Granite 4 7B-A1B-H as unpromoted candidates.
- Present deterministic first-run choices for chat, writing, summarization, image creation, software work, and local-AI setup.
- Present beginner recommendations and advanced model controls from one engine-derived catalog decision that combines exact artifact identity, license, hardware fit, provenance, and evidence without allowing the renderer to promote a model.
- Support repository-optional sessions and clearly identify every artifact location before a write.
- Show capability availability, evidence status, local versus external execution, network effects, repository access, and approval requirements before execution.
- Reuse the Milestone 20 evidence dashboard, health, cleanup, recommendation, installation, validation, and release-readiness workflows.
- Reuse Milestone 21 routing and provider contracts; keep LLM routing advisory and policy enforcement deterministic.
- Add a cross-platform core-engine updater that can check for, stage, and optionally install stable releases published by the official GitHub repository. Never update a production installation with an unattended `git pull` or from a moving branch.
- Separate immutable engine files from user workspaces, local configuration, models, provider data, generated artifacts, and evidence so an engine update cannot overwrite user-owned state.
- Add accessible progress, warning, failure, retry, and recovery experiences over the versioned workflow envelope.
- Add tested multi-step task composition only after individual capabilities and artifact contracts have passed their own gates.
- Keep future surface-specific profiles outside the UI until their exact integrations pass the agent admission policy.
- Use GitHub-hosted platform runners for routine builds. Pursue Microsoft Store or SignPath Foundation Windows signing before paid Artifact Signing, and defer Apple Developer enrollment until the first public macOS beta is otherwise ready.
- Build unsigned development packages, but require signed Windows release components, signed and notarized macOS release packages, and checksummed/attested Linux artifacts before stable promotion.

Exit criteria:

- A beginner can complete the common local-AI setup path without selecting scripts or manually editing configuration.
- A general AI user can complete repository-free chat, writing, summarization, or an available image task and locate the typed result artifact.
- A software user can enter the existing engineering workflow system without the UI bypassing evidence or approved-write gates.
- Every configurable capability offers guided setup, existing-setup connection, and not-now; both active paths expose structured advanced settings without weakening non-overridable safety controls. Eight capability-domain schemas and an effect-free default-deny evaluator now define this boundary.
- The engine visibly derives validated, customized, unverified, or blocked after every advanced change; renderer input cannot promote evidence.
- Unavailable, blocked, failed, and recommendation-only capabilities are visibly distinct and cannot be presented as validated.
- Every material read, write, network call, model download, and external-provider action is disclosed before execution.
- Core updates resolve an immutable GitHub release and platform asset, verify its checksum and release signature or attestation, validate schema and provider compatibility, stage beside the active version, and switch atomically only after a health check passes.
- A failed update automatically restores the previous known-good engine. Offline use remains available, update checks can be disabled, stable is the default channel, and automatic installation is an explicit user choice.
- Windows, Linux, and macOS contract tests cover routing, workflow dispatch, artifacts, failures, recovery, and safe composition.

### Recommended Implementation Order

1. Select the local UI runtime and package boundary without introducing a hosted-service dependency. Done with Tauri 2, bundled React/TypeScript/Vite assets, a packaged engine sidecar, and private typed stdin/stdout IPC.
2. Define and statically validate the Tauri capability allowlist, IPC schema, native path-selection boundary, local-only content policy, and headless loopback separation. Done for the versioned contracts, 46 engine-side hostile cases, and 55 native-authority policy cases; actual native bridge enforcement and adversarial runtime tests remain promotion gates.
3. Validate pinned dependency and license choices, then scaffold the smallest Windows, Linux, and macOS package slice. Direct candidates are reviewed; disposable Windows npm and PyInstaller graphs passed, while five Windows-reachable unmaintained Rust crates, unaudited native build prerequisites, and separate Linux findings block admission.
4. Implement first-run navigation and capability availability views over the Milestone 21 registry. The framework-neutral navigation contract, product-wide progressive onboarding contract, eight capability-setting schemas, effect-free policy evaluator, wireframes, and deterministic view-model builder are done; the native renderer remains gated.
5. Assemble the model-selection view data without visual UI work. Done with a versioned read-only catalog, fail-closed per-artifact license policy, hardware-fit labels, revision-bound evidence, shared beginner/advanced decisions, hostile-input tests, and OS-aware wrappers.
6. Connect setup, health, model choice, engineering workflows, and evidence views from Milestone 20.
7. Add repository-free text and image flows only for providers promoted in Milestone 21 or Milestone 23.
8. Implement the GitHub release updater with explicit channels, network disclosure, immutable asset selection, checksum and signature or attestation verification, compatibility preflight, atomic activation, post-update health checks, rollback, and retained-version cleanup.
9. Add cross-platform UI contract, updater, rollback, packaging, signing, and uninstall tests.
10. Add bounded multi-step composition with explicit intermediate artifacts and approvals.

## Milestone 23: Native Local Image Generation

Goal: Let ordinary Windows, macOS, and Linux users generate images on their own computer without requiring an external server, while preserving the exact evidence boundary already proven by the Linux ComfyUI/SDXL provider.

Current validated baseline:

- ComfyUI `v0.28.2` at the pinned validated commit, PyTorch `2.11.0+cu126`, SDXL Base 1.0 with its verified checksum, a localhost-only hardened Linux service, typed PNG artifacts, metadata exclusion, history cleanup, forced recovery, SSH tunneling, and visual validation passed on Linux with an NVIDIA V100.
- The provider-neutral `media.image.create` capability and `comfyui.local-image` adapter are live-validated for that exact Linux scope. Cross-platform fixture contracts do not promote native Windows or macOS execution.

Remaining scope:

- Make native local image generation the default consumer path instead of requiring an external server; keep a shared Linux provider as an optional advanced deployment.
- Detect hardware and select only an independently promoted profile: Windows NVIDIA CUDA, Windows Intel GPU/XPU, Windows AMD GPU, Apple Silicon MPS, or the validated Linux CUDA profile.
- Treat every operating-system and accelerator combination as separate evidence. Intel GPU support must pass installation, XPU acceleration, generation, metadata, recovery, cleanup, and typed-adapter gates before any Intel runtime files or installer automation ship.
- Install the runtime and checkpoint only after disclosing source, license, size, checksum, storage location, network use, and expected hardware fit.
- Start the image provider on demand, bind it to loopback only, stop it after an idle period, and keep provider state separate from the replaceable core engine.
- Keep custom nodes and external API nodes disabled unless an exact extension independently passes security, compatibility, privacy, cleanup, and promotion gates.

Exit criteria:

- Windows NVIDIA, Windows Intel XPU, Windows AMD, and Apple Silicon MPS are each represented as unavailable or candidate-only until their exact native profile passes; no platform inherits Linux evidence.
- A promoted profile passes install, health, accelerator confirmation, checkpoint verification, text-to-image generation, metadata inspection, typed-artifact validation, cancellation, recovery, retention, cleanup, update, rollback, and uninstall gates.
- Runtime probing rejects silent CPU fallback unless the user explicitly selected a separately tested CPU profile.
- Generated images and provider-retained copies have explicit storage, retention, and cleanup behavior; prompts, endpoints, authentication values, and machine-specific paths are not persisted unintentionally.
- Failed profiles leave only a concise sanitized decision record and ship no scripts, adapters, harnesses, templates, workflows, configuration, runtime files, or installer automation.
- The unified UI exposes only promoted native profiles and clearly distinguishes the validated shared Linux provider from a consumer-local installation.

### Recommended Implementation Order

1. Preserve the current Linux ComfyUI/SDXL profile as the reference contract and do not broaden its evidence.
2. Define hardware discovery and consent-driven local provider onboarding without requiring an external server. Done as a fail-closed contract and guide; it does not install candidate profiles.
3. Validate Windows NVIDIA CUDA and Windows Intel XPU, and complete the partially passing Windows AMD profile, using separate pinned environments and evidence. The Windows AMD cancellation, forced-recovery, repeated-run, retention-cleanup, and uninstall cells passed on 2026-07-23; update/rollback awaits a newer immutable AMD release, and consumer onboarding/installer behavior remains unadmitted.
4. Validate Apple Silicon MPS on a physical Mac as the last native hardware gate to control cost.
5. Add installer and lifecycle automation only for each exact passing profile.
6. Connect promoted local profiles to the Milestone 22 UI with progress, cancellation, cleanup, and provider-update boundaries.

## Milestone 24: Local Music And Audio Generation

Goal: Let an end user create music or sound effects on their own computer through the provider-neutral capability and typed-artifact boundaries, without requiring an external server or exposing provider-specific installation and API complexity.

Candidate scope:

- Evaluate ACE-Step 1.5 as the first full-song candidate because it offers lyrics, vocals, instrumental generation, remixing, a localhost REST API, and documented Windows CUDA, Windows AMD ROCm, Windows Intel XPU, Apple Silicon MLX, Linux CUDA, and reduced CPU paths.
- Evaluate Stable Audio 3.0 Small and Medium as licensing-conscious candidates for local sound effects, instrumental music, editing, continuation, and longer composition. Treat the Stability AI Community and Enterprise license thresholds as product policy inputs, not model-quality evidence.
- Keep YuE as an advanced full-song research candidate only after the consumer-oriented profiles pass.
- Exclude MusicGen from a promoted commercial product profile while its official model weights remain CC-BY-NC 4.0; documentation may retain it as a research comparison.
- Define a provider-neutral `audio.music.create` capability and typed audio artifact only after at least one provider candidate passes its external evaluation. Candidate status alone must not add registry entries, scripts, adapters, templates, workflows, installer files, or model configuration.
- Keep the music runtime loopback-only, start it on demand, stop it after an idle period, and disclose model downloads, disk use, generation time, output retention, reference-audio use, and any license or attribution requirements before execution.
- Treat Windows NVIDIA CUDA, Windows Intel XPU, Windows AMD ROCm, Apple Silicon MLX, and Linux CUDA as independent evidence profiles. An upstream compatibility claim does not promote another operating system, accelerator, or discrete/integrated GPU class.
- Require explicit consent and policy controls for uploaded reference audio, voice cloning, identifiable voices, lyrics, artist-style requests, and commercial-use expectations.

Exit criteria:

- At least one exact provider release, model, license, operating system, accelerator, and hardware tier passes an external install, health, generation, cancellation, recovery, cleanup, sanitization, and uninstall evaluation before any executable integration enters the pack.
- Instrumental and vocal operations are reported separately; success in one does not imply the other is supported.
- Validation checks requested and actual duration, sample rate, channel count, decodability, non-silent signal, clipping, bounded runtime, and output-path fidelity without requiring byte-identical audio across accelerators.
- Promoted adapters produce typed WAV or FLAC artifacts plus sanitized metadata and do not persist prompts, lyrics, reference-audio paths, endpoints, or authentication values unless the user explicitly approves that artifact content.
- Runtime probing confirms the intended accelerator and rejects silent CPU fallback unless the user deliberately selected a tested CPU profile.
- Model and runtime downloads require prior size, source, checksum, license, and storage-location disclosure.
- Failed candidates leave only a concise sanitized decision record; no scripts, adapters, harnesses, templates, workflows, configuration, or registry entries ship.
- The unified UI exposes music creation only after a provider is promoted and preserves evidence, privacy, retention, approval, progress, cancellation, and cleanup states.

### Recommended Implementation Order

1. Record candidate versions, model cards, licenses, distribution terms, download sizes, supported operations, and claimed hardware backends without adding executable integration files. ACE-Step, Stable Audio Small SFX, and Stable Audio Medium are recorded; exact anonymous metadata for gated Stable Audio Small Music remains open.
2. Complete the ACE-Step 1.5 Linux CUDA gate. REST health, deterministic instrumental WAV structure, runtime isolation, and cleanup partially passed; vocal, signal/clipping, listening, cancellation, recovery, retention, and typed-adapter checks remain. This evidence does not promote Windows or macOS.
3. Evaluate Stable Audio 3.0 Small and Medium independently for sound effects, instrumental music, editing, duration, licensing, and consumer hardware fit.
4. Run separate native profiles for Windows NVIDIA CUDA, Windows Intel XPU, Windows AMD ROCm, and Apple Silicon MLX as hardware becomes available; keep the physical Mac gate last to control cost.
5. After one exact profile passes, define the provider-neutral capability, typed audio artifact, availability discovery, and dry-run-first adapter contracts.
6. Add the promoted provider to the UI only after cross-platform offline fixtures, native live evidence, cleanup, packaging, and exact-SHA hosted checks pass.

Official candidate references: [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5), [ACE-Step installation and hardware guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md), [Stable Audio 3.0](https://stability.ai/news-updates/meet-stable-audio-3-the-model-family-built-for-artistic-experimentation-with-open-weight-models), [Stability AI licensing](https://stability.ai/license), [YuE](https://github.com/multimodal-art-projection/YuE), and [AudioCraft/MusicGen](https://github.com/facebookresearch/audiocraft).

## Milestone 25: Local Video Generation

Goal: Let an end user generate short videos locally through provider-neutral capability and typed-artifact boundaries, without presenting high-cost, unsupported, cloud-only, or unvalidated hardware paths as consumer-ready.

Candidate scope:

- Evaluate HunyuanVideo 1.5 first as a consumer-oriented NVIDIA candidate for separate text-to-video and image-to-video operations. Its official implementation requires Linux, CUDA, and at least 14 GB VRAM with offloading; those claims do not promote Windows or other accelerators.
- Evaluate Wan2.2 TI2V-5B as a unified text-to-video and image-to-video candidate with official 720p/24 FPS support and a native ComfyUI workflow. Keep the 14B variants outside consumer profiles unless their much larger memory requirements pass a separate tier.
- Evaluate LTX-2.3 as an advanced candidate for text, image, video, audio, interpolation, and retake workflows. Treat its 32 GB VRAM, 100 GB storage, CUDA requirements, model license, and current lack of native local macOS inference as explicit product constraints.
- Keep Windows Intel, Windows AMD, and Apple Silicon local video generation unavailable until an exact provider and native acceleration path passes; generic ComfyUI or PyTorch compatibility is not evidence.
- Define `media.video.create` and typed MP4 or WebM artifacts only after one exact provider profile passes external evaluation. Candidate status must not add registry entries, scripts, adapters, harnesses, templates, workflows, configuration, runtime files, or installer automation.
- Require consent and policy controls for reference images or video, identifiable people, face animation, voice or likeness use, deepfake risk, artist-style requests, generated-content disclosure, and commercial-use expectations.

Exit criteria:

- Text-to-video and image-to-video are tested and reported independently for an exact provider release, model, license, operating system, accelerator, hardware tier, resolution, duration, and frame rate.
- Validation confirms accelerator use, requested and actual duration, resolution, frame rate, frame count, codec, container decodability, non-empty frames, bounded corruption checks, output-path fidelity, and bounded runtime without requiring byte-identical video across hardware.
- The provider passes installation, health, cancellation, timeout, restart, recovery, retention, cleanup, update, rollback, and uninstall gates.
- Promoted adapters produce sanitized typed artifacts and do not persist prompts, source paths, endpoints, credentials, or identity-bearing inputs without explicit approval.
- Model downloads disclose source, license, size, checksum, storage location, estimated hardware fit, and expected generation time before network or disk writes.
- Failed candidates leave only a concise sanitized decision record and ship no executable integration assets.
- The unified UI exposes video generation only after promotion and preserves evidence, consent, progress, cancellation, retention, cleanup, and generated-content disclosure states.

### Recommended Implementation Order

1. Record exact HunyuanVideo 1.5, Wan2.2 TI2V-5B, and LTX-2.3 versions, model cards, licenses, sizes, operations, and claimed hardware without adding executable integration files. Done with immutable code/model revisions and published primary-file hashes; no executable integration was added.
2. Evaluate HunyuanVideo 1.5 and Wan2.2 independently on available Linux NVIDIA hardware; confirm architecture and CUDA compatibility before downloading large model assets.
3. Evaluate LTX-2.3 only on hardware meeting its documented memory, storage, and CUDA requirements.
4. Define provider-neutral capability and typed video artifacts only after one exact profile passes.
5. Run separate native Windows and macOS profiles only when credible provider-specific paths and suitable hardware are available; keep physical Mac validation last.
6. Add the promoted provider to the UI only after offline fixtures, native live evidence, consent, cleanup, packaging, and exact-SHA hosted checks pass.

Official candidate references: [HunyuanVideo 1.5](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5), [Wan2.2](https://github.com/Wan-Video/Wan2.2), [ComfyUI Wan2.2 workflow](https://docs.comfy.org/tutorials/video/wan/wan2_2), [LTX-2.3 system requirements](https://docs.ltx.io/open-source-model/getting-started/system-requirements), [LTX pipelines](https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-pipelines/README.md), and [LTX license](https://github.com/Lightricks/LTX-2/blob/main/LICENSE).

## Milestone 26: Hardware-Adaptive Model Quantization

Goal: Give an end user a faster and more reliable local-model experience by selecting a trusted existing quantization or reproducibly creating a local derivative that matches the user's exact hardware, runtime, workload, and quality requirements.

Scope:

- Extend hardware discovery beyond a coarse resource tier to include accelerator vendor and model, usable VRAM or unified memory, CPU architecture and instruction support, system RAM, available storage, model runtime, driver/runtime versions, expected context, concurrency, and workload lane.
- Prefer an official or otherwise independently trusted pre-quantized artifact when an exact compatible option exists. Local quantization is a fallback, not an automatic first step.
- Evaluate runtime-specific formats and methods independently, including GGUF quantizations for llama.cpp/Ollama, MLX quantizations for Apple Silicon, and compatible weight-only or reduced-precision formats such as AWQ, GPTQ, FP8, or INT4 only where the selected backend and accelerator explicitly support them.
- Never infer compatibility from a bit count alone. Quantization method, kernel support, model architecture, expert layout, KV-cache precision, context target, batch size, and CPU/GPU offload can materially change fit and performance.
- Resolve every source model and input artifact to an immutable revision, verify checksums where published, inspect model and dataset licenses, and record whether derivative creation and redistribution are permitted.
- Keep source weights and generated derivatives outside the replaceable application and repository trees. Never overwrite the source artifact; retain a manifest that records source revision, input hashes, tool versions, parameters, output hashes, format, license, and intended runtime.
- Require explicit consent before downloading source weights or beginning a potentially long conversion. Disclose expected download size, temporary and final storage, estimated memory, compute time, network use, and cleanup options.
- Do not use private repositories, prompts, conversations, or user documents as calibration data by default. Any calibration corpus must have recorded provenance, license, privacy classification, and explicit user approval.
- Measure cold-load time, time to first token, tokens per second, peak VRAM or unified memory, peak system RAM, disk size, accelerator use, context stability, and concurrent-session behavior on the target machine.
- Compare the candidate against its higher-precision source or a trusted baseline using the exact intended lanes: general chat, summarization, tool calling, read-only engineering work, and approved-write workflows where applicable. A memory or speed pass cannot compensate for unacceptable quality loss or malformed tool behavior.
- Generate a recommendation with alternatives and a confidence level. The user chooses whether to adopt the derivative; the system preserves the previous known-good model/configuration for rollback.
- Treat each model revision, quantization recipe, runtime version, operating system, accelerator, context target, and operation as separate evidence. Never promote one combination based on another combination's result.
- Apply the repository's pass-before-ship rule: failed or incomplete quantization candidates leave only a concise sanitized decision record and add no scripts, conversion harnesses, runtime configuration, model artifacts, or active catalog entries.

Exit criteria:

- A dry-run can explain whether the best choice is an existing trusted artifact, a local derivative, or no safe recommendation, without downloading or changing model state.
- A local quantization plan is reproducible from immutable source identifiers, verified inputs, pinned tools, explicit parameters, and a machine-readable manifest.
- The workflow refuses unsupported accelerator/runtime/format combinations and detects unexpected CPU fallback or excessive memory pressure.
- The candidate passes resource, functional, quality, tool-use, cleanup, and rollback gates on the exact target profile before it becomes selectable as validated.
- Machine-specific paths, hardware identifiers, endpoints, calibration content, and model files remain local and are excluded from commits and release packages.
- The unified UI can disclose the tradeoffs, request approval, show progress and storage use, compare measured results, activate the selected artifact, and restore the previous known-good configuration.

### Recommended Implementation Order

1. Define a versioned quantization-plan and quantized-artifact manifest contract, including immutable source identity, license, hashes, recipe, runtime compatibility, local storage, and cleanup state. Done.
2. Extend hardware and runtime profiling with the exact inputs needed for format selection, context planning, offload, and capacity checks while keeping reports sanitized. Done with an OS-aware, local-only standard-library profiler; exact driver-tool availability remains visible as unknown rather than inferred.
3. Implement dry-run selection of trusted existing artifacts before adding any local conversion path. Done; the planner performs no network, download, conversion, write, or activation effect.
4. Define bounded benchmark and quality gates that compare source and candidate artifacts across the user's intended capability and engineering lanes. Done in the quantization guide and exercised by the first exact Linux NVIDIA validation cell.
5. Validate one Linux NVIDIA GGUF/Ollama path in a disposable environment, using the user's local Ollama host only after explicit test-phase notice and approval. Done for Ollama 0.32.1, Qwen 3.5 9B Q4_K_M versus the official Q8_0 artifact, a 4,096-token context, concurrency one, and an NVIDIA 16 GB profile; Q4_K_M retained the tested functional behavior while using less accelerator memory and producing tokens faster. The disposable Q8_0 artifact was removed after validation.
6. Add Windows NVIDIA, Windows Intel, Windows AMD, and Apple Silicon paths only when an exact runtime and format have credible native support; keep physical Mac validation last. Windows AMD is done for Ollama 0.32.1, its packaged ROCm 7.1 backend, an RX 7800 XT 16 GB profile, Qwen 3.5 9B Q4_K_M versus Q8_0, a 4,096-token context, and concurrency one. Windows NVIDIA and Apple Silicon remain open; Windows Intel is explicitly parked until representative Intel GPU hardware is available.
7. Separate capability, provider contract, inference engine, hardware backend, and model artifact selection. Done with a fail-closed registry. llama.cpp `b10088` CUDA passed bounded engine checks on the exact Linux NVIDIA RTX 5000 profile, and HIP passed on the exact Windows AMD profile; Vulkan failed the Windows AMD Git-applicable-patch gate and remains documentation-only. OpenVINO GenAI and llama.cpp SYCL are parked pending Intel hardware; IPEX-LLM is retired; LM Studio is optional user-installed API-only software. The Linux CUDA source build is evidence, not yet a consumer installation path.
8. Add conversion, activation, rollback, cleanup, and UI integration only for exact profiles that pass all promotion gates.

## Security hardening baseline (implemented)

The current baseline adds private vulnerability reporting guidance, CODEOWNERS, a security PR checklist, immutable GitHub Action pins, bounded CI jobs, CodeQL, fail-closed third-party installers, explicit endpoint trust scopes, redirect denial, bounded provider responses, secure prompt channels, exclusive artifact creation, and structured child-process execution. Branch and repository security controls are enforced in GitHub after the code lands.
