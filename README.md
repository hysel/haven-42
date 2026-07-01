# Continue Enterprise Engineering Pack

Enterprise-focused Continue configuration pack for software engineering teams that want local-first AI assistance, repeatable review workflows, and opinionated guidance for .NET and Clean Architecture repositories.

This repository is currently in scaffold stage. The intended folder layout is present, but the pack content still needs to be implemented before it can be treated as production-ready.

## Purpose

The goal of this pack is to provide a reusable engineering assistant setup for Continue, with workflows for repository discovery, implementation planning, code review, security review, architecture review, performance review, documentation, and product management.

It is designed for teams that want AI support to follow consistent engineering standards instead of relying on ad hoc prompts.

## Intended Capabilities

- Local LLM support through Continue and Ollama
- Enterprise .NET and ASP.NET Core guidance
- Clean Architecture review and implementation support
- Repository discovery and system understanding workflows
- Code review, bug investigation, and implementation planning prompts
- Security, performance, and SonarQube-oriented review guidance
- Documentation and product-management assistant roles
- Reusable templates for architecture, AI, security, and performance artifacts
- Future MCP integration points for richer repository and tool context

## Repository Layout

```text
.continue/
  config.yaml
  agents/
  prompts/
  rules/
  templates/

AI.md
ARCHITECTURE.md
CHANGELOG.md
DECISIONS.md
PROJECT.md
README.md
ROADMAP.md
STYLEGUIDE.md
TODO.md
```

### `.continue/config.yaml`

The Continue entry point. This should eventually define models, context providers, prompts, rules, and integration settings.

### `.continue/agents`

Role-specific assistant definitions, including senior engineer, architect, security engineer, performance engineer, reviewer, documentation specialist, and product manager.

### `.continue/prompts`

Task-oriented workflows for repository discovery, implementation planning, code review, bug investigation, architecture review, security review, performance review, and documentation.

### `.continue/rules`

Reusable engineering standards for general development, Git, .NET, ASP.NET Core, APIs, Clean Architecture, testing, logging, security, performance, and SonarQube.

### `.continue/templates`

Output templates for durable engineering artifacts such as architecture notes, AI guidance, security reviews, and performance reviews.

## Current Status

The repository currently contains the target file and directory structure, but most files are placeholders. Milestone 1 should focus on turning the scaffold into a minimally usable Continue pack.

Recommended first implementation target:

1. Define a valid `.continue/config.yaml`.
2. Implement core engineering rules.
3. Add repository discovery, implementation planning, code review, and security review prompts.
4. Define the senior engineer, architect, and security engineer agents.
5. Add practical output templates.
6. Document setup and usage once the pack can be loaded by Continue.

## Usage

Usage instructions will be added after the Continue configuration and prompt files are implemented.

The intended workflow is:

1. Install or copy this pack into a repository that uses Continue.
2. Configure local models through Ollama.
3. Use the included agents, prompts, rules, and templates during engineering work.
4. Keep project-specific decisions in the top-level documentation files.

## Design Principles

- Prefer local-first operation for private enterprise codebases.
- Make prompts repeatable, reviewable, and version-controlled.
- Keep rules explicit enough to guide AI output without hiding engineering judgment.
- Optimize for .NET, ASP.NET Core, Clean Architecture, secure APIs, and maintainable services.
- Treat AI output as engineering assistance that still requires human review.

## Roadmap

See `ROADMAP.md` once milestone planning is written.

## License

License information has not been added yet.
