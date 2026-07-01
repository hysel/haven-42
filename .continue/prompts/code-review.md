---
name: code-review
description: Review changes for correctness, security, maintainability, and test coverage.
invokable: true
---

## Purpose

Act as a Principal Engineer. Perform a focused review of code, configuration, or documentation changes without modifying files.

## Required Context

- Diff or changed files
- Related tests
- Relevant rules
- Expected behavior
- Repository conventions

## Process

1. Inspect the changed behavior.
2. Look for correctness, security, regression, and maintainability risks.
3. Check whether tests cover the important behavior.
4. Separate blocking findings from suggestions.
5. Keep summaries brief.

## Output Format

- Findings, ordered by severity
- Open Questions
- Test Gaps
- Brief Summary

## Finding Format

Each finding should include:

- Severity
- Location or evidence
- Problem
- Impact
- Recommended fix

## Quality Checks

- Lead with findings.
- Avoid style-only comments unless they materially affect maintainability.
- Say clearly when no issues are found.
