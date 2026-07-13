# Agent Surface Solutions

`config/agent-surface-solutions.json` is the user-facing solution catalog for agent surfaces.

It answers the same three questions for every surface:

- How do I install it?
- How do I configure it?
- How do I test it?

The catalog does not make planned or blocked surfaces look ready. It records the current solution, status, evidence, and blocked reason for each agent.

## Current Summary

| Surface | Install | Configure | Test |
| --- | --- | --- | --- |
| Continue | supported | supported | validated |
| Cline | planned | planned | validated |
| Aider | scaffolded | planned | validated |
| Roo Code | planned | planned | scaffolded |
| Kilo Code | planned | planned | scaffolded |
| OpenCode | planned | planned | scaffolded |
| OpenHands | blocked | blocked | planned |

## Rules

- Every surface must define install, configure, and test.
- Every activity must include a status, solution, workflow list, evidence list, and blocked reason field.
- Workflow IDs must exist in `config/workflows.json`.
- Evidence paths must be repository-relative and sanitized.
- Shared workflows can support many surfaces only when they do not assume a surface-specific configuration format.
- Planned and blocked surfaces must not be promoted by docs, menus, dashboards, or recommendation output.

## How To Use It

Start with `docs/agent-pack-menu.md` for the short user menu.

Use this solution catalog when you need to compare agent surfaces or decide what work remains before a surface can be promoted from planned/scaffolded to supported or validated.

Use `docs/script-reference-appendix.md` for direct command details after you choose a workflow.
