# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple changelog format:

- `Added` for new capabilities
- `Changed` for updates to existing behavior or documentation
- `Fixed` for corrections
- `Removed` for deprecated or deleted behavior

## Unreleased

No unreleased changes.

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
