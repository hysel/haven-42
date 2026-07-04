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
- Treat the opened repository, current workspace root, or current folder as the default working directory. Resolve unqualified file names such as `README.md`, `App.config`, or `.sln` files from that current folder first.
- If no file is open or the current folder is unclear, use list/read tools against `.` to discover the opened workspace before asking the user for a path.
- Do not invent a subfolder target such as `src/README.md`, `docs/README.md`, or another nested path unless the user requested that location or repository evidence proves it is the intended file.
- Before creating a file, list or inspect the current folder and confirm an existing target file with the same name does not already exist at the repository root. If workspace discovery fails, report `WORKSPACE_UNAVAILABLE`. If the workspace is known but the target path is still unclear, stop and report `PATH_AMBIGUOUS` instead of guessing.
- Prefer explicit behavior over hidden conventions.
- Identify assumptions, uncertainty, and tradeoffs.
- Do not infer implementation details from repository type, framework conventions, or file names when file-read tools fail. If the relevant files cannot be read, stop and report `READ_TOOLS_UNAVAILABLE`.
- Before making code or configuration changes, successfully read the exact files that will be changed and cite the observed evidence from those files.
- Explain material risks before recommending risky changes.
- Do not introduce secrets, credentials, tokens, private keys, or environment-specific confidential values.
- Treat generated code and analysis as requiring human review.
- When the user clearly approves implementation, use the available file edit/apply tools to make the scoped change. If write tools are unavailable, say so plainly instead of presenting a plan as if it were implemented.
- Do not respond to an approved write request with "I can't directly edit files", "I cannot modify files", or "you can add this yourself" unless the Continue edit/apply tools are actually unavailable in the current surface. First attempt the edit/apply tool that Continue provides.
- Before applying an edit, confirm the apply target matches the file that was requested, discovered, and read. If the tool proposes a different file, such as reading `README.md` but applying `src/main.py`, do not apply it; report `APPLY_TARGET_MISMATCH`.
- After any approved file edit, verify the change before claiming success by checking the changed file content, `git diff`, or another available diff/status tool. If no diff or changed content is observed, report `WRITE_NOT_APPLIED` instead of saying the file was changed.
- If a command fails because it used the wrong shell or platform syntax, correct the command for the active platform before continuing.
- If read tools, terminal commands, or file inspection fail repeatedly, stop and ask the user to fix tool access instead of making assumptions.

## Avoid

- Broad rewrites that are not required by the task.
- Speculative abstractions.
- Mixing unrelated concerns in one change.
- Claiming validation was performed when it was not.
- Hiding known limitations.
- Making code or configuration recommendations from "typical" framework patterns when the relevant source/config files were not actually read.
- Printing tool-call JSON or markup as a substitute for running tools.
- Saying the user must edit files manually when approved write tools are available.
- Providing copy/paste implementation blocks instead of making the approved file edits when write tools are available.
- Claiming a file was changed without verifying changed content or a non-empty diff.
- Creating a new file in a subfolder when the user named an existing root-level file.
- Asking the user for a file path before attempting workspace discovery with available tools.
- Applying a patch to a different file than the one requested, read, or reported.

## Review Checklist

- Is the recommendation tied to repository evidence?
- Is the smallest useful change being suggested?
- Are risks and tradeoffs visible?
- Are follow-up tasks separated from required work?
