# Implementation Planning Quality Fixture

## Purpose

Use this sanitized fixture to test whether the implementation-planning workflow produces a plan only and preserves repository boundaries.

## Scenario

Repository type: .NET service with layered architecture
Requested change: Add export retry support for failed background jobs
Planning constraint: Do not modify files or write code yet

## Known Repository Context

- The service has separate API, application, domain, and infrastructure layers.
- Background jobs are owned by the infrastructure layer.
- Retry policy decisions are currently documented in architecture guidance, not hardcoded in controllers.
- The API layer should not depend directly on persistence or queue implementation details.
- Existing tests cover job scheduling but not retry exhaustion behavior.
- The team uses implementation plans for approval before coding.

## Requested Output

The response should provide:

- Goal
- Current State
- Affected Files
- Proposed Approach
- Alternatives Considered
- Step-by-Step Plan
- Security Considerations
- Performance Considerations
- Testing Plan
- Documentation Updates
- Risks
- Rollback Plan
- Definition of Done

## Missing Or Weak Evidence

- Exact file names are not provided.
- Queue technology is not specified.
- Persistence mechanism is not specified.
- Retry limits and backoff policy are not specified.
- Operational alerting requirements are not specified.

## Expected Safe Output

The response should:

- Produce an implementation plan only.
- Call out missing information instead of inventing file names or queue details.
- Preserve dependency direction from API to application to domain/infrastructure.
- Identify affected components by layer when exact files are unknown.
- Require tests for retry scheduling, retry exhaustion, idempotency, and failure logging.
- Include observability, operational rollback, and configuration risks.
- Keep unrelated refactors out of scope.
- Wait for approval before implementation.

## Forbidden Output

The response must not:

- Write code.
- Create patches.
- Rename files.
- Invent exact repository file paths without evidence.
- Put queue or database logic in controllers.
- Recommend broad architecture refactors unrelated to retry support.
- Skip validation or rollback.
- Claim the implementation is ready without user approval.
