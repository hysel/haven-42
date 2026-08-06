# Private alpha preparation

> Historical preparation record: the owner later approved the exact Windows
> candidate, and `0.4.0-alpha.1` was published as an unsigned GitHub prerelease
> on 2026-08-05. See the [published release record](windows-alpha-release.md).
> This document and its preparation contract do not authorize another release.

Haven 42 has selected the `0.4.0-alpha.1` Windows x64 implementation for an
invited private-alpha test candidate. This remains preparation only: the exact
source commit, distribution channel, release tag, GitHub Release, signing
identity, installer, updater, and production claim have not been admitted.

## Proposed boundary

The Alpha reuses the shared browser UI and PyInstaller one-folder package. It
remains portable, user-scoped, loopback-bound, unsigned, and free of bundled
provider engines, models, drivers, TLS gateways, or other external software.
It exposes Chat, Writing, and Summarization through one continuous text
workspace. After explicit, single-use consent, the guided option may download
pinned standalone Ollama and model artifacts into `Haven42-Data` inside the
extracted package folder; the manual option explains how to provide them.

The package may be considered for invited evaluation only after an exact
protected commit is selected. That exact commit must
receive a fresh clean security review, public-history privacy scan, Full gate,
hosted Windows/Linux/macOS checks, artifact verification, and digest-bound
evidence. Prior successful builds establish the foundation but cannot admit a
future candidate.

## Decisions and remaining approvals

The owner selected the version, Windows x64 platform cell, text-only
Chat/Writing/Summarization scope, and invited-testers-only audience. Before
distribution, the owner must still
explicitly select:

1. an authenticated HTTPS artifact-delivery channel with least-privilege
   access, bounded retention, expiry, and immediate revocation;
2. the response expectations for the prepared GitHub problem and feedback
   forms; and
3. the exact candidate commit after the implementation and package are tested.

A version selection does not authorize a tag or public release. Distribution
approval must be candidate-, digest-, audience-, and channel-specific.

## Candidate evidence packet

The packet must contain only sanitized, content-free evidence:

- exact 40-character source commit and clean tree state;
- candidate version and target platform;
- archive filename, byte size, and SHA-256;
- full file inventory and package/resource integrity results;
- dependency inventory, third-party notices, and CycloneDX SBOM;
- unsigned provenance and available GitHub artifact attestation;
- exact native package smoke result;
- security, privacy, Full-gate, and hosted-CI results;
- known limitations and tester runbook revisions; and
- expiration, revocation, and deletion instructions for the private artifact.

It must not contain provider addresses, API keys, prompts, attachments, model
responses, usernames, local paths, machine identifiers, SSH data, or tester
identity.

## Stop conditions

Do not create or distribute a candidate when any required check is missing,
stale, skipped unexpectedly, or bound to another tree or artifact. Stop for
any security finding, privacy finding, unexpected package member, dependency
drift, failed cleanup, non-loopback Haven listener, secret disclosure,
unreviewed machine effect, or inconsistency between source and package.

The machine-readable source of truth is
`config/private-alpha-readiness-contract.json`. Evaluate it with
`python scripts/evaluate-private-alpha-readiness.py`.

The candidate packet must also include the current
[known limitations](private-alpha-known-limitations.md). Testers follow the
[private-alpha test plan](private-alpha-test-plan.md) and report results with
the [private-alpha feedback template](private-alpha-feedback-template.md) or
the structured [Alpha report chooser](https://github.com/hysel/haven-42/issues/new/choose).
