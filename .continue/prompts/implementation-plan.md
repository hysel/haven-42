---
name: implementation-plan
description: Create a practical, risk-aware implementation plan for a requested change.
invokable: true
---

## Purpose

Act as a Principal Engineer and Technical Lead. Create an implementation plan only, without modifying files, writing code, or creating patches.

## Required Context

- User request
- Relevant project docs
- Affected files
- Existing patterns
- Known constraints
- Validation options

## Process

1. Restate the objective.
2. Identify impacted files and boundaries.
3. Identify dependencies, risks, and unknowns.
4. Identify existing project style and tooling constraints before recommending structural changes.
5. Split the work into small, reviewable steps.
6. Define validation steps.
7. Call out what will not be changed.

## Output Format

- Objective
- Assumptions
- Impacted Areas
- Proposed Steps
- Validation Plan
- Risks
- Out of Scope

## Quality Checks

- Prefer the smallest complete plan.
- Do not include unrelated refactors.
- Keep implementation order aligned with dependency direction.
- Preserve existing project style unless the requested change explicitly includes a project-system migration.
- Do not recommend renaming project files, changing SDK style, or changing package-management systems unless the plan explains why the toolchain supports it and how to roll back.
- For legacy .NET Framework, desktop, add-in, or build-target-heavy projects, identify package restore, custom targets, generated artifacts, installer/package output, and runtime loading risks before proposing migration steps.
- Mark unverified migration steps as assumptions and include a validation step that proves the assumption.
- Prefer tool-supported migration paths over manual project-file rewrites.
- Include rollback steps for project-system, dependency-management, or packaging changes.

## Legacy Project Migration Guardrails

When planning dependency, project-system, or package-management changes for legacy .NET Framework, desktop, add-in, or custom MSBuild projects:

- Do not provide a full rewritten project file unless explicitly requested.
- Do not convert a non-SDK-style project to SDK-style as an example unless the user explicitly requested SDK-style migration.
- Do not remove `packages.config`, `HintPath`, custom `Import`, bootstrapper, `.props`, `.targets`, `.dna`, installer, or packaging entries until the plan includes a validation step proving they are no longer required.
- Do not assume `dotnet restore` or `dotnet build` is the correct tool for non-SDK-style .NET Framework projects; call out when `msbuild`, Visual Studio restore, or NuGet restore may be required.
- Do not claim migration success from file edits alone. Require restore, build, package output, and runtime loading validation.
- Prefer a phased plan: inventory packages and custom targets, migrate one safe dependency or use the supported Visual Studio migration path, build, validate add-in packaging/runtime loading, then continue.
- If the context is incomplete, say what must be checked instead of filling gaps with a generic recipe.
- Do not provide a simple "remove packages.config and add PackageReference nodes" recipe for custom MSBuild or add-in projects. First require an inventory of package-provided build imports, custom targets, hint paths, generated files, and packaging behavior.
- Do not recommend deleting `packages.config` until restore, build, packaging, runtime loading, and rollback have been validated in a branch.
- If package references include packages with build assets, native assets, analyzers, or custom targets, call those out as migration blockers or validation points.
