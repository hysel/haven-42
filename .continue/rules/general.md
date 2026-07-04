---
name: General Engineering Standards
---

## Scope

Apply these standards to all engineering, review, documentation, and planning work.

## Required Practices

- Understand the existing repository before proposing or making changes.
- Preserve existing style, naming, organization, and framework choices unless there is a clear reason to change them.
- Keep changes small, cohesive, and tied to the stated objective.
- Match commands to the user's active operating system and shell.
- On Windows, prefer PowerShell-native commands such as `Get-ChildItem`, `Select-String`, `Get-Content`, `Set-Location`, and normal `git` commands. Do not use Linux commands such as `grep`, `sed`, `awk`, `find`, or Bash syntax unless the user is explicitly running Git Bash, WSL, or another Unix-like shell.
- On Linux and macOS, prefer shell commands and the repository's native `.sh` scripts. Do not ask Linux or macOS users to run PowerShell scripts unless they explicitly choose that path.
- Prefer explicit behavior over hidden conventions.
- Identify assumptions, uncertainty, and tradeoffs.
- Explain material risks before recommending risky changes.
- Do not introduce secrets, credentials, tokens, private keys, or environment-specific confidential values.
- Treat generated code and analysis as requiring human review.
- When the user clearly approves implementation, use the available file edit/apply tools to make the scoped change. If write tools are unavailable, say so plainly instead of presenting a plan as if it were implemented.
- Do not respond to an approved write request with "I can't directly edit files", "I cannot modify files", or "you can add this yourself" unless the Continue edit/apply tools are actually unavailable in the current surface. First attempt the edit/apply tool that Continue provides.
- If a command fails because it used the wrong shell or platform syntax, correct the command for the active platform before continuing.

## Avoid

- Broad rewrites that are not required by the task.
- Speculative abstractions.
- Mixing unrelated concerns in one change.
- Claiming validation was performed when it was not.
- Hiding known limitations.
- Printing tool-call JSON or markup as a substitute for running tools.
- Saying the user must edit files manually when approved write tools are available.
- Providing copy/paste implementation blocks instead of making the approved file edits when write tools are available.

## Review Checklist

- Is the recommendation tied to repository evidence?
- Is the smallest useful change being suggested?
- Are risks and tradeoffs visible?
- Are follow-up tasks separated from required work?
