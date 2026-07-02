---
name: legacy-dotnet-dependency-migration
description: Plan safe dependency-management migration for legacy .NET Framework, desktop, add-in, or custom MSBuild projects.
invokable: true
---

## Purpose

Create a safe migration plan for legacy .NET dependency-management changes, especially `packages.config` to `PackageReference`, without changing project-system style unless explicitly requested.

Use this workflow for .NET Framework, desktop, Excel-DNA, Office add-in, installer, custom MSBuild, or package-target-heavy projects.

## Required Context

- User request
- Current project file style
- `packages.config`
- Existing package references, `HintPath` entries, and package versions
- Custom `Import`, `.props`, `.targets`, `.dna`, installer, bootstrapper, packaging, or generated artifact configuration
- Build and restore commands currently used
- Runtime loading or packaging validation requirements
- Test and rollback options

## Non-Negotiable Guardrails

- Do not provide a full rewritten project file unless the user explicitly asks for one.
- Do not provide a full `<PackageReference>` replacement block unless the user explicitly asks for generated XML.
- Do not recommend SDK-style conversion unless the user explicitly asks for SDK-style migration.
- Do not treat `packages.config` to `PackageReference` migration as a simple text replacement.
- Do not recommend deleting `packages.config` until restore, build, package output, runtime loading, and rollback have been validated.
- Do not assume `dotnet restore` or `dotnet build` is correct for non-SDK-style .NET Framework projects.
- Do not remove or rewrite custom package `Import`, `.props`, `.targets`, `HintPath`, native asset, analyzer, `.dna`, bootstrapper, installer, or packaging behavior without identifying the replacement behavior.
- If evidence is missing, call it out and make the first step an inventory or spike.
- If asked for a plan, produce a plan only. Do not provide edit-ready XML, project-file patches, or mechanical replacement instructions.

## Forbidden Response Patterns

For this workflow, avoid these patterns unless the user explicitly requests implementation details:

- "Replace the entire ItemGroup with..."
- "Remove packages.config, then add these PackageReference nodes..."
- A complete list of package references as XML.
- A full or partial rewritten `.csproj`.
- A statement that PackageReference is recommended for all modern .NET projects without qualifying legacy .NET Framework/custom MSBuild risk.
- A migration plan that starts with editing before inventorying package build assets and custom targets.

If the requested migration is risky, the correct response is a phased validation plan, not a direct edit recipe.

## Process

1. Restate the migration goal and confirm whether this is package-management migration only or project-system migration too.
2. Classify the project style:
   - SDK-style or non-SDK-style
   - .NET Framework or modern .NET
   - desktop/add-in/service/library
   - custom MSBuild or packaging targets
3. Inventory migration-sensitive assets:
   - package build assets
   - native assets
   - analyzers
   - `HintPath` references
   - `.props` and `.targets`
   - generated artifacts
   - installer, bootstrapper, `.dna`, `.xll`, or packaging output
4. Separate packages into:
   - likely safe to migrate
   - requires package-specific validation
   - should remain unchanged until tool support is confirmed
5. Propose a phased migration:
   - branch and baseline
   - inventory
   - tool-supported migration or one-package spike
   - restore validation
   - build validation
   - package/artifact validation
   - runtime loading validation
   - cleanup only after validation
6. Define rollback:
   - revert commit
   - restore original project/package files
   - restore package folder behavior if needed
   - revalidate build and runtime loading
7. State what not to change.

## Output Format

Use the `LegacyDotNetDependencyMigration` template structure.

Do not add sections outside that template unless the user explicitly asks.
Do not include XML.
Do not include replacement snippets.
Do not include direct edit instructions.

## Minimum Acceptable Plan

The plan must include these phases:

1. Baseline current restore, build, package, and runtime loading behavior.
2. Inventory packages and identify build/native/analyzer/custom-target assets.
3. Decide whether PackageReference migration is supported without SDK-style conversion.
4. Run a small spike or use a tool-supported migration path.
5. Validate restore, build, package output, generated artifacts, and runtime loading.
6. Clean up only after validation.
7. Roll back by reverting migration changes and restoring the prior package restore behavior.

## Quality Checks

- Preserve project style unless a project-system migration is explicitly requested.
- Keep `PackageReference` migration separate from SDK-style conversion.
- Require validation before cleanup.
- Identify custom build and packaging risks before editing package references.
- Prefer a small spike over whole-project migration when package build assets or custom targets exist.
- Avoid generic NuGet migration recipes.
