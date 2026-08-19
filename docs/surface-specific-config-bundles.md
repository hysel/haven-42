# Surface-Specific Config Bundles

The pack should generate surface-specific config bundles, but only after each surface has enough compatibility evidence to make that output useful and safe.

The admission sequence is defined in `docs/agent-integration-admission-policy.md`: test candidate software externally first, then add its repository assets only after every pass-to-ship gate succeeds. A failed candidate receives documentation only and no retained bundle code.

Use `docs/config-generation-strategy.md` for the shared decision model that chooses among maintained surface-specific config outputs.

## Decision

Aider and OpenCode have supported generated local configuration paths today.
Continue config generation is retired. Existing `.continue` material is
historical evidence only and must not be presented as setup or a reusable
contributor workflow.

Future candidate or platform-agent bundles should be added only after the surface has:

- Documented install behavior.
- Documented local model configuration format.
- Read-only validation against a generated or disposable repository.
- Scoped write validation with external diff or file verification before approved-write config generation.
- Sanitized evidence recorded in `config/agent-surface-solutions.json`.

## Bundle Boundary

Reusable pack assets should stay shared wherever possible:

- Prompts.
- Rules.
- Documentation references.
- Runtime validation scripts.
- Evidence formats.
- Model recommendation data.

Generated config files should stay surface-specific. Continue config does not configure Aider, and Aider config does not configure Continue or another agent. A non-Continue bundle must translate shared evidence and model recommendations into that surface's native format.

## Current Status

| Surface | Bundle status | Policy |
| --- | --- | --- |
| Continue | retired | Preserve sanitized historical evidence only; generate no configuration. |
| Aider | supported | Generate explicit local-only `.aider.conf.local.yml` through `setup-agent-surface.*`; launch with `aider --config` and keep real-project approved write blocked. |
| OpenCode | supported | Generate a local-only `.opencode.local.json` through the unified adapter with dry-run-safe install planning, repository-local exclusion, and health checks. Devstral Small 2 24B passed generated-sample read/write-smoke and constrained scoped-edit validation; non-generated-repository validation remains pending for real-project approved-write claims. |
| OpenHands | blocked | The isolation boundary is defined, but do not generate platform-agent config until a rootless isolated implementation is explicitly approved and validated. |

## Implementation Rule

Do not add a new generated bundle just because a surface is listed in the catalog. Add the bundle only when its install, configure, and test evidence can be represented in `config/agent-surface-solutions.json` without planned or blocked caveats.
