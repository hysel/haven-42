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
