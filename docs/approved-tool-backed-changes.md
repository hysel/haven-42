# Approved Tool-Backed Changes

## Purpose

This guide explains how to let the assistant make changes in a project while keeping the user in control.

Use this after reading `docs/tool-use-modes.md`.

Use `docs/scoped-edits.md` when you are ready to convert an approved plan into small, reviewable file changes.

## Simple Rule

The assistant should not change files until the user clearly asks it to implement an approved change.

Good wording:

```text
Implement the approved plan. Keep the changes limited to the files needed for this task.
```

## Before You Start

Open the project you want to change.

Check git status:

```powershell
git status --short --branch
```

If there are uncommitted changes, decide whether they are yours and whether they should stay. The assistant should work around unrelated user changes and should not revert them.

Confirm read-only tools work before approving writes.

Safe test prompt:

```text
Use tools to list the repository files. Do not modify files.
```

Expected behavior:

- Continue shows a tool run or approval UI.
- The tool runs.
- The assistant returns a normal text response.

Do not continue to approved write mode if the assistant prints raw JSON tool calls instead of running tools.

Also confirm file-content reading works. Listing files alone is not enough for implementation.

Safe read-content prompt:

```text
Use tools to read README.md.
Do not modify files.
Return the first heading only.
If you cannot read the file, say READ_TOOLS_UNAVAILABLE.
```

Do not continue to approved write mode if the assistant cannot read real file contents.

Then confirm write tools work in a disposable branch or test repository.

Safe write smoke-test prompt:

```text
Use approved write mode for this smoke test only.

Create a file named continue-agent-write-test.md in the opened repository root with exactly this content:

Continue Agent write test passed.

Do not modify any other files.
Do not create the file under src, docs, Properties, or any other subfolder.
After editing, report the changed file and stop.
Do not commit.
```

Expected behavior:

- The assistant uses an edit/apply tool.
- The assistant does not ask you to create the file manually.
- `git status --short` shows only the smoke-test file.
- The smoke-test file is created in the opened repository root or current folder.
- A normal terminal confirms the file exists and contains the requested content.
- Assistant-only readback is not enough to mark approved write mode as validated.

Verify from the same repository:

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

On Windows, clean up with:

```powershell
Remove-Item .\continue-agent-write-test.md
```

On Linux or macOS, clean up with:

```bash
rm ./continue-agent-write-test.md
```

## Step 1: Start With Read-Only Review

Ask for discovery first:

```text
Review this project. Do not modify files. Explain the structure, risks, and likely affected areas.
```

The assistant may read files and inspect the project, but it should not edit anything.

## Step 2: Ask For A Plan

Ask for a plan before implementation:

```text
Create an implementation plan for this change. Do not write code yet.
```

The plan should include:

- Goal
- Current state
- Affected files or components
- Step-by-step implementation plan
- Risks
- Testing plan
- Rollback plan
- Definition of done

Do not approve implementation if the plan is too broad, unclear, or missing validation.

## Step 3: Approve The Change

When the plan looks right, approve the specific scope:

```text
Go ahead and implement this plan. Only change the files needed for this task.
```

For high-risk changes, be more specific:

```text
Implement steps 1 and 2 only. Do not change dependencies, config, authentication, or deployment files.
```

For a more controlled workflow, approve one plan slice at a time. See `docs/scoped-edits.md`.

If you name a file without a folder, the assistant should resolve it from the
opened repository root or current folder first. It should not create a duplicate
file in `src/`, `docs/`, or another inferred subfolder. If the correct target is
unclear, the assistant should say `PATH_AMBIGUOUS` and stop before editing.

## Step 4: Review What Changed

After implementation, check:

```powershell
git status --short
git diff --check
```

Then review the actual diff:

```powershell
git diff
```

The assistant should explain:

- Which files changed
- Why each change was needed
- What validation was run
- What still needs manual review

If `git diff` is empty for the file the assistant claimed to change, treat the
attempt as failed and do not continue with additional implementation steps.

## Step 5: Validate

Use the validation that fits the project.

Common examples:

```powershell
dotnet test
dotnet build
npm test
npm run build
```

If no automated tests exist, ask for manual validation steps.

## Step 6: Commit Only When Ready

The assistant should not commit unless the user asks.

Good wording:

```text
Commit these changes with a clear message.
```

Push only when the user asks:

```text
Push the commit to the remote repository.
```

## Stop Or Roll Back

If the changes are wrong, stop and inspect first:

```powershell
git status --short
git diff
```

Do not run destructive reset commands unless you are sure you want to discard the work.

Safer options:

- Ask the assistant to explain the diff.
- Ask the assistant to undo only its own last change.
- Restore a single file manually if needed.
- Use a branch before risky work.

## What The Assistant May Change

After approval, the assistant may change:

- Files directly related to the approved task.
- Tests related to the changed behavior.
- Documentation related to the changed behavior.
- Configuration only when the plan explicitly includes it.

## What Needs Extra Approval

Ask again before:

- Deleting files.
- Moving or renaming files.
- Changing dependencies.
- Changing authentication or authorization.
- Changing deployment, release, or CI behavior.
- Formatting unrelated files.
- Committing.
- Pushing.

## Sample Safe Flow

Use this sequence for most projects:

```text
Review this project. Do not modify files.
```

```text
Create an implementation plan for adding this feature. Do not write code yet.
```

```text
Implement the approved plan. Keep changes scoped.
```

```text
Explain the diff and tell me what validation you ran.
```

```text
Commit the changes.
```

## Local Configuration Safety

Do not commit:

- Private IP addresses.
- Local machine paths.
- Tokens or passwords.
- Personal model endpoint overrides.
- Raw private repository output.

Keep local settings in ignored files such as `.continue/config.local.yaml`.
