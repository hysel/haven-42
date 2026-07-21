# Project

## Name

Local Engineering Agent Pack

## Purpose

This repository defines a local-first engineering agent pack for developers, small teams, consultants, and enterprise engineering groups that want repeatable AI-assisted workflows and consistent guidance for .NET, ASP.NET Core, APIs, Clean Architecture, security, performance, testing, and documentation.

The pack is intended to turn common senior engineering activities into version-controlled prompts, rules, agents, and templates that can be reviewed, improved, and reused across repositories.

Continue is the first supported runtime surface, but the project identity is broader than Continue. The reusable assets should remain portable enough to evaluate with other open-source coding agents as they become useful.

## Current Stage

The project is in active implementation. Continue is the supported first
surface, while Aider and OpenCode are the fully maintained non-Continue
install/configure/test adapters. Broader surface parity is evidence-gated.

Capability Evidence Contract v2 now prevents model readiness from being
inherited across surfaces, operating systems, or operations. Deterministic
project classification and project-local language-rule activation are
implemented. Lane-specific model scoring now keeps WRITE SAFE
reliability-first while allowing larger validated PLAN ONLY and DEEP REVIEW
models when hardware permits. Model-backed language promotion, richer
runtime-measured model metadata, additional script-family consolidation, and
the optional web UI remain planned work. The onboarding/navigation family now
shares catalog, command-rendering, output, and native-dispatch plumbing while
preserving stable public commands. A schema-v1 workflow envelope now gives
dispatchers and future UI callers a stable, privacy-conscious JSON boundary.

## Target Users

- Individual developers improving personal or client repositories
- Small teams that want consistent review and planning without heavyweight process
- Senior engineers working in enterprise .NET repositories
- Architects reviewing service boundaries and dependency direction
- Security engineers reviewing API and application risks
- Performance engineers investigating reliability and throughput concerns
- Product and delivery leads who need structured implementation plans
- Teams using Continue or another validated local-first agent surface with local or self-hosted model infrastructure

## Goals

- Provide a usable local-first agent pack for practical engineering workflows.
- Favor local-first operation through Continue, Ollama, and future validated local agent surfaces.
- Make AI-assisted reviews repeatable and auditable.
- Encode practical .NET, ASP.NET Core, Clean Architecture, API, security, testing, logging, performance, and Git guidance.
- Keep role-specific behavior explicit through agents.
- Keep task-specific behavior explicit through prompts.
- Keep reusable standards explicit through rules.
- Provide templates for durable engineering artifacts.

## Non-Goals

- Replacing human engineering review or approval.
- Providing a complete application framework.
- Supporting every language ecosystem equally in the initial release.
- Depending on cloud-hosted LLMs as the default path.
- Encoding organization-specific secrets, policies, or private infrastructure details.

## Product Principles

- Local-first by default.
- Beginner-friendly defaults with enterprise-safe language and workflows where needed.
- Clear separation between agents, prompts, rules, and templates.
- Practical guidance over abstract theory.
- Explicit limitations instead of inflated capability claims.
- Human review remains mandatory for AI-generated recommendations.

## Success Criteria

Milestone 1 is successful when:

- `.continue/config.yaml` can be loaded by Continue.
- Core prompts are available for repository discovery, implementation planning, code review, bug investigation, security review, architecture review, performance review, and documentation.
- Core rules guide .NET, ASP.NET Core, APIs, Clean Architecture, testing, logging, security, performance, SonarQube, and Git work.
- Agents are defined for senior engineering, architecture, security, review, performance, documentation, and product management.
- Templates exist for architecture notes, security reviews, performance reviews, and AI project guidance.
- README usage instructions match validated behavior.
