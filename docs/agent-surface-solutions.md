# Agent Surface Solutions

`config/agent-surface-solutions.json` is the user-facing solution catalog for agent surfaces.

It answers the same three questions for every surface:

- How do I install it?
- How do I configure it?
- How do I test it?

The catalog does not make candidate, historical, or blocked surfaces look ready. It records the support tier, default-menu visibility, current solution, status, evidence, and blocked reason for each tracked agent.

It also records the config-bundle policy. Continue, Aider, and OpenCode have supported generated local config paths; future surface-specific bundles are gated by `docs/surface-specific-config-bundles.md`. Platform-agent validation must also follow `docs/openhands-validation-boundary.md`.

## Current Summary

| Surface | Install | Configure | Test |
| --- | --- | --- | --- |
| Continue | supported | supported | validated |
| Aider | supported | supported | validated |
| Roo Code | retired | retired | retired |
| OpenCode | supported | supported | validated |
| OpenHands | blocked | blocked | blocked |

## Rules

- Every tracked surface must define install, configure, and test.
- Every activity must include a status, solution, workflow list, evidence list, and blocked reason field.
- Workflow IDs must exist in `config/workflows.json`.
- Evidence paths must be repository-relative and sanitized.
- Shared workflows can support many surfaces only when they do not assume a surface-specific configuration format.
- Surface-specific config bundles must follow `docs/surface-specific-config-bundles.md`.
- Planned and blocked surfaces must not be promoted by docs, menus, dashboards, or recommendation output.
- Candidate and historical surfaces remain excluded from the default setup menu.

## How To Use It

Start with `docs/agent-pack-menu.md` for the short user menu.

Use this solution catalog when you need to compare agent surfaces or decide what work remains before a surface can be promoted from planned/scaffolded to supported or validated.

Before changing a non-Continue surface status, use `docs/agent-surface-promotion-gates.md`.

Aider is the first non-Continue adapter promoted end to end. Use
`scripts/setup-agent-surface.*` for install planning/execution, local-only
Ollama config generation, and health checks; use `scripts/test-aider-cli-models.*`
for read-only and disposable write validation. This does not promote Aider to
real-project approved-write readiness.

OpenCode has supported local-only Ollama configuration, dry-run-safe install
planning, and adapter health checks through the same adapter. Devstral Small 2
24B passed disposable read, write-smoke, and constrained scoped-edit validation
with the installed CLI. See [OpenCode CLI model testing](opencode-cli-model-testing.md).
It remains partial for real-project approved-write readiness until explicitly
approved non-generated repository validation passes.

Failed integrations are removed from the active solution catalog and executable
surface. Reintroducing one requires a fresh proposal and complete promotion-gate
validation.

Use `docs/script-reference-appendix.md` for direct command details after you choose a workflow.
