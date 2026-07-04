# Release Guidance

## Purpose

This document defines the release process for the Continue Enterprise Engineering Pack.

The release process is intentionally lightweight because this repository is configuration and documentation heavy, but each release should still be validated, versioned, tagged, and documented.

## Versioning

Use semantic versioning while the pack matures:

- Patch: documentation fixes, prompt refinements, validation improvements, examples, and non-breaking config updates.
- Minor: new workflows, new rule groups, new optional integrations, or meaningful pack capability additions.
- Major: breaking config changes, incompatible Continue schema changes, or default integration/model posture changes.

Current early releases should remain in the `0.1.x` range until the pack is validated across more repositories.

## Files To Update

For each release, update:

- `.continue/config.yaml`
- `CHANGELOG.md`
- `README.md`, if setup, status, or workflow docs changed
- `ROADMAP.md`, if milestone state changed
- `TODO.md`, if tracked work changed

Update `DECISIONS.md` when the release includes a durable policy, architecture, compatibility, or governance decision.

## Validation Checklist

Before tagging a release:

- [ ] Run Windows validation: `.\scripts\validate-pack.ps1` and `.\scripts\test-pack.ps1`.
- [ ] Run Linux validation when Bash is available: `./scripts/validate-pack.linux.sh` and `./scripts/test-pack.linux.sh`.
- [ ] Run macOS validation when available: `./scripts/validate-pack.macos.sh` and `./scripts/test-pack.macos.sh`.
- [ ] Confirm `.continue/config.yaml` has the intended version.
- [ ] Confirm Continue can load `.continue/config.yaml` when runtime validation is available.
- [ ] Confirm local Ollama model assumptions are still documented.
- [ ] Confirm `mcpServers: []` remains the default unless a decision record changes that posture.
- [ ] Confirm no private IPs, private hostnames, tokens, or project identifiers are committed.
- [ ] Confirm new examples and fixtures are sanitized.
- [ ] Confirm `CHANGELOG.md` has a release entry.

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
