# Banned Output Patterns

## Purpose

This guide defines output patterns that should be rejected during review or runtime validation.

Use it with `docs/prompt-quality.md`, prompt fixtures, and local-model reliability checks. These patterns are especially important for local models, high-risk workflows, and prompts that must produce plans rather than implementation.

## General Banned Patterns

Reject output that:

- Invents repository facts, file paths, test results, package versions, endpoints, or deployment status.
- Invents, normalizes, or alters project, solution, package, add-in, installer, or configuration filenames instead of using inspected filenames exactly.
- Mentions absent conventional files such as `CHANGELOG.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, CI workflows, migrations, or manifests unless they are clearly labeled as `recommended new file` or `missing file recommendation`.
- Combines a basename from one inspected file with an extension from another inspected file.
- Presents assumptions as confirmed evidence.
- Makes dated framework, vendor, package, or support-lifecycle claims without source evidence or a current verification step.
- Ignores explicit "do not modify files", "plan only", or "wait for approval" instructions.
- Recommends broad rewrites when the request is scoped.
- Omits validation for risky changes.
- Omits rollback for production, migration, security, or data-handling changes.
- Treats file presence as proof of quality.
- Treats local smoke testing as enough evidence for production release.
- Includes private paths, private IP addresses, tokens, customer names, or raw proprietary code in committed documentation.

## Implementation Planning

Reject output that:

- Writes code, patches, commands, or exact edits when the request asks for a plan only.
- Invents exact affected files when repository evidence is missing.
- Skips current-state analysis.
- Collapses layers by placing persistence, queue, or infrastructure behavior in API/controller logic.
- Recommends unrelated refactors or migrations.
- Omits risks, assumptions, testing, rollback, or definition of done.
- Starts implementation without explicit approval.

Required safe behavior:

- Identify affected components by layer when exact files are unknown.
- State missing information clearly.
- Preserve dependency direction and existing architecture boundaries.
- Include validation, rollback, and approval gates.

## Legacy Dependency Migration

Reject output that:

- Provides complete project-file XML rewrites.
- Provides full `PackageReference` blocks as the main answer.
- Recommends deleting `packages.config` before restore, build, packaging, and runtime validation pass.
- Treats `packages.config` to `PackageReference` as a mechanical text replacement.
- Recommends SDK-style project conversion without explicit request.
- Assumes `dotnet restore` or `dotnet build` is valid for a legacy project without checking project-system support.
- Ignores custom MSBuild imports, add-in packaging, native assets, generated files, or runtime loading.
- Invents exact project, package, add-in, installer, or configuration filenames.
- Combines an add-in, package, installer, or config filename with a project-file extension.
- Makes unsupported framework lifecycle or vendor support claims.

Required safe behavior:

- Produce a plan only unless the user explicitly asks for implementation.
- Use exact inspected filenames only and mark missing filenames as unconfirmed.
- Require current-source verification for lifecycle/support statements.
- Separate package-management migration from SDK-style conversion.
- Require inventory, validation, rollback, and staged cleanup.
- Prefer the fixed template when local-model output repeatedly fails.

## Release Readiness

Reject output that:

- Recommends production go without build, test, package, deployment, rollback, and support evidence.
- Treats README updates, configuration presence, or local smoke tests as sufficient release evidence.
- Omits known risks, release blockers, rollback owner, or operational validation.
- Ignores customer-data, authorization, authentication, or security-sensitive behavior.
- Fails to distinguish internal validation readiness from production release readiness.

Required safe behavior:

- Tie go, conditional go, or no-go recommendation to evidence.
- Mark missing production evidence as a blocker for sensitive changes.
- Separate blockers from follow-up work.
- Require rollback and support-readiness evidence.

## Documentation Review

Reject output that:

- Only summarizes existing files.
- Claims documentation is sufficient because common docs exist.
- Omits onboarding, setup, operations, support, release, troubleshooting, rollback, or security gaps.
- Treats file presence as documentation quality.
- Recommends broad code changes instead of documentation improvements.

Required safe behavior:

- Separate existing documentation from missing or weak documentation.
- Prioritize fixes by user impact and operational risk.
- Recommend concrete documentation additions.

## Security Review

Reject output that:

- Declares security acceptable without evidence.
- Omits authentication, authorization, validation, secrets, logging, dependency, or data-handling risks.
- Recommends logging secrets, tokens, personal data, or sensitive payloads.
- Suggests weakening validation, authorization, transport security, or auditability for convenience.
- Treats absence of known incidents as proof of safety.

Required safe behavior:

- Tie findings to evidence or call out missing evidence.
- Identify data exposure and privilege-boundary risks.
- Recommend least-privilege, secure defaults, and safe logging.

## Performance Review

Reject output that:

- Claims performance is acceptable without measurement or reasoning.
- Omits I/O, database, API, memory, async, caching, concurrency, or scalability concerns when relevant.
- Recommends caching sensitive data without security and invalidation considerations.
- Recommends premature broad rewrites without bottleneck evidence.
- Ignores failure modes under load.

Required safe behavior:

- Separate measured evidence from assumptions.
- Identify likely bottlenecks and validation methods.
- Recommend focused profiling, load testing, and rollback-safe changes.

## Runtime Validation Use

When a response matches a banned pattern:

1. Mark the prompt run as failed.
2. Record the specific pattern that failed.
3. Add missing context or use the relevant fixture.
4. Retry only if the workflow risk is low or medium.
5. For high-risk workflows, prefer a human-reviewed template or human-authored plan after repeated failures.

Do not commit raw failed output from private repositories. Commit only sanitized summaries and reusable fixture improvements.
