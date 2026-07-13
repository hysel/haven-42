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

Continue is the only fully supported install/configure path today. Cline and Aider have validation evidence, while Roo Code, Kilo Code, OpenCode, and OpenHands remain evidence-gated candidates.

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

- Generate surface-specific config bundles only after each surface has compatibility evidence.
- Add install/configure workflows for Cline and Aider if their configuration formats are stable enough to support safely.
- Confirm command shapes for Roo Code, Kilo Code, and OpenCode before promoting wrappers from scaffolded to validated.
- Review OpenHands separately because platform-style agents have different workspace, sandbox, and secret boundaries.
