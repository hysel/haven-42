# Shared Asset Installation

## Purpose

Shared asset installation is a planned opt-in mode for people who use this pack across more than one target repository. The current installer copies `.continue` assets into each project and can generate a global Continue config that points at that one project copy. That is still the safest default for beginners and single-project users.

A shared asset mode would put reusable pack assets in one local machine folder and generate editor configs that point there. Target repositories would keep only project-specific files, validation outputs, and local settings.

## Current Behavior

Today the supported install path is project-local:

- The installer copies reusable assets into the target repository's `.continue` folder.
- Local-only config files can be generated in the target repository and are not committed by default.
- The global Continue config can be generated with absolute references to the target repository's installed prompts and docs.
- Generated global configs omit `rules:` by default to avoid duplicate rule warnings when the project-local `.continue/rules` folder is also loaded.

This behavior remains the default because it is explicit, easy to inspect, and works without a central machine-level asset folder.

## Problem

Project-local install becomes repetitive when one user or team applies the pack to many repositories:

- Every target repository receives its own copy of the same prompts, rules, templates, and docs.
- The global Continue config can point cleanly at one installed project copy at a time unless it is regenerated.
- Moving or deleting the target repository can break global config references.
- Users can accidentally mix old assets in one repository with newer assets in another repository.

## Design Goals

A future shared asset mode should:

- Keep project-local install as the default.
- Be explicit and opt-in, never automatic.
- Keep private endpoints, tokens, usernames, hostnames, and project paths out of committed files.
- Support dry-run output before writing anything.
- Back up any global config it changes.
- Validate every generated `file://` reference.
- Avoid duplicate rule warnings by default.
- Work for Windows, Linux, and macOS users without requiring PowerShell on Linux or macOS.
- Leave target repositories able to carry project-specific rules, evidence, and local validation outputs.

## Proposed Modes

### Project-Local Mode

Project-local mode is the current default. Use it when:

- You are installing the pack into one repository.
- You want every repository to carry its own inspectable `.continue` assets.
- You are new to Continue, local models, or tool-backed Agent workflows.
- You want the least surprising setup.

### Shared-Assets Mode

Shared-assets mode would be an advanced option. Use it when:

- You work across multiple repositories on the same machine.
- You want one centrally updated copy of prompts, rules, docs, templates, and agents.
- Your editor loads one global config file more reliably than project-local configs.
- You are comfortable with generated absolute file references.

## Suggested Shared Asset Locations

The exact default paths are still open, but the installer should support an explicit path such as `-SharedAssetsPath` or `--shared-assets-path`.

Reasonable defaults are:

- Windows: `%USERPROFILE%\.local-engineering-agent-pack\assets`
- Linux: `${XDG_DATA_HOME:-$HOME/.local/share}/local-engineering-agent-pack/assets`
- macOS: `$HOME/Library/Application Support/LocalEngineeringAgentPack/assets`

The installer should print the resolved path during dry-run and install.

## Config Generation Strategy

In shared-assets mode, generated editor config should use absolute references to the shared asset folder:

- Prompts point to the shared `prompts` folder.
- Docs point to the shared `templates` or documentation folder as needed.
- Agents point to the shared `agents` folder when the target surface supports them.
- Rules are omitted by default unless the user explicitly asks to include them.

The global Continue config must not contain project-relative references such as `file://./prompts/repository-discovery.md`. Those references only make sense from inside a project `.continue` folder and can make editors look for prompts under their install directory.

## Install Flow

A future implementation should follow this order:

1. Detect the pack source directory and target repository.
2. Resolve the shared asset path.
3. Run a dry-run preview unless the user explicitly requested install.
4. Copy reusable pack assets into the shared asset path.
5. Preserve or back up any existing shared asset folder before replacing it.
6. Generate global editor config with absolute references to the shared asset path.
7. Omit rules by default to avoid duplicate rule warnings.
8. Validate that every generated `file://` reference exists.
9. Print the next manual validation prompt for the editor surface.

## Validation Requirements

Shared-assets support should not be considered implemented until tests prove that:

- Project-local install still works unchanged.
- Shared asset install writes only to the chosen shared asset path and requested config file.
- Dry-run mode writes nothing.
- Backups are created before overwriting existing assets or config files.
- Global config references resolve to real files.
- Global config does not contain `file://./` references.
- Rules are omitted by default and included only by explicit opt-in.
- Windows, Linux, and macOS wrappers expose the same option names.
- Documentation explains rollback and duplicate-rule behavior.

## Security And Privacy

The shared asset folder should contain reusable pack assets only. It must not contain:

- API keys or tokens.
- Private model server URLs.
- Private repository names.
- User-specific validation outputs.
- Local-only Continue config files that include machine-specific settings.

Generated config files may contain local absolute paths because editors need them, but those files should be treated as local machine state unless explicitly sanitized.

## Rollback

Rollback should be simple:

1. Restore the previous global Continue config backup.
2. Remove or archive the shared asset folder.
3. Re-run the installer in project-local mode if needed.
4. Restart the editor and run the read-only tool validation prompt.

## Implementation Plan

1. Keep this design document and validation coverage in place.
2. Add installer flags for shared asset mode in PowerShell and Bash.
3. Add dry-run tests for Windows, Linux, and macOS wrappers.
4. Add generated global config validation for shared asset references.
5. Update README and wiki setup flows once the implementation exists.
6. Validate with a disposable sample repository before recommending it as a normal workflow.

## Open Questions

- Should the default shared asset path be user-level or configurable only?
- Should the installer create a minimal project marker in each target repository?
- Should shared assets support side-by-side pack versions?
- How should non-Continue agent surfaces consume the same shared asset folder?
