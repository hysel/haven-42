---
name: Git And Change Management
---

## Scope

Use these standards when reviewing or modifying version-controlled files.

## Required Practices

- Check the working tree before making edits.
- Never overwrite user changes without explicit approval.
- Keep commits focused on one logical change.
- Use clear imperative commit messages when asked to commit.
- Separate generated or mechanical changes from design changes when practical.
- Mention uncommitted changes that affect review or validation.

## Avoid

- Destructive Git commands unless explicitly requested and approved.
- Mixing unrelated documentation, configuration, and code changes.
- Committing secrets, machine-local paths, generated binaries, or build artifacts.

## Review Checklist

- Are changed files expected for the task?
- Are unrelated changes preserved?
- Is the change easy to review as a unit?
