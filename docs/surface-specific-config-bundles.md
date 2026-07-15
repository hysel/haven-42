# Surface-Specific Config Bundles

The pack should generate surface-specific config bundles, but only after each surface has enough compatibility evidence to make that output useful and safe.

Use `docs/config-generation-strategy.md` for the shared decision model that chooses project-local, shared-assets, global Continue, or future surface-specific config output.

## Decision

Continue and Aider have supported generated local configuration paths today.

Future Cline, Roo Code, Kilo Code, OpenCode, or platform-agent bundles should be added only after the surface has:

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
| Continue | supported | Generate `.continue` assets and local-only Continue config from recommendation output. |
| Cline | planned | Wait for tested install and local model config boundaries. |
| Aider | supported | Generate explicit local-only `.aider.conf.local.yml` through `setup-agent-surface.*`; launch with `aider --config` and keep real-project approved write blocked. |
| Roo Code | planned | Wait for confirmed command, extension, and local model behavior. |
| Kilo Code | planned | Wait for confirmed command, extension, and local model behavior. |
| OpenCode | scaffolded | Generate a local-only `.opencode.local.json` through the unified adapter. Devstral Small 2 24B passed generated-sample read/write-smoke and constrained scoped-edit validation; non-generated-repository validation remains pending. |
| OpenHands | blocked | Do not generate platform-agent config while workspace, sandbox, and credential boundaries remain outside this pack. |

## Implementation Rule

Do not add a new generated bundle just because a surface is listed in the catalog. Add the bundle only when its install, configure, and test evidence can be represented in `config/agent-surface-solutions.json` without planned or blocked caveats.
