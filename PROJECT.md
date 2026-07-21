# Project

## Name

Haven 42

Tagline: Your private, local AI station.

## Purpose

This repository defines an evidence-gated, local-first AI workbench for individual users, developers, teams, consultants, and enterprise groups. It combines repeatable software-engineering workflows with repository-optional chat, writing, summarization, and image capabilities under common routing, approval, privacy, and typed-artifact contracts.

The engineering pack turns common senior engineering activities into version-controlled prompts, rules, agents, and templates that can be reviewed, improved, and reused across repositories. The broader Haven 42 product direction adds an approachable local web experience over the same tested contracts.

Continue, Aider, and OpenCode are the maintained engineering surfaces. General text capabilities have a live-validated Ollama adapter, Linux image generation has a live-validated ComfyUI/SDXL provider, and all additional providers or surfaces remain pass-before-ship.

## Current Stage

Milestones 1 through 21 are complete for their defined scopes. Milestone 22
owns the planned local web UI and task composition, Milestone 23 owns native
local image profiles, and Milestones 24 and 25 track documentation-only music,
audio, and video research. Broader surface and provider parity remains
evidence-gated.

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

- Provide a usable local-first AI workbench for practical engineering and general-purpose workflows.
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
