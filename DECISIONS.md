# Decisions

This file records important project decisions. Use it for choices that affect architecture, compatibility, governance, or long-term maintenance.

## Format

Each decision should use this structure:

```text
## YYYY-MM-DD: Decision Title

Status: Proposed | Accepted | Superseded

Context:
Why the decision is needed.

Decision:
What was chosen.

Consequences:
Expected benefits, tradeoffs, and follow-up work.
```

## 2026-07-01: Use Continue YAML Configuration

Status: Accepted

Context:
Continue supports YAML configuration for agents, models, rules, prompts, context providers, documentation, and MCP servers. The deprecated JSON configuration format should not be the primary target for this pack.

Decision:
Use `.continue/config.yaml` with `schema: v1` as the composition root for the pack.

Consequences:
The pack should be validated against the Continue YAML schema. Documentation and examples should prefer YAML configuration.

## 2026-07-01: Local-First Model Posture

Status: Accepted

Context:
The project targets enterprise teams that may work with private repositories and regulated codebases.

Decision:
Use Ollama and local models as the default documented path.

Consequences:
Cloud-hosted model configuration may be documented later, but must not become the default assumption.

## 2026-07-01: Separate Agents, Prompts, Rules, And Templates

Status: Accepted

Context:
The repository needs to scale across many workflows without duplicating instructions or creating unclear ownership.

Decision:
Agents define role behavior, prompts define workflow steps, rules define reusable standards, and templates define output shape.

Consequences:
Contributors should move duplicated guidance to the lowest appropriate reusable layer, usually rules or templates.

## 2026-07-01: Keep Rule Dependencies Acyclic

Status: Accepted

Context:
Rules, prompts, agents, and templates can easily become coupled if each layer copies or depends on the others.

Decision:
Rules and templates are lower-level reusable assets. Prompts may reference rules and templates conceptually. Agents may reference prompts and rules conceptually. Rules should not depend on prompts or agents.

Consequences:
The pack should remain easier to extend because policy, workflow, role behavior, and output shape can evolve independently.

## 2026-07-01: Include Supplemental Review Prompts

Status: Accepted

Context:
Additional prompt files existed for AI framework self-review, refactoring planning, product-management review, and release-readiness review. They were useful enterprise workflows but were not wired into the pack configuration.

Decision:
Normalize those prompt files with standard frontmatter, use lower-case kebab-case filenames, and include them in `.continue/config.yaml`.

Consequences:
The pack now exposes broader review and planning workflows. Runtime validation must confirm each prompt is invokable in Continue.

## 2026-07-01: Use MIT License

Status: Accepted

Context:
The repository is a reusable Continue engineering pack made of configuration, prompts, rules, agents, templates, and documentation. Adoption should be simple for teams that want to copy, adapt, or redistribute the pack.

Decision:
Use the MIT License.

Consequences:
The pack is permissively licensed with low adoption friction. The license does not include the explicit patent grant provided by Apache-2.0.

## 2026-07-01: Keep Ollama Endpoint Portable

Status: Accepted

Context:
The pack should be reusable across machines and networks. A local-network Ollama server was used for validation, but committing a concrete private IP address would make the default configuration environment-specific.

Decision:
Do not commit a concrete `apiBase` value for Ollama. Use remote Ollama endpoints only as local test-time overrides.

Consequences:
The committed config remains portable and defaults to Continue's standard Ollama behavior. Users who run Ollama on another host must add their own local `apiBase` override.

## 2026-07-01: Start SonarQube Support With Manual Triage

Status: Accepted

Context:
SonarQube support is part of the enterprise review scope, but direct API, CLI, or MCP integration requires additional design and environment assumptions.

Decision:
Provide a manual workflow first. Users paste relevant SonarQube findings into Continue, and the pack guides classification, prioritization, remediation, and validation.

Consequences:
Teams can use SonarQube findings immediately without integration setup. Automated SonarQube ingestion remains a future Milestone 3 concern.

## 2026-07-01: Use Documentation Checklists For Pack Validation

Status: Accepted

Context:
The pack is primarily composed of markdown and YAML assets. Traditional unit tests do not cover most quality risks in prompts, rules, agents, templates, and examples.

Decision:
Maintain validation checklists in `docs/validation-checklists.md` for prompt, rule, agent, template, config, example, documentation, and release changes.

Consequences:
Contributors have a repeatable review path before automated validation exists. Future scripts can be added later for checks that are easy to automate.
