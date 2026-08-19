# Agent Surface Capability Parity

## Purpose

Every agent surface should be tracked against the same activities:

- Install
- Configure
- Test
- Health
- Cleanup
- Release readiness
- Model selection
- Evidence

`config/agent-surface-capabilities.json` is the machine-readable source for that parity check.

`config/agent-surface-solutions.json` is the companion solution catalog that translates the parity matrix into install, configure, and test answers for users.

## Status Meanings

| Status | Meaning |
| --- | --- |
| `supported` | The pack has a reusable workflow for the activity. |
| `validated` | The activity has surface-specific validation evidence. |
| `scaffolded` | The pack has wrapper or harness support, but live validation is incomplete. |
| `planned` | The activity is tracked and intentionally not implemented yet. |
| `blocked` | The activity requires command-shape, security, platform, or evidence decisions before implementation. |
| `retired` | The integration is not maintained; only sanitized historical evidence remains. |

## Current Shape

Continue is a hidden legacy surface. Its install, configure, test, health,
cleanup, release, and model-selection activities are retired; only sanitized
historical evidence remains available.
Aider and OpenCode are supported adapters within their generated-sample
evidence limits. Failed and retired integrations are absent from the active
capability catalog; OpenHands remains a documentation-only candidate with a
defined but unimplemented isolation boundary.

Shared workflows such as health checks, cleanup, model selection, release readiness, and evidence verification apply across surfaces because they operate on the local repository, local model server, generated outputs, or shared validation artifacts rather than a surface-specific configuration format.

## Parity Rules

- Every surface must list every activity.
- Every activity must declare a status, entry point list, and evidence list.
- Entry points must reference workflow IDs from `config/workflows.json`.
- Evidence paths must be repository-relative and sanitized.
- A surface-specific install or configure workflow should not be marked `supported` until it has tested output for that surface.
- Shared workflows can be marked `supported` for multiple surfaces only when they do not assume Continue-specific config.
- Candidate surfaces stay blocked for approved writes until read-only, plan, write-smoke, and realistic scoped-edit evidence exist.

## Gaps To Close

- Generate surface-specific config bundles only after each surface has compatibility evidence. The policy is tracked in `docs/surface-specific-config-bundles.md`.
- Treat any previously removed integration as new work and require every promotion gate before adding scripts, catalog entries, or default-menu visibility.
- Run explicitly approved non-generated-repository validation for Aider or OpenCode before any real-project approved-write claim.
- Implement OpenHands only inside the documented rootless workspace, credential, and network boundary before adding validation automation.
