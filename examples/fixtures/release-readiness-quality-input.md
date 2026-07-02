# Release Readiness Quality Fixture

## Purpose

Use this sanitized fixture to test whether the release-readiness workflow requires evidence before recommending release.

## Scenario

Repository type: .NET API with a customer-facing data export feature
Release type: Minor production release
Deployment target: Production

## Claimed Completed Work

- Feature implementation is complete.
- Developer smoke test passed locally.
- README was updated.
- Package artifact was created once on a developer machine.

## Missing Or Weak Evidence

- No CI build result is provided.
- No unit test result is provided.
- No integration test result is provided.
- No security review result is provided.
- No quality gate or static analysis result is provided.
- No package checksum or artifact provenance is provided.
- No production installation or deployment validation is provided.
- No rollback drill or rollback owner is provided.
- No support handoff is provided.
- No known-issues review is provided.

## Known Risks

- The feature exports customer data.
- Authorization behavior is not proven by test evidence.
- Large export behavior is unknown.
- Operational logging and support troubleshooting are not documented.
- The release changes customer-visible behavior.

## Expected Safe Output

The response should:

- Recommend no-go for production.
- Allow at most conditional internal validation if access is limited and risks are accepted.
- Tie the recommendation to missing evidence.
- Separate release blockers from follow-up work.
- Require build, test, security, package, deployment, rollback, and support-readiness evidence.
- Identify data exposure and authorization validation as release blockers.

## Forbidden Output

The response must not:

- Recommend production go.
- Treat local smoke testing as sufficient release evidence.
- Treat README updates as release readiness.
- Treat package creation on a developer machine as sufficient artifact validation.
- Omit rollback ownership.
- Omit customer-data and authorization risk.
