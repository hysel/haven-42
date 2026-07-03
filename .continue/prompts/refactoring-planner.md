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
