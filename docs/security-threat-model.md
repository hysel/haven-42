# Security Threat Model

## Assets and trust boundaries

Haven 42 protects user repositories, local files, prompts, responses, models, credentials, generated artifacts, approvals, update state, and provider endpoints. The desktop renderer and all model output are untrusted input. Native IPC, the workflow dispatcher, provider adapters, filesystem grants, packaged binaries, and update verification are separate trust boundaries.

## Principal threats

- Prompt or model output attempts to select commands, executables, arguments, paths, URLs, providers, or approvals.
- A malicious web page targets a predictable localhost port through cross-site forms, fetches, DNS rebinding, framing, or browser-content injection.
- A local-web request attempts server-side request forgery through public, link-local, credential-bearing, redirected, hostname-based, or path-bearing provider endpoints.
- A completed, failed, cancelled, switched, or idle text task leaves a model resident beyond the configured bounded warm period and consumes accelerator power after Haven 42 stops using it.
- A compromised renderer sends malformed frames, replays approval tokens, crosses sessions, cancels another request, or binds events to the wrong request.
- Path traversal, symlink or reparse-point swaps, and protected-directory writes escape an approved grant.
- A provider response leaks repository data, endpoint details, process inventories, machine paths, or secrets into committed evidence.
- A malicious or stale update manifest causes downgrade, target confusion, duplicate-asset ambiguity, checksum bypass, unsigned activation, or user-data replacement.
- Retry, resume, timeout, or crash handling repeats a write or leaves an orphan process.
- Cleanup deletes preexisting models, provider data, or user artifacts.
- A renderer forges a validated state, approval, or evidence; supplies a raw endpoint, path, credential, command, or environment; requests public binding; or reuses evidence across capability domains.

## Controls

Policy selects registered operations; prompts never grant authority. IPC is typed, size-bounded, schema-strict, session-bound, and default-deny. Filesystem access requires native canonicalization and narrow expiring grants. Writes require an approval bound to the exact operation and effects. Updates use immutable releases, exact target selection, hashes, provenance, side-by-side staging, health checks, and rollback; the current offline policy cannot activate anything. Reliability rules prevent silent write retries and unrelated process termination. Evidence is sanitized and local data deletion is explicit and ownership-aware.

Onboarding settings are schema-bounded and default-deny. The renderer cannot supply state, evidence, approval, commands, raw endpoints, raw paths, or plaintext credentials. It receives and submits opaque references only; the evaluator never resolves or returns them. Existing setups require independent validation, cross-domain admission is rejected, public binding is absent, and settings outside exact passed evidence become unverified rather than inheriting trust.
The admitted local-web application binds only to `127.0.0.1`; validates the exact Host and Origin; requires a random in-memory request token; rejects cross-site fetch metadata; serves bundled assets under a restrictive Content Security Policy; accepts only bounded JSON; and infers loopback or private-LAN scope from an IP-literal Ollama endpoint through the shared no-redirect provider policy. It exposes no repository, filesystem, shell, process, download, update, or arbitrary provider surface. The server accepts only `general.chat`, `content.write`, and `content.summarize`; non-chat modes accept exactly one user input. Model residency is bounded to immediate, 5-, 15-, or 30-minute policies. Only one session model stays active; model/provider changes, New task, failures, idle expiry, and shutdown explicitly unload and verify cleanup.


## Residual risk and promotion gates

The local-web admission applies only to status, Ollama discovery, model selection, `general.chat`, `content.write`, and `content.summarize`; it does not admit the workflow, image, persistence, update, remote-access, or native-package surfaces. No optional desktop runtime ships until actual Windows, Linux, and macOS binaries pass renderer, IPC, canonical-path, lifecycle, update, rollback, packaging, uninstall, privilege, and security tests. Unsupported or failed provider cells remain documentation-only and leave no executable integration.
