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

## Current Shape

Continue remains the supported first editor path. Aider and OpenCode are supported non-Continue adapters within their generated-sample evidence limits. Cline CLI 3.0.46 and Kilo CLI 7.4.11 are quarantined and excluded from default setup; OpenHands remains a candidate with a defined but unimplemented isolation boundary. Roo Code is historical only because its upstream project is retired.

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
- Retest the retained Cline and Kilo harnesses only after relevant upstream version or tool-protocol changes; require all promotion gates before restoring default-menu visibility.
- Run explicitly approved non-generated-repository validation for Aider or OpenCode before any real-project approved-write claim.
- Implement OpenHands only inside the documented rootless workspace, credential, and network boundary before adding validation automation.
