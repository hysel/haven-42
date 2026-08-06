# Roadmap

## Status

> **Current release:** Windows `0.4.0-alpha.1` is available as an unsigned
> prerelease for invited testing. It is not signed, installer-backed, stable,
> or production-ready.

### At a glance

| Area | Current position |
| --- | --- |
| Milestones 1–21 | Complete for their defined scope. Historical detail is collapsed below. |
| Milestone 22 | Active. The Windows Alpha is published; dependency, signing, broader lifecycle, and production gates remain open. |
| Milestones 23–27 | Active evidence tracks for images, audio, video, quantization, and local knowledge. Each capability remains independently gated. |
| Milestone 28 | Proposed. Controlled web research remains default-deny and runtime-unadmitted. |

Status terms are intentionally strict:

- **Complete** means complete only for the milestone's written scope.
- **Active** means work or evidence is still open.
- **Proposed** means no runtime capability has been admitted.
- **Gated** means implementation cannot proceed until the named security,
  evidence, owner, hardware, or external prerequisite is satisfied.

### Current priority order

1. Stabilize the published Windows Alpha from tester feedback and complete its
   exact packaged-dependency and license review.
2. Close remaining Milestone 22 release, lifecycle, and platform evidence
   without enabling signing, installers, automatic updates, or production
   promotion prematurely.
3. Advance Milestones 23–27 only through their independent hardware, security,
   cleanup, packaging, and source-versus-package gates.
4. Keep Milestone 28 offline and default-deny until its network and citation
   security boundaries are independently admitted.

`ROADMAP.md` explains direction and milestone boundaries. `TODO.md` is the
exact actionable checklist, and `config/roadmap-closure-ledger.json` ensures
every open parent task has one explicit blocker or work classification.

### Jump to active work

- <a href="#milestone-22-unified-product-ui-and-task-composition">Milestone 22 — Unified Product UI and task composition</a>
- <a href="#milestone-23-native-local-image-generation">Milestone 23 — Native local image generation</a>
- <a href="#milestone-24-local-music-and-audio-generation">Milestone 24 — Local music and audio generation</a>
- <a href="#milestone-25-local-video-generation">Milestone 25 — Local video generation</a>
- <a href="#milestone-26-hardware-adaptive-model-quantization">Milestone 26 — Hardware-adaptive model quantization</a>
- <a href="#milestone-27-local-knowledge-context-and-retrieval">Milestone 27 — Local knowledge context and retrieval</a>
- <a href="#milestone-28-controlled-web-research">Milestone 28 — Controlled web research</a>
- <a href="#security-hardening-baseline-implemented">Implemented security baseline</a>

<details>
<summary>Detailed current status and evidence</summary>

Every unchecked `TODO.md` parent item is covered exactly once by a fail-closed machine-readable closure ledger. It distinguishes local work from external evidence, upstream dependencies, owner decisions, prerequisite admissions, and signing or release gates so implementation cannot silently drift between milestones. The separately recovered 374-task conversation plan in `config/local-batch-task-ledger.tsv` is reconciled one to one: 360 completed, seven explicitly owner-deferred, seven partial, and zero unverified. Classification does not turn deferred or partial product work into completed scope.

Current owner decisions and their strict authority boundaries are recorded in
`docs/roadmap-owner-decisions.md`.

Windows Alpha `0.4.0-alpha.1` is published as an unsigned GitHub prerelease for
Windows 11 x64 and invited testers. Tag `v0.4.0-alpha.1` resolves to exact
validated commit `6624dfb967a58c67d2d5a9a01437cf3213eee289`. Its 16-stage
ledger covers server-enforced text-only Chat, Writing, and Summarization in one
continuous workspace,
readiness, consumer-driver guidance, pinned standalone Ollama and model
identities, current-user setup, prequantized selection, local metrics including
provider-reported generation speed, packaging, and gates. The prerelease remains
unsigned and not production-ready; signing, installers, automatic updates, and
production promotion remain separately denied.

A privacy-preserving Alpha usage report is prepared locally for weekly or
manual GitHub Actions execution. It records the exact uploaded Alpha ZIP and
supporting-asset download totals plus GitHub's aggregate 14-day clone/view
traffic only if a separately approved credential is introduced later. The
built-in workflow token cannot request the traffic API's required repository
Administration permission. The report collects no
identity or IP address, commits no metrics, uses only read-only repository
permission, and retains Markdown/JSON workflow artifacts for 30 days. Public
asset counts remain available without a stored credential.

Completed managed setups now have a fail-closed next-launch path: Haven
rebuilds the device-derived plan, verifies the completion receipt, runtime
inventory, publisher, exact model, managed directories, and loopback provider,
then opens the text workspace without a redundant connection step. Windows
readiness reports Windows 10 or Windows 11, build, architecture, accelerator
driver version, and bounded software probe versions. External provider setup
remains available as an explicit later choice.

The product and primary documentation now follow a novice-first standard.
Setup leads with one safe recommendation, defines local-AI terms in context,
explains downloads and permissions before approval, and places connection,
evidence, and engineering detail under clearly labelled advanced paths. A
shared glossary and automated policy checks keep later work aligned with this
standard.

One exact physical Windows 11 Intel Arc B580 cell now passes the unsigned Alpha
package's no-effect, managed first-run, and managed reuse paths. That evidence
includes immutable runtime/model verification, Intel Vulkan inference with
nonzero model VRAM, real Chat and token/resource reporting, unload, port
closure, and exact-process shutdown. It does not promote other Windows hardware
cells; CPU-only/low-memory, NVIDIA, and AMD coverage remain separate evidence
tracks. See `docs/windows-alpha-native-validation.md`.

Milestone 22A also includes explicit candidate-only public Ollama catalog
search without installation authority: the explicit submit action replaces a
redundant checkbox, installed and uninstalled states are labeled, changing the
target capability resets and re-ranks results, installed filtering stays
offline, uninstalled choices stay in browser memory with execution disabled,
and Haven 42 never executes the displayed pull instruction. System exposes all
four bounded cleanup policies and applies changes through the existing validated
provider connection. Wizard and workspace provider controls now share compact,
tested sizing and typography rather than diverging between setup surfaces.

The repository has entered user-visible product implementation. Milestones 1
through 21 are complete for their defined scopes.

Milestone 22A now ships a runnable local-web application and
security-hardened unsigned PyInstaller one-folder development packaging. It
includes sanitized system status, immutable-digest Ollama recommendations,
accessible private chat, writing, summarization and recovery, provider run
metrics, two bounded one-reviewer blind writing packets, plan-only registered
read-only software workflows, lifecycle-aware effect-free composition
planning, the promoted Linux ComfyUI/SDXL image flow, and verified cleanup on
Windows, Linux, and macOS.

Build inputs are hash-locked. Native hosted tests cover hostile resources,
shutdown authority, relocation, read-only startup, abrupt-exit recovery,
repeated lifecycle, occupied ports, hostile environments, bounded archive
structure, checksums, exact inventories, notices, SBOM, and unsigned
provenance. The owner-approved Windows `0.4.0-alpha.1` artifact is a public
unsigned prerelease bound to its exact commit, size, digest, hosted evidence,
and reporting routes. The main-push-only GitHub job continues to reverify and
attest unsigned development archives after native package success, with no
pull-request write authority, platform-signing, notarization, updater-trust,
or production claim.

The portable builder now embeds the Haven 42 license, generated third-party
notice, and exact hash-verified CPython, Apache 2.0, and libffi license texts in
the extracted package as non-signable distribution evidence. The immutable
published Alpha ZIP predates this correction; equivalent documents remain
available beside it as Release assets. Exact Microsoft runtime redistribution
clearance remains open, so this correction does not authorize signing or
production promotion. A fresh 41-file Windows rebuild passed exact inventory,
archive, parity, relocation, recovery, lifecycle, shutdown, and integrity
checks, and the builder now keeps PyInstaller cache beneath its ignored output
instead of the user profile. Build outputs cannot escape the repository's
ignored `dist` tree, and package links cannot resolve outside the bundle.

That fresh 41-file archive also passed a physical Windows 11 Intel Arc B580
non-administrator closure cell on 2026-08-06: exact transfer and extraction,
loopback and shutdown authority, approved portable Ollama/model setup, Vulkan
inference, Chat/Writing/Summarization metrics, zero-download relaunch,
sanitized logs outside managed components, human-filename attachment context,
disguised-script rejection, local/private-network/local switching, external
model unload, marker-owned uninstall, retained logs/application files, and
package-verified empty-state relaunch. A later closure candidate repeated fresh
managed setup, exact model validation, GPU-backed Chat, unload, shutdown, and
port closure on Windows AMD/ROCm and Windows NVIDIA/CUDA. It also passed the
trusted-LAN Ollama `0.32.6` Chat/Writing/Summarization switch and returned to
verified local AI with zero external models left loaded. A replacement archive
containing the resulting fail-closed relaunch-error correction passed package,
browser, and no-effect native selection/shutdown cells on all three Windows
accelerator families. These archives remain uncommitted unsigned development
evidence; exact Microsoft redistribution clearance, signing, and production
promotion remain open.

Public signing and privacy policies, a fail-closed SignPath audit,
deterministic Windows executable metadata, and build-time metadata verification
are prepared. Repository-account MFA was owner-confirmed on 2026-07-27.
Provider eligibility and future signing remain blocked by provider acceptance,
signing-service MFA, and exact dependency/license review.

Offline installer and update foundations model install, upgrade, uninstall,
compatibility, health, interrupted recovery, replay defense, rollback,
retention, disabled mode, a structural future-verifier receipt handoff, and
verifier registry/root transitions with every machine effect denied. A
cryptographic inventory and 37-case post-quantum readiness suite defines
hybrid-preferred TLS with a visible secure classical fallback plus
dual-signature candidates while activating no algorithm, dependency, key,
verifier, trust, or machine effect.

Separate 49-case execution-admission and 46-case digest-chained journal
simulators validate effect disclosure, typed intermediate metadata, digest-
and lifecycle-bound approval scope, retry, cancellation, bounded record time
and ordering, absent approval on non-execution paths, and blocked recovery.
They do not issue or accept a token, write a journal, or grant execution. A
20-case admission-readiness ledger separates the admitted unsigned/read-only
development scope from owner-deferred, policy-blocked, security-blocked, and
external-blocked promotion work without granting authority.

Platform signing, notarization, real updater cryptographic verification, PQC
activation, real installers, activated online updates, stable or production
promotion, workflow execution, executable composition, and optional Tauri
packaging remain separately gated.

Milestone 23 adds a 28-case effect-free lifecycle planner around its promoted
Linux image profile while keeping all three native Windows profiles partial
and unpromoted. Milestone 24 has partial Linux CUDA ACE-Step evidence, while
Milestone 25 remains documentation-only. Milestone 26 has its foundation plus
exact Linux/NVIDIA and Windows/AMD evidence. Milestone 27 admits bounded inert
CSV, JSON, source text, `.txt`, `.md`, and PNG. PDF and Office remain blocked;
an exact ignored `pypdf` wheel is exercised only by an offline synthetic-corpus
worker prototype with no runtime, UI, provider, dependency, or package
admission.

</details>

## Milestone status

<details>
<summary>Full milestone-by-milestone status table</summary>

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
| Milestone 22: Unified Product UI And Task Composition | In progress; Windows Alpha published | The shared local-web application and unsigned PyInstaller one-folder packages provide system status, inferred local/LAN Ollama scope, immutable-digest model selection, provider metrics, a bounded read-only committed-evidence view, accessible chat/writing/summarization recovery, plan-only read-only software workflows, lifecycle-aware effect-free composition, structural updater trust/transition and future execution/journal simulations, promoted loopback ComfyUI/SDXL images, hostile integrity and bounded-archive validation, native source/packaged browser parity on Windows/Linux/macOS, an additional least-privilege physical Windows Intel parity cell, bounded cleanup, and effect-free offline installer/update simulation. The owner-approved Windows `0.4.0-alpha.1` artifact is published as an exact-recorded unsigned prerelease. Broader human review, real cryptographic verification, workflow execution, executable composition, persistence, wider machine effects, signing, stable or production promotion, and Tauri remain gated. |
| Milestone 23: Native Local Image Generation | In progress | External provider engines, models, drivers, and installers are never bundled with Haven; users connect separately acquired compatible providers. The Linux ComfyUI/SDXL profile is live-validated and promoted; a 28-case effect-free lifecycle planner covers lifecycle outcomes without granting machine authority. Windows NVIDIA, AMD, and Intel have exact-profile evidence but remain independently gated. Runtime audits remain compatibility/security evidence and do not grant redistribution or package authority. Consumer onboarding, automatic idle shutdown, complete cleanup/parity, and Apple Silicon remain gated. |
| Milestone 24: Local Music And Audio Generation | Live feasibility in progress | ACE-Step has partial Linux CUDA evidence across V100 and Quadro profiles. The Quadro cell passes instrumental/vocal-request WAV structure, signal/clipping, cancellation, recovery, GPU-use, isolated retention, and review-only typed evidence. Listening, deletion/uninstall, a production adapter, package parity, and an upstream route-authentication fix remain open. |
| Milestone 25: Local Video Generation | Research and hardware preflight in progress | Exact HunyuanVideo, Wan2.2, and LTX-2.3 candidate records plus identity/media consent policy are complete. A Quadro RTX 5000 preflight rejected Wan2.2 for VRAM, LTX-2.3 for VRAM/storage, and HunyuanVideo for insufficient safe storage before downloading any runtime or model. No live provider is promoted. |
| Milestone 26: Hardware-Adaptive Model Quantization | Engine evidence expanded | Exact Ollama comparisons passed on Linux NVIDIA and Windows AMD; llama.cpp CUDA and HIP passed their exact profiles. The same hash-pinned 11-model portable GGUF corpus passes b10088 execution, full-offload, bounded-exit, and cleanup gates on Windows AMD/HIP and Linux NVIDIA/CUDA, with matching exact-output outcomes. Separate Windows NVIDIA and Windows AMD follow-ons record patch, context, repeated-lifecycle, vision, and direct structured tool-call outcomes without promoting failed quality cells. A 62-check structured tool-transport parser validates exact final Ollama 0.32.5 and normalized OpenAI-compatible candidate shapes while granting no execution, approval, provider, or runtime authority. A bounded manual live run passed four tool-capable installed models and correctly classified one unsupported model; it retained no content and unloaded every tested model. Physical Intel Arc B580 candidate evidence covers Linux llama.cpp SYCL plus Linux and Windows OpenVINO GenAI. A native Windows llama.cpp SYCL cell passed exact artifact preflight but was rejected after zero-free-memory reporting, tensor-load failure, and an OpenCL fallback fast-fail; no engine is promoted. Vulkan failed the patch gate. |
| Milestone 27: Local Knowledge Context And Retrieval | Bounded attachment slice and offline history/retrieval/parser foundations in progress | Explicit bounded text, structured-text, source-code, and PNG attachments are admitted and pass source/native-package browser smoke on Windows, Linux, and macOS. Retrieval, history, PDF, Office, OpenDocument, folder scanning, embeddings, OCR, persistence, physical macOS clipboard evidence, and complex-document UI remain independently gated. |
| Milestone 28: Controlled Web Research | Proposed; runtime unadmitted | Default-deny contracts plus offline result, page-text, citation, and cited-synthesis hostile suites exist, but no model invocation, model tool, renderer route, DNS, network, page retrieval, active citation, or autonomous follow-up authority is admitted. |

</details>

## Completed milestone details

<details>
<summary>Milestones 1–21 (completed for their defined scope)</summary>

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
- Track Moonshot AI's Kimi family as documentation-only experimental and
  untested because the flagship checkpoints exceed the current validation
  hardware. Accept sanitized community evidence from suitable hardware for
  review without adding Kimi to active catalogs, recommendations, installers,
  providers, or support claims before the exact profile passes every promotion
  gate. Done as a documentation and evidence-submission boundary; no Kimi
  compatibility validation is claimed.
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

</details>

## Active and proposed milestone details

## Milestone 22: Unified Product UI And Task Composition

Goal: Provide one local-first product surface over the completed engineering workflows and general-purpose capability platform without reimplementing their business logic or weakening their safety boundaries.

Scope:

- Continue using the shared browser UI and the minimum trusted PyInstaller
  launcher/service for ordinary desktop operation. Keep Tauri/Rust unadmitted
  unless a future owner decision explicitly reopens its independent security
  and dependency gates.
- Permit only registered capability and workflow IDs through the loopback
  service's narrow typed routes; ship no arbitrary shell bridge, unrestricted
  filesystem API, remote UI code, or non-loopback listening port.
- Keep hardened loopback/browser operation as the common tested Windows,
  Linux, and macOS product surface.
- Implement the unified web UI over stable workflow IDs, capability IDs, typed artifacts, and versioned request/result envelopes.
- Keep chat as the primary interaction surface with compact sticky navigation and provider/system configuration. Done for the local web slice; responsive contract and visual regression coverage remain part of each UI change.
- Present Chat, Writing, and Summarization through one continuous conversation
  instead of destructive mode tabs. Done with narrow browser-memory intent
  hints, capability-specific server prompts and evidence, preserved bounded
  messages, and an explicit keep-or-switch decision before a different model
  can be used.
- Keep exactly one primary content panel visible, provide dedicated Models and About views, and support conventional Enter-to-send with Shift+Enter for multiline input. Done with headless-browser visibility, focus, heading-boundary, selection, and keyboard regressions.
- Evaluate text models independently for chat, writing, and summarization. Done for the bounded exact-artifact evaluation without comparative promotion. The engine automatically selects only an installed model name and immutable digest with matching passed capability evidence. Qwen 3.5 9B remains the exact adapter baseline, not a best-writer claim. The repeated Qwen, Gemma, Mistral, and Granite automated constraint matrix passed 9/9, 9/9, 9/9, and 6/9 cases respectively with verified unloads. Two randomized three-scenario packets captured forced rankings from one reviewer, with Qwen leading the first and Granite the second. Further comparative review is owner-deferred unless end users report inconsistency.
- Present deterministic first-run choices for chat, writing, summarization, image creation, software work, and local-AI setup. Done for Guided setup, Connect existing setup, and Explore in the admitted local-web slice; broader capability-specific onboarding remains open.
- Detect sanitized local operating system, architecture, CPU count, memory, storage, accelerators, and registered software only after explicit consent. Done with bounded shell-free, network-free probes, memory-only snapshots, hostile-input tests, and a CSRF-protected API. Installed models remain provider-scoped discovery after an explicit connection. Existing Ollama endpoints may use fixed memory-only Bearer or X-API-Key authentication; authenticated private-network traffic requires HTTPS, arbitrary headers and URL credentials remain blocked, and secrets are omitted from every response and evidence record.
- Build an engine-owned setup plan from the exact current readiness snapshot. Done as a zero-effect, disabled-installation plan; real downloading, verification, elevation, install, rollback, and uninstall remain unadmitted. The inactive Ollama install contract now requires loopback-only Ollama by default and a separately reviewed HTTPS gateway for private-network use, with a locally generated certificate option gated by exact-IP SAN, explicit trust, key protection, negative TLS tests, rotation, rollback, and exact cleanup.
- The admitted local-web slice exposes five truthful capability states: Chat, Writing, and Summarization require a validated exact provider artifact; Software admits registry-backed read-only plans without arguments or process execution; Images admit only the promoted Linux ComfyUI/SDXL profile through a loopback endpoint with browser-memory delivery and explicit provider-retention disclosure.
- Present beginner recommendations and advanced model controls from one engine-derived catalog decision that combines exact artifact identity, license, hardware fit, provenance, and evidence without allowing the renderer to promote a model.
- Let users filter installed models locally and explicitly search the fixed public Ollama catalog. Done with bounded query/response controls, candidate-only results, browser-memory desired selection, disabled execution until installed inventory verification, and a copyable command that Haven 42 never executes.
- Support repository-optional sessions and clearly identify every artifact location before a write.
- Show capability availability, evidence status, local versus external execution, network effects, repository access, and approval requirements before execution.
- Reuse the Milestone 20 evidence dashboard, health, cleanup, recommendation, installation, validation, and release-readiness workflows. Done for one shared cross-platform evidence engine plus a bounded read-only committed-evidence UI summary; live validation, installation, and release-readiness execution remain gated.
- Reuse Milestone 21 routing and provider contracts; keep LLM routing advisory and policy enforcement deterministic.
- Add a cross-platform core-engine updater that can check for, stage, and optionally install stable releases published by the official GitHub repository. Never update a production installation with an unattended `git pull` or from a moving branch.
- After the Windows Alpha, add opt-in update discovery for Haven-managed
  components such as the Ollama runtime, accelerator support package, and
  models. Alpha packages must continue using exact reviewed versions and must
  never interpret an upstream "latest" version as approved. A future component
  catalog must distinguish the installed version, current Haven-tested version,
  a newer Haven-tested update, and an upstream version that has not passed Haven
  compatibility and security review. Only immutable catalog entries may become
  eligible for an explicitly approved download.
- Separate immutable engine files from user workspaces, local configuration, models, provider data, generated artifacts, and evidence so an engine update cannot overwrite user-owned state.
- Add accessible progress, warning, failure, retry, and recovery experiences over the versioned workflow envelope. Done for strict local-web text envelopes, visible unverified-model warnings, typed failures, and memory-only input restoration that requires a new request; broader workflow execution remains open.
- Before invited Alpha distribution, add bounded privacy-safe diagnostic logging
  under the sibling portable directory `Haven42-Logs` with immediate writes for important lifecycle
  transitions, rotation and storage limits, sanitized stable event/reference
  IDs, setup and integrity outcomes, component versions, hardware-selection
  decisions, owned-process lifecycle, and clean versus observed-abnormal
  shutdown state. Add novice-facing Troubleshooting controls to view recent
  activity, copy one error's safe details, create an explicitly saved sanitized
  support report, and clear logs. Never record prompts, responses, attachment
  content or names, credentials, full endpoints, usernames, hostnames, personal
  paths, environment values, commands, or arbitrary child output. Nothing is
  uploaded automatically. Removing managed components must never delete
  `Haven42-Logs`; full uninstall must present logs as a separate explicit removal
  choice. The fixed-schema event writer, two-file rotation, unclean-session
  marker, local support-report creation, separate clear/remove controls, and
  hostile privacy tests are implemented. Fixed-code backend, exact registered
  component/version, model-selection, interrupted-write recovery,
  insufficient-space, and storage-write-failure events are implemented without
  accepting arbitrary diagnostic details. Packaged UI parity and owner review
  remain release gates.
- The same Troubleshooting surface should provide **Report this answer** using
  only a sanitized local event reference, model artifact identity, capability,
  app/runtime version, selected issue category, and optional tester note. It
  must not capture or upload the prompt, response, attachments, or conversation;
  sharing redacted content remains a separate explicit tester action. Done in
  the source UI with a per-answer action, fixed issue categories, a bounded
  optional note, exact model digest/task/runtime metadata, a local event
  reference, local-only report storage, and hostile/browser privacy tests.
  Packaged UI parity and owner review remain gates.
- Render typed text artifacts and progress/result/error states in the admitted local-web slice without granting filesystem authority. Done for admitted text artifacts, warning/failure/recovery states, and an active Stop control that closes only the exact tracked provider stream, unloads the active model, discards partial output, and restores the prompt; broader workflow and artifact-location UI remain open.
- Apply one compact universal response policy to Chat, Writing, and
  Summarization: preserve explicitly supplied individual pronouns exactly; when
  none are supplied, use the person's name or a neutral noun and never assign
  an individual pronoun, including singular they/them; no unsupported
  sensitive-trait inference, no
  stereotypes, explicit separation of supplied facts and assumptions, visible
  uncertainty, no invented browsing/file/execution claims, no unnecessary
  secret repetition, cautious high-stakes guidance, safe framing of destructive
  commands, and preservation of source meaning. Prompt delivery and hostile
  deterministic tests are implemented. A reusable digest-bound native runner
  completed the fixed 30-cell matrix twice against exact `qwen3.5:9b`. The
  first run exposed invented credential-shaped text in Writing. After a prompt
  remediation, Writing repeated that finding and Chat assigned singular `they`
  to an invented individual. These remain advisory model-quality evidence and
  do not override the approved hardware-based automatic default. The ten
  Summarization cells completed without an observed violation during agent
  pre-review; owner review remains required. Every future exact model considered
  for automatic selection should run the same fixed matrix. Default eligibility,
  hardware routing, or model-policy changes require explicit owner approval.
  Candidate-only critical screens also rejected exact Gemma 3 12B and Mistral
  Small 3.2 24B for Writing. Exact Qwen 3.5 4B advanced to the full Writing
  matrix but then failed no-pronoun, explicit-pronoun, and credential-handling
  cases. None earned a higher quality ranking than the current default.
  Treat these instructions as behavior guidance only, never as the security
  boundary.
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
- Windows signing readiness now has a public inactive policy, privacy statement,
  fail-closed SignPath eligibility audit, CODEOWNERS protection, deterministic
  `haven42.exe` identity metadata, and build-time metadata verification.
  Exact runtime-component evidence now covers every packaged file, rejects
  unclassified paths and evidence divergence, expands the SBOM/notices, and
  excludes all upstream components from Haven 42 signing scope.
  Native runner labels, Python 3.14.6, the immutable `setup-python` action, and
  each official platform archive digest are now fixed and provenance-bound.
  Windows CPython, OpenSSL, and libffi source/version chains plus their exact
  license evidence are recorded. Two retained Visual C++ runtime DLLs match
  the official Python.org distribution. A stale local package containing 39
  host-derived JDK UCRT/API-set files is rejected. Its replacement 31-file
  local build passes independent artifact verification and the native package
  gate. GitHub Actions run `30297195387` then reproduced and verified the
  unsigned package on clean hosted Windows, Linux, and macOS runners at exact
  main commit `04baca39b26ec58c189a6ae21ea78b507444e9fa`; applicable Microsoft
  redistribution review and repetition for any later release candidate remain
  open.
  The public unsigned Alpha supplies an exact binary form for provider review,
  but eligibility remains externally blocked until the exact packaged
  dependency/license inventory is cleared and the provider accepts the project
  with signing-service MFA. Repository-account MFA was
  owner-confirmed on 2026-07-27. No signing, stable publication, or production
  promotion is active.
- A failed update automatically restores the previous known-good engine. Offline use remains available, update checks can be disabled, stable is the default channel, and automatic installation is an explicit user choice.
- Post-Alpha managed-component updates require network disclosure and explicit
  user approval, exact size and SHA-256 verification, expected publisher
  signature verification where applicable, safe archive inspection,
  hardware/driver/model compatibility preflight, side-by-side staging inside
  `Haven42-Data`, a local health test, atomic activation, and automatic rollback
  to the retained known-good version. Models use a separate decision because an
  update can be large and can change behavior or hardware requirements.
  Unreviewed upstream versions remain visible only as unsupported information
  and cannot be downloaded or activated by Haven 42. Drivers, firmware,
  Windows components, certificate stores, firewall rules, and services remain
  outside automatic update authority.
- Windows, Linux, and macOS contract tests cover routing, workflow dispatch, artifacts, failures, recovery, and safe composition.
- Invited Alpha errors expose a stable reference ID that maps to bounded local
  sanitized diagnostics, and a tester can create a support report without
  exposing chat content, attachments, credentials, identities, endpoints, or
  personal filesystem paths.

### Recommended Implementation Order

1. Select the local UI runtime and package boundary without introducing a
   hosted-service dependency. Done with the shared browser UI and unsigned
   PyInstaller one-folder development launcher/service on Windows, Linux, and
   macOS. Tauri/Rust remains unadmitted.
2. Define and validate the loopback route/resource allowlists, request
   contracts, path-free browser selection boundary, local-only content policy,
   lifecycle authority, and package integrity. Done for the admitted
   development surface; any future native bridge remains an independent
   promotion decision.
3. Validate pinned dependency and license choices, then scaffold the smallest Windows, Linux, and macOS package slice. Direct candidates are reviewed; disposable Windows npm and PyInstaller graphs passed, while five Windows-reachable unmaintained Rust crates, unaudited native build prerequisites, and separate Linux findings block admission.
4. Implement first-run navigation and capability availability views over the Milestone 21 registry. The local-web renderer now provides keyboard-accessible Guided, Existing, and Explore paths, explicit read-only readiness scanning, a disabled setup plan, five engine-derived capability states, and policy disclosures; the framework-neutral contracts remain the source of truth and the native renderer remains gated.
5. Assemble the model-selection view data without visual UI work. Done with a versioned read-only catalog, fail-closed per-artifact license policy, hardware-fit labels, revision-bound evidence, shared beginner/advanced decisions, hostile-input tests, and OS-aware wrappers.
6. Connect setup, health, model choice, engineering workflows, and evidence views from Milestone 20. Readiness inspection, zero-effect setup planning, the provider wizard, exact-digest text recommendations, provider metrics, typed text results with safe DOM-built Markdown and Unicode emoji, configurable task-bound prompt recall, provider health, a shared cross-platform evidence dashboard engine, a bounded read-only committed-evidence view, disabled-update status, and registered read-only workflow planning are done; real installation, live validation, and workflow execution remain.
7. Add repository-free text and image flows only for providers promoted in Milestone 21 or Milestone 23. Done for admitted text tools and the promoted Linux ComfyUI/SDXL profile; other image profiles remain independently gated.
8. Implement the GitHub release updater with explicit channels, network disclosure, immutable asset selection, checksum and signature or attestation verification, compatibility preflight, atomic activation, post-update health checks, rollback, and retained-version cleanup. The offline candidate and lifecycle policies now validate strict release fixtures and model healthy, failed-health, interrupted, rollback, retention, and disabled paths while denying network, download, writes, staging, activation, cleanup, and every other machine effect. A 30-case structural trust handoff binds a future verifier receipt to exact verifier/release/asset/platform/lifetime/replay metadata. A separate 33-case transition model checks consecutive verifier-registry versions, validity overlap, exact verifier continuity, active-root continuity, current-root threshold claims, and replay. A cryptographic inventory and 37-case post-quantum readiness suite add an inactive hybrid-preferred `X25519MLKEM768` TLS candidate with visible secure classical fallback, an unselected dual classical/ML-DSA update-signature candidate, an SLH-DSA alternative, downgrade rules, and exact activation gates. None performs cryptographic verification, accepts authorization, changes trust or TLS policy, handles keys, or stages an asset. Actual acquisition, trusted cryptographic verification, PQC selection, staging, activation, and rollback remain unadmitted.
9. After Alpha completion, implement a separate managed-component update catalog
   and UI over exact reviewed Ollama/runtime/model entries. Keep checks manual by
   default, identify but never activate unreviewed upstream releases, require a
   fresh approval for each download, stage versions side by side, validate them
   locally, retain the prior version for rollback, and clean retained versions
   only with explicit consent. Do not place driver or operating-system updates
   in this channel.
10. Add cross-platform UI contract, updater, rollback, packaging, signing, and uninstall tests. Source browser UI and native packaged browser/parity smoke coverage now run on Windows, Linux, and macOS; offline updater/rollback/uninstall policy tests remain effect-free, while signing/notarization and real lifecycle tests remain gated.
11. Add bounded multi-step composition with explicit intermediate artifacts and approvals. The registry-backed dependency planner, cancellation-before-execution, and metadata-only intermediate references are done. A 49-case effect-free admission model validates exact workflow effects, typed intermediate metadata, digest- and lifecycle-bound engine approval scope, expiry/replay state, retry, cancellation, absent approval on non-execution paths, and blocked recovery. A 46-case digest-chained journal model binds later scenario records to that scope and rejects cross-admission reuse, forged completion, future or reordered records, understated cancellation risk, unsafe retry, and uncertain recovery while treating every claimed event as untrusted. Neither accepts a token, writes a journal, or grants execution. Native opaque-token issuance, executable dispatch, durable effect journaling, runtime cancellation/retry/recovery, and rollback remain gated.

## Milestone 23: Native Local Image Generation

Goal: Let ordinary Windows, macOS, and Linux users generate images on their own computer without requiring an external server, while preserving the exact evidence boundary already proven by the Linux ComfyUI/SDXL provider.

Current validated baseline:

- ComfyUI `v0.28.2` at the pinned validated commit, PyTorch `2.11.0+cu126`, SDXL Base 1.0 with its verified checksum, a localhost-only hardened Linux service, typed PNG artifacts, metadata exclusion, history cleanup, forced recovery, SSH tunneling, and visual validation passed on Linux with an NVIDIA V100.
- The provider-neutral `media.image.create` capability and `comfyui.local-image` adapter are live-validated for that exact Linux scope. Cross-platform fixture contracts do not promote native Windows or macOS execution.
- ComfyUI v0.29.2 NVIDIA portable with SDXL Base 1.0 passed an exact Windows 11/Quadro RTX 5000 development cell for integrity, CUDA detection, loopback binding, hardened startup, typed generation, PNG inspection, repeated runs, invalid-workflow handling, active cancellation, exact-process forced recovery, retention cleanup, and secure shutdown. This is partial evidence only; the UI and provider registry remain unchanged.
- The same Windows NVIDIA cell passed an immutable side-by-side update to the
  hash-verified ComfyUI v0.30.0 NVIDIA portable and rollback to the untouched
  v0.29.2 runtime. Both versions passed the production adapter, typed PNG,
  metadata/history cleanup, bounded idle-stability, exact-process shutdown,
  and endpoint-closure gates. Automatic updating, idle shutdown, uninstall,
  package parity, redistribution review, and profile promotion remain open.
- ComfyUI v0.30.0 Intel portable with the same exact SDXL checkpoint passed a
  native Windows 11/Arc B580 XPU development cell for archive and checkpoint
  integrity, runtime and service XPU identity, loopback binding, hardened
  startup, typed generation, metadata exclusion, repeated-run stability,
  invalid-workflow recovery, active cancellation, exact-process forced
  recovery, history cleanup, and shutdown. This remains a partial profile;
  no runtime, model, installer, registry entry, or UI route is admitted.
- The Windows AMD cell passed an immutable side-by-side update from the
  hash-verified ComfyUI v0.28.0 AMD portable to v0.30.0 and rollback to the
  untouched v0.28.0 runtime. Both versions independently confirmed the exact
  HIP/PyTorch and RX 7800 XT identity and passed the production adapter, typed
  PNG, metadata/history cleanup, bounded idle-stability, exact-process
  shutdown, and endpoint-closure gates. Automatic updating, idle shutdown,
  package parity, redistribution review, and profile promotion remain open.

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
3. Complete the partially passing Windows NVIDIA CUDA, Windows Intel XPU, and Windows AMD profiles using separate pinned environments and evidence. Windows NVIDIA generation, cancellation, exact-process recovery, repeated-run, retention-cleanup, and shutdown cells passed on 2026-08-01; an exact v0.30.0 side-by-side update and v0.29.2 rollback passed on 2026-08-03. Windows Intel v0.30.0 passed XPU identity, generation, repeated-run, invalid-workflow, cancellation, forced-recovery, metadata/history-cleanup, idle-stability, and shutdown cells on 2026-08-03; an exact v0.29.2 rollback and v0.30.0 forward-selection transition then passed on the same machine. Windows AMD passed comparable core cells plus uninstall on 2026-07-23, followed by an exact v0.30.0 side-by-side update and v0.28.0 rollback on 2026-08-03. Consumer onboarding remains unadmitted; Intel complete cleanup/uninstall, automatic idle shutdown, package parity, and redistribution review remain open where applicable.
4. Validate Apple Silicon MPS on a physical Mac only after suitable hardware is
   acquired. This gate is owner-parked; it does not block continued Windows or
   Linux development and must not be inferred from hosted macOS CI.
5. Add installer and lifecycle automation only for each exact passing profile. A strict effect-free planner and hostile suite now model install, update, failed-health recovery, rollback, retention, interruption, and uninstall for `tested-passed` profiles only; candidate profiles, raw authority, scenario evidence, and every machine effect remain blocked.
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
2. Complete the ACE-Step 1.5 Linux CUDA gate. REST health, deterministic instrumental and vocal-request WAV structure, signal/clipping analysis, GPU execution, exact-process cancellation, restart recovery, isolated retention, and review-only typed evidence pass across exact V100 and Quadro profiles. Human listening, retention deletion, complete uninstall, production adapter/package parity, and a production fix for the upstream unauthenticated shadowing `/v1/models` route remain. This evidence does not promote Windows or macOS.
3. Evaluate Stable Audio 3.0 Small and Medium independently for sound effects, instrumental music, editing, duration, licensing, and consumer hardware fit.
4. Run separate native profiles for Windows NVIDIA CUDA, Windows Intel XPU,
   Windows AMD ROCm, and Apple Silicon MLX as hardware becomes available.
   Continue with the available Linux CUDA machine; physical Apple Silicon is
   owner-parked until hardware is acquired.
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
5. Run separate native Windows and macOS profiles only when credible
   provider-specific paths and suitable hardware are available. Continue
   research and any bounded feasibility work on the available Linux machine;
   physical macOS validation is owner-parked until hardware is acquired.
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
6. Add Windows NVIDIA, Windows Intel, Windows AMD, and Apple Silicon paths only
   when an exact runtime and format have credible native support. Windows AMD is
   done for Ollama 0.32.1, its packaged ROCm 7.1 backend, an RX 7800 XT 16 GB
   profile, Qwen 3.5 9B Q4_K_M versus Q8_0, a 4,096-token context, and
   concurrency one. Windows NVIDIA now has candidate-only b10088/CUDA evidence
   for exact identity, full offload, baseline execution, strict patch,
   repeated lifecycle, and Gemma vision. Qwen 3 8B failed both bounded context
   recall cells and its strict patch cell. A 40-check offline structured
   tool-transport foundation accepts only one allowlisted, bounded call from
   exact Ollama or OpenAI-compatible response shapes, while all provider,
   approval, execution, package, and runtime authority remains false. The
   bounded manual Ollama provider-envelope run is complete. Direct b10088
   llama.cpp tool-call cells pass independently on the exact Windows
   NVIDIA/CUDA and Windows AMD/HIP profiles with loopback-only authenticated
   transport, full offload, no tool execution, and exact shutdown. Runtime
   integration remains open. A physical Intel Arc B580 supplies candidate-only Linux
   llama.cpp SYCL evidence plus Linux and Windows OpenVINO GenAI evidence.
   A native Windows llama.cpp SYCL attempt passed exact artifact preflight but
   failed model loading after zero-free-memory reporting; a bounded OpenCL
   fallback fast-failed, so the profile remains rejected. Physical Apple Silicon is
   owner-parked until hardware is acquired. WSL2 Ubuntu 24.04 now has
   candidate-only llama.cpp HIP/DXG evidence on the RX 7800 XT: all 11 pinned
   artifacts passed the bounded operational matrix with full model-layer
   offload, while the same four passed the strict exact-output cell. This does
   not establish native Linux AMD support.
7. Separate capability, provider contract, inference engine, hardware backend,
   and model artifact selection. Done with a fail-closed registry. llama.cpp
   CUDA passed bounded engine checks on the exact Linux NVIDIA RTX 5000
   profile, and HIP passed on the exact Windows AMD profile. WSL2 DXG/HIP
   remains a separate candidate profile; Vulkan failed the
   Windows AMD Git-applicable-patch gate and remains documentation-only.
   Physical Intel Arc B580 tests remove the hardware blocker for Linux
   llama.cpp SYCL and Linux/Windows OpenVINO GenAI, but both engines remain
   candidate-only: llama.cpp passed 50 of 53 upstream tests, while OpenVINO's
   Linux host was outside its documented OS baseline and its small control
   model missed strict output constraints on both systems. Native Windows
   llama.cpp SYCL additionally failed model loading and remains rejected.
   IPEX-LLM is retired;
   LM Studio is optional user-installed API-only software. No source-built or
   portable candidate engine is yet a consumer installation path.
8. Add conversion, activation, rollback, cleanup, and UI integration only for exact profiles that pass all promotion gates.

## Milestone 27: Local Knowledge Context And Retrieval

Goal: Let an end user explicitly add selected local documents to a text task without granting Haven 42 general filesystem authority, silently scanning the machine, or obscuring when document content crosses to a private-network provider.

Current status: The explicit bounded `.txt`/`.md`/`.csv`/`.json`, narrow source-text, and browsed-or-pasted PNG attachment slice is implemented with path-free selection, type/content checks, inert previews, compact scrolling, removal, memory-only cleanup, warned private-network transfer, and native Windows plus Ubuntu evidence. The current admitted attachment slice passes source and native packaged browser smoke on Windows, Linux, and macOS. Physical macOS clipboard validation remains owner-parked. The deterministic lexical-retrieval core now reports matching, selected, omitted, and truncation-reason counts; it and the optional conversation-history lifecycle/encryption architecture remain offline and inactive with no route, application database, provider, or persistence authority. A fixed-synthetic-record SQLite development validator now covers parameterized access, backup/read-only restore, cascade deletion, permissions, and residue cleanup only in a fresh temporary directory. A separate explicit-folder development inspector is non-recursive by default, bounded, descriptor-based, link/reparse-safe, and metadata-only. Neither is connected to the runtime, UI, provider, or package; semantic embeddings and an encrypted persistent library remain unselected gates. A 27-case metadata-only parser boundary covers PDF, Office Open XML, and OpenDocument candidate identities. The exact ignored `pypdf` 6.14.2 artifact is exercised only by an offline review worker that passed 61 corpus security, 64 static, and 40 contract-parity/package-exclusion checks with Windows and Ubuntu source evidence. A production-isolation assessment plus a 37-check exact OS-control evidence gate now rejects WSL2 as native Linux evidence and keeps missing sandbox controls explicit. A native Ubuntu KVM availability probe found all five required Linux isolation primitive categories, but implementation, enforcement, hostile escape testing, and source/package parity remain false, so admission remains denied. Metadata-only corpus research still selects no artifact, and the intake/parity gates remain offline and false. The bounded standard-library Office/OpenDocument foundation passes 49 container checks across 24 fixtures, including empty, disguised, whitespace-obscured, or encoded external URI and relationship traversal cases, 62 semantic checks across 19 fixtures, and 33 source/package-exclusion checks with Windows and Ubuntu source evidence, without archive extraction or a dependency. Three deterministic PDF compliance files are generated only beneath ignored local review. No user document, dependency, application route, UI, provider path, package, installer, updater, or release uses either prototype. macOS source evidence, admitted non-synthetic hostile review, implemented production isolation, remaining semantic fidelity, actual package compliance integration, native package parity, and explicit admission remain open. Vision promotion, broader image conversion, runtime folder scans, active retrieval, embeddings, encrypted history, and runtime persistence remain unadmitted.

Scope:

- Begin with an explicit multi-file browser picker. Do not add automatic discovery, background indexing, file watching, operating-system search, arbitrary path entry, or whole-machine scanning.
- Let the browser transfer only user-selected bytes to the loopback service. Strip path metadata, reject traversal-like names, and never expose a generic read-path API to the renderer or model.
- Admit a minimal initial unified file-picker allowlist: UTF-8 plain text, Markdown, bounded CSV/JSON, the separately reviewed inert `.cs`/`.py`/`.js`/`.jsx`/`.ts`/`.tsx`/`.java`/`.go`/`.rs`/`.sql`/`.tf` source-text set, and bounded PNG screenshots. Clipboard PNG shares the same screenshot validation path. Reject shell, PowerShell, batch, binary, project, archive, configuration, other image, non-PNG clipboard, PDF, Office, OCR, malformed-encoding, and unsupported formats until each boundary passes independent review.
- Treat clipboard MIME representation as browser- and platform-dependent. Detect and report the representation supplied by the browser without logging clipboard content or platform-private metadata. Do not claim native Windows, Linux, or macOS compatibility from synthetic browser events alone.
- Keep PNG as the canonical screenshot representation. Evaluate JPEG and WebP clipboard input only through a separately reviewed, bounded browser-decoding and PNG-normalization path; reject TIFF and any representation the browser cannot safely normalize. Conversion must not add a native clipboard library, OS integration, filesystem write, remote codec, metadata leak, or new launcher authority.
- Enforce strict per-file, total-byte, file-count, extracted-text, chunk-count, request-context, and processing-time limits. Parsing and deterministic chunking remain local and memory-only.
- Treat every broader document parser as a separate dependency and attack boundary. Extraction must run in a restricted worker with no network, shell, child-process, arbitrary path, provider, model, or filesystem-write authority; use bounded input/output, memory, CPU, wall-clock, page/part/entry counts, compression ratios, recursion, and cancellation. A parser crash or timeout fails closed and leaves no temporary file or partial context.
- Never open an attachment through Microsoft Office, LibreOffice, Preview, a PDF viewer, the OS shell, or another installed application. Never execute document JavaScript, actions, macros, formulas, links, embedded files, OLE objects, external relationships, or model-produced code.
- For PDF, begin with text extraction from unencrypted, structurally valid documents only. Reject passwords/encryption, JavaScript, actions, launch instructions, embedded or associated files, external references, malformed cross-reference structures, excessive pages/objects, and decompression abuse. Scanned-image PDF and OCR remain a later independent gate.
- For Office, begin with non-macro Open XML only and parse package parts without invoking Office. Reject macro-enabled formats (`.docm`, `.xlsm`, `.pptm`, macro-enabled templates/add-ins), legacy binary formats (`.doc`, `.xls`, `.ppt`), encrypted packages, external relationships, embedded/OLE objects, unsafe or duplicate ZIP member names, excessive compression/parts, and unsupported custom content. Review `.docx`, `.pptx`, and `.xlsx` independently because their extraction and presentation semantics differ.
- Show extracted provenance appropriate to the format—filename plus page, slide, sheet, or bounded part—and let the user review extracted text, omissions, truncation, and rejection reasons before it can enter a provider request.
- Pin and review every parser and codec dependency. Packaging promotion requires hashes, dependency inventory, license review, third-party notices, CycloneDX SBOM inclusion, known-vulnerability review, source-versus-packaged parity, and exact native evidence on each supported target.
- Start with exact-content attachment for small inputs and deterministic lexical retrieval for larger admitted text. Local embeddings, an additional embedding model, and semantic indexing remain separate evidence gates.
- Show every admitted, partially admitted, or rejected file; extracted-text preview; size; estimated token cost; truncation; selected chunks; and removal controls before execution.
- Treat document content as untrusted data. Document instructions cannot choose tools, commands, providers, models, approvals, paths, network destinations, or product policy.
- Disclose the execution destination. Private-network providers require a prominent warning that selected content will leave the current machine; deliberate Send after that warning is the confirmation, with no separate checkbox. Public provider destinations remain blocked.
- Keep source bytes, extracted text, chunk indexes, document identifiers, and retrieval results in process/browser memory only. New task, provider change, model change, explicit removal, and shutdown clear them.
- Defer any persistent knowledge library until encrypted storage, key handling, migration, corruption recovery, deletion, export, backup, multi-user, and uninstall semantics pass separate approval and native evidence.

### Optional Local Conversation History Database

- Use an embedded SQLite-compatible database as the initial architecture
  candidate; require no database server, administrator access, system service,
  global runtime, or browser-owned database. The trusted loopback service owns
  every database operation.
- Keep conversation persistence disabled by default until separately promoted.
  Preserve a clearly visible **Private session** mode that never creates or
  updates a history record and retains the current memory-only behavior.
- Expose only typed, parameterized, allowlisted operations such as create,
  rename, list, load, append, retention update, delete, clear all, backup, and
  restore. The renderer and model cannot submit SQL, database paths, filenames,
  migration commands, or arbitrary filters.
- Version a bounded schema for conversations, ordered messages, locally
  generated context summaries, model/capability identity, sanitized token and
  timing metadata, retention policy, and attachment references. Do not store
  credentials, provider endpoints, usernames, machine paths, environment
  values, model-generated commands, or raw security logs.
- Keep attachment bytes out of history by default. Saving an attachment requires
  a separate explicit choice, content/type/size validation, a disclosed storage
  effect, and independent deletion semantics. Never save a live path or silently
  reread the original file. If separately admitted, retain a conversation-owned,
  encrypted snapshot of the exact validated bytes plus safe name, media type,
  digest, size, validation version, and message binding. Text, CSV, and JSON may
  use the admitted normalized UTF-8 snapshot; image context requires the exact
  admitted canonical image bytes rather than a misleading thumbnail. A saved
  message must never expand its original file-selection grant.
- When a saved conversation is reopened, show which attachment snapshots are
  available and which will be resent before the next provider request. If bytes
  were not retained, were deleted, or fail integrity validation, mark that
  context unavailable and do not imply that the model received it. Never
  silently add attachments from another message or conversation.
- Provide per-conversation retention choices, permanent delete, clear all,
  database-size limits, and predictable uninstall behavior. Deletion must cover
  messages, summaries, attachment references, indexes, free-page handling,
  backups, and temporary journal/WAL files under a documented threat model.
- Use recent bounded messages directly and, only after separate validation, a
  locally generated summary for older context. Show exactly which saved
  messages or summary will be sent to the selected model; never silently send
  unrelated conversations.
- Treat standard SQLite as unencrypted at rest. Do not promote saved private
  content as secure storage until a reviewed encryption design passes. Evaluate
  SQLCipher or an equivalent maintained SQLite-compatible implementation,
  operating-system credential storage for keys, key loss and rotation,
  locked-device behavior, backup/restore, and cross-platform packaging.
- Restrict database and key material to the current operating-system user.
  Define Windows, Linux, and macOS data locations separately from immutable
  application files, models, provider data, generated artifacts, and caches.
- Require atomic transactions, schema migrations with rollback, busy/locked
  handling, bounded queries, crash recovery, corruption detection, backup and
  restore verification, downgrade refusal, disk-full behavior, secure shutdown,
  and recovery from interrupted writes.
- Keep export/import as an explicit sanitized portability and backup feature,
  not the normal conversation workflow. Imported data is untrusted and must
  pass schema, size, count, encoding, and active-content rejection before any
  record is admitted.
- Add no synchronization, cloud backup, multi-user sharing, remote database,
  telemetry, or cross-device history until each becomes a separately approved
  provider and security boundary.

Exit criteria:

- Only files explicitly selected by the user can enter context, and neither a renderer nor model can supply a filesystem path or expand the grant.
- The UI previews admitted content and discloses the exact provider trust scope before any selected content is transmitted.
- A successful HTTP connection remains visibly identified as unencrypted:
  loopback HTTP receives a same-machine notice, while private-network HTTP
  receives a prominent interception/tampering warning and HTTPS or a loopback
  tunnel is recommended.
- Unsupported, oversized, malformed, traversal-like, binary, archive, and parser-hostile inputs fail closed without residual temporary files or unsanitized logs.
- Native clipboard tests prove the exact browser-exposed representation and paste behavior on admitted Windows, Linux, and macOS targets. Unsupported representations receive a clear local warning and are not silently converted, uploaded, or discarded.
- Screenshot normalization, if later admitted, produces a bounded metadata-free PNG whose decoded dimensions, pixel count, structure, and canonical bytes are revalidated by the loopback engine. Browser conversion alone is never trusted as validation.
- PDF and Office promotion requires hostile fixtures for embedded content, active actions, macros, external relationships, encryption, malformed containers, duplicate/traversal members, decompression bombs, excessive objects/parts, parser crashes, timeouts, cancellation, and residue-free cleanup.
- Context budgeting deterministically bounds transmitted chunks and clearly reports partial admission or truncation.
- Prompt injection inside a document cannot add filesystem, process, network, model-management, approval, or persistence authority.
- New task, provider/model changes, removal, failure, and shutdown clear all document state; tests verify no cache, browser storage, log, package-tree, or temporary-file residue.
- Source-versus-packaged parity and native Windows, Linux, and macOS package smoke tests cover selection, validation, retrieval, disclosure, cleanup, and hostile inputs before promotion.
- Private sessions remain provably write-free. When history is enabled, the UI
  discloses the local storage effect and exact retained content, and neither a
  model nor renderer can gain database, path, SQL, retention, or deletion
  authority.
- Conversation-history promotion requires encryption-at-rest and key-management
  decisions, least-privilege file permissions, deterministic migrations,
  crash/corruption/disk-full recovery, complete delete/clear/uninstall behavior,
  bounded context reconstruction, source-versus-packaged parity, and native
  Windows, Linux, and macOS evidence.

### Recommended Implementation Order

1. Define the versioned document-ingestion, context-budget, provider-disclosure, execution-isolation, and memory-lifecycle contracts with all effects denied by default. Done for the bounded `.txt`/`.md`/`.csv`/`.json` and browsed-or-pasted PNG slice.
2. Add offline hostile fixtures for filenames, encodings, oversized input, duplicate content, prompt injection, truncation, cleanup, exact provider payloads, PNG structure/CRC/dimensions, content-identity masquerading, and inert execution boundaries. Done for admitted text/structured-text/PNG, renamed PowerShell/shell/batch and binary/container rejection, the metadata-only parser-worker admission boundary, and review-only execution of 14 synthetic PDFs; retrieval truncation and non-synthetic hostile PDF evidence remain open.
3. Implement explicit memory-only multi-file attachment for the minimal text allowlist without directory selection or persistence. Done with five-file, 64-KiB-per-file, 128-KiB-total text limits and warned submit-confirmed private-network transfer; browsed or pasted PNG screenshots default to two with an advanced one-through-four per-task choice while the engine retains absolute four-image, 4-MiB-per-image, 8-MiB-total, 16.7-million-per-image and 33.5-million-combined-pixel, and unverified-model-warning bounds.
4. Run native clipboard-paste smoke tests on the admitted Windows, Linux, and
   macOS browser/package matrix and record the exact clipboard MIME
   representation. Sanitized Windows and Ubuntu x86_64 source and unsigned
   packaged/default-browser cells are done; the Ubuntu browser exposed the
   native pasted item through the admitted PNG path. Physical macOS is
   owner-parked until hardware is acquired. Keep unsupported representations
   rejected with a clear warning.
5. Evaluate bounded browser-side JPEG/WebP-to-PNG normalization only if native evidence shows it is needed. Keep TIFF, arbitrary image upload, native clipboard integration, metadata retention, and unbounded decoding unadmitted.
6. Extend inert plain-text selection to CSV and JSON, then separately reviewed source-code extensions, with format-aware previews and the existing no-execution boundary. Done for bounded UTF-8 CSV/JSON with client and engine syntax/resource validation and no formula evaluation, plus the narrow `.cs`/`.py`/`.js`/`.jsx`/`.ts`/`.tsx`/`.java`/`.go`/`.rs`/`.sql`/`.tf` set with exact client/engine parity, `text/plain` normalization, no syntax claim, and hostile shell/PowerShell/type-confusion rejection. All remain memory-only inert provider context.
7. Introduce the restricted parser-worker contract and hostile parser harness before admitting any complex document parser. Done at the offline admission boundary with 27 cases covering PDF, Office Open XML, and OpenDocument candidate identities plus paths, authority fields, size/object/nesting/expansion budgets, encryption, active content, macros, external relationships, embedded objects, and exact worker limits. No parser dependency, worker, route, filesystem access, or runtime authority is admitted.
8. Add text-only PDF extraction for unencrypted, inactive documents after PDF-specific hostile, resource, dependency, packaging, and native gates pass. Candidate comparison, exact universal-wheel/metadata/license digest verification, and a deterministic 14-file synthetic hostile corpus are complete for `pypdf` 6.14.2. A review-only worker opened those synthetic bytes and passed 61 Windows security, 64 static contract, and 40 contract-parity/package-exclusion checks. A 33-check bounded native-validation foundation passed source orchestration on Windows and Ubuntu Linux. The 27-check production-isolation assessment records missing Windows restricted-token/AppContainer-equivalent, Linux namespaces/seccomp/Landlock-equivalent, and macOS sandbox controls; no fallback is allowed. Metadata-only research cataloged three public corpus sources but selected, downloaded, opened, parsed, or retained no document because per-artifact origin, rights, privacy, malware, revision, and digest evidence remain unresolved. A 23-case offline intake verifier binds public same-host HTTPS artifact paths to immutable revisions and rejects private destinations; the 15-check source/package parity contract also fails closed. Prospective inventory/notices/SBOM remain ignored local evidence. The wheel remains ignored, uninstalled, absent from dependencies and packages, and unreachable from the application; macOS execution, production isolation, admitted non-synthetic hostile evidence, package integration, native package parity, and explicit admission remain open. Keep embedded files, JavaScript/actions, external references, PDF rendering, and OCR blocked.
9. Add non-macro `.docx`/`.xlsx`/`.pptx` extraction only after independent Open XML package, relationship, formula, presentation-semantics, dependency, and native gates pass. The shared candidate-only ZIP/XML inspection foundation passes 49 checks across 24 deterministic containers and rejects relationship traversal plus empty, absolute, URI, disguised, whitespace-obscured, or percent-encoded external targets. The standard-library semantic prototype now passes 62 checks across 19 six-format fixtures, distinguishes DOCX body/table/header/footer/comment provenance, XLSX shared/inline/literal cells, and PPTX slide/speaker-note text, and rejects formulas, tracked changes, charts, drawings, invalid shared-string indexes, and over-budget parts/text. Windows and Ubuntu Linux source orchestration pass without archive extraction or third-party dependencies. A separate 33-check parity contract keeps every package cell false. Relationship-aware ordering, richer comment/change semantics, non-synthetic evidence, production isolation, native package parity, and runtime admission remain open.
10. Add `.odt`/`.ods`/`.odp` extraction only after an independent OpenDocument ZIP/XML parser review and equivalent relationship, embedded-content, formula, expansion, dependency, packaging, and native gates pass. Candidate identity, first stored mimetype, hostile external-link/embedded-object/DTD/entity/mimetype-confusion rejection, runtime/package exclusion, bounded paragraph/heading review, formula rejection, and Windows/Ubuntu source evidence are covered by the shared foundations; no OpenDocument dependency, worker, provider payload, package, UI, or runtime route is admitted.
11. Evaluate `.pptx` and `.xlsx` independently with slide/sheet provenance and format-specific bounds. Keep macro-enabled, legacy binary, encrypted, embedded-object, and unsupported Office formats blocked.
12. Evaluate scanned-PDF and image OCR as a separate capability with pinned models/tools, capacity planning, quality evidence, cleanup, and no-network enforcement.
13. Add deterministic in-memory lexical retrieval and per-response source/chunk disclosure. Done offline with strict budgets, stable ranking, explicit matching/selected/omitted counts and truncation reasons, hostile-input isolation, removal, clear-all, and failure cleanup; runtime route, UI, and provider integration remain unadmitted.
14. Evaluate explicit folder selection only after canonicalization, exclusions, symlink/reparse handling, preview, cancellation, and bounded traversal tests pass on every platform.
15. Evaluate optional local embeddings independently, including model identity, download consent, capacity, quality, cleanup, and provider separation.
16. Define a versioned, default-deny conversation-history contract and hostile
    fixtures with every database route, file write, migration, import, and
    persistence effect disabled. Done: the contract, logical schema boundary,
    and 16 inert hostile requests grant no runtime or storage authority.
17. Build a simulation-only SQLite schema, migration planner, retention planner,
    context-reconstruction planner, and corruption/recovery fixtures without
    creating a runtime database. Done for the effect-free foundation, including
    deletion, backup, restore, busy/locked, interrupted-write, corruption, and
    disk-full plans; no SQLite module is imported and no database is opened.
18. Review the encryption and key-management architecture, including
    SQLCipher-equivalent dependency, license, supply-chain, native packaging,
    operating-system credential storage, key rotation/loss, and backup/restore.
    Done at the architecture boundary: dependency selection and implementation
    remain separately gated, and unavailable credential storage fails closed to
    Private session without a plaintext key fallback.
19. Admit an opt-in development history database only after explicit approval
    and the storage, deletion, recovery, privacy, and cross-platform package
    gates pass. Keep Private session as the default until a separate product
    decision changes it.
20. Add conversation list, rename, search, retention, delete, clear-all,
    context-preview, backup, and restore UI only over typed engine operations;
    add no renderer SQL or filesystem path authority.
21. Consider an optional persistent document/knowledge library only as a
    separately approved storage product with its own encryption, deletion,
    migration, export, rollback, retrieval, and uninstall evidence.

## Milestone 28: Controlled Web Research

Goal: Let an end user explicitly research current public information with a local model while keeping all network authority in a narrow engine-owned search and retrieval broker rather than granting the model, renderer, or browser unrestricted internet access.

Current status: Proposed, security-scoped, and offline-only. A machine-readable foundation plus ten inert hostile fixtures deny runtime routes, model tools, network, DNS, URL fetching, browser automation, page execution, credentials, downloads, persistence, and autonomous follow-up. A separate 28-check caller-fixture boundary validates bounded queries, strict public-HTTPS result metadata, engine-derived inactive citations, and exact source accounting without importing a network stack or entering the application/package. A disabled fixed-Wikipedia metadata-query adapter adds 15 request/response security checks through an injected fixture transport; it has no HTTP client or live destination authority. A 25-check effect-free transport guard validates fixed HTTPS destinations, public DNS snapshots before and at connection, rebinding, redirects, response type, encoding, time, and bytes without performing DNS or network I/O. A 17-check memory-only state proof requires exact single-use query/page approvals and lifecycle cleanup. Self-hosted-provider and at-most-four-query evaluation contracts preserve disclosure, separate approval, cancellation, SSRF, and source-accounting gates without selecting or activating a provider. A 26-check caller-bytes-only page-text foundation strictly converts bounded UTF-8 text or allowlisted HTML into inert untrusted segments while retaining no attributes or remote references and granting no fetch, filesystem, runtime, UI, package, or model authority. A separate 26-check cited-synthesis foundation builds URL-free digest-accounted source envelopes and accepts only bounded claims with exact engine-derived citation IDs; it invokes no model and grants no tool, follow-up, runtime, or network authority. No live search adapter, page transport, or UI control exists. Text models retain no general research authority, and the existing fixed-origin Ollama model-catalog search remains a separate candidate-discovery feature.

Scope:

- Begin with a dedicated **Search web** action for one text request. Never infer consent from an ordinary prompt or enable search by default.
- Generate or accept one bounded proposed query, show exactly what will leave the local environment, and let the user edit or cancel it before the first network request.
- Use one engine-configured search adapter at a time. Renderer and model input cannot choose a host, raw URL, credential, header, proxy, executable, command, or environment.
- Send only the approved bounded query. Do not automatically include conversation history, local documents, provider endpoints, hardware facts, repository content, usernames, paths, or model metadata.
- Return a strict bounded result shape containing title, excerpt, public source URL, domain, and retrieval time. Treat every field as untrusted and never treat search ranking or page claims as product evidence.
- Render citations through a trusted component, not model Markdown. External navigation must disclose the destination and require an explicit user action; remote images, scripts, styles, frames, downloads, cookies, and tracking remain blocked.
- Add page retrieval only after separate approval. Re-resolve DNS, reject loopback/private/link-local/reserved/credential-bearing destinations, constrain redirects to independently validated public HTTPS targets, cap response bytes and time, allowlist textual content types, and perform no JavaScript execution.
- Strip active markup and extract bounded text locally. Search results and page content are untrusted prompt context and cannot grant tools, follow-up searches, approvals, filesystem access, provider changes, or policy changes.
- Require explicit approval for each additional query and page retrieval initially. Bounded multi-query research remains a later gate with visible budgets, cancellation, and source accounting.
- Keep queries, results, extracted content, citations, and research state in memory only. New task, provider/model change, explicit clear, failure, and shutdown discard them.
- Support an independently reviewed self-hosted search adapter later without weakening the same query, SSRF, content, disclosure, and cleanup controls.

Exit criteria:

- No text model or renderer can open a socket, choose a network destination, fetch an arbitrary URL, execute page code, or silently trigger a search.
- The user sees and approves the exact bounded query and search provider before data leaves the local environment.
- Search and retrieval reject DNS rebinding, redirects to unsafe address classes, credentials, oversized or non-text responses, decompression abuse, malformed encodings, and hostile result shapes.
- Retrieved instructions cannot add authority or trigger another query, page, tool, process, file, model, approval, or network action.
- Every grounded answer distinguishes retrieved claims from model knowledge and binds citations to engine-validated sources and retrieval times.
- Cancellation, failure, New task, provider/model change, and shutdown leave no query, page, cookie, cache, browser-storage, log, download, or temporary-file residue.
- Offline fixtures, hostile local servers, source/package parity, and native Windows, Linux, and macOS smoke tests pass before any adapter is promoted.

### Recommended Implementation Order

1. Define versioned search-query, result, citation, provider-disclosure, research-budget, and memory-lifecycle contracts with network and follow-up effects denied by default. Done for the inactive offline foundation; a future adapter result schema remains separately gated.
2. Add offline hostile tests for destination confusion, DNS/IP classes, redirects, credentials, malformed responses, oversized content, prompt injection, citation forgery, cancellation, and cleanup. Ten inert contract fixtures plus the effect-free 25-check transport guard and 17-check approval lifecycle are present; executable broker tests remain with a future adapter.
3. Implement one explicit query-only search adapter returning bounded titles, excerpts, domains, public HTTPS URLs, and retrieval times. The general offline caller-fixture validator passes 28 checks, and a fixed-Wikipedia metadata request adapter passes 15 additional fixture-transport checks. Neither contains a live HTTP transport or runtime/network authority.
4. Add trusted citation rendering and per-query disclosure without model-supplied links. The inactive engine-derived citation shape and exact source-accounting validator are done; trusted visual rendering and active user navigation remain unimplemented.
5. Add explicit user-selected page retrieval with SSRF revalidation, strict content limits, inert text extraction, and no page execution. The 26-check offline caller-bytes extractor establishes strict text/HTML parsing behavior; network transport, destination validation, response binding, runtime integration, and promotion remain unimplemented.
6. Add cited model synthesis from only the approved result/page set, with exact source accounting and no autonomous follow-up. The offline caller-fixture foundation now validates URL-free source envelopes and claim-level engine-derived citations in 26 hostile/static checks, and the same sanitized source bundle passes on native Windows and Ubuntu Linux. It invokes no model and remains absent from the runtime and package; macOS and native package evidence remain open.
7. Evaluate a self-hosted adapter and bounded multi-query research independently after the single-query path passes native evidence. Default-deny evaluation contracts now cap the latter at four visible, separately approved queries and prohibit autonomous or page-derived follow-up; no provider is selected or active.

## Security hardening baseline (implemented)

The current baseline adds private vulnerability reporting guidance, CODEOWNERS, a security PR checklist, immutable GitHub Action pins, bounded CI jobs, CodeQL, fail-closed third-party installers, explicit endpoint trust scopes, redirect denial, bounded provider responses, secure prompt channels, exclusive artifact creation, and structured child-process execution. A standing pre-commit gate now requires a zero-finding review bound to the exact staged tree for large, binary, and security-sensitive changes; any finding stops the flow until the owner is notified and every finding is fixed. Branch and repository security controls are enforced in GitHub after the code lands.
