# Project

## Name

Haven 42

Tagline: Your private, local AI station.

Primary audience: people who want private AI but may have no experience with
models, local AI engines, command lines, or computer administration. Advanced
users and contributors remain supported through clearly separated controls and
documentation.

## Purpose

This repository defines an evidence-gated, local-first AI workbench for individual users, developers, teams, consultants, and enterprise groups. It combines repeatable software-engineering workflows with repository-optional chat, writing, summarization, and image capabilities under common routing, approval, privacy, and typed-artifact contracts.

The engineering pack turns common senior engineering activities into version-controlled prompts, rules, agents, and templates that can be reviewed, improved, and reused across repositories. The broader Haven 42 product now includes a runnable loopback-only local web experience over the same tested contracts and an unsigned PyInstaller one-folder development package. Tauri/Rust remains unadmitted.

Continue, Aider, and OpenCode are the maintained engineering surfaces. General text capabilities share a provider-neutral adapter: Ollama is live-validated, and llama.cpp's OpenAI-compatible path is live-validated for its exact Linux NVIDIA/CUDA profile. Windows AMD/HIP retains engine-only evidence. Linux Intel Arc B580 has candidate-only llama.cpp SYCL and OpenVINO GenAI evidence, while Windows OpenVINO is separately candidate-only and native Windows llama.cpp SYCL failed its model-load gate; none is selectable or packaged. Every other profile fails closed. Linux image generation has a live-validated ComfyUI/SDXL provider, and all additional providers or surfaces remain pass-before-ship.

## Current Stage

The recovered local-closure plan now has a durable 374-task ledger with stable
IDs and evidence-required states. Its reconciliation records 360 completed,
seven owner-deferred, seven partial, and zero unverified tasks. The existing
48-item parent-roadmap blocker ledger remains valid; classification does not
turn deferred or partial product work into completed scope.

The current public test build is Haven 42 `0.4.0-alpha.1` for Windows 11 x64
and invited testers, with server-enforced text-only Chat, Writing, and
Summarization in one continuous workspace. Automatic request routing is the
default with explicit task choices available, and provider-reported generation
speed appears beside local resource and token totals. Its current-user managed
setup does not bundle external software or automate drivers. The exact unsigned
artifact, source commit, tag, public prerelease, checksums, and reporting routes
are recorded in `config/windows-alpha-release-record.json`. Signing, stable or
production promotion, installer activation, and online updates remain inactive.

A completed Haven-managed local setup reconnects on later launches only after
fresh receipt, runtime-integrity, publisher, exact-model, managed-path, and
loopback verification, then bypasses redundant connection onboarding. The
system summary uses the detected Windows 10/11 name, build, architecture, and
available software/driver versions rather than a generic platform label.

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

A least-privilege GitHub build-provenance job is active for the
unsigned Windows, Linux, and macOS development archives. It is main-push-only,
depends on all native package jobs, reverifies every downloaded artifact set,
and grants no pull-request write authority or Release publication. The job has
produced GitHub attestations for qualifying unsigned development archives,
including run `30826478326` at commit
`28bba796876a398869034e4d3b8b0c1ab6fa3056`. This does not authorize signing,
notarization, a GitHub Release, updater activation, or production use.

A separate weekly/manual Alpha usage-report workflow is prepared locally. It
uses only `contents: read`, reports cumulative counts for the exact public Alpha
ZIP and its supporting assets, and includes aggregate 14-day repository
clone/view traffic only if a separately approved credential with repository
Administration read access is introduced later. The default workflow uploads
bounded Markdown/JSON reports for 30 days, commits nothing, and collects no
downloader identity, IP address, device data, or Haven 42 telemetry.

Public code-signing and privacy policies plus a fail-closed SignPath
eligibility audit are now prepared locally. The Windows package specification
defines deterministic Haven 42 executable identity metadata, and the package
builder verifies it before generating an archive. This is readiness evidence
only: the public unsigned `0.4.0-alpha.1` prerelease does not establish SignPath
eligibility or production readiness. Exact packaged-dependency review and
provider enrollment remain open, and no certificate, signing workflow, or
signature is active. The owner confirmed repository-account MFA on 2026-07-27;
signing-service MFA remains a future enrollment requirement.

Portable evidence now adds an exact runtime-component inventory alongside the
whole-package inventory. Every file is bound by path, digest, and size to
Haven 42 or an explicit upstream/runtime group; unclassified files fail, SBOM
and notice rows must match, and upstream components cannot enter Haven 42's
signing scope. Future packages also embed the Haven 42 license, generated
third-party notice, and exact hash-verified upstream license texts in a
non-signable distribution-evidence group. The published Alpha predates this
correction and provides those documents as separate Release assets rather than
inside its immutable ZIP. Runtime redistribution and production promotion
remain false until the Microsoft licensed-user condition, complete license
review, and platform provenance are resolved.

Fresh Windows development builds also isolate PyInstaller configuration and
cache beneath the ignored build output. They do not create Haven-specific
build-tool state in the user's profile. Output paths and package links fail
closed if they escape the repository build tree or bundle.

A fresh 41-file unsigned development archive passed an end-to-end physical
Windows 11 Intel Arc B580/non-administrator cell on 2026-08-06. The cell covers
archive identity, package integrity, loopback confinement, approved portable
Ollama `0.32.5` plus `qwen3.5:9b` setup, Vulkan inference, Chat/Writing/
Summarization metrics, zero-download relaunch, sanitized logs outside managed
components, inert human-filename attachments, disguised-script rejection,
local/private-network/local provider switching with external Ollama `0.32.6`,
complete external model unload, scoped uninstall, and package-verified empty-
state relaunch. This is uncommitted development evidence, not a replacement
release, redistribution clearance, signing eligibility, or production
promotion.

The hosted package matrix now uses versioned Windows 2025, Ubuntu 24.04, and
macOS 15 runners, one immutable `setup-python` action, and exact official
Python 3.14.6 archive digests recorded in provenance. Local builds remain
explicitly unverified for that hosted-source claim.

Milestones 1 through 21 are complete for their defined scopes. Milestone 22A now has
a runnable Python standard-library local web application with loopback-only serving, sanitized system
status, automatically classified local/LAN Ollama connection, installed-model discovery, explicit candidate-only public Ollama catalog search, per-capability model choice, bounded chat, writing, summarization, strict typed progress/warning/result/error envelopes, memory-only failed-input recovery with no automatic retry, bounded effect-free composition planning, verified idle/lifecycle model cleanup, and security-hardened unsigned PyInstaller one-folder development packaging for Windows, Linux, and macOS. Public catalog results cannot execute or download a model; the UI only exposes a validated copyable external installation instruction. Packaging now has hash-locked build inputs, strict evidence allowlists, hostile native integrity tests, whole-archive inventories, and unsigned provenance. Windows dependency discovery is path-constrained and fails closed on host-derived API-set/UCRT files after a stale local build exposed unrelated JDK DLL contamination; a clean 31-file local rebuild and native package gate pass, and exact main commit `04baca39b26ec58c189a6ae21ea78b507444e9fa` passed clean hosted Windows/Linux/macOS reproduction and unsigned archive attestation. Applicable redistribution review and any future release-candidate repetition remain open. Milestone 22B now also has a 30-case structural updater-verifier receipt handoff, a 33-case verifier registry/root-transition model, a 37-case inactive post-quantum readiness suite, a 49-case future execution-admission simulator, and a 46-case digest-chained effect-journal simulator. The PQC layer inventories current boundaries and records unselected hybrid-preferred TLS with a visible secure classical fallback plus dual-signature candidates without changing TLS, selecting a parameter set, adding a dependency, handling a key, or verifying a signature. None establishes trust, issues or accepts an executable approval, writes a journal, stages an update, or grants runtime authority. Milestone 22B retains real cryptographic verification, PQC activation, executable capability composition, optional Tauri packaging, activated updates, signed distribution, and remaining native platform gates. Milestone 23 owns native
local image profiles and now has consumer-local discovery and consent contracts
plus a 28-case effect-free lifecycle planner that admits no machine effects.
An exact Windows 11/Quadro RTX 5000 ComfyUI/SDXL cell now passes integrity,
CUDA, generation, cancellation, forced recovery, cleanup, and shutdown, but it
remains partial and adds no runtime or UI admission.
External provider engines, models, accelerator runtimes, drivers, installers,
and updater payloads are excluded from Haven packages by policy. Provider
audits support connection compatibility and security review but cannot grant
bundling, redistribution, installation, or update authority.
Milestone 24 has partial external Linux CUDA audio evidence but no admitted
provider, while Milestone 25 retains candidate research plus a fail-closed
hardware/storage preflight. Both remain behind the shared media-consent policy.
Milestone 26 now has quantization plan/artifact
contracts, OS-aware sanitized profiling, explicit support boundaries, a
no-effect dry-run selector, exact Linux NVIDIA and Windows AMD evidence, and
candidate-only physical Intel Arc B580 llama.cpp SYCL/OpenVINO GenAI evidence.
The native Windows llama.cpp SYCL cell passed artifact preflight but failed
model loading and was rejected. Intel upstream/runtime/OS/quality/provider/package blockers, live conversion
recipes, and activation remain unpromoted. A new identical-byte llama.cpp
b10088 matrix has completed matching 11-model Windows AMD/HIP and Linux
NVIDIA/CUDA operational, exact-output, full-offload, and cleanup cells with
identical artifact hashes; this comparison changes no runtime admission.
Milestone 27 now
has an explicit-selection, memory-only unified `.txt`/`.md`/`.csv`/`.json`/PNG picker plus clipboard-PNG
attachment slice with strict atomic byte/count/dimension/structured-text limits, path-free transfer,
warned submit-confirmed private-network transfer, visible unverified image-input status, inert-data
isolation with no attachment-driven execution or tools, and no temporary
files. A 27-case restricted parser-worker foundation rejects hostile PDF,
Office Open XML, and OpenDocument metadata but admits no dependency, worker,
route, or filesystem access. The review-only complex-document layer now passes
49 container checks across 24 fixtures and 62 semantic checks across 19
fixtures with Windows and Ubuntu source evidence; a separate 33-check parity
contract keeps all package
cells false. PDF production isolation also has a 37-check native OS-control
evidence gate that rejects WSL2 as native Linux and permits no fallback or
runtime authority.
Automatic scan, directory access, real complex parsers, embedding indexes,
and runtime persistence remain unadmitted. The deterministic memory-only
lexical core now rejects exact duplicate content, discloses source/chunk and
truncation accounting, and clears on failure, removal, provider change, and
shutdown, but its
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

Owner-approved development validation now exercises a real fixed-schema SQLite
database using only synthetic records inside a fresh temporary directory. It
passes parameterized create/read, backup/restore, cascade-deletion, permission,
and residue-cleanup checks while accepting no user content or caller database
path. A separate explicit-folder foundation produces only bounded relative
metadata and rejects links, hidden or unsupported entries, binaries,
executables, archives, encoding failures, resource overruns, and files changed
during read. Neither foundation is connected to the runtime, UI, provider, or
package.
Milestone 28 defines proposed controlled web research with inactive offline
contracts and hostile fixtures. A 28-check caller-fixture boundary validates
bounded queries, strict public-HTTPS result metadata, engine-derived inactive
citations, and exact source accounting without importing a network stack or
entering the runtime/package. A 26-check caller-bytes-only foundation converts
bounded UTF-8 text or strict allowlisted HTML into inert untrusted segments
without retaining attributes or remote references and without network,
filesystem, runtime, package, UI, or model authority. Live transport, DNS,
page retrieval, trusted UI
navigation, actual DNS/network execution, and autonomous
follow-up remain unadmitted; no model or renderer internet tool exists. Broader
surface and provider parity remains evidence-gated.

A fixed-provider development query adapter now validates the exact Wikipedia
metadata-search request and response shape through an injected fixture
transport. Fifteen security checks cover request tampering, duplicate keys,
strict unused metadata, Unicode controls, credential-like and
active queries, result and response budgets, non-finite JSON, model-supplied
links, duplicate identifiers, timestamps, and disabled authority. It imports
no network client. Separate contracts now preserve self-hosted, bounded
multi-query, semantic-embedding, encrypted-library, audio, and video gates
without selecting or admitting an implementation.

An effect-free transport guard now validates fixed HTTPS destinations, public
pre-connect and connected DNS snapshots, rebinding, redirects, response type,
encoding, time, and byte bounds. A separate memory-only state proof requires
exact single-use query and page approvals and clears them on cancellation,
failure, provider change, and shutdown. Neither performs DNS or network I/O or
enters the runtime/package.

Local object-only inspection also passes against immutable Click 8.2.1,
Express 5.1.0, and serde_json 1.0.140 public permissive repositories. Exact
license bytes, commit identity, safe tree modes, and aggregate budgets were
verified from ignored bare clones without checkout or target execution. A
ripgrep candidate was rejected for a symlink and replaced without weakening
the policy. Candidate Aider and OpenCode profiles remain read-only and do not
promote real-project writes.

Those three repositories also pass content-free project detection,
runtime-context planning, read-only workflow selection, and language-rule
selection from bare object metadata. Candidate Aider/OpenCode planning pins
exact expected versions, validates injected discovery facts and local/private
Ollama endpoints, and supplies rollback/cleanup plans without installation,
configuration writes, executable launch, or promotion.

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
