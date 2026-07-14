# Project Profile Classification

## Purpose

Project profile classification gives installers and future user interfaces a deterministic way to identify repository ecosystems before enabling language-specific guidance. It inspects filenames and relative paths only. It does not read source-file contents or record the target repository path.

The signal catalog is `config/project-profile-rules.json`. The output contract is a sanitized `.continue/project-profile.json` file with:

- schema version and classification method
- primary and detected ecosystems
- high, medium, or unconfirmed confidence
- relative evidence filenames and matched signal patterns
- selected optional rule-pack IDs
- source and active rule-pack paths
- explicit privacy metadata

## Run It Directly

Windows PowerShell:

```powershell
.\scripts\get-project-profile.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -OutputPath ".\runtime-validation-output\project-profile.json"
```

Linux:

```bash
./scripts/get-project-profile.linux.sh \
  --target-repo /path/to/your-project \
  --output-path ./runtime-validation-output/project-profile.json
```

macOS:

```bash
./scripts/get-project-profile.macos.sh \
  --target-repo /path/to/your-project \
  --output-path ./runtime-validation-output/project-profile.json
```

Use `-AsJson` on Windows or `--as-json` on Linux and macOS to also print the result. Linux and macOS classification requires `python3` for structured JSON processing.

## Installer Behavior

Project-local installation runs classification before changing the target:

1. The installer reports the detected primary ecosystem and selected rule packs.
2. Dry-run shows the planned profile and activation without writing files.
3. Install copies reusable source packs under `.continue/rule-packs/`.
4. Install writes the sanitized profile to `.continue/project-profile.json`.
5. Each selected pack is copied to `.continue/rules/active-language-<id>.md` so project-local rule discovery can load it.
6. Unmatched optional packs remain available as inactive source files and are not copied into `.continue/rules/`.

Mixed repositories can activate more than one pack. For example, a Node service with a `package.json` and `Dockerfile` can select both TypeScript and Infrastructure as Code guidance.

The committed `.continue/config.yaml` still does not reference optional source packs globally. This prevents every language pack from loading for every repository and avoids adding duplicate global rule references.

## Confidence And Safety

- High confidence means at least one strong project marker matched, such as `pyproject.toml`, `package.json`, `go.mod`, or `Cargo.toml`.
- Medium confidence means supporting file evidence matched without a strong marker.
- Unconfirmed means no configured ecosystem signal matched.

The current catalog permits high- and medium-confidence optional pack activation. Rule packs still contain their own evidence gates, and agents must label frameworks, package managers, test runners, and deployment assumptions as `unconfirmed` when metadata does not prove them.

Ignored directories include source-control metadata, editor configuration, dependency caches, build outputs, virtual environments, and runtime validation output. Symlinked or reparse-point directories are not traversed.

## Shared Assets

Shared-assets mode intentionally skips project-specific activation. One centralized asset folder can serve many repositories, so it cannot safely choose one language profile for all of them.

Use project-local installation when automatic activation is required. A future shared-assets design may add a small per-project overlay containing only the sanitized profile and active rule copies; that overlay is not implemented yet.

## Verification

After a project-local install, inspect:

```powershell
Get-Content .\.continue\project-profile.json
Get-ChildItem .\.continue\rules\active-language-*.md
```

or:

```bash
cat .continue/project-profile.json
find .continue/rules -maxdepth 1 -name 'active-language-*.md' -print
```

The profile must not contain usernames, hostnames, IP addresses, absolute target paths, or file contents.
