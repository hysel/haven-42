---
name: .NET Engineering
---

## Scope

Apply these standards to .NET application, library, and service code.

## Required Practices

- Prefer clear domain and application code over framework-heavy implementation.
- Use dependency injection for infrastructure dependencies.
- Keep public APIs intentional and stable.
- Use async APIs for I/O-bound operations.
- Pass `CancellationToken` through async call chains where appropriate.
- Prefer nullable reference type correctness over defensive noise.
- Keep exception handling purposeful; do not swallow exceptions silently.
- Use options binding and validation for configuration.
- Prefer structured logging over string-concatenated logs.
- Keep tests close to observable behavior.

## Avoid

- Static service locators.
- Hidden global state.
- Fire-and-forget tasks in request or service flows.
- Blocking on async code with `.Result` or `.Wait()`.
- Leaking persistence models into domain or API contracts by default.

## Review Checklist

- Are dependencies injected at the boundary?
- Are async and cancellation handled consistently?
- Are configuration, logging, and errors production-safe?
- Are tests covering meaningful behavior?
