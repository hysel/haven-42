---
name: Logging And Observability
---

## Scope

Apply these standards to logging, metrics, tracing, and operational diagnostics.

## Required Practices

- Use structured logging with stable property names.
- Log at levels that match operational severity.
- Include correlation identifiers when available.
- Avoid logging secrets, tokens, credentials, personal data, or full request payloads by default.
- Emit enough context to diagnose failures without exposing sensitive data.
- Prefer metrics for rates, counts, latency, and saturation.
- Prefer traces for cross-service workflows.

## Avoid

- String-concatenated logs that lose structure.
- Catch-and-log-only exception handling.
- Logging noisy success paths at warning or error levels.
- Sensitive data in logs.

## Review Checklist

- Would the log help diagnose a production issue?
- Is sensitive data protected?
- Are metrics or traces more appropriate than logs?
