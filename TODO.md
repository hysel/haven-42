# TODO

## Milestone 1: Minimum Usable Pack

### Project Documentation

- [x] Create initial README.
- [x] Define project purpose in `PROJECT.md`.
- [x] Define architecture boundaries in `ARCHITECTURE.md`.
- [x] Define staged roadmap in `ROADMAP.md`.
- [x] Define documentation and prompt style in `STYLEGUIDE.md`.
- [x] Define AI contributor guidance in `AI.md`.
- [x] Define decision log structure in `DECISIONS.md`.
- [x] Define changelog structure in `CHANGELOG.md`.
- [x] Add temporary license status.
- [x] Choose final license terms.

### Continue Configuration

- [x] Identify target Continue configuration schema.
- [x] Define local Ollama model assumptions.
- [x] Implement `.continue/config.yaml`.
- [x] Statically verify configured local file references exist.
- [x] Verify Continue can load the pack.
- [x] Verify model-backed prompt execution with Ollama.
- [x] Document setup and usage in `README.md`.

### Core Rules

- [x] Implement `.continue/rules/general.md`.
- [x] Implement `.continue/rules/git.md`.
- [x] Implement `.continue/rules/dotnet.md`.
- [x] Implement `.continue/rules/aspnetcore.md`.
- [x] Implement `.continue/rules/clean-architecture.md`.
- [x] Implement `.continue/rules/api.md`.
- [x] Implement `.continue/rules/testing.md`.
- [x] Implement `.continue/rules/logging.md`.
- [x] Implement `.continue/rules/security.md`.
- [x] Implement `.continue/rules/performance.md`.
- [x] Implement `.continue/rules/sonarqube.md`.

### Core Prompts

- [x] Implement `.continue/prompts/repository-discovery.md`.
- [x] Implement `.continue/prompts/implementation-plan.md`.
- [x] Implement `.continue/prompts/code-review.md`.
- [x] Implement `.continue/prompts/bug-investigation.md`.
- [x] Implement `.continue/prompts/security-review.md`.
- [x] Implement `.continue/prompts/architecture-review.md`.
- [x] Implement `.continue/prompts/performance-review.md`.
- [x] Implement `.continue/prompts/documentation.md`.
- [x] Implement `.continue/prompts/ai-framework-self-review.md`.
- [x] Implement `.continue/prompts/refactoring-planner.md`.
- [x] Implement `.continue/prompts/product-manager.md`.
- [x] Implement `.continue/prompts/release-readiness.md`.

### Primary Agents

- [x] Implement `.continue/agents/senior-engineer.md`.
- [x] Implement `.continue/agents/architect.md`.
- [x] Implement `.continue/agents/security-engineer.md`.
- [x] Implement `.continue/agents/reviewer.md`.
- [x] Implement `.continue/agents/performance.md`.
- [x] Implement `.continue/agents/documentation.md`.
- [x] Implement `.continue/agents/product-manager.md`.

### Core Templates

- [x] Implement `.continue/templates/Architecture.md`.
- [x] Implement `.continue/templates/SecurityReview.md`.
- [x] Implement `.continue/templates/PerformanceReview.md`.
- [x] Implement `.continue/templates/AI.md`.

## Milestone 2: Review Depth

- [x] Implement architecture review prompt.
- [x] Implement performance review prompt.
- [x] Implement documentation prompt.
- [x] Implement reviewer agent.
- [x] Implement performance agent.
- [x] Implement documentation agent.
- [x] Implement product manager agent.
- [x] Add example outputs for major workflows.
- [x] Expand SonarQube guidance.
- [x] Add validation checklists for prompt and rule changes.
- [x] Add decision records for major design choices.

## Milestone 3: Integrations

- [x] Research MCP options for repository and GitHub context.
- [x] Research SonarQube integration options.
- [x] Document manual SonarQube review workflow.
- [x] Add MCP setup documentation when implementation path is selected.
- [x] Add troubleshooting guidance.

## Release Hardening: 0.1.3

- [x] Add `CONTRIBUTING.md`.
- [x] Add release tagging guidance.
- [x] Add sample review fixtures.
- [x] Add validation automation.
- [x] Update pack version to `0.1.3`.
- [x] Update changelog for `0.1.3`.

## Milestone 4: Runtime Validation And CI

- [x] Add CI automation for `scripts/validate-pack.ps1`.
- [x] Update pack version to `0.1.4`.
- [x] Update changelog for `0.1.4`.
- [ ] Validate the pack against additional real repositories.
- [ ] Add security review fixture.
- [ ] Add performance review fixture.
- [ ] Add release-readiness fixture.
- [ ] Add runtime validation documentation.
