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
- [x] Validate the pack against additional realistic fixture inputs.
- [x] Add security review fixture.
- [x] Add performance review fixture.
- [x] Add release-readiness fixture.
- [x] Add runtime validation documentation.
- [x] Add runtime context generation.
- [x] Add legacy .NET dependency migration prompt.
- [x] Add legacy .NET dependency migration template.
- [x] Update pack version to `0.1.5`.
- [x] Update changelog for `0.1.5`.

## Milestone 5: Prompt Quality Hardening

- [x] Add implementation-planning quality fixture.
- [x] Add legacy dependency migration quality fixture.
- [x] Add documentation-review quality fixture.
- [x] Add release-readiness quality fixture.
- [x] Define pass/fail expectations for sensitive prompts.
- [x] Add local-model reliability guidance.
- [x] Extend static validation for prompt frontmatter and required metadata.
- [x] Add banned-output-pattern guidance for high-risk workflows.

## Milestone 6: Applied Tooling And Adaptive Models

- [x] Define safe tool-use modes for reviewed repositories.
- [x] Document how to enable approved tool-backed project changes.
- [x] Add guidance for converting approved plans into scoped edits.
- [ ] Define hardware-aware local model selection strategy.
- [ ] Add hardware-profile helper or documented collection commands.
- [ ] Define recommended Ollama model tiers by RAM, VRAM, context size, and workflow risk.
- [ ] Document how to keep machine-specific model and endpoint details out of committed config.
