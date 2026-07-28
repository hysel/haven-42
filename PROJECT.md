# Project

## Name

Haven 42

Tagline: Your private, local AI station.

## Purpose

This repository defines an evidence-gated, local-first AI workbench for individual users, developers, teams, consultants, and enterprise groups. It combines repeatable software-engineering workflows with repository-optional chat, writing, summarization, and image capabilities under common routing, approval, privacy, and typed-artifact contracts.

The engineering pack turns common senior engineering activities into version-controlled prompts, rules, agents, and templates that can be reviewed, improved, and reused across repositories. The broader Haven 42 product now includes a runnable loopback-only local web experience over the same tested contracts; Tauri remains an optional later packaging path.

Continue, Aider, and OpenCode are the maintained engineering surfaces. General text capabilities share a provider-neutral adapter: Ollama is live-validated, and llama.cpp's OpenAI-compatible path is live-validated for its exact Linux NVIDIA/CUDA profile. Windows AMD/HIP retains engine-only evidence, and every other profile fails closed. Linux image generation has a live-validated ComfyUI/SDXL provider, and all additional providers or surfaces remain pass-before-ship.

## Current Stage

The admitted local web UI now enforces one visible primary panel, provides
dedicated Models and About views, exposes capability-specific installed-model
selection beside explicit candidate search, labels installed versus uninstalled
results, resets and re-ranks discovery when the target capability changes,
exposes all bounded cleanup policies in System, keeps provider inputs and
selectors visually consistent across the wizard and workspace, and supports
Enter-to-send with Shift+Enter for multiline input. Assistant chat and
Markdown-document results now render a safe DOM-built Markdown allowlist and
Unicode emoji while keeping raw HTML inert. Prompt recall uses Up/Down with
multiline-safe boundaries, defaults to 20 entries, offers 50 or 100 in System,
and remains task-bound browser memory.

A dedicated advanced **Evidence** navigation section now exposes a bounded
summary derived by one cross-platform standard-library engine from committed
sanitized catalogs. Keeping it outside the everyday chat and setup flow avoids
turning developer validation metrics into a primary user task. It displays
evidence counts and supported/candidate agent-surface status without running
tests, contacting a provider, reading a user repository, starting a process,
writing a file, or claiming production readiness. Source browser validation
and native packaged browser/parity smoke tests cover Windows, Linux, and macOS.
The page exposes outcome totals and per-surface activity counts directly, with
one fixed explicit-click no-referrer link to the detailed repository wiki.

A machine-readable Milestone 22 admission-readiness ledger now separates the
admitted read-only development scope from owner-deferred model comparison and
blocked native runtime, production package, installer, updater, and executable
composition work. Its offline hostile-tested evaluator grants no authority and
keeps the unsigned development package independent from future promotion
decisions.

A least-privilege GitHub build-provenance job is prepared locally for the
unsigned Windows, Linux, and macOS development archives. It is main-push-only,
depends on all native package jobs, reverifies every downloaded artifact set,
and grants no pull-request write authority or Release publication. No
attestation exists until an approved future push runs that job.

Public code-signing and privacy policies plus a fail-closed SignPath
eligibility audit are now prepared locally. The Windows package specification
defines deterministic Haven 42 executable identity metadata, and the package
builder verifies it before generating an archive. This is readiness evidence
only: the project has no public binary Release in the form required for an
application, exact packaged-dependency review and provider enrollment remain
open, and no certificate, signing workflow, signature, or publication is
active. The owner confirmed repository-account MFA on 2026-07-27;
signing-service MFA remains a future enrollment requirement.

Portable evidence now adds an exact runtime-component inventory alongside the
whole-package inventory. Every file is bound by path, digest, and size to
Haven 42 or an explicit upstream/runtime group; unclassified files fail, SBOM
and notice rows must match, and upstream components cannot enter Haven 42's
signing scope. Runtime redistribution and production promotion remain false
until complete license texts and platform provenance pass review.

The hosted package matrix now uses versioned Windows 2025, Ubuntu 24.04, and
macOS 15 runners, one immutable `setup-python` action, and exact official
Python 3.14.6 archive digests recorded in provenance. Local builds remain
explicitly unverified for that hosted-source claim.

Milestones 1 through 21 are complete for their defined scopes. Milestone 22A now has
a runnable Python standard-library local web application with loopback-only serving, sanitized system
status, automatically classified local/LAN Ollama connection, installed-model discovery, explicit candidate-only public Ollama catalog search, per-capability model choice, bounded chat, writing, summarization, strict typed progress/warning/result/error envelopes, memory-only failed-input recovery with no automatic retry, bounded effect-free composition planning, verified idle/lifecycle model cleanup, and security-hardened unsigned PyInstaller one-folder development packaging for Windows, Linux, and macOS. Public catalog results cannot execute or download a model; the UI only exposes a validated copyable external installation instruction. Packaging now has hash-locked build inputs, strict evidence allowlists, hostile native integrity tests, whole-archive inventories, and unsigned provenance. Windows dependency discovery is path-constrained and fails closed on host-derived API-set/UCRT files after a stale local build exposed unrelated JDK DLL contamination; a clean 31-file local rebuild and native package gate pass, and exact main commit `04baca39b26ec58c189a6ae21ea78b507444e9fa` passed clean hosted Windows/Linux/macOS reproduction and unsigned archive attestation. Applicable redistribution review and any future release-candidate repetition remain open. Milestone 22B now also has a 30-case structural updater-verifier receipt handoff, a 33-case verifier registry/root-transition model, a 49-case future execution-admission simulator, and a 46-case digest-chained effect-journal simulator. None establishes trust, issues or accepts an executable approval, writes a journal, stages an update, or grants runtime authority. Milestone 22B retains real cryptographic verification, executable capability composition, optional Tauri packaging, activated updates, signed distribution, and remaining native platform gates. Milestone 23 owns native
local image profiles and now has consumer-local discovery and consent contracts
plus a 28-case effect-free lifecycle planner that admits no machine effects.
Milestones 24 and 25 retain documentation-only audio/video candidate inventories and
shared media-consent policy. Milestone 26 now has quantization plan/artifact contracts,
OS-aware sanitized profiling, explicit support boundaries, and a no-effect dry-run
selector; live model recipes and activation remain unpromoted. Milestone 27 now
has an explicit-selection, memory-only unified `.txt`/`.md`/`.csv`/`.json`/PNG picker plus clipboard-PNG
attachment slice with strict atomic byte/count/dimension/structured-text limits, path-free transfer,
warned submit-confirmed private-network transfer, visible unverified image-input status, inert-data
isolation with no attachment-driven execution or tools, and no temporary
files. A 24-case restricted parser-worker foundation rejects hostile PDF and
Office metadata but admits no dependency, worker, route, or filesystem access.
Automatic scan, directory access, real complex parsers, embedding indexes,
and runtime persistence remain unadmitted. The deterministic memory-only
lexical core now has bounded offline hostile and lifecycle tests, but its
default-deny contract still exposes no runtime route, UI control, or provider
payload.
The optional conversation-history foundation now defines a non-executable
logical SQLite-compatible schema plus pure migration, retention, context,
deletion, recovery, backup, and restore planners. It imports no SQLite runtime,
opens or creates no database, accepts no caller path or SQL, keeps every effect
false, and preserves Private session as the write-free default. The encryption
and key-management architecture review now requires user-scoped OS credential
storage and fail-closed Private session with no plaintext fallback. Dependency
selection, per-user storage implementation, UI activation, and saved messages
remain separate approval gates.
Milestone 28 defines proposed
controlled web research with an inactive offline contract and hostile fixtures, followed later by explicit reviewed queries, engine-owned adapters,
trusted citations, SSRF controls, and memory-only cleanup; no model or renderer
internet tool is admitted. Broader surface and provider parity remains
evidence-gated.

Capability Evidence Contract v2 now prevents model readiness from being
inherited across surfaces, operating systems, or operations. Deterministic
project classification and project-local language-rule activation are
implemented. Lane-specific model scoring now keeps WRITE SAFE
reliability-first while allowing larger validated PLAN ONLY and DEEP REVIEW
models when hardware permits. Model-backed language promotion, richer
runtime-measured model metadata, additional script-family consolidation, and
the desktop UI implementation remain planned work. The onboarding/navigation family now
shares catalog, command-rendering, output, and native-dispatch plumbing while
preserving stable public commands. A schema-v1 workflow envelope now gives
dispatchers and future UI callers a stable, privacy-conscious JSON boundary.

## Target Users

- Individual developers improving personal or client repositories
- Small teams that want consistent review and planning without heavyweight process
- Senior engineers working in enterprise .NET repositories
- Architects reviewing service boundaries and dependency direction
- Security engineers reviewing API and application risks
- Performance engineers investigating reliability and throughput concerns
- Product and delivery leads who need structured implementation plans
- Teams using Continue or another validated local-first agent surface with local or self-hosted model infrastructure

## Goals

- Provide a usable local-first AI workbench for practical engineering and general-purpose workflows.
- Favor local-first operation through Continue, Ollama, and future validated local agent surfaces.
- Make AI-assisted reviews repeatable and auditable.
- Encode practical .NET, ASP.NET Core, Clean Architecture, API, security, testing, logging, performance, and Git guidance.
- Keep role-specific behavior explicit through agents.
- Keep task-specific behavior explicit through prompts.
- Keep reusable standards explicit through rules.
- Provide templates for durable engineering artifacts.

## Non-Goals

- Replacing human engineering review or approval.
- Providing a complete application framework.
- Supporting every language ecosystem equally in the initial release.
- Depending on cloud-hosted LLMs as the default path.
- Encoding organization-specific secrets, policies, or private infrastructure details.

## Product Principles

- Local-first by default.
- Beginner-friendly defaults with enterprise-safe language and workflows where needed.
- Clear separation between agents, prompts, rules, and templates.
- Practical guidance over abstract theory.
- Explicit limitations instead of inflated capability claims.
- Human review remains mandatory for AI-generated recommendations.

## Success Criteria

Milestone 1 is successful when:

- `.continue/config.yaml` can be loaded by Continue.
- Core prompts are available for repository discovery, implementation planning, code review, bug investigation, security review, architecture review, performance review, and documentation.
- Core rules guide .NET, ASP.NET Core, APIs, Clean Architecture, testing, logging, security, performance, SonarQube, and Git work.
- Agents are defined for senior engineering, architecture, security, review, performance, documentation, and product management.
- Templates exist for architecture notes, security reviews, performance reviews, and AI project guidance.
- README usage instructions match validated behavior.
