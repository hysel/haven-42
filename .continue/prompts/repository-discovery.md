---
name: repository-discovery
description: Build a concise understanding of a repository before planning or implementation.
invokable: true
---

## Purpose

Discover the repository structure, architecture, technology choices, and current maturity before making recommendations.

## Required Context

- File tree
- README and top-level docs
- Build, dependency, and configuration files
- Source layout
- Tests
- Existing conventions and style

## Process

1. Identify the repository purpose and current stage.
2. Map the major directories and responsibilities.
3. Identify runtime architecture, dependencies, and integration points.
4. Identify missing or placeholder components.
5. Note risks, assumptions, and open questions.

## Output Format

- Executive Summary
- Repository Structure
- Current Architecture
- Key Workflows
- Missing Components
- Risks
- Recommended Next Steps

## Quality Checks

- Do not claim implementation exists when files are placeholders.
- Separate evidence from inference.
- Keep recommendations tied to repository facts.
