# Multi-Repository Validation

## Purpose

Use this guide to validate the pack against more than one repository shape.

The goal is to prove that the prompts, rules, install scripts, model guidance,
and tool-use guardrails work across realistic projects without committing
private code, local paths, endpoints, raw transcripts, or customer details.

## Repository Categories

Track coverage by repository category instead of by private repository name.

Recommended categories:

| Category | What to validate |
| --- | --- |
| Legacy .NET or .NET Framework | Project discovery, dependency migration planning, config handling, and conservative modernization guidance. |
| Modern .NET or ASP.NET Core | Clean Architecture, API, security, testing, logging, and performance review behavior. |
| Documentation or configuration pack | Repository-type classification, setup docs, validation scripts, and non-application recommendations. |
| Frontend application | Repository discovery, package/tooling awareness, test guidance, and scoped edits. |
| Script or tooling repository | Cross-platform commands, install/update instructions, validation scripts, and shell safety. |

Add new categories only when they represent a meaningfully different project
shape or risk profile.

## Minimum Validation Flow

For each repository category:

1. Start from a clean git working tree.
2. Install or update the pack with the documented installer.
3. Confirm Continue is using the intended config.
4. Run repository discovery in read-only mode.
5. Run implementation planning in plan-only mode.
6. Run one review workflow that matches the repository type.
7. If tools are required, run read-content validation before approved writes.
8. If approved writes are required, run the approved-write smoke test first.
9. Verify any claimed changes with external shell or git commands.
10. Run deterministic output verification for generated workflow outputs.
11. Record sanitized evidence with `examples/multi-repository-validation.md`.

When additional real repositories are not available, create local sample repositories for representative categories. Generated samples should contain realistic file names, minimal source/configuration files, and no private code or endpoints.

Do not skip the clean-tree check. It is the easiest way to avoid mixing pack
validation with unrelated user changes.

## What To Record

Record only reusable, sanitized evidence:

- Repository category.
- Repository size bucket, such as small, medium, or large.
- Primary language or framework family.
- Editor surface, Continue version, model, and provider.
- Operating system.
- Whether MCP was enabled.
- Prompts tested.
- Tool-use status.
- Pass/fail result.
- Failure signals.
- Follow-up changes made to this pack.

Do not record:

- private repository names.
- Private file paths.
- Private endpoints or IP addresses.
- Usernames, hostnames, tokens, or secrets.
- Raw source code.
- Raw model transcripts.
- Customer, employer, or internal project identifiers.

## Pass Criteria

A validation run passes when:

- The assistant classifies the repository type correctly.
- The assistant uses actual repository evidence instead of generic advice.
- The assistant respects read-only and plan-only boundaries.
- Any tool use matches the active operating system and shell.
- Any approved write is scoped, externally verified, and reversible.
- Sensitive information is not copied into committed pack documentation.

## Failure Signals

Use the existing failure labels where possible:

- `READ_TOOLS_UNAVAILABLE`
- `WRITE_TOOLS_UNAVAILABLE`
- `WRITE_NOT_APPLIED`
- `PATH_AMBIGUOUS`
- `WORKSPACE_UNAVAILABLE`
- `APPLY_TARGET_MISMATCH`
- `DUPLICATE_APPROVALS`
- `DUPLICATE_CONTENT`
- `RAW_TOOL_CALL_OUTPUT`
- `THINK_TAG_LEAK`

Add a short plain-language note when a new failure mode appears. Convert
repeated failure modes into prompt, rule, documentation, or script changes.

## Updating Shared Guidance

Use this decision path after each validation run:

1. If the issue is caused by one repository only, keep it in sanitized evidence.
2. If the issue affects a project category, update docs or prompts.
3. If the issue affects install, validation, model selection, or tooling, add a
   test before changing behavior.
4. If the issue affects private environment setup only, document the pattern
   without committing private endpoints, paths, or names.

## Related Docs

- `docs/runtime-validation.md`
- `docs/runtime-output-verification.md`
- `docs/model-tool-use-validation.md`
- `docs/tool-use-modes.md`
- `docs/scoped-edits.md`
- `docs/local-config-safety.md`
- `examples/multi-repository-validation.md`
