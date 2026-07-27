# Security Threat Model

## Assets and trust boundaries

Haven 42 protects user repositories, local files, prompts, responses, models, credentials, generated artifacts, approvals, update state, and provider endpoints. The desktop renderer and all model output are untrusted input. Native IPC, the workflow dispatcher, provider adapters, filesystem grants, packaged binaries, and update verification are separate trust boundaries.

## Principal threats

- Prompt or model output attempts to select commands, executables, arguments, paths, URLs, providers, or approvals.
- A malicious web page targets a predictable localhost port through cross-site forms, fetches, DNS rebinding, framing, or browser-content injection.
- A hostile inherited environment redirects automatic browser launch to an attacker-selected command, or a renderer supplies a non-loopback launch URL.
- A malicious or compromised renderer repeatedly triggers expensive readiness scans, supplies executable/argument/environment input, forges hardware facts or a snapshot ID, or causes raw probe output, identity, private paths, credentials, or network addresses to cross the engine boundary.
- A setup screen turns a recommendation into installation authority, injects an unregistered component, URL, command, or path, or claims that renderer consent is an OS-level approval.
- A public model search leaks local context, follows a redirect, accepts a hostile model name or command, treats catalog claims as evidence, or turns desired selection into download or execution authority.
- A future research search leaks conversation or file context, lets the model choose a destination, reaches a private service through SSRF or DNS rebinding, follows a hostile redirect, executes page content, forges citations, or turns retrieved prompt injection into additional authority.
- A future history feature accepts renderer/model SQL or paths, stores secrets or attachment bytes, silently mixes conversations, weakens Private session, exposes unencrypted records, mishandles a migration or disk-full failure, incompletely deletes WAL/journal/backups, or restores hostile data.
- A local-web request attempts server-side request forgery through public, link-local, credential-bearing, redirected, hostname-based, or path-bearing provider endpoints.
- A completed, failed, cancelled, switched, or idle text task leaves a model resident beyond the configured bounded warm period and consumes accelerator power after Haven 42 stops using it.
- A compromised renderer sends malformed frames, replays approval tokens, crosses sessions, cancels another request, or binds events to the wrong request.
- Path traversal, symlink or reparse-point swaps, and protected-directory writes escape an approved grant.
- A provider response leaks repository data, endpoint details, process inventories, machine paths, or secrets into committed evidence.
- Model-supplied Markdown or HTML creates active markup, links, remote images, scripts, event handlers, misleading hidden content, or an accessibility-breaking document outline.
- A malicious or stale update manifest or activation journal causes downgrade, target confusion, duplicate-asset ambiguity, checksum bypass, unsigned activation, approval replay, interrupted-state confusion, unsafe retention cleanup, or user-data replacement.
- Forged GitHub release metadata points the update checker at a fork, draft, prerelease, mutable release, mismatched tag, duplicate manifest, credential-bearing URL, or unapproved asset host.
- A renderer or compromised update component forges, replays, expires, or substitutes a verifier receipt; confuses a verifier profile, trust root, release, asset, platform, or digest; or treats a structural receipt as cryptographic proof.
- A verifier-registry transition skips a version, removes every continuity anchor, backdates a candidate, uses a new or retired signer, forges a threshold claim, replays a transition, or treats rotation metadata as authorization to change the trust store.
- A future composition request broadens an approval scope, reuses a token across attempts or lifecycles, substitutes typed intermediate artifacts, retries after possible effects, or treats cancellation and uncertain recovery as execution authority.
- A future effect journal omits or reorders records, substitutes an admission binding, forges completion, records an unapproved effect, resumes after uncertain effects, or treats renderer/runtime claims as durable recovery evidence.
- Retry, resume, timeout, or crash handling repeats a write or leaves an orphan process.
- Cleanup deletes preexisting models, provider data, or user artifacts.
- A renderer forges a validated state, approval, or evidence; supplies a raw endpoint, path, credential, command, or environment; requests public binding; or reuses evidence across capability domains.

## Controls

Policy selects registered operations; prompts never grant authority. IPC is typed, size-bounded, schema-strict, session-bound, and default-deny. Filesystem access requires native canonicalization and narrow expiring grants. Writes require an approval bound to the exact operation and effects. Updates use immutable releases, exact target selection, hashes, provenance, side-by-side staging, health checks, and rollback; the current offline manifest, release-metadata, and lifecycle policies cannot use the network, download, write, stage, activate, roll back, clean, install, elevate, terminate processes, or touch user data. The lifecycle policy rejects raw paths and renderer authority, treats all evidence booleans as untrusted scenario inputs rather than proof, protects the active and previous known-good versions, and deterministically models failed health and interrupted-journal recovery. Reliability rules prevent silent write retries and unrelated process termination. Evidence is sanitized and local data deletion is explicit and ownership-aware.

The structural update-trust handoff accepts only a schema-strict, short-lived,
single-use receipt bound to an exact verifier profile and binary digest, trust
root, repository, immutable release and commit, manifest, asset, and platform.
It rejects raw signatures, certificates, transparency material, paths, URLs,
unknown fields, mismatches, expiry, and replay. The current evaluator performs
no cryptography, establishes no trust, promotes no evidence, and cannot stage or
activate a package; scenario claim booleans remain non-authoritative.

The verifier-transition simulator requires consecutive registry versions,
validity overlap and extension, exact verifier continuity, active trust-root
continuity, current-root threshold descriptions, and replay defense. It accepts
no raw keys, signatures, certificates, proofs, paths, or URLs. Authorization
claims remain non-authoritative, so no transition is accepted and no registry,
trust store, runtime verifier, package, credential, or filesystem state changes.

The future task-execution admission simulator binds a complete approval
lifecycle to an exact admission, composition, step, registered workflow,
attempt, sorted effect disclosure, and metadata-only typed artifact set. It
rejects secrets in approval descriptions, raw token material, artifact content
or paths, prohibited machine effects, cross-attempt reuse, cancellation with
approval data, unsafe retries, and uncertain recovery after possible effects.
Even a structurally valid request cannot accept an approval, execute a workflow,
or produce filesystem, process, network, service, driver, firewall, credential,
or machine effects.

The effect-journal simulator chains strict scenario records to the exact
admission scope and approval identifier. It rejects gaps, reordering, digest
substitution, cross-admission reuse, forged or incomplete completion, effects
outside scope, records after a terminal event, unsafe retry, and understated
recovery risk. Start, completion, failure, and cancellation records remain
untrusted claims: no journal is persisted, no effect is proven, and neither
retry, recovery, approval consumption, nor execution is authorized.

Onboarding settings are schema-bounded and default-deny. The renderer cannot supply state, evidence, approval, commands, raw endpoints, raw paths, or plaintext credentials. It receives and submits opaque references only; the evaluator never resolves or returns them. Existing setups require independent validation, cross-domain admission is rejected, public binding is absent, and settings outside exact passed evidence become unverified rather than inheriting trust.
The admitted local-web application binds only to `127.0.0.1`; validates the exact Host and Origin; requires a random in-memory request token; rejects cross-site fetch metadata; serves bundled assets under a restrictive Content Security Policy; accepts only bounded JSON; and classifies IP-literal provider endpoints through the shared no-redirect policy. Automatic browser launch accepts only the engine-generated IPv4-loopback HTTP origin, uses fixed platform mechanisms without a shell, ignores `BROWSER`, strips unneeded inherited Unix environment authority, and safely falls back to a printed URL. It exposes no repository, generic filesystem, shell, arbitrary process, download, update, or arbitrary provider surface. Recommendation catalog loading rejects unknown fields, unsafe or duplicate model names, invalid or mismatched digests, forged capability/operation bindings, duplicate evidence IDs, traversal-like evidence paths, and evidence rows that do not exactly match committed records. Automatic text selection requires exact name, digest, and capability evidence. Provider-reported metrics use a strict nullable numeric shape and are memory-only.

Public model search is a separately disclosed outbound boundary. It accepts
only a bounded phrase after explicit opt-in, targets one fixed HTTPS origin,
rejects redirects and oversized or malformed HTML, and emits at most 20 strict
model names. The renderer revalidates the exact response shape and reconstructed
copy command. Candidate selection stays in browser memory and cannot reach text
execution until the provider's installed inventory contains that exact name.

The text server accepts only `general.chat`, `content.write`, and
`content.summarize`, each with the same bounded 20-message conversation limit.
The unified browser surface uses a narrow, local-only prefix hint to select a
writing or summarization prompt; the hint grants no authority and no text is
sent while a different-model confirmation is visible. A model change requires
an explicit user action, while keeping the current model remains available.
Software
admits only unique `uiReady`, `read-only` registry records and emits plan
artifacts without arguments or process execution. Images admit only a loopback
ComfyUI endpoint, the promoted SDXL checkpoint, a fixed built-in workflow,
bounded settings, and a capped PNG. The client cannot supply a model, node,
filename, provider path, or workflow graph. API history is cleared, browser
delivery is memory-only, and unavoidable provider retention is warned.

Event rendering rejects unknown fields, malformed codes, gaps, reordering,
multiple terminals, wrong terminal kinds, and events after a terminal.
Assistant text rendering accepts only a small Markdown block/inline allowlist,
creates every element directly, assigns all model text through `textContent`,
maps model headings below the page heading, and never creates model-supplied
links, images, HTML, scripts, or handlers. Hostile tags remain visible text.
Prompt recall is a bounded task-local browser-memory ring with a 20-entry
default and fixed 50/100-entry options. It stores only submitted user text,
suppresses consecutive duplicates, preserves multiline cursor behavior, and
clears on New task, a direct model/provider change, and shutdown without browser
storage or server persistence.
Advanced unverified model use emits a warning. Provider failures emit typed
errors, never retry automatically, and may restore failed text input only in
browser memory for a new request. Model residency is bounded to immediate, 5-,
15-, or 30-minute policies. Only one session text model stays active;
model/provider changes, New task, failures, idle expiry, and shutdown explicitly
unload and verify cleanup.

Readiness inspection is an explicit CSRF-protected POST with a single concurrent scan, a 15-second whole-scan deadline, three-second per-probe deadlines, and a 64 KiB hard output bound. Only fixed engine-owned probes run with `shell=False`, a minimal environment, no stdin, no network, and no renderer-provided executable or argument. Windows accelerator discovery derives a small allowlisted fact set from a fixed read-only registry location; raw registry values and paths are not returned. The server validates the exact schema and all-false effect declaration before retaining a snapshot in memory. Setup planning accepts only the current unexpired snapshot ID and one registered intent. The strict component registry cannot be extended by the renderer, every install control is disabled, and the simulation-only broker rejects commands, URLs, paths, environment, evidence, unknown fields, and renderer approval.

## Residual risk and promotion gates

Milestone 27 admits only explicit bounded UTF-8 `.txt`/`.md` attachment and browsed-or-pasted PNG screenshots. The browser exposes no arbitrary path or background scan authority; the loopback engine revalidates normalized names, exact media types and byte counts, text count/size budgets, PNG base64 and signature, chunk bounds and CRCs, screenshot count/size/dimension/pixel budgets, duplicates, NUL content, and provider consent. All attachment content, including visible image text, is labeled untrusted inert reference data and cannot add authority. The runtime exposes no attachment-driven tool invocation, shell, process launch, filesystem write, archive expansion, or model-output execution path, and makes no antivirus claim. Screenshot transport uses Ollama's documented message-image field, while model image understanding stays unverified and visibly warned until exact evidence passes. Private-network transfer shows a prominent warning and deliberate Send confirms it without a separate checkbox; the engine still rejects a forged request missing that confirmation. State remains memory-only, and no temporary file is allowed. PDF, Office, archive, OCR, directory, retrieval-index, embedding, and persistent-index support do not inherit approval from this slice.

The lexical-retrieval contract is simulation-only. It grants no runtime route, UI, provider payload, filesystem path, parser, network, model-ranking, embedding, temporary-file, or persistent-index authority. Its hostile fixtures are inert data used to preserve the future boundary; they are not a retrieval engine.

The conversation-history contract is also simulation-only. Its logical
SQLite-compatible schema includes no executable SQL, and its planner does not
import SQLite, open or create a database, read or write a file, invoke a
provider, or expose a runtime route. Exact typed requests reject SQL, queries,
paths, filenames, URLs, endpoints, credentials, commands, environment values,
unknown fields, cross-conversation context, unvalidated summaries, schema
downgrades, attachment bytes, and unverified or active-content restores. Pure
plans model atomic upgrade/rollback, retention, bounded metadata-only context
selection, complete deletion scope, busy/locked, interrupted-write, corruption,
disk-full, backup, and restore behavior with every effect false. Private session
remains the write-free default. Standard SQLite is treated as unencrypted at
rest; runtime persistence stays blocked until encryption/key management,
least-privilege per-user storage, deletion/recovery, and native package evidence
pass separate approval.

Milestone 28 controlled web research remains proposed and unadmitted. Its offline contract and hostile fixtures cannot open a socket, resolve DNS, fetch a URL, automate a browser, execute a page, download content, or expose a model tool. Its promotion gate requires explicit reviewed queries, engine-owned fixed adapters, no renderer/model destination control, DNS and resolved-IP revalidation, redirect and content limits, no page execution, trusted citation rendering, hostile-content prompt isolation, exact source accounting, and residue-free memory cleanup. The admitted fixed Ollama catalog search does not grant or imply general research-search authority.

The local-web admission applies to read-only readiness inspection, zero-effect setup planning, status, exact-digest Ollama discovery and text, plan-only registered read-only software workflows, and the exact promoted Linux ComfyUI/SDXL image profile through loopback. It does not admit workflow process execution, arbitrary provider profiles, client persistence, installation, elevation, service or driver changes, updates, remote UI access, or Tauri packaging. No optional desktop runtime ships until actual Windows, Linux, and macOS binaries pass renderer, IPC, canonical-path, lifecycle, update, rollback, packaging, uninstall, privilege, and security tests. Unsupported or failed provider cells remain documentation-only and leave no executable integration.
