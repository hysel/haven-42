---
name: ASP.NET Core Standards
globs: ["**/Program.cs", "**/Startup.cs", "**/appsettings*.json", "**/*Controller.cs", "**/*Endpoint.cs"]
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

## Evidence Gate

Apply this rule only when inspected files or supplied context confirm an ASP.NET Core web surface, such as ASP.NET SDK/framework references, `Program.cs` web-host setup, `Startup.cs`, controllers, endpoints, middleware, or matching web configuration.

If ASP.NET Core evidence is absent or unreadable, do not apply web-host, controller, endpoint, middleware, or ASP.NET service-lifetime recommendations; label those assumptions as `unconfirmed`.
