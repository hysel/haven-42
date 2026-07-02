# Continue Enterprise Engineering Pack

Enterprise-focused Continue configuration pack for software engineering teams that want local-first AI assistance, repeatable review workflows, and opinionated guidance for .NET and Clean Architecture repositories.

This repository is in early implementation stage. The documentation foundation, Continue configuration, agents, prompts, rules, and templates are present, but the pack should still be validated in Continue before it is treated as production-ready.

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

docs/
examples/
scripts/
AI.md
ARCHITECTURE.md
CHANGELOG.md
CONTRIBUTING.md
DECISIONS.md
PROJECT.md
README.md
ROADMAP.md
STYLEGUIDE.md
TODO.md
```

### `.continue/config.yaml`

The Continue entry point. It defines local Ollama models, repository context providers, local rule files, local prompt files, and an empty MCP server list for future integrations.

### `.continue/agents`

Role-specific assistant definitions, including senior engineer, architect, security engineer, performance engineer, reviewer, documentation specialist, and product manager.

### `.continue/prompts`

Task-oriented workflows for repository discovery, implementation planning, code review, bug investigation, architecture review, security review, performance review, and documentation.

### `.continue/rules`

Reusable engineering standards for general development, Git, .NET, ASP.NET Core, APIs, Clean Architecture, testing, logging, security, performance, and SonarQube.

### `.continue/templates`

Output templates for durable engineering artifacts such as architecture notes, AI guidance, security reviews, and performance reviews.

### `examples`

Representative outputs for major workflows. These examples show expected structure, tone, and level of detail for repository discovery, implementation planning, code review, architecture review, security review, performance review, and release readiness.

### `docs`

Workflow documentation for enterprise review practices, including MCP research and setup guidance, SonarQube integration options, compatibility notes, the manual SonarQube review workflow, validation checklists, and troubleshooting guidance.

### `scripts`

Repository validation automation for release checks and portable configuration invariants.

## Current Status

The repository contains an initial usable pack structure:

- `.continue/config.yaml` targets Continue `schema: v1`.
- Local-first Ollama model defaults are defined.
- Core rules, prompts, agents, and templates are implemented.
- Configured local rule and prompt file references have been statically checked.
- Continue CLI can load the pack configuration.
- Model-backed execution has been validated with a test-time Ollama endpoint override.
- MCP and SonarQube support are documented as optional integration paths, not default wired integrations.

Version `0.1.3` includes integration hardening, release guidance, contributor guidance, validation automation, and sanitized fixtures. Remaining work should focus on broader runtime validation and project-specific integration examples.

## Usage

The intended workflow is:

1. Install or copy this pack into a repository that uses Continue.
2. Ensure Ollama is running with the configured models available.
3. Point Continue at `.continue/config.yaml`.
4. Use the included prompts for discovery, planning, review, security, architecture, performance, and documentation workflows.
5. Keep project-specific decisions in the top-level documentation files.

Default local model assumptions:

- Chat/edit/apply: `qwen2.5-coder:7b`
- Embeddings: `nomic-embed-text`
- Ollama endpoint: default local Ollama endpoint

Expected Ollama setup:

```powershell
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

Expected Continue CLI usage:

```powershell
cn --config .continue/config.yaml
```

Runtime status:

- Continue CLI config loading was validated with `npx @continuedev/cli`.
- Continue initialized the config, model, MCP, system-message, and file-index services.
- Model-backed execution was validated using a local-network Ollama endpoint as a test-time override.
- A prompt-file smoke test completed successfully.
- Representative workflow examples are available in `examples/`.

## Examples

- `examples/repository-discovery.md`
- `examples/implementation-plan.md`
- `examples/code-review.md`
- `examples/architecture-review.md`
- `examples/security-review.md`
- `examples/performance-review.md`
- `examples/release-readiness.md`
- `examples/sonarqube-review.md`
- `examples/fixtures/repository-context.md`
- `examples/fixtures/sonarqube-findings.md`

## Workflow Docs

- `docs/sonarqube-review.md`
- `docs/sonarqube-integration-options.md`
- `docs/mcp-options.md`
- `docs/mcp-setup.md`
- `docs/compatibility.md`
- `docs/validation-checklists.md`
- `docs/troubleshooting.md`
- `docs/release.md`

## Validation

Run the local validation script before release-oriented changes:

```powershell
.\scripts\validate-pack.ps1
```

The script checks the configured version, required files, local `.continue` file references, default MCP posture, and obvious committed private endpoints or secrets.

## Design Principles

- Prefer local-first operation for private enterprise codebases.
- Make prompts repeatable, reviewable, and version-controlled.
- Keep rules explicit enough to guide AI output without hiding engineering judgment.
- Optimize for .NET, ASP.NET Core, Clean Architecture, secure APIs, and maintainable services.
- Treat AI output as engineering assistance that still requires human review.

## Roadmap

See `ROADMAP.md`.

## License

MIT License. See `LICENSE`.
