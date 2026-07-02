# Legacy Dependency Migration Fixture

## Purpose

Use this sanitized fixture to test whether the legacy .NET dependency migration workflow produces a safe plan instead of a mechanical package-reference rewrite.

## Scenario

Repository type: Legacy .NET Framework desktop add-in project

Migration request:

Plan a safe migration from `packages.config` to `PackageReference` where appropriate.

Do not migrate the project to SDK-style unless explicitly requested.
Do not provide XML.
Do not provide direct edit instructions.

## Sanitized Project Signals

- Target framework: .NET Framework 4.8
- Project style: non-SDK-style project file
- Runtime host: desktop host process
- Package management: `packages.config`
- Package references: explicit assembly references with package-folder hint paths
- Build behavior: custom package imports and package-provided targets
- Packaging behavior: generated add-in artifact
- Runtime validation: add-in must load in the target desktop host
- Tests: no automated test evidence provided

## Migration-Sensitive Assets

- Package-provided `.props` files
- Package-provided `.targets` files
- Native dependency assets
- Explicit `HintPath` references
- Generated add-in package output
- Runtime host loading behavior
- Bootstrapper or installer behavior
- Restore behavior tied to package folder layout

## Expected Safe Output

The response should:

- Produce a plan only.
- Use the legacy dependency migration template structure.
- Start with current-state inventory.
- Distinguish package-management migration from SDK-style project migration.
- Classify packages/assets by migration risk.
- Require a branch-based spike or tool-supported migration path.
- Require restore, build, package output, generated artifact, and runtime loading validation.
- Include rollback.
- State that cleanup happens only after validation passes.

## Forbidden Output

The response must not:

- Include XML.
- Include a full or partial project-file rewrite.
- Include complete `PackageReference` blocks.
- Recommend deleting `packages.config` before validation.
- Recommend SDK-style conversion unless explicitly requested.
- Assume `dotnet restore` or `dotnet build` is correct without checking project-system support.
- Treat migration as a simple text replacement.
