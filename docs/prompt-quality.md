# Prompt Quality

## Purpose

This document defines prompt-quality expectations for high-risk workflows in the Continue Enterprise Engineering Pack.

Use it when validating prompt changes, local-model behavior, examples, and fixtures.

## General Expectations

Prompt output should:

- Separate confirmed evidence from assumptions.
- Ask for missing information instead of inventing details.
- Prefer plans and recommendations that preserve existing project constraints.
- Avoid generic advice when repository context indicates a specialized workflow.
- Include validation and rollback for risky changes.
- Avoid leaking private paths, endpoints, secrets, customer names, or raw proprietary code into committed docs.

## Legacy Dependency Migration

Fixture:

- `examples/fixtures/legacy-dependency-migration-input.md`

Prompt:

- `.continue/prompts/legacy-dotnet-dependency-migration.md`

Template:

- `.continue/templates/LegacyDotNetDependencyMigration.md`

### Pass Criteria

The response passes when it:

- Uses the legacy dependency migration template structure.
- Produces a plan only.
- Starts with inventory and current-state evidence.
- Separates package-management migration from SDK-style project migration.
- Identifies custom build, packaging, native asset, and runtime loading risks.
- Requires restore, build, generated artifact, package output, and runtime loading validation.
- Includes rollback.
- Defers cleanup until validation passes.

### Fail Criteria

The response fails when it:

- Includes XML.
- Includes full or partial project-file rewrites.
- Provides complete `PackageReference` blocks.
- Recommends deleting `packages.config` before validation.
- Recommends SDK-style conversion without explicit user request.
- Assumes `dotnet restore` or `dotnet build` is correct without checking project-system support.
- Treats migration as a simple text replacement.
- Omits rollback.

## Documentation Review

Fixture:

- `examples/fixtures/documentation-review-quality-input.md`

Prompt:

- `.continue/prompts/documentation.md`

The response should identify missing or weak documentation, not only summarize existing files.

Pass criteria:

- Identifies setup, architecture, operations, troubleshooting, support, and release documentation gaps.
- Separates existing documentation from missing documentation.
- Prioritizes documentation fixes by user impact.
- Identifies security, data-handling, API-example, rollback, and observability documentation gaps when present in the fixture.
- Recommends concrete documentation additions instead of broad code changes.

Fail criteria:

- Only summarizes project configuration.
- Claims documentation is sufficient without evidence.
- Omits onboarding or support risks.
- Treats file presence as documentation quality.
- Ignores release validation, rollback, operations, or security documentation gaps.

## Release Readiness

Fixture:

- `examples/fixtures/release-readiness-quality-input.md`

Prompt:

- `.continue/prompts/release-readiness.md`

The response should require evidence before recommending release.

Pass criteria:

- Requires build, test, package, install, rollback, and known-risk evidence.
- Distinguishes internal validation readiness from production release readiness.
- Produces a go, conditional go, or no-go recommendation tied to evidence.
- Recommends no-go when production release evidence is missing for customer-data or authorization-sensitive changes.
- Separates blockers from follow-up work.

Fail criteria:

- Recommends go without build/test/package/runtime evidence.
- Treats configuration presence as release readiness.
- Omits rollback or operational validation.
- Treats local smoke testing as sufficient for production release.
- Omits customer-data or authorization risk when the fixture includes it.

## Implementation Planning

Fixture:

- `examples/fixtures/implementation-planning-quality-input.md`

Prompt:

- `.continue/prompts/implementation-plan.md`

The response should produce a practical, risk-aware plan without slipping into implementation.

Pass criteria:

- Uses the requested implementation-plan section structure.
- Identifies affected files and boundaries.
- Calls out missing information when exact files, technologies, or policies are unknown.
- Lists risks, assumptions, validation, rollback, and out-of-scope work.
- Preserves existing project style unless migration is explicitly requested.
- Waits for approval before implementation when the request requires planning only.

Fail criteria:

- Provides direct edit instructions when asked for a plan.
- Includes large code or XML blocks without request.
- Invents exact file paths, technologies, or policies without evidence.
- Collapses layering by putting infrastructure behavior into API/controller logic.
- Recommends unrelated refactors.
- Omits validation for risky changes.
- Omits rollback or definition of done.
