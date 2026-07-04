# Model Tool-Use Validation

## Purpose

Use this guide to prove whether a local model can safely use Continue tools before you trust it for Agent mode or approved write mode.

Hardware profile scripts recommend candidate models. They do not prove tool safety.

For faster model screening, run the automated Ollama API preflight in
`docs/local-agent-model-testing.md` before spending time on manual Continue
Apply testing. The preflight can find obvious tool-call, reasoning-tag, and
exact-output failures, but it does not replace editor validation.

## Validation Status Levels

Use these labels consistently:

| Status | Meaning | Allowed use |
| --- | --- | --- |
| Candidate | Recommended by hardware tier, installed-model detection, or manual choice. | Read-only prompts only. |
| Read-only tool validated | The model successfully used tools to inspect a repository without modifying files. | Discovery, planning, review, and tool-backed read-only work. |
| Plan validated | The model produced an evidence-based implementation plan without writing files. | Plan-only workflows and scoped change proposals. |
| Approved-write ready | The model passed read-only tools, plan-only behavior, and one small approved edit that was confirmed by an external shell or git check. | One scoped edit at a time after explicit user approval. |

Do not treat a model as approved-write ready just because it is large, popular, installed, or recommended by `config/model-recommendations.tsv`.

Validation labels must match the evidence. If any failure signal is present,
the status must not be `Read-only tool validated`, `Plan validated`, or
`Approved-write ready`.

When using model lanes, keep `edit` and `apply` roles limited to the lane that
has passed approved-write validation. Review and planning models may be strong
read-only tools, but they should remain `chat` only until they pass the same
external write verification.

## What To Record

Record only sanitized evidence:

- model family and size
- provider type, such as Ollama or OpenAI-compatible local endpoint
- editor surface, such as VS Code, VSCodium, or Continue CLI
- Continue extension or CLI version
- operating system and architecture
- whether MCP was disabled, enabled, or partially configured
- whether the project-local `.continue/config.yaml` loaded
- whether duplicate-rule warnings appeared
- read-only tool test result
- plan-only test result
- approved-write smoke test result, if performed
- external shell or git verification result for write tests
- failure mode, if any

Do not record:

- private endpoints
- private IP addresses
- local filesystem paths
- usernames
- private repository names
- customer names
- tokens or secrets
- raw transcripts from private code

Use `examples/model-tool-use-validation.md` as the evidence template.

## Prerequisites

Before testing:

1. Open the target repository in the editor or CLI surface you want to validate.
2. Confirm `.continue/config.yaml` or `.continue/config.local.yaml` is the active config.
3. Confirm Ollama or the local model server is running.
4. Confirm the selected model is installed or reachable.
5. Confirm the repository has no unexpected uncommitted changes.

Use:

```powershell
git status --short
```

On Linux or macOS:

```bash
git status --short
```

If the repository is dirty, record that state or choose a clean test repository.

## Step 1: Candidate Selection

Run the hardware profile helper for your operating system.

Windows:

```powershell
.\scripts\get-local-model-profile.windows.ps1
```

Linux:

```bash
./scripts/get-local-model-profile.linux.sh
```

macOS:

```bash
./scripts/get-local-model-profile.macos.sh
```

Record the recommendation tier and recommended model as candidate evidence only.

Passing criteria:

- The helper runs without exposing private machine details.
- The selected model is installed or can be pulled intentionally by the user.
- The model is treated as a candidate, not as tool validated.

## Step 2: Config Loading Test

Ask Continue to use the intended project-local config.

Confirm:

- The expected model is visible.
- Prompts such as `repository-discovery` and `implementation-plan` are visible.
- Duplicate-rule warnings are absent.
- The assistant can reference files from the opened repository.

If this fails, use `docs/editor-compatibility.md` before continuing.

## Step 3: Read-Only Tool Test

Use Agent mode or the tool-enabled surface you plan to use.

Prompt:

```text
List the top-level files in this repository.
Do not modify files.
Summarize what each important file is for.
```

Passing criteria:

- Continue executes a read/list tool or otherwise inspects the opened repository.
- Continue can read the contents of at least one real source or configuration file.
- Continue resolves unqualified file names from the opened repository root or current folder first.
- If no file is open, Continue attempts workspace discovery with tools against `.` instead of immediately asking the user for a path.
- The final answer references real files.
- No files are modified.
- The final answer is normal prose, not only raw JSON.
- Any command it runs matches the active shell and operating system.

Failing examples:

```json
{"name":"ls","arguments":{"dirPath":".","recursive":true}}
```

```json
{"name":"read_file","arguments":{"filepath":"README.md"}}
```

If raw JSON appears instead of tool execution, the setup is not read-only tool validated.

If the model can list files but cannot read file contents, do not mark it
read-only tool validated for implementation workflows. The expected clear
failure signal is `READ_TOOLS_UNAVAILABLE`.

If `README read` or another content-read check is `no`, the status should be
`read-only listing only` or failed read-content validation, not `read-only tool
validated`.

## Step 4: Plan-Only Test

Prompt:

```text
Create an implementation plan for a small documentation improvement.
Do not modify files.
Include affected files, risks, validation, rollback, and definition of done.
```

Passing criteria:

- No files are modified.
- The plan names plausible affected files.
- The plan includes risks, validation, rollback, and definition of done.
- The model states assumptions instead of inventing unavailable facts.

## Step 5: Optional Approved-Write Smoke Test

Run this only in a disposable repository, test branch, or small documentation-only task.

For existing-file validation, temporarily set `create_new_file` to Excluded in
Continue built-in tools. Keep `edit_existing_file` and `single_find_and_replace`
as Ask First. Pre-create the target file so the model must edit an existing file
instead of taking both create and edit paths.

Pre-create the test file:

Windows:

```powershell
Set-Content .\continue-agent-write-test.md "before"
```

Linux or macOS:

```bash
printf '%s\n' 'before' > ./continue-agent-write-test.md
```

Prompt:

```text
Use approved write mode for this smoke test only.

Edit the existing file continue-agent-write-test.md in the opened repository root.
Replace the entire file content with exactly this content:

Continue Agent write test passed.

Do not edit any other files.
Do not create a new file.
Do not append.
Do not create the file under src, docs, Properties, or any other subfolder.
Use one edit tool call.
Stop after the first Apply diff.
Do not commit.
```

After the assistant reports success, verify from a normal terminal in the same
repository. The assistant's own claim that it read the file back is not enough.

Windows:

```powershell
git status --short
Test-Path .\continue-agent-write-test.md
Get-Content .\continue-agent-write-test.md
git diff --check
```

Linux or macOS:

```bash
git status --short
test -f ./continue-agent-write-test.md && cat ./continue-agent-write-test.md
git diff --check
```

Passing criteria:

- The assistant uses an edit/apply tool instead of telling the user to create the file manually.
- The assistant does not answer with "I can't directly edit files" or copy/paste implementation instructions when write tools are available.
- Before editing, the assistant can read the target file or confirms that it is creating a new file.
- For unqualified file names, the assistant edits or creates the file in the opened repository root or current folder, unless the user requested another folder or repository evidence proves another target.
- If no file is open or the current folder is unclear, the assistant first discovers the workspace with available tools.
- If workspace discovery fails, the assistant says `WORKSPACE_UNAVAILABLE` and stops.
- If the target path is ambiguous, the assistant says `PATH_AMBIGUOUS` instead of inventing a subfolder path.
- The assistant does not make changes based on "typical" project patterns without file evidence.
- The apply target matches the requested and read target file. If it does not match, record `APPLY_TARGET_MISMATCH`.
- Only `continue-agent-write-test.md` changes.
- `git status --short` shows `continue-agent-write-test.md` in the opened repository root.
- A shell `Test-Path`/`test -f` check confirms the file exists on disk.
- A shell `Get-Content`/`cat` check confirms the exact requested content.
- Only one approval or Apply path is used.
- The diff is small and reviewable.
- The model reports what changed.
- Validation runs or a clear manual validation is recorded.
- `git diff --check` passes.

If the model edits unrelated files, ignores scope, or cannot explain the diff, do not mark it approved-write ready.

If both `create_new_file` and `edit_existing_file` prompts appear for the same
target, stop and record the failure signal as `DUPLICATE_APPROVALS`. If the
final file contains the requested line twice, record `DUPLICATE_CONTENT`.

If the model creates the requested file in the wrong folder, such as
`src/README.md` when an existing root `README.md` was the intended target, do
not mark it approved-write ready.

If the model reads one file but the Continue Apply panel targets another file,
such as reading `README.md` but proposing `src/main.py`, do not apply the patch
and do not mark it approved-write ready. Record the failure as
`APPLY_TARGET_MISMATCH`.

If the model claims it changed a file but `git status`, `git diff`, or an
external shell file check cannot see the requested file/content, record the
result as `WRITE_NOT_APPLIED`.

If the model claims it created and read back a file, but a normal terminal
cannot find that file in the repository root, record the result as
`WRITE_NOT_APPLIED`. Treat the assistant's readback as insufficient evidence
until the filesystem check passes.

If the model prints an `edit_file` call or other edit-shaped text but the
repository file does not change, also record the result as `WRITE_NOT_APPLIED`.
Tool-call text is not a successful edit.

If the model says it cannot read the relevant files, or it proposes a change
based on assumptions rather than observed file content, mark the write test as
failed for real code changes even if a simple file-creation smoke test passed.

Clean up the smoke-test file after recording the result.

## Step 6: Evidence Review

Before committing sanitized evidence:

1. Remove raw transcripts.
2. Remove private repository names.
3. Remove private paths and endpoints.
4. Replace sensitive details with generic labels.
5. Keep only the results needed to update guidance.

Use status labels precisely:

- Candidate
- Read-only listing only
- Read-only tool validated
- Plan validated
- Approved-write ready
- Failed read-only tool validation
- Failed read-content validation
- Failed plan-only validation
- Failed approved-write smoke test

## Where Evidence Lives

For now, keep reusable template evidence in `examples/model-tool-use-validation.md`.

Commit sanitized validation notes only when they change shared guidance. Routine private test runs can stay local.

If evidence grows beyond a few records, create a dedicated docs page or catalog in a future milestone.

## Related Docs

- `docs/local-model-selection.md`
- `docs/local-model-reliability.md`
- `docs/editor-compatibility.md`
- `docs/tool-use-modes.md`
- `docs/scoped-edits.md`
- `docs/local-config-safety.md`
