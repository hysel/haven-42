# Architecture

## Overview

The Local Engineering Agent Pack is organized as a documentation, configuration, and workflow repository. Its first supported deliverable is the `.continue` directory, supported by top-level project documentation.

The currently validated runtime architecture is:

```text
Continue
  loads .continue/config.yaml
  exposes configured models, context providers, prompts, and rules
  uses role-specific agents for specialized engineering workflows
  applies reusable rules during code and documentation tasks
  produces structured outputs through templates
```

The long-term architecture should keep prompts, rules, templates, validation scripts, and evidence formats portable enough to evaluate with other local-first coding-agent surfaces.

## Repository Layers

### Project Documentation

Top-level markdown files define the product contract, architecture, roadmap, style conventions, implementation tasks, decisions, and release notes.

These files explain why the pack exists and how contributors should evolve it.

### Agent Surface Configuration

`.continue/config.yaml` is the intended entry point for the current Continue integration.

It should eventually define:

- Local model configuration
- Context providers
- Prompt references
- Rule references
- Agent or mode wiring, where supported
- MCP integration points, when implemented

### Agents

`.continue/agents` contains role-specific assistant definitions.

Agents should describe durable professional behavior, responsibilities, boundaries, and expected outputs. They should not duplicate every task instruction from prompts or every standard from rules.

Initial agents:

- `senior-engineer.md`
- `architect.md`
- `security-engineer.md`

Secondary agents:

- `reviewer.md`
- `performance.md`
- `documentation.md`
- `product-manager.md`

### Prompts

`.continue/prompts` contains task-specific workflows.

Prompts should define:

- When to use the workflow
- What context to gather
- How to reason about the task
- Expected output format
- Risk checks and verification steps

Prompts should reference rules by concept, but should avoid copying entire rule files.

### Rules

`.continue/rules` contains reusable engineering standards.

Rules should be concise, enforceable, and broadly applicable. They should define expectations for quality, security, maintainability, testing, logging, API design, and framework usage.

Rules should avoid task-specific instructions that belong in prompts.

### Templates

`.continue/templates` contains structured output formats for artifacts that may be committed or shared.

Templates should make review outputs consistent and easy to scan.

## Responsibility Boundaries

- `config.yaml` wires the pack together.
- Agents define role behavior.
- Prompts define task flow.
- Rules define standards.
- Templates define durable output shape.
- Top-level docs define project intent and governance.

## Dependency Policy

The pack uses a simple dependency direction:

```text
config.yaml
  -> agents
  -> prompts
  -> rules
  -> templates

top-level docs govern all layers but are not runtime dependencies
```

Allowed references:

- `config.yaml` may reference rules, prompts, docs, context providers, models, and future MCP servers.
- Agents may reference rules and prompts conceptually.
- Prompts may reference rules and templates conceptually.
- Rules should not depend on prompts or agents.
- Templates should not depend on prompts, agents, or rules.
- Top-level docs may describe any layer.

This keeps reusable policy below workflow orchestration and prevents circular instruction dependencies.

## Domain Language

The project domain is local-first engineering workflow guidance.

- Pack: the complete reusable engineering-agent bundle in this repository.
- Agent surface: the editor, CLI, or runtime environment that loads the pack assets and executes model/tool workflows.
- Agent: a role-specific assistant definition.
- Prompt: a task-specific workflow that can be invoked by a user.
- Rule: reusable engineering guidance applied across workflows.
- Template: structured output for a durable artifact or review.
- Finding: a concrete issue identified during review.
- Recommendation: an actionable change or decision proposal.
- Workflow: a repeatable task sequence such as repository discovery, code review, or security review.

## Initial Architecture Decisions

- The pack is local-first and should work with Ollama before cloud model assumptions are introduced.
- Continue remains the first supported agent surface, but the project should avoid coupling reusable guidance to Continue-only behavior when a portable abstraction is practical.
- The first ecosystem focus is .NET and ASP.NET Core, with enterprise-grade guidance kept useful for smaller projects too.
- Clean Architecture guidance should be practical and testable, not ceremonial.
- Security and performance review guidance should be built into early milestones.
- MCP and SonarQube support should be documented as integration targets until implemented.
- Tool-enabled project changes should be treated as an approved execution mode, not the default review posture.
- Local model selection should remain hardware-aware but portable, keeping machine-specific endpoints and hardware details out of committed shared config.

## Open Questions

- Should the current local file references in `.continue/config.yaml` be adjusted after validation in Continue?
- Which Ollama models should be recommended for larger enterprise repositories?
- Which additional agent surfaces should be validated first after Continue?
- Should agents be further integrated as native Continue agent files if the target Continue version supports richer agent packaging?
- How should SonarQube findings be provided to the assistant: pasted reports, MCP, CLI output, or another integration?
- Which MCP servers are in scope for the first integration milestone?
- Should prompt examples be added as committed fixtures or generated on demand during release validation?
- What tool execution surface should be considered the supported path for approved project changes?
- Which hardware signals are reliable enough to drive dynamic local model selection across Windows, Linux, and macOS?
