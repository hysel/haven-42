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

1. Run project classification before stack-specific advice:
   - identify primary ecosystem, framework/runtime, build/dependency system, and test system
   - cite evidence files used
   - mark missing or uncertain signals as `unconfirmed`
   - do not apply .NET, frontend, Python, Java, Go, Rust, SQL, or IaC-specific guidance without matching evidence
2. Inspect the changed behavior.
3. Look for correctness, security, regression, and maintainability risks.
4. Check whether tests cover the important behavior.
5. Separate blocking findings from suggestions.
6. Keep summaries brief.

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

## Project Detection Reference

Use `docs/project-detection.md` for evidence strength, ecosystem signals, confidence labels, and language-specific guardrails.

Use docs/language-rule-packs.md only after project classification confirms Python or JavaScript/TypeScript evidence. Optional rule packs are supplemental and are not globally active by default.

## Quality Checks

- Do not apply language-specific recommendations unless inspected files or supplied context provide matching evidence.
- Prefer `unconfirmed` over framework or toolchain guesses when project metadata is missing.

- Lead with findings.
- Avoid style-only comments unless they materially affect maintainability.
- Say clearly when no issues are found.
- Review the repository type before making recommendations.
- For configuration packs, documentation packs, and prompt-pack repositories, treat docs, prompts, rules, examples, fixtures, validation scripts, CI, and release metadata as the review surface.
- Do not flag intentionally documented fallback commands, such as `npx @continuedev/cli`, as defects unless they contradict repository guidance.
- Only recommend code-level application changes when changed files provide evidence of application code.
