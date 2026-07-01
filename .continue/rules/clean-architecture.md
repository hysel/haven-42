---
name: Clean Architecture
---

## Scope

Apply these standards when reviewing architecture, layering, and dependency direction.

## Required Practices

- Keep domain rules independent of frameworks, databases, queues, HTTP, and UI.
- Put use-case orchestration in an application layer.
- Put infrastructure implementation behind interfaces owned by inner layers when inversion is needed.
- Keep dependency direction pointing inward toward domain and application policies.
- Use DTOs at boundaries to avoid leaking transport or persistence concerns.
- Prefer explicit ports and adapters for external systems.
- Keep cross-cutting concerns observable and testable.

## Avoid

- Domain objects depending on EF Core, ASP.NET Core, message brokers, or HTTP clients.
- Application services directly constructing infrastructure clients.
- Persistence models becoming the default domain model without intent.
- Circular references between layers.
- Layering that exists only as ceremony.

## Review Checklist

- Which layer owns the business rule?
- Do dependencies point inward?
- Can the use case be tested without real infrastructure?
- Are external systems isolated behind a boundary?
