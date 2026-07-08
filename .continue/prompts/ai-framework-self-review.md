---
name: ai-framework-self-review
description: Review this local-first engineering agent pack as a reusable software product.
invokable: true
---

## Purpose

Review the Local Engineering Agent Pack itself as a reusable engineering-assistant product.

## Required Context

- Top-level project documentation
- `.continue/config.yaml`
- Agents
- Prompts
- Rules
- Templates
- Roadmap and TODO state

## Process

1. Evaluate architecture, folder structure, naming, maintainability, and extensibility.
2. Review prompt quality, agent design, rules, documentation, and standards.
3. Assess open-source readiness and enterprise readiness.
4. Identify technical debt and future feature opportunities.
5. Recommend a version and roadmap direction.

## Filename Fidelity Gate

- Treat the inspected repository context as the only source of truth for existing filenames.
- Use exact filenames only when they appear in inspected files, tool output, or supplied context.
- Do not invent, normalize, or substitute conventional filenames such as `CHANGELOG.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, CI workflow names, migration names, Kubernetes manifests, or `.continue/config.yaml`.
- Do not assume this engineering pack's own files, rules, prompts, docs, `.continue/config.yaml`, or workflow names exist in the repository being reviewed.
- If a useful file is missing, label it as `recommended new file: <path>` or `missing file recommendation: <path>` instead of describing it as an existing file.
- If a filename is uncertain, write `unconfirmed filename` and describe the evidence needed before naming the file exactly.
## Output Format

- Executive Summary
- Strengths
- Weaknesses
- Technical Debt
- Future Features
- Prioritized Roadmap
- Version Recommendation
