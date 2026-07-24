# Security Threat Model

## Assets and trust boundaries

Haven 42 protects user repositories, local files, prompts, responses, models, credentials, generated artifacts, approvals, update state, and provider endpoints. The desktop renderer and all model output are untrusted input. Native IPC, the workflow dispatcher, provider adapters, filesystem grants, packaged binaries, and update verification are separate trust boundaries.

## Principal threats

- Prompt or model output attempts to select commands, executables, arguments, paths, URLs, providers, or approvals.
- A malicious web page targets a predictable localhost port through cross-site forms, fetches, DNS rebinding, framing, or browser-content injection.
- A malicious or compromised renderer repeatedly triggers expensive readiness scans, supplies executable/argument/environment input, forges hardware facts or a snapshot ID, or causes raw probe output, identity, private paths, credentials, or network addresses to cross the engine boundary.
- A setup screen turns a recommendation into installation authority, injects an unregistered component, URL, command, or path, or claims that renderer consent is an OS-level approval.
- A local-web request attempts server-side request forgery through public, link-local, credential-bearing, redirected, hostname-based, or path-bearing provider endpoints.
- A completed, failed, cancelled, switched, or idle text task leaves a model resident beyond the configured bounded warm period and consumes accelerator power after Haven 42 stops using it.
- A compromised renderer sends malformed frames, replays approval tokens, crosses sessions, cancels another request, or binds events to the wrong request.
- Path traversal, symlink or reparse-point swaps, and protected-directory writes escape an approved grant.
- A provider response leaks repository data, endpoint details, process inventories, machine paths, or secrets into committed evidence.
- A malicious or stale update manifest or activation journal causes downgrade, target confusion, duplicate-asset ambiguity, checksum bypass, unsigned activation, approval replay, interrupted-state confusion, unsafe retention cleanup, or user-data replacement.
- Forged GitHub release metadata points the update checker at a fork, draft, prerelease, mutable release, mismatched tag, duplicate manifest, credential-bearing URL, or unapproved asset host.
- Retry, resume, timeout, or crash handling repeats a write or leaves an orphan process.
- Cleanup deletes preexisting models, provider data, or user artifacts.
- A renderer forges a validated state, approval, or evidence; supplies a raw endpoint, path, credential, command, or environment; requests public binding; or reuses evidence across capability domains.

## Controls

Policy selects registered operations; prompts never grant authority. IPC is typed, size-bounded, schema-strict, session-bound, and default-deny. Filesystem access requires native canonicalization and narrow expiring grants. Writes require an approval bound to the exact operation and effects. Updates use immutable releases, exact target selection, hashes, provenance, side-by-side staging, health checks, and rollback; the current offline manifest, release-metadata, and lifecycle policies cannot use the network, download, write, stage, activate, roll back, clean, install, elevate, terminate processes, or touch user data. The lifecycle policy rejects raw paths and renderer authority, treats all evidence booleans as untrusted scenario inputs rather than proof, protects the active and previous known-good versions, and deterministically models failed health and interrupted-journal recovery. Reliability rules prevent silent write retries and unrelated process termination. Evidence is sanitized and local data deletion is explicit and ownership-aware.

Onboarding settings are schema-bounded and default-deny. The renderer cannot supply state, evidence, approval, commands, raw endpoints, raw paths, or plaintext credentials. It receives and submits opaque references only; the evaluator never resolves or returns them. Existing setups require independent validation, cross-domain admission is rejected, public binding is absent, and settings outside exact passed evidence become unverified rather than inheriting trust.
The admitted local-web application binds only to `127.0.0.1`; validates the exact Host and Origin; requires a random in-memory request token; rejects cross-site fetch metadata; serves bundled assets under a restrictive Content Security Policy; accepts only bounded JSON; and classifies IP-literal provider endpoints through the shared no-redirect policy. It exposes no repository, generic filesystem, shell, arbitrary process, download, update, or arbitrary provider surface. Recommendation catalog loading rejects unknown fields, unsafe or duplicate model names, invalid or mismatched digests, forged capability/operation bindings, duplicate evidence IDs, traversal-like evidence paths, and evidence rows that do not exactly match committed records. Automatic text selection requires exact name, digest, and capability evidence. Provider-reported metrics use a strict nullable numeric shape and are memory-only.

The text server accepts only `general.chat`, `content.write`, and
`content.summarize`; non-chat modes accept exactly one user input. Software
admits only unique `uiReady`, `read-only` registry records and emits plan
artifacts without arguments or process execution. Images admit only a loopback
ComfyUI endpoint, the promoted SDXL checkpoint, a fixed built-in workflow,
bounded settings, and a capped PNG. The client cannot supply a model, node,
filename, provider path, or workflow graph. API history is cleared, browser
delivery is memory-only, and unavoidable provider retention is warned.

Event rendering rejects unknown fields, malformed codes, gaps, reordering,
multiple terminals, wrong terminal kinds, and events after a terminal.
Advanced unverified model use emits a warning. Provider failures emit typed
errors, never retry automatically, and may restore failed text input only in
browser memory for a new request. Model residency is bounded to immediate, 5-,
15-, or 30-minute policies. Only one session text model stays active;
model/provider changes, New task, failures, idle expiry, and shutdown explicitly
unload and verify cleanup.

Readiness inspection is an explicit CSRF-protected POST with a single concurrent scan, a 15-second whole-scan deadline, three-second per-probe deadlines, and a 64 KiB hard output bound. Only fixed engine-owned probes run with `shell=False`, a minimal environment, no stdin, no network, and no renderer-provided executable or argument. Windows accelerator discovery derives a small allowlisted fact set from a fixed read-only registry location; raw registry values and paths are not returned. The server validates the exact schema and all-false effect declaration before retaining a snapshot in memory. Setup planning accepts only the current unexpired snapshot ID and one registered intent. The strict component registry cannot be extended by the renderer, every install control is disabled, and the simulation-only broker rejects commands, URLs, paths, environment, evidence, unknown fields, and renderer approval.

## Residual risk and promotion gates

The local-web admission applies to read-only readiness inspection, zero-effect setup planning, status, exact-digest Ollama discovery and text, plan-only registered read-only software workflows, and the exact promoted Linux ComfyUI/SDXL image profile through loopback. It does not admit workflow process execution, arbitrary provider profiles, client persistence, installation, elevation, service or driver changes, updates, remote UI access, or Tauri packaging. No optional desktop runtime ships until actual Windows, Linux, and macOS binaries pass renderer, IPC, canonical-path, lifecycle, update, rollback, packaging, uninstall, privilege, and security tests. Unsupported or failed provider cells remain documentation-only and leave no executable integration.
