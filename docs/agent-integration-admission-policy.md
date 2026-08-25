# Agent Integration Admission Policy

This policy defines when agent software may add executable or operational assets to the shipped pack.

## Decision

The project may evaluate any agent software, but evaluation does not grant repository admission. Before the repository accepts or ships any agent-specific script, harness, wrapper, adapter, configuration generator, template, example, workflow, active catalog entry, or package asset, the new agent must pass the required promotion gates.

If an evaluation fails, commit only a concise sanitized decision record. Do not commit the evaluation harness, generated configuration, detailed transcript, raw output, temporary fixture, or partially working integration. Git history and external maintainer records are not product surfaces and must not be used to keep dormant code in the shipped repository.

## Evaluation Workspace

- Run candidate evaluations in a disposable directory outside the tracked repository or under an ignored temporary output directory.
- Keep test commands, temporary harnesses, candidate configuration, logs, and generated fixtures untracked.
- Use generated repositories or explicitly approved non-generated repositories under the existing safety rules.
- Keep credentials, private endpoints, local paths, usernames, customer data, and raw private source out of results.
- Delete disposable evaluation assets after recording the outcome.

## Pass-To-Ship Gate

Before agent-specific assets may be committed, the exact agent version and intended operating mode must pass:

1. Installation and command discovery on every claimed operating system.
2. Local-only configuration without committed private endpoints or credentials.
3. Read-only repository inspection with grounded filenames and content.
4. Disposable write-smoke verification.
5. Realistic scoped-edit verification with exact changed-file checks, direct content checks, and `git diff --check`.
6. Cleanup and model-unload behavior where applicable.
7. Cross-platform deterministic contract tests for every shipped script.
8. The full local pack suite and exact-SHA GitHub Windows, Linux, and macOS jobs.

Passing an external evaluation permits a reviewed integration change; it does not bypass repository tests, code review, or release readiness.

## Failed Evaluation Record

A failed evaluation record should contain only:

- Agent name and exact tested version.
- Operating system and sanitized runtime category.
- Gates attempted and their pass/fail outcome.
- Concise failure reason without raw transcripts or machine details.
- Decision: not admitted and no artifacts shipped.
- Conditions that would justify a completely new evaluation.

Record the summary in the removed-integrations section of `docs/agent-surface-options.md`, `DECISIONS.md`, or the changelog as appropriate. Do not add failed candidates to active solution, capability, defaults, workflow, evidence, or packaging catalogs.

## Candidate Documentation Boundary

Architecture or isolation-boundary documentation may be committed before execution when it is necessary to define a safe evaluation. It must not contain runnable integration code, claim validation, expose an end-user workflow, or enter the default package menu. OpenHands currently occupies this documentation-only candidate state.

## Re-entry

Removed or previously failed software has no dormant implementation path. A future version starts as a new external evaluation and must pass the complete gate before any agent-specific artifact returns.
