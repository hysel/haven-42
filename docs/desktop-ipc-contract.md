# Desktop IPC And Capability Contract

## Purpose

`config/desktop-ipc-contract.json` and `config/desktop-capability-policy.json` define the first versioned security boundary for the Milestone 22 Tauri application. They extend the existing workflow envelope and typed artifact contract; they do not create a second workflow engine or grant the UI direct script access.

The ordinary desktop application loads bundled local assets and launches exactly one packaged, target-matched Haven 42 engine sidecar. Messages use UTF-8 JSON Lines over private stdin/stdout. No desktop HTTP server or listening TCP port is part of this contract.

## Authority Flow

```text
Bundled renderer
    | one of seven allowlisted Tauri commands
    v
Native bridge: schema, registry, grant, approval, and size checks
    | versioned JSON Lines; no raw command or path
    v
Packaged engine sidecar
    | registered capability/workflow implementation only
    v
Typed progress, warning, result, error, and artifact events
```

The renderer is untrusted input. Tauri permissions reduce exposure, but the native bridge and engine must independently validate the request. Tauri's [capability model](https://v2.tauri.app/security/capabilities/) explicitly warns that permissive Rust code or scopes remain application risks.

## Operation Resolution

A request chooses one `operationKind` and exact `operationId`:

- `capability` resolves only against `config/capabilities.json`;
- `workflow` resolves only against `config/workflows.json` and requires `uiReady: true`;
- unknown, unavailable, blocked, failed, or policy-conflicting operations fail closed;
- `configuration-required` may render setup guidance but cannot execute until runtime discovery passes;
- the renderer never supplies a script name, executable, command, working directory, endpoint, URL, or implementation path.

The engine converts an admitted workflow request into the existing schema-v1 workflow envelope. Results use `config/typed-artifact-contract.json`, and progress/error semantics extend `config/workflow-envelope-contract.json`.

## Path Grants

The renderer cannot pass raw paths into an execution request. A user selects a repository, input file, or artifact directory through a narrowly scoped native dialog. The native bridge canonicalizes the selection and issues an opaque, expiring, session-bound grant.

Every later access re-resolves and canonicalizes the target. The bridge rejects traversal, root escape, disallowed symlink or Windows reparse-point escape, expired or transferred grants, grant-type mismatch, and attempts to access application, engine, update, rollback, credential, or key directories. Read permission never becomes write permission. The UI previews every intended write location before approval.

Application-owned paths such as the session's default artifact directory follow the same native policy but do not require the renderer to learn their raw location unless the user asks to reveal the artifact.

## Effect Approval

Planning is distinct from execution and application. Network access, downloads, external providers, writes, `apply` mode, and approved-write workflows require the existing policy disclosure plus an opaque approval token when applicable.

The native layer binds the token to the request, operation, mode, disclosed effects, grants, session, and expiry. A changed input or effect requires a new preview and approval. Tokens are short-lived, single-use, held in memory, and never written to logs or configuration.

## Message And Lifecycle Rules

- One UTF-8 JSON object occupies one line; the maximum encoded line is 1 MiB.
- Request IDs contain only bounded safe ASCII characters and are unique among active requests.
- Event sequence numbers start at one, increase strictly, and end in exactly one `result` or `error`.
- Cancellation targets only an active request in the same desktop session and cannot signal an arbitrary process.
- Malformed JSON, unsupported schemas, additional fields, forbidden command/path fields, and mismatched grants or approvals are rejected.
- Repeated framing violations terminate the sidecar session. The UI may offer a clean restart; it must not silently replay a write.
- Closing the desktop app stops the child process. Orphan detection and forced termination require platform-specific lifecycle tests before promotion.

## Tauri Capability Translation

When runtime files are eventually scaffolded, only the `main` window is assigned a capability. Explicitly enumerate the seven renderer commands from `config/desktop-capability-policy.json`; do not use a wildcard capability. Do not configure remote capability URLs.

The dialog permission is limited to user-driven selection. Sidecar spawn is native-owned and fixed to the packaged target-triple binary. No shell, process, generic filesystem, or arbitrary URL-opening API is exported to JavaScript. External documentation links pass through a native allowlist and require an explicit user action.

The production Content Security Policy permits only bundled application resources required by the build. Remote pages, scripts, styles, fonts, frames, inline script, and `unsafe-eval` remain disabled. Development-only exceptions cannot enter a release configuration.

## Required Negative Tests

Before any runtime code is admitted, automated tests must prove rejection of:

1. malformed, oversized, duplicate-ID, additional-property, and wrong-version messages;
2. arbitrary commands, executable paths, arguments, working directories, raw paths, URLs, and endpoints;
3. unknown capability/workflow IDs and workflows without `uiReady: true`;
4. unavailable/blocked/failed operations and configuration-required execution without successful discovery;
5. traversal, symlink/reparse escape, grant reuse, read-to-write escalation, and protected-directory access;
6. missing, expired, reused, or altered-effect approval tokens;
7. out-of-order/duplicate terminal events and cross-session cancellation;
8. remote navigation, remote resource loading, and access from any unassigned window/webview;
9. renderer attempts to select the sidecar binary, arguments, environment, or working directory;
10. headless-loopback settings appearing in the ordinary desktop build.

These contract checks are necessary but not sufficient. Native Windows, Linux, and macOS build/install/launch/shutdown/uninstall tests, WebView inspection, dependency audits, sidecar packaging, state preservation, and signing gates remain separate promotion requirements.

## Sidecar Policy Reference

`scripts/desktop-ipc-policy.py` implements the engine-side, standard-library admission boundary and a 46-case offline hostile self-test. It rejects malformed and oversized frames, invalid UTF-8, extra or forbidden nested command/path/URL fields, wrong schemas and field types, duplicate active requests, unknown or non-UI operations, unavailable execution, invalid or duplicated grants, missing/replayed/expired/mismatched approvals, cross-session cancellation, inactive cancellation, and invalid event bindings, sequences, or terminal events.

This is sidecar policy evidence only. It is not a listening service, accepts no production message-processing CLI mode, starts no process, and grants no filesystem or network authority. The future native Rust bridge must independently enforce the same rules plus canonical path, symlink/reparse, protected-directory, WebView, process lifecycle, and privilege tests against the admitted runtime. No native bridge test is marked complete until that code exists and passes on each promoted platform.
