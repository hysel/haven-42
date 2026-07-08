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

1. Run project classification before stack-specific advice:
   - identify primary ecosystem, framework/runtime, build/dependency system, and test system
   - cite evidence files used
   - mark missing or uncertain signals as `unconfirmed`
   - do not apply .NET, frontend, Python, Java, Go, Rust, SQL, or IaC-specific guidance without matching evidence
2. Restate the objective.
3. Identify impacted files and boundaries.
4. Identify dependencies, risks, and unknowns.
5. Identify existing project style and tooling constraints before recommending structural changes.
6. Split the work into small, reviewable steps.
7. Define validation steps.
8. Call out what will not be changed.

## Filename Fidelity Gate

- Treat the inspected repository context as the only source of truth for existing filenames.
- Use exact filenames only when they appear in inspected files, tool output, or supplied context.
- Do not invent, normalize, or substitute conventional filenames such as `CHANGELOG.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, CI workflow names, migration names, Kubernetes manifests, or `.continue/config.yaml`.
- Do not assume this engineering pack's own files, rules, prompts, docs, `.continue/config.yaml`, or workflow names exist in the repository being reviewed.
- If a useful file is missing, label it as `recommended new file: <path>` or `missing file recommendation: <path>` instead of describing it as an existing file.
- If a filename is uncertain, write `unconfirmed filename` and describe the evidence needed before naming the file exactly.
## Output Format

- Objective
- Assumptions
- Impacted Areas
- Proposed Steps
- Validation Plan
- Risks
- Out of Scope

## Project Detection Reference

Use `docs/project-detection.md` for evidence strength, ecosystem signals, confidence labels, and language-specific guardrails.

Use docs/language-rule-packs.md only after project classification confirms Python or JavaScript/TypeScript evidence. Optional rule packs are supplemental and are not globally active by default.

## Quality Checks

- Do not apply language-specific recommendations unless inspected files or supplied context provide matching evidence.
- Prefer `unconfirmed` over framework or toolchain guesses when project metadata is missing.

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
