# Continue Enterprise Engineering Pack

Enterprise-focused Continue configuration pack for software engineering teams that want local-first AI assistance, repeatable review workflows, and opinionated guidance for .NET and Clean Architecture repositories.

In plain terms: this repository gives Continue a ready-made set of prompts, rules, and templates so it can help review and plan software work in a more consistent way.

## Purpose

The goal of this pack is to provide a reusable engineering assistant setup for Continue, with workflows for repository discovery, implementation planning, code review, security review, architecture review, performance review, documentation, and product management.

It is designed for teams that want AI support to follow consistent engineering standards instead of relying on ad hoc prompts.

## Quick Start

Use this path if you are new to Continue, Ollama, or command-line tools.

### 1. Install the basics

Install:

- Ollama
- Node.js
- Continue for your editor

Then open PowerShell and download the default local models:

```powershell
ollama pull qwen3-coder:30b
ollama pull nomic-embed-text
```

### 2. Copy this pack into your project

Copy the `.continue` folder from this repository into the project you want to review.

Your project should then look like this:

```text
your-project/
  .continue/
    config.yaml
    prompts/
    rules/
    agents/
    templates/
```

### 3. Start Ollama

Make sure Ollama is running. To check it, run:

```powershell
ollama list
```

If the command shows your models, you are ready.

### 4. Open your project in Continue

Open the project in your editor and point Continue at:

```text
.continue/config.yaml
```

### 5. Run a prompt

Start with one of these:

- `repository-discovery`
- `implementation-plan`
- `code-review`
- `documentation`
- `release-readiness`

Good first request:

```text
Run repository discovery for this project. Do not modify files.
```

### 6. If something fails

Use `docs/troubleshooting.md`.

Most first-time problems are one of these:

- Ollama is not running.
- The model was not downloaded.
- Continue cannot find `.continue/config.yaml`.
- The `cn` command is not installed, so you should use `npx @continuedev/cli` instead.

## Beginner Safety Rules

- Start with review and planning prompts before asking for changes.
- Do not commit private IP addresses, tokens, local paths, or raw company code into this pack.
- Keep machine-specific settings in local files, not in `.continue/config.yaml`.
- Treat AI output as a draft. Review it before changing code.
- Use `git status` before and after AI-assisted work so you know what changed.
- Use `docs/tool-use-modes.md` before asking the assistant to modify a reviewed project.
- Use `docs/scoped-edits.md` to turn an approved plan into one small, reviewable change at a time.

## Intended Capabilities

- Local LLM support through Continue and Ollama
- Enterprise .NET and ASP.NET Core guidance
- Clean Architecture review and implementation support
- Repository discovery and system understanding workflows
- Code review, bug investigation, and implementation planning prompts
- Legacy .NET dependency migration planning for high-risk package-management changes
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

Task-oriented workflows for repository discovery, implementation planning, legacy .NET dependency migration, code review, bug investigation, architecture review, security review, performance review, and documentation.

### `.continue/rules`

Reusable engineering standards for general development, Git, .NET, ASP.NET Core, APIs, Clean Architecture, testing, logging, security, performance, and SonarQube.

### `.continue/templates`

Output templates for durable engineering artifacts such as architecture notes, AI guidance, security reviews, performance reviews, and legacy .NET dependency migration plans.

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

Version `0.1.6` includes runtime validation tooling, prompt quality hardening, beginner setup guidance, and a human-reviewed legacy .NET dependency migration workflow. Current work is focused on tool-enabled workflows and hardware-aware local model selection.

## Standard Usage

The standard workflow is:

1. Install or copy this pack into a repository that uses Continue.
2. Ensure Ollama is running with the configured models available.
3. Point Continue at `.continue/config.yaml`.
4. Use the included prompts for discovery, planning, review, security, architecture, performance, and documentation workflows.
5. Keep project-specific decisions in the top-level documentation files.

Default local model assumptions:

- Chat/edit/apply/tool workflows: `qwen3-coder:30b`
- Embeddings: `nomic-embed-text`
- Ollama endpoint: default local Ollama endpoint

For smaller machines or higher-risk workflows, use `docs/local-model-selection.md` before changing models.

Expected Ollama setup:

```powershell
ollama pull qwen3-coder:30b
ollama pull nomic-embed-text
```

Optional Continue CLI usage with `npx`:

```powershell
npx @continuedev/cli --config .continue/config.yaml
```

If the Continue CLI is installed globally, `cn` may also be available:

```powershell
cn --config .continue/config.yaml
```

If PowerShell reports that `cn` is not recognized, use the `npx` command above or install the CLI globally:

```powershell
npm install -g @continuedev/cli
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
- `examples/fixtures/security-review-input.md`
- `examples/fixtures/performance-review-input.md`
- `examples/fixtures/release-readiness-input.md`
- `examples/fixtures/sonarqube-findings.md`

## Workflow Docs

- `docs/sonarqube-review.md`
- `docs/sonarqube-integration-options.md`
- `docs/mcp-options.md`
- `docs/mcp-setup.md`
- `docs/compatibility.md`
- `docs/validation-checklists.md`
- `docs/troubleshooting.md`
- `docs/tool-use-modes.md`
- `docs/approved-tool-backed-changes.md`
- `docs/scoped-edits.md`
- `docs/local-model-selection.md`
- `docs/local-model-reliability.md`
- `docs/banned-output-patterns.md`
- `docs/release.md`
- `docs/runtime-validation.md`
- `docs/prompt-quality.md`

## Validation

Run the local validation script before release-oriented changes:

```powershell
.\scripts\validate-pack.ps1
```

The script checks the configured version, required files, local `.continue` file references, default MCP posture, and obvious committed private endpoints or secrets.

For runtime validation against a target repository, run:

```powershell
$Pack = "C:\path\to\continue-enterprise-engineering-pack"
& "$Pack\scripts\run-runtime-validation.ps1" -TargetRepo (Get-Location).Path
```

Raw runtime outputs are written to an ignored local folder and should be reviewed before any sanitized summary is committed.

To generate a context file without relying on Continue tool execution:

```powershell
$Pack = "C:\path\to\continue-enterprise-engineering-pack"
& "$Pack\scripts\generate-runtime-context.ps1" -TargetRepo (Get-Location).Path -OutputPath .\runtime-context.md
```

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
