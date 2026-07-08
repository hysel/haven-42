---
name: refactoring-planner
description: Identify refactoring opportunities and rank them by return on investment.
invokable: true
---

## Purpose

Analyze a repository and create a refactoring roadmap without modifying files.

## Required Context

- Repository structure
- Architecture documentation
- Current implementation state
- Known risks and TODOs
- Existing tests and validation options

## Process

1. Identify refactoring opportunities.
2. Estimate risk, effort, business value, dependencies, and expected benefits.
3. Sort opportunities by return on investment.
4. Separate quick wins from structural work.
5. Produce a safe implementation roadmap.

## Filename Fidelity Gate

- Treat the inspected repository context as the only source of truth for existing filenames.
- Use exact filenames only when they appear in inspected files, tool output, or supplied context.
- Do not invent, normalize, or substitute conventional filenames such as `CHANGELOG.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, CI workflow names, migration names, Kubernetes manifests, or `.continue/config.yaml`.
- Do not assume this engineering pack's own files, rules, prompts, docs, `.continue/config.yaml`, or workflow names exist in the repository being reviewed.
- If a useful file is missing, label it as `recommended new file: <path>` or `missing file recommendation: <path>` instead of describing it as an existing file.
- If a filename is uncertain, write `unconfirmed filename` and describe the evidence needed before naming the file exactly.
## Output Format

- Executive Summary
- Top Refactoring Opportunities
- ROI Ranking
- Dependencies
- Risks
- Implementation Roadmap

## Quality Checks

- Classify the repository type before proposing refactors.
- For configuration packs, documentation packs, prompt libraries, examples, templates, and validation-script repositories, focus on duplicated guidance, prompt/rule/template drift, validation coverage, fixture gaps, script portability, release metadata, and contributor ergonomics.
- Do not propose centralizing duplicate configuration unless you identify the specific duplicated files or settings.
- Do not recommend application-layer refactors unless there is application source code evidence.
