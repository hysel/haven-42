# Legacy .NET Dependency Migration Plan

## Goal

Plan a safe dependency-management migration for a legacy .NET project.

Do not perform edits in this document.

## Migration Scope

- Package-management migration:
- Project-system migration:
- Runtime or packaging migration:

## Current-State Evidence

- Project style:
- Target framework:
- Package management:
- Restore/build tooling:
- Custom build assets:
- Packaging/runtime loading behavior:
- Tests or validation assets:

## Migration-Sensitive Assets

List assets that must be preserved or explicitly replaced:

- Package build assets:
- Native assets:
- Analyzer assets:
- `HintPath` references:
- `.props` and `.targets` imports:
- Generated artifacts:
- Installer/bootstrapper behavior:
- Add-in, plugin, or runtime loading behavior:

## Package Risk Classification

Use this table. Do not include XML.

| Package or Asset | Classification | Reason | Validation Needed |
| --- | --- | --- | --- |
| Unknown | Needs inventory | Evidence not collected yet | Inspect package assets and build behavior. |

Classifications:

- Likely safe to evaluate
- Requires package-specific validation
- Blocked until tool support is confirmed
- Should remain unchanged

## Proposed Phased Plan

1. Create a branch and capture baseline restore, build, package, and runtime-loading behavior.
2. Inventory package assets, custom targets, native assets, generated files, and packaging behavior.
3. Decide whether the migration is package-management only or also project-system migration.
4. Run a small migration spike or a tool-supported migration path.
5. Validate restore behavior.
6. Validate build behavior.
7. Validate generated artifacts and package output.
8. Validate runtime loading in the target host.
9. Clean up legacy files only after validation passes.
10. Document remaining risks and accepted deferrals.

## Validation Plan

- Restore validation:
- Build validation:
- Package/artifact validation:
- Runtime loading validation:
- Regression testing:
- Manual smoke testing:

## Rollback Plan

- Revert migration branch or commit.
- Restore original package-management files.
- Restore original project-file references and imports.
- Restore prior package restore behavior.
- Rebuild and confirm runtime loading returns to baseline.

## Out Of Scope

- SDK-style conversion unless explicitly requested.
- Full project-file rewrite unless explicitly requested.
- Package version upgrades unless explicitly requested.
- Runtime architecture changes.

## Open Questions

- Which packages provide build assets, native assets, analyzers, or custom targets?
- Which restore/build tool is the supported baseline?
- What generated artifacts must remain byte-for-byte or behaviorally equivalent?
- How is runtime loading validated in the target host?
