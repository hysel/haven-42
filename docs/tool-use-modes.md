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

Before using this mode with a local model, validate tool execution with `docs/model-tool-use-validation.md`.

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

Expected behavior:

- The assistant inspects the relevant files.
- The assistant treats the opened repository root or current folder as the default working directory.
- If no file is open or the current folder is unclear, the assistant uses list/read tools against `.` to discover the workspace before asking the user for a path.
- For unqualified file names such as `README.md`, the assistant checks the current folder first and does not create a duplicate in `src/`, `docs/`, or another subfolder unless requested or proven by repository evidence.
- If workspace discovery fails, the assistant says `WORKSPACE_UNAVAILABLE` and stops.
- If the correct target path cannot be proven, the assistant says `PATH_AMBIGUOUS` and stops before editing.
- The assistant successfully reads the exact files it plans to change before editing.
- The assistant uses Continue edit/apply tools to change the approved files.
- The assistant confirms the apply target matches the requested, discovered, and read target file before applying. If the apply target differs, the assistant says `APPLY_TARGET_MISMATCH` and stops.
- The assistant verifies the edit with changed file content, `git diff`, or another available diff/status tool before claiming success.
- Approved-write readiness requires an external shell or git check after the assistant reports success. Assistant-only readback is not enough evidence that the file exists on disk.
- If no changed content or diff is observed after an edit attempt, the assistant says `WRITE_NOT_APPLIED` and stops.
- The assistant does not only describe the change.
- The assistant does not infer implementation details from repository type or typical framework patterns when it could not read the target files.
- If read tools are unavailable, the assistant says `READ_TOOLS_UNAVAILABLE` clearly and stops before proposing edits.
- If write tools are unavailable, the assistant says `WRITE_TOOLS_UNAVAILABLE` clearly and stops before pretending the change was made.
- The assistant should not say "I can't directly edit files" and then provide copy/paste code unless write tools are actually unavailable.

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

## Platform-Aware Commands

The assistant should use commands for the shell it is actually running in.

Windows PowerShell examples:

```powershell
Get-ChildItem
Select-String -Path .\BrickLinkBrickset.cs -Pattern "config"
Get-Content .\README.md
git status --short
```

Linux and macOS examples:

```bash
ls
grep -n "config" ./BrickLinkBrickset.cs
cat ./README.md
git status --short
```

If the assistant tries a Linux command on Windows, correct it and continue with PowerShell. If the assistant tries a PowerShell command on Linux or macOS, correct it and continue with shell commands.

## Approved Write Smoke Test

Use this only in a disposable branch or a test repository.

For existing-file write validation, pre-create the test file and make the
assistant edit it. This better matches real project work and avoids double
approval paths.

Recommended temporary Continue built-in tool settings:

| Tool | Setting |
| --- | --- |
| `read_file` | Automatic |
| `ls` | Automatic |
| `view_diff` | Automatic |
| `create_new_file` | Excluded |
| `edit_existing_file` | Ask First |
| `single_find_and_replace` | Ask First |
| `run_terminal_command` | Ask First |

Pre-create the test file:

Windows:

```powershell
Set-Content .\continue-agent-write-test.md "before"
```

Linux or macOS:

```bash
printf '%s\n' 'before' > ./continue-agent-write-test.md
```

Ask:

```text
Use approved write mode for this smoke test only.

Edit the existing file continue-agent-write-test.md in the opened repository root.
Replace the entire file content with exactly this content:

Continue Agent write test passed.

Do not modify any other files.
Do not create a new file.
Do not append.
Do not create the file under src, docs, Properties, or any other subfolder.
Use one edit tool call.
Stop after the first Apply diff.
Do not commit.
```

Expected result:

- Continue edits the existing file through one write/apply tool path.
- `git status --short` shows only `continue-agent-write-test.md`.
- The file is created in the opened repository root or current folder, not in `src/`, `docs/`, or another inferred subfolder.
- The apply target shown by Continue is `continue-agent-write-test.md`, not an unrelated file.
- An external shell check confirms the file exists and contains the requested content.
- The assistant reports the file change instead of asking the user to create it manually.
- Only one approval or Apply path is used. If both `create_new_file` and
  `edit_existing_file` prompts appear for the same target, stop and record
  `DUPLICATE_APPROVALS`.
- If the final file contains the requested line twice, record
  `DUPLICATE_CONTENT`.

Windows verification:

```powershell
git status --short
Test-Path .\continue-agent-write-test.md
Get-Content .\continue-agent-write-test.md
git diff --check
```

Linux or macOS verification:

```bash
git status --short
test -f ./continue-agent-write-test.md && cat ./continue-agent-write-test.md
git diff --check
```

Clean up after the test:

```powershell
Remove-Item .\continue-agent-write-test.md
```

Linux or macOS cleanup:

```bash
rm ./continue-agent-write-test.md
```

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

In validation, switching from a previous small coder model to `qwen3-coder:30b`
fixed this behavior for the tested local Ollama setup.

Use one of these safer fallbacks:

- Attach files with `@Files`.
- Include selected text or the current file as context.
- Generate `runtime-context.md` with the runtime context generator for your operating system.
- Ask the model: `Do not use tools. Do not output JSON. Use only the attached context.`

Do not use approved write mode until read-only tool execution works reliably.

Do not use approved write mode if the assistant can list files but cannot read
the source or config files it plans to change. Listing files alone is not enough
evidence for implementation.

For the model-level validation checklist, use `docs/model-tool-use-validation.md`. For reliability fallback guidance, use `docs/local-model-reliability.md`.
