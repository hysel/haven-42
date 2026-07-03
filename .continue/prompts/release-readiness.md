---
name: release-readiness
description: Evaluate whether the repository is ready for release and identify blockers.
invokable: true
---

## Purpose

Review the repository for release readiness without modifying files.

## Required Context

- README and project docs
- TODO and roadmap
- Configuration files
- License and changelog
- Validation status
- Examples and automation, if present

## Process

1. Evaluate documentation, testing, logging, security, performance, and configuration.
2. Review examples, versioning, license, contributing guidance, issue templates, and GitHub Actions.
3. Identify blocking issues and release risks.
4. Recommend a version number and go/no-go decision.

## Output Format

- Go/No-Go Recommendation
- Release Checklist
- Blocking Issues
- Recommended Version Number
- Follow-up Recommendations

## Quality Checks

- Classify the repository type before deciding what "release" means.
- For configuration packs, documentation packs, prompt libraries, examples, templates, and validation-script repositories, evaluate version metadata, changelog, README/setup guidance, validation scripts, CI status, release notes, tags, fixtures, examples, local-config safety, and rollback guidance.
- Do not require application runtime controls such as structured logging, production operations, database rollback, API security, or deployment runbooks unless the repository includes an application runtime.
- Treat missing evidence as a risk or open question; do not invent release blockers.
- Give a no-go only for concrete blockers or clearly missing release evidence.
