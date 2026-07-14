---
name: API Design
---

## Scope

Apply these standards to HTTP APIs, service contracts, and integration boundaries.

## Required Practices

- Design APIs around explicit resources, commands, queries, or use cases.
- Keep request and response contracts stable and versionable.
- Validate all input at the boundary.
- Return consistent success and error shapes.
- Avoid leaking internal identifiers or implementation details unless intentional.
- Use idempotency for retryable write operations where needed.
- Consider pagination, filtering, sorting, and rate limits for collection endpoints.
- Document authentication and authorization expectations.

## Avoid

- Ambiguous endpoint names.
- Overloaded endpoints that perform unrelated operations.
- Returning database entities directly.
- Breaking contract changes without a migration path.

## Review Checklist

- Is the contract clear to a client?
- Are errors predictable?
- Can the endpoint evolve without breaking consumers unnecessarily?

## Evidence Gate

Apply this rule only when inspected files or supplied context confirm an HTTP API, RPC/service contract, message contract, webhook, or external integration boundary. Do not infer an API from repository naming alone.

If an API or integration boundary is absent or unreadable, do not recommend endpoints, pagination, rate limits, authentication schemes, or contract versioning; label those concerns as `unconfirmed` or not applicable.
