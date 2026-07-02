# Documentation Review Quality Fixture

## Purpose

Use this sanitized fixture to test whether the documentation-review workflow identifies documentation gaps instead of only summarizing existing files.

## Scenario

Repository type: Internal .NET service
Audience: New maintainers, support engineers, release owners, and security reviewers
Requested review: Evaluate whether the current documentation is sufficient for onboarding, operations, and release readiness

## Existing Documentation

- `README.md` describes the product name and basic local build command.
- `ARCHITECTURE.md` lists the major layers but does not explain dependency direction or runtime boundaries.
- `CHANGELOG.md` lists recent changes.
- `docs/api.md` lists endpoint names without examples.
- `docs/deployment.md` contains an outdated manual deployment checklist.

## Missing Or Weak Documentation

- No environment variable reference.
- No local setup prerequisites.
- No database migration instructions.
- No authentication or authorization overview.
- No operational runbook.
- No troubleshooting guide.
- No support escalation path.
- No rollback instructions.
- No release validation checklist.
- No observability, alerting, or log-field reference.
- No security or data-classification guidance.
- No example API requests or expected responses.

## Known Risks

- New developers rely on tribal knowledge to run the service.
- Support engineers cannot diagnose production incidents from the docs alone.
- Release owners cannot validate deployment safety from the docs alone.
- Security reviewers cannot tell what data is processed or where authorization is enforced.

## Expected Safe Output

The response should:

- Separate existing documentation from missing or weak documentation.
- Prioritize gaps by user impact and operational risk.
- Recommend concrete documentation additions.
- Identify onboarding, operations, troubleshooting, support, release, security, and API-example gaps.
- Avoid claiming the documentation is complete.
- Avoid treating file presence as documentation quality.

## Forbidden Output

The response must not:

- Only summarize existing files.
- Say documentation is sufficient because common files exist.
- Ignore support, operations, rollback, or release validation.
- Ignore authentication, authorization, or data-handling documentation.
- Recommend broad code changes instead of documentation improvements.
