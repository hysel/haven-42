---
name: Testing
---

## Scope

Apply these standards to unit, integration, contract, and end-to-end testing.

## Required Practices

- Test observable behavior rather than implementation trivia.
- Keep unit tests fast and deterministic.
- Use integration tests for persistence, messaging, HTTP, and framework behavior.
- Include negative, edge, and authorization cases when risk warrants them.
- Make test names describe behavior.
- Avoid shared mutable state between tests.
- Use realistic fixtures without hiding important setup.
- Run the relevant test subset after changes when possible.

## Avoid

- Tests that only assert mocks were called unless interaction is the behavior.
- Brittle snapshots for frequently changing content.
- Tests that depend on execution order.
- Disabling flaky tests without tracking the reason.

## Review Checklist

- Does the test fail for the bug or behavior it protects?
- Is the right test level being used?
- Are important edge cases covered?
