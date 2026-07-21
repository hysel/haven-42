# Release Guidance

## Purpose

This document defines the release process for Haven 42.

The release process is intentionally lightweight because this repository is configuration and documentation heavy, but each release should still be validated, versioned, tagged, and documented.

## Milestone 19 Completion Basis

Milestone 19 is complete for the Continue release-packaging scope because Continue installer profiles cover default, read-only, and approved-write workflows; `config/evidence-catalog.tsv` provides the structured sanitized evidence index; and the release packaging scripts generate archives plus checksums on Windows, Linux, and macOS.

Milestone 19 is complete for the promoted supported-surface set. Continue, Aider, and OpenCode have evidence-backed install/configure/test positions and deterministic cross-platform contracts. Failed and retired integrations are excluded from active catalogs and executable assets, while OpenHands remains a documentation-only candidate under a defined but unimplemented isolation boundary. Real-project approved write for non-Continue surfaces remains separately evidence-gated.

Additional surface-specific installer profiles remain evidence-gated until each surface has install, configure, and test evidence that can be represented safely in `config/agent-surface-solutions.json`.

Agent-specific files are admitted under `docs/agent-integration-admission-policy.md`. Release packages must contain only integrations that passed the complete pass-to-ship gate. Failed evaluations may contribute a concise sanitized decision record, but no scripts, harnesses, configuration, examples, workflows, active catalog rows, or other operational assets.

## Versioning

Use semantic versioning while the pack matures:

- Patch: documentation fixes, prompt refinements, validation improvements, examples, and non-breaking config updates.
- Minor: new workflows, new rule groups, new optional integrations, or meaningful pack capability additions.
- Major: breaking config changes, incompatible Continue schema changes, or default integration/model posture changes.

The current release line is `0.3.0`. Changes after its release remain under `Unreleased` until the next version is deliberately prepared. Do not create a release tag until the release readiness gate and exact-SHA hosted CI pass.

## Files To Update

For each release, update:

- `.continue/config.yaml`
- `CHANGELOG.md`
- `README.md`, if setup, status, or workflow docs changed
- `ROADMAP.md`, if milestone state changed
- `TODO.md`, if tracked work changed

Update `DECISIONS.md` when the release includes a durable policy, architecture, compatibility, or governance decision.

Synchronize the separate GitHub wiki whenever a mapped source changes. Follow `docs/wiki-maintenance.md`, commit and push the wiki first, and do not complete the release while the hosted `Wiki synchronization` job is failing.

## Validation Checklist

Before tagging a release:

- [ ] Run the local release readiness gate: `.\scripts\test-release-readiness.ps1`.
- [ ] Enable local Git hooks once per clone: `.\scripts\install-git-hooks.ps1`.
- [ ] Run Windows validation: `.\scripts\validate-pack.ps1` and `.\scripts\test-pack.ps1`.
- [ ] Run Linux validation when Bash is available: `./scripts/validate-pack.linux.sh` and `./scripts/test-pack.linux.sh`.
- [ ] Run macOS validation when available: `./scripts/validate-pack.macos.sh` and `./scripts/test-pack.macos.sh`.
- [ ] Confirm `.continue/config.yaml` has the intended version.
- [ ] Confirm Continue can load `.continue/config.yaml` when runtime validation is available.
- [ ] Confirm local Ollama model assumptions are still documented.
- [ ] Confirm `mcpServers: []` remains the default unless a decision record changes that posture.
- [ ] Confirm no private IPs, private hostnames, tokens, or project identifiers are committed.
- [ ] Confirm new examples and fixtures are sanitized.
- [ ] Confirm shell scripts and hooks are executable in Git before pushing.
- [ ] Confirm `CHANGELOG.md` has a release entry.
- [ ] Run the wiki synchronization script, review and commit the wiki repository, and confirm `--check` or `-Check` passes.
- [ ] After pushing, run the exact-SHA hosted verifier and require `CI passed` for the Windows, Linux, and macOS jobs.

## Verify The Pushed Commit

Local release readiness is only the pre-push gate. After pushing, verify the
exact commit with GitHub Actions:

```powershell
$sha = git rev-parse HEAD
.\scripts\verify-hosted-ci.ps1 -CommitSha $sha
```

```bash
./scripts/verify-hosted-ci.linux.sh --commit-sha "$(git rev-parse HEAD)"
```

The verifier waits with `gh run watch --exit-status`, checks the required
Windows, Linux, and macOS jobs, and retrieves failed logs automatically. Report
the exact SHA, run URL, and one of `Pushed`, `CI running`, `CI passed`, or
`CI failed`. See `docs/hosted-ci-verification.md`.


## Build Release Artifacts

Use the packaging scripts after validation passes and the working tree is clean.
The scripts package tracked repository files, write a manifest, and create a
SHA-256 checksum next to the archive.

Windows PowerShell creates a `.zip` archive:

```powershell
.\scripts\build-release-package.ps1 -Version 0.3.0
```

Linux creates a `.tar.gz` archive:

```bash
./scripts/build-release-package.linux.sh --version 0.3.0
```

macOS creates a `.tar.gz` archive and uses `shasum -a 256` when `sha256sum` is
not installed:

```bash
./scripts/build-release-package.macos.sh --version 0.3.0
```

Preview the package plan without writing files:

```powershell
.\scripts\build-release-package.ps1 -Version 0.3.0 -DryRun
```

The release readiness gate combines validation, tests, package dry-run, Git state, workflow registry checks, and agent-surface parity checks:

```powershell
.\scripts\test-release-readiness.ps1
```

```bash
./scripts/build-release-package.linux.sh --version 0.3.0 --dry-run
```

```bash
./scripts/test-release-readiness.linux.sh
```

The default output folder is `dist/`, which is ignored by Git.

## Package Contents And Exclusions

Release packages are built from Git-tracked files and exclude local or generated
state:

- `.git/`
- `.vscode/`
- `runtime-validation-output/`
- `dist/`
- `.continue/config.local*`
- `.continue.backup-*`
- `.env*`, secret, and token-style files

Do not use `-AllowDirty` or `--allow-dirty` for an actual release. Those flags
exist only for local packaging smoke tests.

## Verify Checksums

Windows PowerShell:

```powershell
Get-FileHash .\dist\haven-42-0.3.0.zip -Algorithm SHA256
Get-Content .\dist\haven-42-0.3.0.sha256
```

Linux:

```bash
sha256sum -c dist/haven-42-0.3.0.sha256
```

macOS:

```bash
shasum -a 256 -c dist/haven-42-0.3.0.sha256
```

The checksum file uses the standard format:

```text
<sha256>  <archive-file-name>
```

## GitHub Release Upload

Attach the generated archive, `.sha256` file, and `.manifest.txt` file to the
GitHub Release for the matching tag. The release notes should include the
validation summary and the checksum verification command.

## Commit And Tag

Use a release commit message:

```powershell
git add .
git commit -m "Release 0.1.3"
```

Create an annotated tag:

```powershell
git tag -a v0.1.3 -m "Release 0.1.3"
```

Push the branch and tag:

```powershell
git push origin main
git push origin v0.1.3
```

If a tag already exists, do not overwrite it without an explicit decision.

## Rollback

If a release contains a documentation or configuration issue:

1. Create a follow-up fix commit.
2. Add a new changelog entry.
3. Tag a new patch release.

Avoid rewriting public release tags unless the repository owner explicitly chooses that approach before others consume the release.

## Release Notes Shape

Use this summary format when announcing a release:

```text
Version:
Date:

Highlights:
- 

Validation:
- 

Upgrade notes:
- 
```
