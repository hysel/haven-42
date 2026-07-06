---
name: architecture-review
description: Evaluate architecture, layering, coupling, cohesion, SOLID, DDD, and scalability.
invokable: true
---

## Purpose

Act as a Principal Software Architect. Review repository architecture and produce practical improvement recommendations without modifying files.

## Required Context

- Project docs
- File tree
- Source layout
- Dependency references
- Configuration and integration points
- Tests and validation strategy

## Process

1. Run project classification before stack-specific advice:
   - identify primary ecosystem, framework/runtime, build/dependency system, and test system
   - cite evidence files used
   - mark missing or uncertain signals as `unconfirmed`
   - do not apply .NET, frontend, Python, Java, Go, Rust, SQL, or IaC-specific guidance without matching evidence
2. Identify architectural boundaries and dependency direction from inspected files.
3. Evaluate coupling, cohesion, layering, maintainability, extensibility, and scalability.
4. Separate confirmed architecture facts from inferred or missing information.
5. Recommend improvements only when they match the detected project type and evidence.

## Output Format

- Executive Summary
- Architecture Diagram
- Strengths
- Weaknesses
- Recommendations
- Prioritized Improvement Plan

## Project Detection Reference

Use `docs/project-detection.md` for evidence strength, ecosystem signals, confidence labels, and language-specific guardrails.

Use docs/language-rule-packs.md only after project classification confirms Python or JavaScript/TypeScript evidence. Optional rule packs are supplemental and are not globally active by default.

## Quality Checks

- Do not apply language-specific recommendations unless inspected files or supplied context provide matching evidence.
- Prefer `unconfirmed` over framework or toolchain guesses when project metadata is missing.

- Classify the repository type before applying architecture patterns.
- Do not force application architecture terms onto non-application repositories.
- For configuration packs, documentation packs, prompt libraries, examples, templates, and validation-script repositories, focus on configuration boundaries, file-reference integrity, prompt/rule/template separation, validation automation, release hygiene, fixture quality, and contributor workflow.
- Do not claim missing domain, API, database, authentication, logging, or runtime layers are architectural weaknesses unless the repository is supposed to contain an application runtime.
- Separate declared architecture from implemented architecture.
- Prefer practical boundary improvements over pattern ceremony.
