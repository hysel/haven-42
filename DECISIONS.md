# Decisions

This file records important project decisions. Use it for choices that affect architecture, compatibility, governance, or long-term maintenance.

## 2026-07-22: Admit Desktop Dependencies And Authority In Evidence-Gated Slices

Status: Accepted

Context:
Selecting Tauri did not by itself establish a safe resolved dependency graph or renderer-to-engine authority model. Adding a generated starter application would immediately admit transitive packages, filesystem/process surfaces, and platform assumptions before they had been reviewed or tested.

Decision:
Record exact direct dependency candidates separately from runtime admission. Begin with Tauri 2.11.5, its version-matched official packages, React 19.2.8, Vite 8.1.5, TypeScript 7.0.2, Node.js 24.18.0 LTS, Rust 1.97.1, and PyInstaller 6.21.0. Ship no manifest, lock file, frontend source, crate, sidecar binary, or installer in this slice. Before implementation admission, resolve the full platform-specific graphs and pass vulnerability, license, provenance, checksum, private-IPC, packaging, and lifecycle gates.

Use a default-deny versioned desktop contract. The renderer may name only registered capability or UI-ready workflow IDs. Native-issued path grants and effect-bound approval tokens replace raw paths and implicit authority. The bridge exposes no generic shell, process, filesystem, URL, remote-content, or listening-socket surface. Headless loopback operation remains a separately promoted product mode.

Consequences:
The repository gains testable architecture contracts without prematurely claiming that a desktop application works. The initial implementation slice stays narrow, and any dependency or permission expansion requires an explicit re-evaluation. Native enforcement and adversarial tests are still required before the desktop runtime can ship.

## 2026-07-21: Use Tauri With Private Typed IPC For The Desktop Product

Status: Accepted

Context:
Haven 42 needs one mainstream local interface across Windows, Linux, and macOS without exposing repository operations through an always-on network service or duplicating the existing workflow and capability logic. A general browser plus loopback API is useful for headless systems, but it adds port, origin, authentication, lifecycle, and filesystem-selection risks to ordinary desktop use.

Decision:
Use a Tauri 2 desktop shell with a React and TypeScript UI built by Vite. Bundle the Haven 42 core engine as a platform-specific sidecar and communicate through a versioned, typed stdin/stdout IPC contract derived from the existing workflow envelopes. Allow only explicit capability and workflow IDs; do not expose arbitrary shell execution, unrestricted filesystem access, remote UI code, or a generic command bridge. Keep a separately hardened, explicitly enabled loopback mode only for headless Linux, SSH-tunneled access, development, and diagnostics.

Build unsigned packages during development. For public releases, use GitHub-hosted platform runners, pursue no-cost Windows signing through Microsoft Store signing or the SignPath Foundation before paid Artifact Signing, and defer Apple Developer enrollment until the first public macOS beta. Windows and macOS packages must be signed and macOS packages notarized before stable promotion. Linux artifacts require checksums and release attestations. No desktop runtime or signing integration ships until its exact OS and architecture package passes the repository promotion gates.

Consequences:
Desktop users receive a single web-technology UI without a default listening port, while headless users retain a bounded browser option. Tauri, Rust, WebView2, WKWebView, WebKitGTK, sidecar packaging, installers, signing, notarization, updates, and rollback become independently tested supply-chain boundaries. Node.js, Rust, and Python remain build dependencies rather than global end-user prerequisites. A physical Mac is reserved for final end-user release validation rather than routine CI or signing.

## 2026-07-21: Keep capability selection separate from execution authority

Status: Accepted

The provider-neutral capability registry describes user intent, typed outputs, availability, and material effects above the engineering workflow registry. Deterministic or future LLM routing may select or suggest a capability, but routing never invokes it. Provider availability, privacy, filesystem scope, network effects, artifact destination, engineering evidence, and approvals are enforced independently before execution.

## 2026-07-21: Place capability contracts before the unified product UI

Status: Accepted

Milestone 20 closes as the completed hardware-aware automation and workflow foundation. Milestone 21 implements general-purpose capability, artifact, provider, workspace, routing, and policy contracts. Milestone 22 then implements the unified local-first UI and, only after individual capability validation, bounded multi-step composition. Future surface-specific agent profiles remain evidence-gated integration work and do not keep Milestone 20 open.

## 2026-07-21: Treat mapped wiki pages as generated release documentation

Status: Accepted

The main repository is authoritative for mapped GitHub wiki content. Cross-platform synchronization scripts copy mapped sources, regenerate navigation, and remove explicitly retired pages. Mapped wiki pages are committed to the separate wiki repository before the related main-repository push, and hosted CI rejects a main commit when the live wiki is stale. This prevents support, release, and safety guidance from drifting across the two repositories.

## Format

Each decision should use this structure:

```text
## YYYY-MM-DD: Decision Title

Status: Proposed | Accepted | Superseded

Context:
Why the decision is needed.

Decision:
What was chosen.

Consequences:
Expected benefits, tradeoffs, and follow-up work.
```

## 2026-07-21: Require Agent Software To Pass Before Repository Admission

Status: Accepted

Context:
Candidate agent integrations can leave dormant scripts, harnesses, configuration, and maintenance obligations even when the tested software fails required safety or correctness gates.

Decision:
Evaluate any agent software only in an external or ignored disposable workspace. Admit agent-specific executable or operational assets to the repository only after the exact version and operating mode pass the complete promotion and cross-platform validation gates. When an evaluation fails, commit only a concise sanitized decision record and ship no scripts, harnesses, wrappers, configuration, detailed evidence, active catalog entries, or package assets for that software.

Consequences:
The shipped repository stays narrower and fully vetted. A failed or removed agent has no dormant implementation path; a future version requires a fresh evaluation. Architecture-only candidate documentation is allowed when needed to define a safe evaluation boundary, but it cannot expose runnable code or claim support.

## 2026-07-01: Use Continue YAML Configuration

Status: Accepted

Context:
Continue supports YAML configuration for agents, models, rules, prompts, context providers, documentation, and MCP servers. The deprecated JSON configuration format should not be the primary target for this pack.

Decision:
Use `.continue/config.yaml` with `schema: v1` as the composition root for the pack.

Consequences:
The pack should be validated against the Continue YAML schema. Documentation and examples should prefer YAML configuration.

## 2026-07-01: Local-First Model Posture

Status: Accepted

Context:
The project targets enterprise teams that may work with private repositories and regulated codebases.

Decision:
Use Ollama and local models as the default documented path.

Consequences:
Cloud-hosted model configuration may be documented later, but must not become the default assumption.

## 2026-07-01: Separate Agents, Prompts, Rules, And Templates

Status: Accepted

Context:
The repository needs to scale across many workflows without duplicating instructions or creating unclear ownership.

Decision:
Agents define role behavior, prompts define workflow steps, rules define reusable standards, and templates define output shape.

Consequences:
Contributors should move duplicated guidance to the lowest appropriate reusable layer, usually rules or templates.

## 2026-07-01: Keep Rule Dependencies Acyclic

Status: Accepted

Context:
Rules, prompts, agents, and templates can easily become coupled if each layer copies or depends on the others.

Decision:
Rules and templates are lower-level reusable assets. Prompts may reference rules and templates conceptually. Agents may reference prompts and rules conceptually. Rules should not depend on prompts or agents.

Consequences:
The pack should remain easier to extend because policy, workflow, role behavior, and output shape can evolve independently.

## 2026-07-01: Include Supplemental Review Prompts

Status: Accepted

Context:
Additional prompt files existed for AI framework self-review, refactoring planning, product-management review, and release-readiness review. They were useful enterprise workflows but were not wired into the pack configuration.

Decision:
Normalize those prompt files with standard frontmatter, use lower-case kebab-case filenames, and include them in `.continue/config.yaml`.

Consequences:
The pack now exposes broader review and planning workflows. Runtime validation must confirm each prompt is invokable in Continue.

## 2026-07-01: Use MIT License

Status: Accepted

Context:
The repository is a reusable Continue engineering pack made of configuration, prompts, rules, agents, templates, and documentation. Adoption should be simple for teams that want to copy, adapt, or redistribute the pack.

Decision:
Use the MIT License.

Consequences:
The pack is permissively licensed with low adoption friction. The license does not include the explicit patent grant provided by Apache-2.0.

## 2026-07-01: Keep Ollama Endpoint Portable

Status: Accepted

Context:
The pack should be reusable across machines and networks. A local-network Ollama server was used for validation, but committing a concrete private IP address would make the default configuration environment-specific.

Decision:
Do not commit a concrete `apiBase` value for Ollama. Use remote Ollama endpoints only as local test-time overrides.

Consequences:
The committed config remains portable and defaults to Continue's standard Ollama behavior. Users who run Ollama on another host must add their own local `apiBase` override.

## 2026-07-01: Start SonarQube Support With Manual Triage

Status: Accepted

Context:
SonarQube support is part of the enterprise review scope, but direct API, CLI, or MCP integration requires additional design and environment assumptions.

Decision:
Provide a manual workflow first. Users paste relevant SonarQube findings into Continue, and the pack guides classification, prioritization, remediation, and validation.

Consequences:
Teams can use SonarQube findings immediately without integration setup. Automated SonarQube ingestion requires separate integration guidance before it should become a default workflow.

## 2026-07-01: Use Documentation Checklists For Pack Validation

Status: Accepted

Context:
The pack is primarily composed of markdown and YAML assets. Traditional unit tests do not cover most quality risks in prompts, rules, agents, templates, and examples.

Decision:
Maintain validation checklists in `docs/validation-checklists.md` for prompt, rule, agent, template, config, example, documentation, and release changes.

Consequences:
Contributors have a repeatable review path before automated validation exists. Future scripts can be added later for checks that are easy to automate.

## 2026-07-02: Keep MCP Optional And Local-First

Status: Accepted

Context:
MCP can connect Continue to external tools such as GitHub, filesystems, databases, and quality systems. These integrations are useful, but they expand trust boundaries, may require secrets, and can create network dependencies. The pack must continue to work with local Ollama systems and without cloud services.

Decision:
Keep `mcpServers: []` in the default config. Document MCP as optional. Prefer read-only, local-first MCP integrations first, with GitHub MCP as the first candidate for repository, issue, and pull request context.

Consequences:
The default pack remains portable and local-model compatible. Users can adopt MCP intentionally through documented setup. SonarQube and other external integrations require separate security and setup guidance before they are recommended.

## 2026-07-02: Use SonarQube Web API As First Automation Path

Status: Accepted

Context:
SonarQube findings are valuable review inputs, but direct integration can require tokens, internal endpoints, project identifiers, organization keys, and network access. The pack must remain usable with local Ollama and without granting agent tools live access to quality systems.

Decision:
Keep manual SonarQube triage as the default workflow. Use the SonarQube Web API as the first documented automation path for sanitized, read-only review input. Treat the SonarQube MCP server as optional until it is validated with Continue, local Ollama, and enterprise credential-handling expectations.

Consequences:
Teams can automate retrieval of quality gate status, measures, and findings without changing the default Continue config. MCP remains a future opt-in setup rather than a default dependency.

## 2026-07-02: Document GitHub MCP As Optional First MCP Setup

Status: Accepted

Context:
MCP can provide useful external context, but enabling MCP by default would add credentials, network dependencies, tool execution, and possible data exposure. The pack needs a concrete setup path while keeping local Ollama workflows unaffected.

Decision:
Document GitHub MCP as the first optional MCP setup path. Keep the default config unchanged with `mcpServers: []`. Prefer a separate local `.continue/mcpServers/` file for users who opt in.

Consequences:
Teams have a reproducible MCP starting point without changing the portable default configuration. GitHub MCP can be validated independently from local model behavior, and SonarQube MCP can remain separate until API-based workflows are proven.

## 2026-07-02: Add Scripted Release Validation

Status: Accepted

Context:
The pack is mostly markdown and YAML, so traditional unit tests do not cover the main failure modes. Release risk is concentrated around broken local file references, accidental endpoint or secret commits, stale version values, and accidental changes to the local-first default posture.

Decision:
Add a PowerShell validation script that checks the pack version, required files, local `.continue` references, default MCP posture, and obvious private endpoints or secrets.

Consequences:
Release checks are repeatable on the current Windows-first maintenance environment. Future CI can run the same script or add cross-platform equivalents.
