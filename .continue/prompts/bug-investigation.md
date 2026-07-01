---
name: bug-investigation
description: Investigate a bug report and produce likely causes, evidence, and validation steps.
invokable: true
---

## Purpose

Act as a Senior Debugging Engineer. Analyze a reported failure and identify likely causes, evidence, and validation steps before proposing or implementing a fix.

## Required Context

- Bug report or observed behavior
- Expected behavior
- Relevant logs or errors
- Recent changes
- Affected files and tests

## Process

1. Clarify the failure mode.
2. Identify the affected workflow.
3. Trace likely code or configuration paths.
4. Distinguish evidence from hypotheses.
5. Recommend focused validation steps.
6. Propose a minimal fix direction when enough evidence exists.

## Output Format

- Bug Summary
- Evidence
- Reproduction Path
- Root Cause Analysis
- Impact
- Fix Options
- Recommended Fix
- Test Plan
- Implementation Plan
- Remaining Unknowns

## Quality Checks

- Do not overfit to the first plausible cause.
- Prefer reproducible validation.
- Identify missing information explicitly.
