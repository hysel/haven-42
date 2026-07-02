# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple changelog format:

- `Added` for new capabilities
- `Changed` for updates to existing behavior or documentation
- `Fixed` for corrections
- `Removed` for deprecated or deleted behavior

## Unreleased

### Added

- Added Milestone 5 tracking for prompt quality hardening.
- Added prompt-quality documentation with legacy dependency migration, documentation review, release readiness, and implementation planning pass/fail expectations.
- Added an implementation-planning quality fixture for plan-only, layered-change validation.
- Added a documentation-review quality fixture for onboarding, operations, release, and support gap validation.
- Added a legacy dependency migration quality fixture.
- Added a release-readiness quality fixture for no-go evidence validation.
- Added local-model reliability guidance for Ollama-backed prompt validation and escalation.
- Added banned-output-pattern guidance for high-risk prompt workflows.
- Added static validation for prompt frontmatter, required metadata, filename style, and config coverage.

## 0.1.5 - 2026-07-02

### Added

- Added runtime validation tracking documentation and security, performance, and release-readiness fixtures.
- Added README and troubleshooting guidance for using `npx @continuedev/cli` when `cn` is not installed.
- Added a runtime validation runner that captures prompt outputs to ignored local files.
- Added runtime context generation for local-model validation without CLI tool execution.
- Added a dedicated legacy .NET dependency migration prompt for safe `packages.config` to `PackageReference` planning.
- Added a fixed legacy .NET dependency migration template to reduce unsafe local-model migration recipes.

### Changed

- Tightened implementation planning guidance for legacy .NET project and dependency-management migrations.
- Strengthened legacy project migration guardrails after runtime validation showed unsafe project-file rewrite recommendations.
- Added explicit safeguards against mechanical `packages.config` migration recipes for custom MSBuild and add-in projects.
- Added forbidden response patterns and minimum acceptable plan requirements to the legacy .NET dependency migration workflow.
- Recorded local-model validation failure for legacy dependency migration despite explicit no-XML instructions.
- Recorded template-driven legacy dependency migration failure and documented the human-reviewed template fallback.

## 0.1.4 - 2026-07-02

### Added

- Added GitHub Actions validation workflow for the pack validation script.

## 0.1.3 - 2026-07-02

### Added

- Added validation checklists for prompts, rules, agents, templates, config, examples, documentation, and releases.
- Added troubleshooting guidance for config loading, local file references, Ollama connectivity, model availability, prompt visibility, rules, local endpoint overrides, and line-ending warnings.
- Added MCP options research with a local-first recommendation that keeps MCP optional and compatible with Ollama-backed systems.
- Added SonarQube integration options research with a manual-first, Web API automation recommendation and optional MCP guidance.
- Added optional GitHub MCP setup guidance and compatibility notes for Continue, Ollama, MCP, and SonarQube workflows.
- Added contributor guidance, release tagging guidance, validation automation, and sanitized review fixtures.

## 0.1.2

### Changed

- Selected the MIT License for repository reuse and redistribution.
- Verified that Continue CLI can load the pack configuration.
- Validated model-backed execution against a local-network Ollama endpoint used only as a test-time override.
- Added representative examples for major workflows.
- Added manual SonarQube review workflow documentation and example output.

## 0.1.1

### Added

- Project documentation foundation.
- Continue pack governance guidance.
- Architecture, roadmap, style, and task tracking documentation.
- Initial decision log.
- Continue `schema: v1` configuration with local-first Ollama defaults.
- Core agents, prompts, rules, and templates.
- Supplemental review prompts for AI framework self-review, refactoring planning, product-management review, and release readiness.

### Changed

- README now documents early implementation status, setup assumptions, and pending runtime validation.

## 0.1.0

### Added

- Initial repository structure for a Continue Enterprise Engineering Pack.
