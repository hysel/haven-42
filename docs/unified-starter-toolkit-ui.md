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

| Area | Source of truth |
| --- | --- |
| Intent menu | `docs/agent-pack-menu.md`, `scripts/show-agent-pack-menu.*`, `config/workflows.json` |
| Workflow execution | `scripts/invoke-workflow.*` |
| Request and result contract | `config/workflow-envelope-contract.json` and `docs/workflow-envelope-contract.md` |
| Evidence dashboard | `scripts/generate-evidence-dashboard.*`, `config/evidence-catalog.tsv`, `config/agent-surface-capabilities.json`, `config/agent-surface-solutions.json` |
| Beginner setup | `scripts/get-beginner-setup-plan.*`, `docs/beginner-setup-mode.md` |
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

The first implementation can be local-only and static/serverless if it shells out to existing scripts from the user machine. A hosted production service is out of scope because this pack is local-first and should not upload repository content, hardware profiles, local endpoints, or raw validation transcripts.

## Roadmap Placement

Milestone 20 completed the stable workflow, evidence, onboarding, and dispatcher foundation. Milestone 21 defines and validates general-purpose capabilities, typed artifacts, providers, repository-optional sessions, and routing policy. Milestone 22 implements this UI and later bounded multi-step composition over those two foundations.

Remaining product decisions stay on `TODO.md`:

- Keep surface-specific profile generation gated by non-Continue compatibility evidence.
- Decide which local text and image providers form the first supported Milestone 21 vertical slice.
- Select the local-first Milestone 22 UI runtime and packaging boundary without introducing a hosted-service dependency.
