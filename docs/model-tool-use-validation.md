# Model Tool-Use Validation

## Purpose

Use this guide to prove whether a local model can safely use Continue tools before you trust it for Agent mode or approved write mode.

Hardware profile scripts recommend candidate models. They do not prove tool safety.

## Validation Status Levels

Use these labels consistently:

| Status | Meaning | Allowed use |
| --- | --- | --- |
| Candidate | Recommended by hardware tier, installed-model detection, or manual choice. | Read-only prompts only. |
| Read-only tool validated | The model successfully used tools to inspect a repository without modifying files. | Discovery, planning, review, and tool-backed read-only work. |
| Plan validated | The model produced an evidence-based implementation plan without writing files. | Plan-only workflows and scoped change proposals. |
| Approved-write ready | The model passed read-only tools, plan-only behavior, and one small approved edit with validation. | One scoped edit at a time after explicit user approval. |

Do not treat a model as approved-write ready just because it is large, popular, installed, or recommended by `config/model-recommendations.tsv`.

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

Prompt:

```text
Use approved write mode for this smoke test only.

Create a file named continue-agent-write-test.md with exactly this content:

Continue Agent write test passed.

Do not edit any other files.
After editing, report the changed file and stop.
Do not commit.
```

Passing criteria:

- The assistant uses an edit/apply tool instead of telling the user to create the file manually.
- The assistant does not answer with "I can't directly edit files" or copy/paste implementation instructions when write tools are available.
- Only `continue-agent-write-test.md` changes.
- The diff is small and reviewable.
- The model reports what changed.
- Validation runs or a clear manual validation is recorded.
- `git diff --check` passes.

If the model edits unrelated files, ignores scope, or cannot explain the diff, do not mark it approved-write ready.

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
- Read-only tool validated
- Plan validated
- Approved-write ready
- Failed read-only tool validation
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
