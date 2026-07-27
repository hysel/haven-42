# Architecture

## Overview

Haven 42 is organized as a provider-neutral capability, configuration, documentation, and workflow repository. Its engineering foundation includes the `.continue` directory plus maintained Aider and OpenCode paths; its general-purpose layer adds repository-optional sessions, routing, provider adapters, and typed artifacts.

The currently validated runtime architecture is:

`capability -> provider contract -> inference engine -> hardware backend -> model artifact`

Text capability discovery and invocation currently normalize Ollama and OpenAI-compatible llama.cpp APIs behind one dry-run-first contract. The direct llama.cpp path is live-validated only for the exact Linux NVIDIA/CUDA profile. OpenAI-compatible selection requires an exact admitted engine, backend, and hardware profile from `config/inference-engine-registry.json`; unknown, failed, parked, and cross-profile combinations fail closed.

```text
Agent surfaces
  Continue -> project or shared .continue assets
  Aider -> local-only generated Aider config
  future surfaces -> evidence-gated adapters

Reusable pack assets and catalogs
  prompts, rules, agents, templates, project profiles, model fit, evidence
        |
        v
config/workflows.json -> scripts/invoke-workflow.*
        |                       |
        |                       +-> schema-v1 request/result envelope
        v
tested workflow engines -> sanitized reports, local-only config, validation evidence
```

The long-term architecture should keep prompts, rules, templates, validation scripts, and evidence formats portable enough to evaluate with other local-first coding-agent surfaces.

Milestone 22A adds a runnable local web slice without replacing these contracts:

```text
Bundled HTML/CSS/JavaScript on 127.0.0.1
        |
Host + Origin + session-token enforcement
        |
Python standard-library local server
        |
shared endpoint security -> exact-digest Ollama text + loopback ComfyUI image
        |
workflow registry -> read-only plan artifacts (no process or arguments)
        |
unload and process-list verification after every response
```

The process persists no endpoint, prompt, response, or provider run detail; exposes no repository, generic filesystem, shell, or arbitrary process API; permits no remote UI assets; and cannot bind to a LAN interface. A shared standard-library evidence engine reads only the three bundled sanitized catalogs and produces the same dashboard schema for PowerShell, Linux, macOS, source web, and frozen web callers. The browser receives a smaller strict read-only summary that excludes paths, raw notes, and live provider data and declares every network, process, repository, write, provider, and machine effect false. Automatic text selection requires the exact installed Ollama digest and matching capability evidence. Text, workflow-plan, and image execution use the shared schema-v1 event vocabulary. The browser rejects malformed, non-monotonic, multiple-terminal, or post-terminal event streams before rendering an artifact. Assistant chat and Markdown-document text pass through a small dependency-free block/inline allowlist that creates nodes with `createElement` and `textContent`; raw HTML cannot become markup, links, images, scripts, or handlers. Unicode emoji remain ordinary text with cross-platform font fallbacks. Unverified manual models add a warning event; provider failures return typed errors and memory-only recovery declarations. No automatic retry occurs, and a retry is always a new request.

Model discovery is separate from model installation. Installed-model filtering is browser-local, results explicitly distinguish the connected provider inventory from uninstalled candidates, and changing the target capability clears stale query/candidate state before ranking installed choices by selected and evidence status. The explicit **Search public catalog** submit action crosses the engine boundary with only a bounded query, which can reach only the fixed `https://ollama.com/search` origin with redirects disabled and a capped HTML response. The engine normalizes strict model names and returns at most 20 candidate-only records. An uninstalled choice is browser-memory intent, not execution authority; its command is constructed from the validated name, copied only on request, and never executed. Text execution still requires the model to appear in the connected provider's installed inventory.

The renderer maintains a single-primary-panel invariant across Chat, Software, Images, Models, and About. Chat is one continuous bounded conversation; Writing and Summarization remain capability-specific engine prompts and evidence lanes rather than destructive renderer tabs. A narrow browser-memory prefix hint selects only among those already admitted text capabilities. If the selected lane has a different configured installed model, the renderer sends nothing until the user explicitly keeps the current model or switches. The hint cannot invoke a provider, promote evidence, or add authority. Models owns capability-specific evidence, installed selection, and candidate discovery; the provider connection remains a separate configuration surface. Connected provider and System controls compare the current form against the last successfully applied endpoint, timeout, and model-residency policy. Unchanged values expose disabled `Connected` or `Applied` state and short-circuit even programmatic form submission; only an actual edit enables `Apply changes`, whose successful validated provider transition starts a new task. About is informational only. Keyboard submission maps Enter to the existing bounded text form and reserves Shift+Enter for multiline input. A browser-memory prompt ring defaults to 20 and permits 50 or 100 entries; Up/Down enters recall only at the appropriate first/last textarea line, restores the unfinished draft, suppresses consecutive duplicates, and clears on every task boundary without persistence or new authority.

The Software view is registry-derived but plan-only: it admits only `uiReady`,
`read-only` records, accepts no renderer arguments, and starts no process. The
Images view is a separate authority boundary for the promoted Linux
ComfyUI/SDXL profile. It requires a loopback endpoint, discovers the exact
checkpoint, submits a fixed built-in workflow, caps and validates the PNG,
clears API history, and returns a browser-memory artifact for a user-triggered
download. Provider-side image retention is disclosed and is not confused with
a Haven 42 client write. The admitted machine-readable boundary is
`config/local-web-runtime-policy.json`.

The initial native distribution path freezes that same process and UI into a PyInstaller one-folder package. PyInstaller supplies only a local launcher/runtime boundary: it does not add browser authority, an installer, privileged service, global dependency, or native UI framework. Frozen startup verifies a strict embedded path/size/SHA-256 resource manifest before serving. Browser launch accepts only the engine-generated IPv4-loopback HTTP origin: Windows uses the registered URL association, macOS uses fixed `/usr/bin/open`, and Linux uses fixed allowlisted `/usr/bin/gio` or `/usr/bin/xdg-open` commands. Unix launch uses no shell, strips `BROWSER` and other unneeded inherited environment authority, and falls back to a printed manual URL. Full validation runs the source browser flow on Windows, Linux, and macOS; each native packaging job repeats the flow against its frozen executable. Native package tests compare source and frozen capabilities, privacy, updates, assets, and assurance data and require read-only-package startup, abrupt-exit recovery, repeated lifecycle, and token-protected model-cleanup-first shutdown. `config/portable-development-package-contract.json` is the machine-readable boundary; Tauri/Rust remains unadmitted.

The portable supply-chain boundary has two layers. Build inputs are exact-version and wheel-hash locked, while evidence collection admits only the exact reviewed platform-specific tool/version/license set. Build outputs bind the complete one-folder tree to a file inventory and archive checksums, then independently validate bounded archive size/count, safe and case-unique member names, regular unencrypted file shape, SBOM/runtime identity, notices, target naming, and exact source/environment provenance. This provenance makes no signature or attestation claim.

The first composition boundary is deliberately non-executable. A strict engine-owned contract admits at most six registry-backed `read-only` workflow references, rejects renderer arguments and approvals, validates fresh/retry/cancel identity with one bounded retry, orders dependencies deterministically, and emits exactly typed metadata-only intermediate plan references. Cancellation ends before plan artifacts are emitted. The result always denies process, filesystem, network, approval-grant, and machine-modification authority; executable composition is a separate future admission.

Milestone 27 adds a narrow document-context boundary. The initial admitted slice uses explicit browser selection for at most five UTF-8 `.txt`/`.md` files, 64 KiB each and 128 KiB total, plus explicit PNG file selection or clipboard PNG paste for at most two screenshots, 4 MiB each and 8 MiB total. PNG signature, chunk CRCs, exact size, dimensions, and a 4096×4096/16.7-million-pixel budget are revalidated before the loopback service passes canonical base64 through Ollama's message-image field. The browser transfers normalized names, media types, exact byte counts, and selected content; no filesystem path or generic read API crosses the boundary. All attachment content is labeled untrusted inert reference data. The runtime exposes no attachment-driven tools, process launch, archive expansion, filesystem writes, or model-output execution and makes no antivirus claim. Private-network transfer shows a prominent warning and deliberate Send confirms that transfer without a separate checkbox. Screenshot understanding is visibly unverified because no image-input model evidence is admitted. Selection state stays in memory and clears on New task, direct model/provider changes, request failure, or process shutdown. A confirmed task-specific model switch retains only the context already selected for that pending request; nothing is sent before confirmation. Directories, background scanning, file watching, general filesystem reads, temporary files, broader parsers, retrieval indexes, embeddings, and persistence remain unadmitted.

Milestone 27 also defines an inactive deterministic lexical-retrieval foundation. It accepts only already validated memory attachments, fixes resource budgets and stable tie-breaking, and denies runtime routes, UI controls, provider payloads, paths, parsers, network, model ranking, embeddings, temporary files, and persistence. This contract and its hostile fixtures are evidence for a later implementation, not an admitted retrieval capability.

The optional conversation-history boundary is likewise simulation-only. A versioned contract and non-executable logical SQLite-compatible schema describe engine-owned typed operations and bounded records without importing SQLite or accepting renderer/model SQL, paths, filenames, credentials, endpoints, commands, or arbitrary filters. Pure planners cover schema upgrade and rollback, retention, metadata-only context selection, scoped deletion, busy/locked and failure recovery, backup, and restore while declaring every database, file, browser-storage, network, process, provider, and machine effect false. Private session remains the default and never creates or updates a record. Runtime storage stays blocked until encryption/key management, per-user permissions, atomicity, deletion, recovery, native packaging, and explicit product approval pass.

Milestone 28 proposes a separate controlled web-research boundary. Its current machine-readable contract and hostile fixtures are offline-only and expose no route or network effect. Future network authority stays in an engine-owned adapter; ordinary prompts cannot trigger it, and neither renderer nor model can choose a host, raw URL, credential, header, proxy, command, or environment. The initial path discloses and approves one bounded query, returns a strict inert result shape, and renders citations through trusted UI rather than model Markdown. Page retrieval, self-hosted adapters, and multi-query research remain separate gates with DNS/IP revalidation, SSRF and redirect controls, textual content limits, prompt-injection isolation, cancellation, and memory-only cleanup.

The update boundary remains outside the portable runtime. Strict offline
policies validate immutable release metadata, manifest and package identity,
then separately simulate compatibility, staged/post health, interrupted
activation recovery, rollback, retention, and disabled mode. The lifecycle
schema accepts no raw path, URL, executable, argument, environment, approval,
or renderer evidence. Its transitions are counterfactual review output and
every network, filesystem, process, installation, activation, cleanup, and
machine-effect flag remains false. No portable or browser route invokes these
policies.

The optional Milestone 22B desktop architecture adds a Tauri 2 shell without replacing these contracts:

```text
Bundled React/TypeScript UI
        |
        v
Tauri capability allowlist and native path selection
        |
        v
versioned typed stdin/stdout IPC
        |
        v
packaged Haven 42 engine sidecar
        |
        v
capability registry -> workflow registry -> existing tested engines
```

The optional desktop path loads no remote UI code, exposes no generic shell bridge, and listens on no TCP port. It cannot inherit local-web evidence. Windows, Linux, and macOS launchers, webviews, sidecars, packages, signing, updates, and uninstall behavior are promoted independently.

The broader product-navigation slice is defined by `config/ui-navigation-contract.json` and rendered as framework-neutral state by `scripts/build-ui-view-model.py`. That full-navigation model still exposes no executable path, endpoint, approval token, or execution authority; its `runtimeAdmitted` and `executionEnabled` values remain false. The smaller admitted local-web chat runtime is governed independently by `config/local-web-runtime-policy.json`.

The future native-owned authority is separately modeled by `config/native-bridge-boundary-contract.json` and `scripts/native-bridge-boundary-policy.py`. Its 55 offline cases cover canonical path grants, protected roots, external-link allowlisting, approval replay, sidecar lifecycle, environment filtering, cancellation ownership, and privilege rejection. This policy starts no process and grants no authority; it complements the 46 engine-side IPC cases but is not native implementation evidence. See `docs/native-bridge-boundary-evidence.md`.

## Repository Layers

### Project Documentation

Top-level markdown files define the product contract, architecture, roadmap, style conventions, implementation tasks, decisions, and release notes.

These files explain why the pack exists and how contributors should evolve it.

### Agent Surface Configuration

`.continue/config.yaml` is the intended entry point for the current Continue integration.

It should eventually define:

- Local model configuration
- Context providers
- Prompt references
- Rule references
- Agent or mode wiring, where supported
- MCP integration points, when implemented

### Agents

`.continue/agents` contains role-specific assistant definitions.

Agents should describe durable professional behavior, responsibilities, boundaries, and expected outputs. They should not duplicate every task instruction from prompts or every standard from rules.

Initial agents:

- `senior-engineer.md`
- `architect.md`
- `security-engineer.md`

Secondary agents:

- `reviewer.md`
- `performance.md`
- `documentation.md`
- `product-manager.md`

### Prompts

`.continue/prompts` contains task-specific workflows.

Prompts should define:

- When to use the workflow
- What context to gather
- How to reason about the task
- Expected output format
- Risk checks and verification steps

Prompts should reference rules by concept, but should avoid copying entire rule files.

### Rules

`.continue/rules` contains reusable engineering standards.

Rules should be concise, enforceable, and broadly applicable. They should define expectations for quality, security, maintainability, testing, logging, API design, and framework usage.

Rules should avoid task-specific instructions that belong in prompts.

### Project Profiles And Optional Rule Activation

`config/project-profile-rules.json` defines deterministic ecosystem signals.
The cross-platform `get-project-profile` scripts inspect relative filenames,
emit a sanitized project profile, and select optional language rule-pack IDs.

During project-local installation, selected sources from
`.continue/rule-packs/` are copied into
`.continue/rules/active-language-<id>.md`. Unmatched source packs remain
inactive. Shared-assets mode skips this project-specific step because one
central asset folder can serve repositories with different ecosystems.

### Templates

`.continue/templates` contains structured output formats for artifacts that may be committed or shared.

Templates should make review outputs consistent and easy to scan.

### Capability Evidence

`config/capability-evidence-contract.json` defines Capability Evidence Contract
v2, and `config/evidence-catalog.tsv` stores sanitized records. Capability
readiness is keyed by surface, surface version, provider, model, operating
system, operation, and validation mode.

Recommendation and reporting consumers aggregate duplicate keys to the most
conservative status while retaining provenance. They do not inherit write
readiness across agent surfaces, operations, or operating systems.

### Workflow Orchestration

`config/workflows.json` provides stable workflow IDs and platform entry points.
`config/workflow-envelope-contract.json` defines schema-v1 requests and
execution responses for the PowerShell and native Linux/macOS dispatchers.

The envelope reports accepted, progress, warning, result, and error events.
Argument values and child output are omitted by default so future UI callers
do not casually persist local paths, endpoints, or repository output. Existing
direct CLI dispatcher behavior remains supported.

The onboarding/navigation family preserves three beginner-facing commands but
shares non-domain mechanics. `scripts/OnboardingGuidance.psm1` owns catalog
loading, workflow lookup, platform command rendering, and report output for
PowerShell. The Linux/macOS wrappers delegate argument routing to
`scripts/onboarding-guidance.shared.sh`. Full native rendering for these
informational views remains a known portability gap; native validation and
installer workflows are unaffected and continue to require no PowerShell.

## Responsibility Boundaries

- `config.yaml` wires the pack together.
- Agents define role behavior.
- Prompts define task flow.
- Rules define standards.
- Templates define durable output shape.
- Capability evidence defines what a specific surface/model/environment operation has actually proven.
- Project profiles define which optional language rules a target repository activates and the filename evidence supporting that decision.
- The language workflow validation matrix maps optional rule packs to medium-complexity fixtures and required operations while keeping unexecuted editor/model evidence explicitly pending.
- Workflow registry and envelope contracts define stable, versioned automation boundaries without owning workflow business logic.
- Top-level docs define project intent and governance.

## Dependency Policy

The pack uses a simple dependency direction:

```text
config.yaml
  -> agents
  -> prompts
  -> rules
  -> templates

top-level docs govern all layers but are not runtime dependencies
```

Allowed references:

- `config.yaml` may reference rules, prompts, docs, context providers, models, and future MCP servers.
- Agents may reference rules and prompts conceptually.
- Prompts may reference rules and templates conceptually.
- Rules should not depend on prompts or agents.
- Templates should not depend on prompts, agents, or rules.
- Top-level docs may describe any layer.

This keeps reusable policy below workflow orchestration and prevents circular instruction dependencies.

## Domain Language

The project domain is local-first engineering workflow guidance.

- Pack: the complete reusable engineering-agent bundle in this repository.
- Agent surface: the editor, CLI, or runtime environment that loads the pack assets and executes model/tool workflows.
- Agent: a role-specific assistant definition.
- Prompt: a task-specific workflow that can be invoked by a user.
- Rule: reusable engineering guidance applied across workflows.
- Template: structured output for a durable artifact or review.
- Finding: a concrete issue identified during review.
- Recommendation: an actionable change or decision proposal.
- Workflow: a repeatable task sequence such as repository discovery, code review, or security review.
- Model lane: a purpose-specific local model role such as WRITE SAFE, PLAN ONLY, or DEEP REVIEW.
- Selection policy: a versioned scoring contract that requires exact capability evidence and ranks eligible models for one model lane.
- Model-fit profile: a versioned, reviewable memory-planning assumption for an exact model tag, including quantization assumption, weights, context-sensitive cache, runtime overhead, architecture, and reserve.
- Quantization plan: a no-effect decision that binds immutable source identity, license, target runtime/format, local hardware inputs, storage, disclosures, and either an exact trusted artifact, a possible local derivative, or no safe recommendation.
- Quantized-artifact manifest: a local lifecycle record for exact input/output hashes, pinned tools, recipe parameters, runtime/hardware evidence, validation, activation, rollback, and cleanup.

## Initial Architecture Decisions

- The pack is local-first and should work with Ollama before cloud model assumptions are introduced.
- Continue remains the first supported agent surface, but the project should avoid coupling reusable guidance to Continue-only behavior when a portable abstraction is practical.
- The first ecosystem focus is .NET and ASP.NET Core, with enterprise-grade guidance kept useful for smaller projects too.
- Clean Architecture guidance should be practical and testable, not ceremonial.
- Security and performance review guidance should be built into early milestones.
- MCP and SonarQube support should be documented as integration targets until implemented.
- Tool-enabled project changes should be treated as an approved execution mode, not the default review posture.
- Local model selection should remain hardware-aware but portable, keeping machine-specific endpoints and hardware details out of committed shared config.
- Model-lane eligibility must require exact surface, version, provider, operating system, operation, and validation-mode evidence; scores may rank eligible models but must not manufacture missing capability evidence.
- WRITE SAFE selection should favor validated reliability and VRAM headroom, while planning and review may favor greater fitting capacity after exact lane evidence is established.
- Curated model-fit profiles should take precedence over name-derived estimates, disclose every assumption, and keep unknown tags labeled as low-confidence rather than implying measured compatibility.
- Trusted compatible pre-quantized artifacts should be preferred over local conversion; equal bit counts never imply format, kernel, runtime, or accelerator compatibility.
- Quantization planning may inspect local hardware but must omit persistent identity fields, perform no network/download/conversion/activation effects, and keep profiles and model artifacts out of commits.
- Future UI callers should use stable workflow IDs and the versioned envelope rather than invoking or parsing individual script families directly.

## Open Questions

- Should the current local file references in `.continue/config.yaml` be adjusted after validation in Continue?
- Which Ollama models should be recommended for larger enterprise repositories?
- Which additional agent surfaces should be validated first after Continue?
- Should agents be further integrated as native Continue agent files if the target Continue version supports richer agent packaging?
- How should SonarQube findings be provided to the assistant: pasted reports, MCP, CLI output, or another integration?
- Which MCP servers are in scope for the first integration milestone?
- Should prompt examples be added as committed fixtures or generated on demand during release validation?
- What tool execution surface should be considered the supported path for approved project changes?
- Which hardware signals are reliable enough to drive dynamic local model selection across Windows, Linux, and macOS?
