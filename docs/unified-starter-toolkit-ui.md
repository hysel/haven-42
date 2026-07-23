# Unified Starter Toolkit UI

## Purpose

The future starter-toolkit UI should give new and experienced AI users one guided surface for general chat and content tasks, software work, setup, hardware profiling, model choice, config generation, agent-surface testing, validation, cleanup, and release readiness.

The UI must be a wrapper over existing workflow registry entries and tested scripts. It should not reimplement hardware profiling, recommendation logic, config generation, evidence parsing, or validation.

## Primary Users

| User | Need |
| --- | --- |
| Beginner local user | A short path from prerequisites to health check, model recommendation, install, and validation. |
| General AI user | A repository-optional path to chat, writing, summarization, image creation, and clearly identified output artifacts. |
| Advanced local user | Direct access to profile, recommend, test, install, evidence, cleanup, and release workflows. |
| Maintainer | A dashboard over milestone status, evidence gaps, workflow registry coverage, and release readiness. |
| Team or enterprise user | Evidence-first install/configuration decisions with audit-friendly output and no private data committed. |

## First Screens

The first screen should ask what the user wants to do, then route to an available capability or the setup console when prerequisites are missing.

The approved first product slice, navigation map, interaction flow, and low-fidelity wireframes are recorded in `docs/product-ui-first-slice.md`. The framework-neutral source is `config/ui-navigation-contract.json`, and `scripts/build-ui-view-model.py` produces renderer-safe state with execution disabled until desktop runtime admission.

| Area | Source of truth |
| --- | --- |
| Intent menu | `docs/haven-42-menu.md`, `scripts/show-haven-42-menu.*`, `config/workflows.json` |
| Workflow execution | `scripts/invoke-workflow.*` |
| Request and result contract | `config/workflow-envelope-contract.json` and `docs/workflow-envelope-contract.md` |
| Evidence dashboard | `scripts/generate-evidence-dashboard.*`, `config/evidence-catalog.tsv`, `config/agent-surface-capabilities.json`, `config/agent-surface-solutions.json` |
| Beginner setup | `scripts/get-beginner-setup-plan.*`, `docs/beginner-setup-mode.md` |
| Progressive onboarding | `config/progressive-onboarding-contract.json`, `docs/progressive-onboarding.md` |
| Model choice | `scripts/recommend-local-agent-config.*`, `docs/hardware-aware-recommendations.md` |
| Install/configure/test by surface | `config/agent-surface-solutions.json`, `docs/agent-surface-solutions.md` |
| Script appendix | `docs/script-reference-appendix.md` |

Milestone 21 adds a provider-neutral capability registry above this engineering workflow layer. The capability registry owns user intent, modality, availability, policy metadata, and typed results; `config/workflows.json` remains the source of truth when the selected capability is an engineering operation.

## Evidence States

Every model, workflow, agent surface, and installer profile shown in the UI must have one visible state:

| State | Meaning | UI behavior |
| --- | --- | --- |
| `tested-passed` | Committed evidence or tests show the workflow passed for the stated scope. | Allow next step if safety level permits. |
| `tested-partial` | Evidence exists with recorded caveats or failure signals. | Show caveats before allowing use. |
| `failed` | Evidence records deterministic failures such as `EMPTY_MODEL_OUTPUT` or `FILENAME_NOT_IN_CONTEXT`. | Block promotion; allow rerun or remediation only. |
| `recommended-only` | Recommendation exists but validation has not passed. | Do not show as ready for edits. |
| `blocked` | Missing input, command shape, validation target, or safety boundary. | Show required input and link TODO item. |

## Progressive Onboarding Pattern

Every configurable product area offers **Set it up for me**, **Connect or use my existing setup**, and **Not now**. The first two paths both expose collapsed **Customize advanced settings** controls. This applies to text providers, engineering agent surfaces, images, audio, video, models, quantization, inference engines, local or remote connections, storage, retention, updates, rollback, and cleanup.

The engine derives the user-facing configuration state: `validated`, `customized`, `unverified`, or `blocked`. Advanced settings can narrow or remove validation but cannot create it, and the renderer cannot select the state. Advanced mode never bypasses consent, checksum verification, credential protection, network exposure, exact hardware/provider admission, or preservation of existing user data. See `docs/progressive-onboarding.md`.

## Safety Model

- Read-only workflows may run after showing inputs and output paths.
- Controlled-write workflows must preview output location and generated artifacts.
- Network-write workflows must disclose model pulls or downloads before execution.
- Approved-write workflows must require a dry-run or review step before applying changes.
- Local-only config files must stay uncommitted.
- The UI must show whether an action reads the current repository, writes generated output, writes config, or touches a model server.
- An LLM may suggest a capability or ask a clarifying question, but application policy must independently validate availability, filesystem scope, network use, and required approval.
- The UI must offer deterministic navigation when no routing model is available or routing confidence is insufficient.

## Main Flows

1. First-time setup:
   Generate a beginner setup plan, run health checks, collect hardware profile, recommend model/config, install pack assets, and validate.

2. Model and config:
   Profile hardware, recommend model lanes, review evidence, write local-only config, and rerun health checks.

3. Agent surface testing:
   Show install/configure/test status from `config/agent-surface-solutions.json`, then route to validated surface-specific or shared harnesses.

4. Evidence review:
   Generate dashboard and model scorecard, then surface milestone gaps from `docs/solution-architecture-review.md`.

5. Maintenance:
   Run validation, tests, release readiness, cleanup, and packaging through registry-backed workflows.

6. General-purpose assistance:
   Start without a repository, select or describe a chat, writing, summarization, or image task, disclose local versus external execution, and return a typed artifact.

## Implementation Boundary

The UI should call only stable workflow IDs from `config/workflows.json` through `scripts/invoke-workflow.*` using the schema-v1 workflow envelope. Any new UI action should first exist as a script or registry entry with tests.

The accepted desktop runtime is Tauri 2 with a React and TypeScript UI built by Vite. The production window loads only bundled local assets. Tauri starts one packaged, platform-specific Haven 42 engine sidecar and exchanges versioned typed JSON over private stdin/stdout IPC. The bridge accepts only registered capability IDs, workflow IDs, and schema-valid arguments. It must not expose arbitrary shell execution, unrestricted filesystem access, raw process spawning, remote UI code, or a generic command method.

The desktop application does not listen on a TCP port. A separately hardened loopback server may be evaluated for headless Linux, SSH-tunneled access, development, and diagnostics, but it is not the ordinary Windows, Linux desktop, or macOS runtime and cannot inherit desktop promotion evidence.

The pinned direct dependency candidates and non-admission decision are recorded in `docs/desktop-runtime-dependency-evaluation.md`. The renderer/native/engine message and authority boundaries are versioned in `config/desktop-ipc-contract.json`, `config/desktop-capability-policy.json`, and `docs/desktop-ipc-contract.md`.

A hosted production service is out of scope because Haven 42 is local-first and should not upload repository content, hardware profiles, local endpoints, prompts, generated artifacts, or raw validation transcripts.

## Desktop Security Boundary

- Use Tauri capability scopes to allow only the packaged Haven 42 sidecar and exact required operations.
- Keep the webview Content Security Policy restrictive and load no remote scripts, styles, frames, or application pages.
- Validate every renderer request again in the native bridge and core engine; renderer state is not execution authority.
- Use native directory selection, then scope repository and artifact access to the explicitly selected roots.
- Validate external documentation URLs against an allowlist before opening the system browser.
- Keep provider downloads, model pulls, network probes, writes, and approved-write workflows behind their existing disclosure and approval gates.
- Keep guided setup and existing-setup configuration on the shared progressive-onboarding contract; do not duplicate capability-specific state machines in React or Tauri.
- Preserve the schema-v1 workflow envelope as the initial IPC contract rather than introducing UI-only business logic.
- Package Node.js, Rust, and Python as build-time or application-private components; do not install them globally for end users.

## Platform Packages

| Platform | Initial package | Native renderer | Promotion boundary |
| --- | --- | --- | --- |
| Windows x64 and ARM64 | Per-user EXE installer plus optional portable ZIP | Edge WebView2 | Sign executable components and installer before stable public promotion. |
| Linux x64 and ARM64 | AppImage first; DEB and RPM only after separate validation | WebKitGTK | Validate each supported distribution and architecture; publish checksums and attestations. |
| macOS Apple Silicon and Intel | DMG containing `Haven 42.app` | WKWebView | Sign nested code and app, notarize, staple, and complete a final physical-Mac user-flow check. |

Application files are immutable and versioned separately from configuration, state, models, repositories, provider data, generated artifacts, and evidence. Installation must not silently add Ollama, ComfyUI, models, GPU drivers, agent software, startup entries, services, firewall rules, telemetry, or system-wide runtimes.

## Signing And Build Cost Strategy

- Use standard GitHub-hosted Windows, Linux, and macOS runners for the public repository; do not rent an AWS Mac for routine builds or signing.
- Build unsigned packages during development and sign only approved release candidates.
- Pursue free Windows signing through Microsoft Store MSIX signing or the SignPath Foundation before paid Microsoft Artifact Signing.
- Defer Apple Developer Program enrollment until the first public macOS beta is otherwise ready.
- Store signing credentials only in protected GitHub environments or equivalent secret storage, require release approval, and never commit private keys.
- Keep macOS physical-hardware testing as the last release gate rather than a routine CI dependency.

## Desktop Runtime Promotion Gates

Tauri and its package assets remain architecture-only until the implementation is explicitly approved and the exact runtime passes:

1. Dependency, license, and supply-chain review for Tauri, Rust crates, frontend packages, WebView2, WKWebView, WebKitGTK, and the packaging toolchain.
2. Typed IPC tests proving unknown operations, malformed envelopes, arbitrary commands, unauthorized paths, and remote navigation are rejected.
   The preparatory boundary now includes 46 engine-side and 55 native-authority policy cases; these do not replace actual Rust/Tauri and platform tests.
3. Windows, Linux, and macOS build, install, launch, workflow dispatch, shutdown, uninstall, and user-data-preservation tests.
4. Updater checksum, attestation or signature, compatibility, atomic activation, health-check, rollback, offline, and retained-version tests.
5. Platform signing and verification gates for public release candidates, plus the final physical-Mac Gatekeeper and Finder flow.

## Roadmap Placement

Milestone 20 completed the stable workflow, evidence, onboarding, and dispatcher foundation. Milestone 21 defines and validates general-purpose capabilities, typed artifacts, providers, repository-optional sessions, and routing policy. Milestone 22 implements this UI and later bounded multi-step composition over those two foundations.

Remaining product work stays on `TODO.md`:

- Keep surface-specific profile generation gated by non-Continue compatibility evidence.
- Implement the approved local chat and system-readiness first slice in the native renderer after runtime admission; keep image actions availability-gated.
- Define and validate the Tauri IPC, packaging, signing, updater, and platform promotion contracts before scaffolding a shippable UI.
