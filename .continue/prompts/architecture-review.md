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

1. Identify the system type and current maturity.
2. Map layers and responsibility boundaries.
3. Evaluate Clean Architecture, SOLID, DDD, separation of concerns, coupling, cohesion, dependency direction, scalability, maintainability, and extensibility.
4. Identify architecture strengths and weaknesses.
5. Prioritize improvements by risk and sequencing.

## Output Format

- Executive Summary
- Architecture Diagram
- Strengths
- Weaknesses
- Recommendations
- Prioritized Improvement Plan

## Quality Checks

- Classify the repository type before applying architecture patterns.
- Do not force application architecture terms onto non-application repositories.
- For configuration packs, documentation packs, prompt libraries, examples, templates, and validation-script repositories, focus on configuration boundaries, file-reference integrity, prompt/rule/template separation, validation automation, release hygiene, fixture quality, and contributor workflow.
- Do not claim missing domain, API, database, authentication, logging, or runtime layers are architectural weaknesses unless the repository is supposed to contain an application runtime.
- Separate declared architecture from implemented architecture.
- Prefer practical boundary improvements over pattern ceremony.
