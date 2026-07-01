---
name: Security
---

## Scope

Apply these standards to code, configuration, APIs, dependencies, and review output.

## Required Practices

- Treat all external input as untrusted.
- Validate, authorize, and encode at the correct boundaries.
- Enforce authentication and authorization explicitly.
- Use least privilege for identities, tokens, files, network access, and databases.
- Store secrets only in approved secret stores or environment-specific secure configuration.
- Avoid exposing sensitive data in logs, errors, telemetry, commits, or generated examples.
- Check dependency, deserialization, injection, path traversal, SSRF, CSRF, XSS, and authorization risks where relevant.
- Prefer secure defaults and fail-closed behavior.

## Avoid

- Hardcoded credentials.
- Client-controlled authorization decisions.
- Dynamic SQL or command execution without safe parameterization.
- Insecure temporary files.
- Overly broad exception messages returned to users.

## Review Checklist

- What is the trust boundary?
- Who is authorized to perform the action?
- What sensitive data is handled?
- What happens when validation or authorization fails?
