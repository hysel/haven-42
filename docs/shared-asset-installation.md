# Shared Asset Installation

> **Historical Continue evidence:** Continue is a legacy, evidence-only surface in
> Haven 42. This page preserves the exact shared-assets experiment and its commands;
> every Continue installation or configuration step below is historical reproduction
> input, not current setup guidance. Maintained surfaces require their own admitted
> shared-asset design and validation.

## Purpose

This page records an opt-in Continue experiment for using the pack across more than one target repository. The project-local and shared-assets commands below describe that historical fixture only.

The experiment targeted editors that loaded the global Continue config and maintainers who did not want each repository to carry a duplicate copy of the same pack assets.

`docs/config-generation-strategy.md` preserves the comparison among project-local, global Continue, shared-assets, and future surface-specific config choices.

## Historical Modes

### Project-Local Mode

Project-local mode is the default. The installer copies `.continue` assets into the target repository.

Use it when:

- You are installing the pack into one repository.
- You want every repository to carry its own inspectable `.continue` assets.
- You are new to Continue, local models, or tool-backed Agent workflows.
- You want the least surprising setup.

### Shared-Assets Mode

Shared-assets mode is advanced and explicit. The installer copies reusable assets into one local folder and updates the global Continue config to point at that folder.

Use it when:

- You work across multiple repositories on the same machine.
- Your editor loads the global Continue config more reliably than project-local config.
- You want one centrally updated copy of prompts, rules, docs, templates, and agents.
- You are comfortable with generated absolute `file://` references in a local config file.

## What Gets Copied

Shared-assets mode copies reusable files from this pack's `.continue` folder:

- `config.yaml`
- `agents/`
- `prompts/`
- `rules/`
- `rule-packs/`
- `templates/`

It excludes local overrides such as `config.local.yaml` and `config.local*.yaml`.

By default, the generated global Continue config omits the `rules:` section. This avoids duplicate rule warnings when the opened repository also contains `.continue/rules`. Use the explicit include-rules option only when the editor will not load project-local rules.

## Default Shared Asset Locations

If you do not pass an explicit shared asset path, the installers use a user-level local folder:

- Windows: `%USERPROFILE%\.haven-42\assets`
- Linux: `${XDG_DATA_HOME:-$HOME/.local/share}/haven-42/assets`
- macOS: `$HOME/Library/Application Support/LocalEngineeringAgentPack/assets`

You can override the location with `-SharedAssetsPath` or `--shared-assets-path`.

## Windows Commands

Preview the install:

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -SharedAssets `
  -SharedAssetsPath "$HOME\.haven-42\assets" `
  -GlobalConfigPath "$HOME\.continue\config.yaml" `
  -DryRun
```

Install shared assets and update the global Continue config:

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -SharedAssets `
  -SharedAssetsPath "$HOME\.haven-42\assets" `
  -GlobalConfigPath "$HOME\.continue\config.yaml"
```

Use a local-network Ollama endpoint only in the generated global config:

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -SharedAssets `
  -GlobalConfigApiBase "http://127.0.0.1:11434"
```

## Linux Commands

Preview the install:

```bash
./scripts/install-continue-pack.linux.sh   --target-repo /path/to/your-project   --shared-assets   --shared-assets-path "$HOME/.local/share/haven-42/assets"   --global-config-path "$HOME/.continue/config.yaml"   --dry-run
```

Install shared assets and update the global Continue config:

```bash
./scripts/install-continue-pack.linux.sh   --target-repo /path/to/your-project   --shared-assets   --shared-assets-path "$HOME/.local/share/haven-42/assets"   --global-config-path "$HOME/.continue/config.yaml"
```

## macOS Commands

Preview the install:

```bash
./scripts/install-continue-pack.macos.sh   --target-repo /path/to/your-project   --shared-assets   --shared-assets-path "$HOME/Library/Application Support/LocalEngineeringAgentPack/assets"   --global-config-path "$HOME/.continue/config.yaml"   --dry-run
```

Install shared assets and update the global Continue config:

```bash
./scripts/install-continue-pack.macos.sh   --target-repo /path/to/your-project   --shared-assets   --shared-assets-path "$HOME/Library/Application Support/LocalEngineeringAgentPack/assets"   --global-config-path "$HOME/.continue/config.yaml"
```

## Behavior

When shared-assets mode is enabled, the installer:

1. Requires a target repository path for safety checks and workflow context.
2. Does not replace the target repository's `.continue` folder.
3. Copies reusable assets into the shared asset path.
4. Backs up an existing shared asset folder before replacing it.
5. Generates the global Continue config automatically.
6. Backs up the previous global Continue config before replacing it.
7. Rewrites `file://./...` references into absolute references to the shared asset folder.
8. Omits `rules:` by default to prevent duplicate rule warnings.
9. Validates that copied `file://` references resolve.
10. Skips project-specific classification and language-rule activation because the same shared folder can serve repositories with different ecosystems.
10. Skips project-specific classification and language-rule activation because the same shared folder can serve repositories with different ecosystems.

Shared-assets mode currently supports reusable assets and global config generation only. Do not combine it with `-AutoModelConfig`, `-ModelLanes`, or read-only/approved-write install profiles. Those profile features still write project-local config today.

## Validation

The historical campaign restarted the editor and ran this read-only test in Continue Agent mode:

```text
Use tools to inspect the repository root.
Do not modify files.
Do not guess.
If tools are unavailable, say: TOOLS_UNAVAILABLE.
Return only the actual top-level file and folder names you inspected.
```

Then verify externally:

Windows PowerShell:

```powershell
git status --short
Select-String -Path "$HOME\.continue\config.yaml" -Pattern "file://|rules:|prompts"
```

Linux or macOS:

```bash
git status --short
grep -E "file://|rules:|prompts" "$HOME/.continue/config.yaml"
```

Expected result:

- The global config contains absolute `file://` references to the shared asset folder.
- The global config does not contain `file://./` references.
- The global config does not contain `rules:` unless you explicitly included rules.
- The opened repository remains clean unless you intentionally installed project-local assets separately.

## Security And Privacy

The shared asset folder should contain reusable pack assets only. It must not contain:

- API keys or tokens.
- Private model server URLs unless they are intentionally written to a local-only generated global config.
- Private repository names.
- User-specific validation outputs.
- Raw runtime validation transcripts.
- Local-only `config.local*.yaml` files.

Generated global config files may contain local absolute paths because editors need them. Treat those files as local machine state unless explicitly sanitized.

## Rollback

Rollback is straightforward:

1. Restore the previous global Continue config backup.
2. Remove or archive the shared asset folder.
3. Re-run the installer in project-local mode if needed.
4. Restart the editor.
5. Run the read-only tool validation prompt again.

## Known Limitations

- Shared-assets mode was implemented for historical Continue global config generation.
- Project-local model profile generation remains separate.
- Maintained non-Continue surfaces may reuse this folder layout only after surface-specific validation. See `docs/surface-specific-config-bundles.md`.
- The target repository can still have its own `.continue` folder for project-specific rules, evidence, or local overrides.
- Automatic language-rule activation requires project-local installation today. A future per-project overlay for centralized assets remains planned.
- Automatic language-rule activation requires project-local installation today. A future per-project overlay for centralized assets remains planned.
