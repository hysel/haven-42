# Repository Context Fixture

## Purpose

Use this sanitized fixture to test repository discovery, architecture review, implementation planning, and code review workflows.

## Repository Summary

Name: `sample-order-service`
Type: ASP.NET Core service
Architecture: Clean Architecture
Primary Language: C#
Database: PostgreSQL
Messaging: Optional event publishing through an infrastructure adapter

## Directory Shape

```text
src/
  Api/
  Application/
  Domain/
  Infrastructure/
tests/
  UnitTests/
  IntegrationTests/
docs/
```

## Key Behaviors

- Accept customer orders through HTTP APIs.
- Validate order requests in the application layer.
- Enforce order invariants in the domain layer.
- Persist orders through infrastructure repositories.
- Publish order-created events after successful persistence.

## Known Concerns

- Some application services mix validation, orchestration, and persistence details.
- Logging needs review for sensitive identifiers.
- Integration tests cover happy paths but have limited failure-path coverage.
- Infrastructure adapters should not leak into domain code.

## Expected Discovery Output

- Identify Clean Architecture boundaries.
- Call out dependency direction risks.
- Separate confirmed facts from assumptions.
- Recommend tests around failure paths, logging safety, and adapter boundaries.
