# MCP Workflow Examples

## Purpose

This document gives practical MCP workflow examples for people using this pack with Continue.

Use these examples only after the normal pack works without MCP. MCP is optional and should stay disabled until you intentionally add it.

## Before You Start

Confirm these basics first:

- Continue works with your local model.
- Your repository has a local copy of this pack's `.continue` folder.
- Continue is running in agent mode.
- Your MCP server is configured locally and is not committed with secrets.
- You can run a read-only prompt successfully before approving any write workflow.

Keep the default pack config unchanged:

```yaml
mcpServers: []
```

Use local MCP configuration only for your own machine or team setup.

## Example 1: Read-Only Repository And Pull Request Review

Use this when you want Continue to inspect GitHub repository, issue, or pull request context without changing anything.

### Goal

Summarize repository or pull request context and separate MCP evidence from local repository evidence.

### Recommended Prompt

```text
Use GitHub MCP in read-only mode.

Review the current pull request and summarize:

1. The user-facing change
2. The files changed
3. Any linked issue or discussion context
4. Risks that should be reviewed before merge
5. Test evidence that is present or missing

Do not modify issues, pull requests, files, branches, labels, comments, releases, or repository settings.

Separate your answer into:

- MCP-derived evidence
- Local repository evidence
- Inferences
- Open questions
```

### Expected Good Output

The response should:

- Say which facts came from MCP.
- Say which facts came from local files or diffs.
- Avoid treating guesses as facts.
- Avoid making comments, labels, commits, or file edits.
- Ask for approval before any write action.

### Stop If You See

- Raw JSON tool-call text instead of executed tools.
- A request for broad credentials.
- A proposed write action before you approved write mode.
- Claims that do not identify whether evidence came from MCP or local files.

## Example 2: Approved Tool-Backed Change

Use this only after read-only MCP and local tool execution work reliably.

### Goal

Let Continue make a small, reviewed change in the repository while keeping control over scope.

### Recommended Prompt

```text
Use approved write mode for this specific task only.

Task:
Update the setup documentation to clarify how users should run the validation script.

Scope:
- You may edit README.md and files under docs/.
- Do not edit source code, build files, package files, workflow files, or local config files.
- Do not commit or push unless I explicitly ask.

Before editing:
1. Read the relevant existing documentation.
2. Explain which files you plan to edit and why.
3. Keep the wording beginner-friendly.

After editing:
1. Show the changed files.
2. Run the repository validation script if available.
3. Summarize exactly what changed.
```

### Expected Good Output

The assistant should:

- Read before editing.
- Keep edits within the approved files.
- Avoid unrelated cleanup.
- Avoid touching local secrets or machine-specific config.
- Run validation when available.
- Leave commit and push decisions to you.

### Stop If You See

- Edits outside the approved scope.
- Attempts to change local machine config.
- Attempts to commit, push, tag, or open a pull request without approval.
- Large refactors for a documentation-only task.

## Example 3: MCP Context Plus Local Runtime Validation

Use this when you want MCP context to support a release-readiness or implementation-plan review.

### Goal

Combine external repository context with local files and validation output.

### Recommended Prompt

```text
Use MCP only for read-only GitHub context.

Use local repository files and validation output as the primary source of truth.

Review this repository for release readiness.

Include:
- Current branch and latest local changes
- Recent pull request or issue context from MCP
- Validation or test evidence from local files
- Release blockers
- Risks that require human confirmation

Do not modify files, issues, pull requests, releases, branches, labels, or repository settings.

Clearly label:
- MCP-derived evidence
- Local file evidence
- Command output evidence
- Inferences
```

### Expected Good Output

The review should be useful even if MCP is later disabled. MCP should add context, not replace local evidence.

## Local Model Notes

MCP can work with local Ollama models, but not every model handles tool use well.

Before using approved write mode:

1. Run a read-only tool test.
2. Confirm the model executes tools instead of printing raw JSON.
3. Confirm the model labels evidence clearly.
4. Confirm it asks before write actions.
5. Use the model recommendation scripts as a starting point, then validate behavior in Continue.

## Safety Checklist

- [ ] Default `.continue/config.yaml` still has `mcpServers: []`.
- [ ] MCP setup is local-only or safely generic.
- [ ] Tokens are stored in environment variables or a secret manager.
- [ ] Read-only workflow succeeds before write mode.
- [ ] Write scope is explicit and narrow.
- [ ] The assistant separates MCP evidence, local evidence, command output, and inferences.
- [ ] No private repository names, private endpoints, secrets, usernames, or local paths are copied into committed documentation.

## Related Docs

- `docs/mcp-setup.md`
- `docs/mcp-options.md`
- `docs/tool-use-modes.md`
- `docs/approved-tool-backed-changes.md`
- `docs/scoped-edits.md`
- `docs/local-model-selection.md`
