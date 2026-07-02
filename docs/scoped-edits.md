# Scoped Edits From Approved Plans

## Purpose

This guide explains how to turn an approved implementation plan into small, reviewable changes in the project being worked on.

Use this after:

- `docs/tool-use-modes.md`
- `docs/approved-tool-backed-changes.md`

## Simple Rule

Do not ask for broad implementation after a large plan.

Instead, choose one small part of the approved plan and ask the assistant to edit only that part.

Good wording:

```text
Implement step 1 from the approved plan only. Keep the change scoped to the listed files. Do not make unrelated cleanup changes.
```

## Before Editing

Check the repository state:

```powershell
git status --short --branch
```

If the project has existing uncommitted changes, identify them first. The assistant should not overwrite or revert changes it did not make.

Confirm the approved plan includes:

- The goal
- Affected files
- Validation steps
- Rollback steps
- Definition of done

If any of these are missing, ask for a better plan before allowing edits.

## Step 1: Pick One Slice

A good slice is small enough to review in one diff.

Good slices:

- Add one missing document section.
- Update one prompt.
- Add one focused validation check.
- Change one config option and its matching documentation.
- Add one test fixture and one expected-output note.

Too broad:

- "Implement the whole roadmap."
- "Refactor the architecture."
- "Fix all warnings."
- "Update all docs."
- "Modernize the project."

## Step 2: Name The Files

When possible, tell the assistant which files it may change.

Example:

```text
Implement step 1 only.

Allowed files:
- README.md
- docs/tool-use-modes.md
- TODO.md

Do not modify any other files.
```

If the assistant discovers another file is needed, it should explain why before editing it.

## Step 3: Set Boundaries

Add clear limits to the request.

Useful boundaries:

```text
Do not change dependencies.
Do not change CI.
Do not change authentication or authorization.
Do not rename or delete files.
Do not commit.
```

For code work, add:

```text
Keep existing patterns. Add or update tests only for the changed behavior.
```

For documentation work, add:

```text
Keep the wording beginner-friendly. Avoid private paths, private IP addresses, secrets, and project-specific output.
```

## Step 4: Ask For The Edit

Use a request like this:

```text
Implement step 1 from the approved plan only.

Allowed files:
- path/to/file-a
- path/to/file-b

Do not modify other files.
After editing, run the relevant validation and explain the diff.
Do not commit.
```

This gives the assistant enough freedom to work while keeping the change reviewable.

## Step 5: Review The Diff

After the edit, inspect the changed files:

```powershell
git status --short
git diff --check
git diff
```

Look for:

- Files changed outside the approved scope
- Unrelated formatting churn
- Private machine details
- Missing validation
- Missing documentation updates
- Broad behavior changes hidden inside a small task

If the diff is too large, stop and ask the assistant to explain why.

## Step 6: Validate

Run the smallest useful validation first.

For this pack:

```powershell
.\scripts\validate-pack.ps1
```

For .NET projects:

```powershell
dotnet build
dotnet test
```

For Node projects:

```powershell
npm test
npm run build
```

If validation cannot run, record why and list manual checks.

## Step 7: Decide What Comes Next

After review and validation, choose one:

- Ask for a small fix.
- Approve the next plan slice.
- Commit the change.
- Stop and roll back the assistant's last change.

Do not continue stacking edits if the current diff has not been reviewed.

## Safe Prompt Template

Use this template for most approved edits:

```text
Implement this approved plan slice only:

[paste or describe the specific step]

Allowed files:
- [file 1]
- [file 2]

Boundaries:
- Do not modify other files.
- Do not rename or delete files.
- Do not change dependencies, CI, authentication, authorization, or deployment.
- Do not commit.

After editing:
- Run the relevant validation.
- Explain each changed file.
- Call out anything you could not validate.
```

## When To Stop

Stop and review manually if:

- The assistant wants to change many unrelated files.
- The assistant prints raw JSON tool calls instead of running tools.
- The assistant cannot read the target files.
- Continue reports filepath resolution errors.
- Validation fails in a way the assistant cannot explain.
- The change touches secrets, auth, deployment, or production data.

## Rollback Guidance

Prefer targeted rollback.

Safe options:

- Ask the assistant to undo only its own last edit.
- Restore one file from source control.
- Create a patch from the diff before experimenting further.
- Commit known-good work before starting another risky slice.

Avoid destructive repository-wide reset commands unless you are certain you want to discard all local changes.
