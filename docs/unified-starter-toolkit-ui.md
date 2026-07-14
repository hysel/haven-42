# Unified Starter Toolkit UI

## Purpose

The future starter-toolkit UI should give local-AI coding users one guided surface for setup, hardware profiling, model choice, config generation, agent-surface testing, validation, cleanup, and release readiness.

The UI must be a wrapper over existing workflow registry entries and tested scripts. It should not reimplement hardware profiling, recommendation logic, config generation, evidence parsing, or validation.

## Primary Users

| User | Need |
| --- | --- |
| Beginner local user | A short path from prerequisites to health check, model recommendation, install, and validation. |
| Advanced local user | Direct access to profile, recommend, test, install, evidence, cleanup, and release workflows. |
| Maintainer | A dashboard over milestone status, evidence gaps, workflow registry coverage, and release readiness. |
| Team or enterprise user | Evidence-first install/configuration decisions with audit-friendly output and no private data committed. |

## First Screens

The first screen should be the actual setup console, not a marketing page.

| Area | Source of truth |
| --- | --- |
| Intent menu | `docs/agent-pack-menu.md`, `scripts/show-agent-pack-menu.*`, `config/workflows.json` |
| Workflow execution | `scripts/invoke-workflow.*` |
| Evidence dashboard | `scripts/generate-evidence-dashboard.*`, `config/evidence-catalog.tsv`, `config/agent-surface-capabilities.json`, `config/agent-surface-solutions.json` |
| Beginner setup | `scripts/get-beginner-setup-plan.*`, `docs/beginner-setup-mode.md` |
| Model choice | `scripts/recommend-local-agent-config.*`, `docs/hardware-aware-recommendations.md` |
| Install/configure/test by surface | `config/agent-surface-solutions.json`, `docs/agent-surface-solutions.md` |
| Script appendix | `docs/script-reference-appendix.md` |

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

## Implementation Boundary

The UI should call only stable workflow IDs from `config/workflows.json` through `scripts/invoke-workflow.*`. Any new UI action should first exist as a script or registry entry with tests.

The first implementation can be local-only and static/serverless if it shells out to existing scripts from the user machine. A hosted production service is out of scope because this pack is local-first and should not upload repository content, hardware profiles, local endpoints, or raw validation transcripts.

## Open Decisions

These remain on `TODO.md`:

- Confirm scope and priority for the unified starter-toolkit web UI.
- Add the unified web UI wrapper after script-level workflows are stable.
- Keep surface-specific profile generation gated by non-Continue compatibility evidence.
