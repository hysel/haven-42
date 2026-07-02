# Tool Use Modes

## Purpose

This guide explains how the pack should behave when reviewing or changing another project.

The goal is simple: the assistant may help inspect, plan, and change a project, but write actions should happen only after the user clearly approves them.

## The Three Modes

Use these modes when working in a reviewed repository.

## Mode 1: Read-Only Discovery

Use this mode when the assistant needs to understand the project.

Allowed:

- List files.
- Read documentation.
- Read source code.
- Inspect configuration.
- Inspect git status.
- Summarize architecture, risks, and missing information.

Not allowed:

- Edit files.
- Delete files.
- Move files.
- Run formatters that change files.
- Commit or push changes.

Good user request:

```text
Review this project and explain how it works. Do not modify files.
```

## Mode 2: Plan-Only

Use this mode before making risky or unclear changes.

Allowed:

- Read files.
- Identify affected components.
- Create an implementation plan.
- List risks, tests, rollback steps, and assumptions.
- Ask for approval before implementation.

Not allowed:

- Write code.
- Create patches.
- Update documentation.
- Change config.
- Run commands that modify the repository.

Good user request:

```text
Create an implementation plan for this change. Do not write code yet.
```

## Mode 3: Approved Write Mode

Use this mode only after the user approves a specific change.

Allowed:

- Edit files related to the approved task.
- Add focused tests or docs when they support the task.
- Run validation commands.
- Report exactly what changed.

Still not allowed unless the user explicitly asks:

- Reformat unrelated files.
- Refactor unrelated code.
- Delete user work.
- Commit changes.
- Push changes.
- Add secrets, private endpoints, or machine-specific settings.

Good user request:

```text
Implement the approved plan. Keep changes limited to the files needed for this feature.
```

## Approval Rules

The assistant should ask for or wait for approval before writing when:

- The user requested a plan only.
- The change touches security, authentication, authorization, customer data, release flow, or dependency management.
- The change could affect production behavior.
- The change requires deleting, moving, or renaming files.
- The repository has uncommitted changes that may belong to the user.

The assistant may proceed directly when:

- The user explicitly asks to implement.
- The requested change is scoped and low risk.
- The assistant has enough repository context.
- The change can be validated locally.

## Git Safety

Before write mode:

```powershell
git status --short --branch
```

After write mode:

```powershell
git status --short
git diff --check
```

Commit only when the user explicitly asks.

Push only when the user explicitly asks.

## Validation Expectations

For code changes, prefer:

- Unit tests.
- Integration tests when behavior crosses boundaries.
- Build commands.
- Static validation.
- Manual verification steps when automated tests are unavailable.

For documentation-only changes, prefer:

- Pack validation.
- Link/path checks.
- Privacy scans for local paths, private IP addresses, and secrets.

## Safe Language For Users

When asking the assistant to work on a project, use clear mode words:

- "Review only"
- "Plan only"
- "Do not modify files"
- "Implement this approved plan"
- "Commit these changes"
- "Push these changes"

If the request is unclear, the assistant should choose the safer mode.

## What This Pack Should Not Do By Default

The committed pack should not default to broad write access.

Do not add default configuration that:

- Enables remote write-capable tools automatically.
- Commits private endpoint values.
- Grants broad external service permissions.
- Skips approval for destructive actions.
- Treats tool output as trusted without review.

Tool-enabled project changes should remain explicit, scoped, validated, and reversible.

## Tool Execution Fallback

If Agent mode prints raw JSON instead of running a tool, do not click Apply.

Example raw JSON:

```json
{"name":"ls","arguments":{"dirPath":".","recursive":true}}
```

This is not a patch. It means the model or Continue surface did not execute the tool call.

In validation, switching from `qwen2.5-coder:7b` to `qwen3-coder:30b` fixed this behavior for the tested local Ollama setup.

Use one of these safer fallbacks:

- Attach files with `@Files`.
- Include selected text or the current file as context.
- Generate `runtime-context.md` with `scripts/generate-runtime-context.ps1`.
- Ask the model: `Do not use tools. Do not output JSON. Use only the attached context.`

Do not use approved write mode until read-only tool execution works reliably.
