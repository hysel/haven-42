# Surface-Specific Config Bundles

The pack should generate surface-specific config bundles, but only after each surface has enough compatibility evidence to make that output useful and safe.

## Decision

Continue remains the only supported generated config bundle today.

Future Cline, Aider, Roo Code, Kilo Code, OpenCode, or platform-agent bundles should be added only after the surface has:

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

Generated config files should stay surface-specific. A Continue config should not pretend to configure Cline, Aider, Roo Code, Kilo Code, OpenCode, or OpenHands. A future non-Continue bundle should translate shared evidence and model recommendations into that surface's native config format.

## Current Status

| Surface | Bundle status | Policy |
| --- | --- | --- |
| Continue | supported | Generate `.continue` assets and local-only Continue config from recommendation output. |
| Cline | planned | Wait for tested install and local model config boundaries. |
| Aider | planned | Wait for a validated CLI install and config shape. |
| Roo Code | planned | Wait for confirmed command, extension, and local model behavior. |
| Kilo Code | planned | Wait for confirmed command, extension, and local model behavior. |
| OpenCode | planned | Wait for confirmed CLI install and local model behavior. |
| OpenHands | blocked | Do not generate platform-agent config while workspace, sandbox, and credential boundaries remain outside this pack. |

## Implementation Rule

Do not add a new generated bundle just because a surface is listed in the catalog. Add the bundle only when its install, configure, and test evidence can be represented in `config/agent-surface-solutions.json` without planned or blocked caveats.
