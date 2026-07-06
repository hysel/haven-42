# Language Support

## Purpose

This document tracks how the Local Engineering Agent Pack should grow beyond its current .NET-centered guidance.

.NET, ASP.NET Core, APIs, and Clean Architecture remain the most mature and most validated path today. Multi-language support is a planned direction, not a claim that every ecosystem is already equally supported.

## Current Position

| Ecosystem | Current status | Notes |
| --- | --- | --- |
| .NET / ASP.NET Core | Most mature | Existing rules, prompts, examples, and validation are strongest here. |
| Python | Optional rule pack added; static generated-sample validation recorded | Needs implementation-planning, code-review, and editor/model validation before promotion. |
| JavaScript / TypeScript | Optional rule pack added; static generated-sample validation recorded | Needs implementation-planning, code-review, and editor/model validation before promotion. |
| Java / Spring | Planned | Needs build-tool and framework-specific review guidance. |
| Go | Planned | Needs module, concurrency, API, and deployment guidance. |
| Rust | Planned | Needs cargo, ownership, error-handling, and performance guidance. |
| SQL / database projects | Planned | Needs schema, migration, query, and data-safety guidance. |
| Infrastructure as Code | Planned | Terraform, Docker, Kubernetes, and GitHub Actions need separate safety rules. |

## Project Detection

Use `docs/project-detection.md` as the source of truth for ecosystem signals, evidence strength, confidence labels, and unconfirmed assumptions. Language-specific guidance should not be applied until project detection has enough repository evidence.

## Shared Guidance

These standards should remain cross-language:

- Repository discovery before recommendations.
- Exact filename fidelity.
- Security review and secrets handling.
- Testability and rollback planning.
- Logging and observability expectations.
- Performance and scalability checks.
- Git hygiene and change isolation.
- Documentation updates with behavior changes.

## Language-Specific Guidance

Language-specific rules should be added only when they are useful and validated. Optional Python and TypeScript rule packs now live in `.continue/rule-packs/` and are documented in `docs/language-rule-packs.md`. Static generated-sample validation evidence is recorded in `examples/language-rule-pack-validation.md`. They are not loaded by default from `.continue/config.yaml`.

Each language pack should define:

- Project detection signals.
- Common build and test commands.
- Dependency management expectations.
- Security-sensitive patterns.
- Testing conventions.
- Performance and reliability risks.
- Documentation expectations.
- Sample repositories or fixtures for validation.

## Guardrails

- Do not apply .NET-specific advice to non-.NET repositories.
- Do not guess the language or framework from a single file when repository evidence is incomplete.
- Do not recommend framework-specific commands until the relevant project files are inspected.
- Treat generated sample repositories as validation fixtures, not proof of production readiness.
- Keep language-specific guidance optional until it has validation evidence.

## Recommended First Expansion

Start with Python and JavaScript/TypeScript because they cover common personal, small-team, and open-source project shapes.

Suggested sequence:

1. Add generated local sample repositories for Python and TypeScript.
2. Add project-detection rules for each ecosystem.
3. Add language-specific review notes without changing default behavior.
4. Validate repository discovery, implementation planning, and code review against each sample.
5. Record sanitized evidence.
6. Promote language guidance only after the validation output is grounded and useful.
