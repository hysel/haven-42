# Agent Surface Solutions

`config/agent-surface-solutions.json` is the user-facing solution catalog for agent surfaces.

It answers the same three questions for every surface:

- How do I install it?
- How do I configure it?
- How do I test it?

The catalog does not make planned or blocked surfaces look ready. It records the current solution, status, evidence, and blocked reason for each agent.

It also records the config-bundle policy. Continue and Aider have supported generated local config paths; future surface-specific bundles are gated by `docs/surface-specific-config-bundles.md`. Platform-agent validation must also follow `docs/openhands-validation-boundary.md`.

## Current Summary

| Surface | Install | Configure | Test |
| --- | --- | --- | --- |
| Continue | supported | supported | validated |
| Cline | planned | planned | validated |
| Aider | supported | supported | validated |
| Roo Code | retired | retired | retired |
| Kilo Code | scaffolded | scaffolded | scaffolded |
| OpenCode | scaffolded | scaffolded | validated |
| OpenHands | blocked | blocked | planned |

## Rules

- Every surface must define install, configure, and test.
- Every activity must include a status, solution, workflow list, evidence list, and blocked reason field.
- Workflow IDs must exist in `config/workflows.json`.
- Evidence paths must be repository-relative and sanitized.
- Shared workflows can support many surfaces only when they do not assume a surface-specific configuration format.
- Surface-specific config bundles must follow `docs/surface-specific-config-bundles.md`.
- Planned and blocked surfaces must not be promoted by docs, menus, dashboards, or recommendation output.

## How To Use It

Start with `docs/agent-pack-menu.md` for the short user menu.

Use this solution catalog when you need to compare agent surfaces or decide what work remains before a surface can be promoted from planned/scaffolded to supported or validated.

Before changing a non-Continue surface status, use `docs/agent-surface-promotion-gates.md`.

Aider is the first non-Continue adapter promoted end to end. Use
`scripts/setup-agent-surface.*` for install planning/execution, local-only
Ollama config generation, and health checks; use `scripts/test-aider-cli-models.*`
for read-only and disposable write validation. This does not promote Aider to
real-project approved-write readiness.

OpenCode has a scaffolded local-only Ollama config and installer path through
the same adapter. Devstral Small 2 24B passed disposable read and write-smoke
validation with the installed CLI. See [OpenCode CLI model testing](opencode-cli-model-testing.md).
It remains a candidate until explicitly approved non-generated repository
validation passes.

Kilo Code now has an explicit npm install plan and a local-only
`.kilo.local.json` generator through the same adapter. It uses the documented
Ollama `/v1` provider shape, model tool metadata, token limits, and
ask-by-default permissions. Live generated-sample validation is still pending;
do not treat generated config as real-project approval.

Use `docs/script-reference-appendix.md` for direct command details after you choose a workflow.
