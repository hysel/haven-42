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
