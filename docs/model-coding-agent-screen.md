# Coding-agent evidence screen

Every executable local-model candidate receives the same coding-agent screen,
including models not marketed for coding. The machine-readable gate list is
`config/model-coding-agent-qualification-policy.json`; the executable checker
is `scripts/model-coding-agent-screen.py`.

Each evidence cell is specific to one model digest, runtime artifact,
hardware profile, editor or CLI surface, and surface version. Results do not
carry across VS Code, VSCodium, native chat, or an extension. Every gate and
subcheck must be recorded as `passed`, `failed`, `blocked`, or `not-run`.
Missing or inconsistent fields fail closed.

A maintained surface must pass its own disposable-repository read, review,
scoped-write, external-diff, and unintended-write checks. Evidence does not
carry over from another CLI, editor, extension, or native chat surface. A
passing screen makes that exact cell eligible for human recommendation review;
it does not change automatic defaults, runtime admission, support labels, or
release policy.

Continue CLI and the VS Code/VSCodium Continue extensions are historical,
evidence-only surfaces. Their sanitized records remain available, but even a
fully passing historical Continue cell is not eligible for a new coding
recommendation and is not a prerequisite for another surface.

Raw prompts, raw responses, private endpoints, machine identity, and network
identity do not belong in the sanitized cell. Unintended writes are a failed
gate, not a recoverable warning.

Use `scripts/model-coding-agent-cell-template.py` to create a complete
`not-run` cell before a new surface test. Use
`scripts/model-coding-agent-history-audit.py` for older aggregate results.
Historical workflow passes remain useful observations, but the audit does not
manufacture missing current subchecks or convert them into recommendations.

Apple Silicon qualification additionally uses
`scripts/alpha2-macos-opencode-coding-screen.py` and its independent
`scripts/validate-alpha2-macos-opencode-coding-result.py` validator. This is a
version-pinned OpenCode CLI cell on a generated disposable repository. It does
not stand in for VS Code, VSCodium, either editor's native chat, another
OpenCode version, or a non-generated project.
