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

## Filename Fidelity Gate

- Treat the inspected repository context as the only source of truth for existing filenames.
- Use exact filenames only when they appear in inspected files, tool output, or supplied context.
- Do not invent, normalize, or substitute conventional filenames such as `CHANGELOG.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, CI workflow names, migration names, Kubernetes manifests, or `.continue/config.yaml`.
- Do not assume this engineering pack's own files, rules, prompts, docs, `.continue/config.yaml`, or workflow names exist in the repository being reviewed.
- If a useful file is missing, label it as `recommended new file: <path>` or `missing file recommendation: <path>` instead of describing it as an existing file.
- If a filename is uncertain, write `unconfirmed filename` and describe the evidence needed before naming the file exactly.
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
