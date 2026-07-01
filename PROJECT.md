# Project

## Name

Continue Enterprise Engineering Pack

## Purpose

This repository defines an enterprise-focused Continue configuration pack for software engineering teams that want local-first AI assistance, repeatable engineering workflows, and consistent guidance for .NET, ASP.NET Core, APIs, Clean Architecture, security, performance, testing, and documentation.

The pack is intended to turn common senior engineering activities into version-controlled prompts, rules, agents, and templates that can be reviewed, improved, and reused across repositories.

## Current Stage

The project is in early implementation stage.

The expected file layout exists and initial Continue configuration, agents, prompts, rules, and templates are implemented. The pack still needs validation in Continue before it should be treated as production-ready.

## Target Users

- Senior engineers working in enterprise .NET repositories
- Architects reviewing service boundaries and dependency direction
- Security engineers reviewing API and application risks
- Performance engineers investigating reliability and throughput concerns
- Product and delivery leads who need structured implementation plans
- Teams using Continue with local or self-hosted model infrastructure

## Goals

- Provide a usable Continue pack for enterprise engineering workflows.
- Favor local-first operation through Continue and Ollama.
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
- Enterprise-safe language and workflows.
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
