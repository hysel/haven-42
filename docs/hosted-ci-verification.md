# Hosted CI Verification

## Purpose

Local tests prove that a change works on the current machine. They do not prove
that the pushed commit passes the hosted Windows, Linux, and macOS jobs.

Use the hosted CI verifier after every push. A push is not complete until the
verifier reports `CI passed` for the exact 40-character commit SHA.

## Required States

The verifier reports these states in order:

- `Pushed`: the expected commit SHA has been selected.
- `CI running`: an exact-SHA GitHub Actions run was found and is being watched.
- `CI passed`: the workflow and every required hosted job succeeded.
- `CI failed`: run discovery, SHA matching, workflow completion, or a required job failed.

Do not describe a push as successful while the state is only `Pushed` or
`CI running`.

## Required Hosted Jobs

The `Validate Pack` workflow must complete these jobs successfully:

- `Public repository privacy`
- `Wiki synchronization`
- `Windows PowerShell validation`
- `Linux script smoke tests`
- `macOS script smoke tests`
- `Windows portable package`
- `Linux portable package`
- `macOS portable package`

The verifier rejects a successful-looking run if it belongs to another commit
or omits one of these jobs. `CodeQL Python analysis` is separately required by
branch protection.

## Prerequisites

Install GitHub CLI, authenticate it, and run the command from the repository:

```powershell
gh auth login
gh auth status
```

The verifier treats a failed `gh auth status` preflight as advisory because public workflow APIs may still be queryable when the stored default account is stale or another credential source is active. The actual repository and exact-run queries remain authoritative: if they cannot access the requested run, verification fails and the operator must reauthenticate.

## Windows

Verify the current commit after pushing:

```powershell
git push origin main
$sha = git rev-parse HEAD
.\scripts\verify-hosted-ci.ps1 -CommitSha $sha
```

## Linux

```bash
git push origin main
./scripts/verify-hosted-ci.linux.sh --commit-sha "$(git rev-parse HEAD)"
```

## macOS

```bash
git push origin main
./scripts/verify-hosted-ci.macos.sh --commit-sha "$(git rev-parse HEAD)"
```

Use `-Repository owner/repository` or `--repository owner/repository` when the
current directory cannot be resolved by `gh repo view`. Use `-RunId` or
`--run-id` only to verify a known run; the script still rejects a SHA mismatch.

## Failure Handling

When verification fails, the script runs `gh run view --log-failed`, exits
nonzero, and reports `CI failed`. Fix the cause, run local validation again,
push the new commit, and verify that new exact SHA. Never reuse a successful run
from an older commit as evidence for a newer push.

## Required Completion Report

Every push report must include:

- The exact commit SHA.
- The GitHub Actions run URL.
- The final state.
- Confirmation that all seven `Validate Pack` jobs succeeded, or the failed job and
  relevant failure signal.
- Confirmation that branch protection also reports `CodeQL Python analysis`
  successful before merge.
