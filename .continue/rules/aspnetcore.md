---
name: ASP.NET Core Standards
---

## Scope

Apply these standards to ASP.NET Core APIs and services.

## Required Practices

- Keep endpoints thin and delegate business work to application services or handlers.
- Validate request models at the boundary.
- Return consistent error responses.
- Use appropriate HTTP status codes.
- Protect endpoints with explicit authorization where required.
- Keep middleware ordering intentional.
- Use health checks for externally operated services.
- Prefer typed clients and resilient outbound HTTP patterns.
- Keep OpenAPI metadata accurate when APIs are documented.

## Avoid

- Business logic embedded directly in controllers or route handlers.
- Returning raw exceptions to clients.
- Trusting client-supplied identity, tenant, or authorization data.
- Using service lifetime scopes incorrectly.

## Review Checklist

- Is the API boundary thin and explicit?
- Are validation, authorization, and errors handled consistently?
- Are service lifetimes and middleware order safe?
