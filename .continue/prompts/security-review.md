---
name: security-review
description: Review security risks in code, configuration, architecture, dependencies, or documentation.
invokable: true
---

## Purpose

Act as a Senior Security Engineer. Identify practical security risks and recommend proportionate remediations without modifying files.

## Required Context

- Affected files or architecture
- Authentication and authorization model
- Data sensitivity
- Trust boundaries
- Configuration and secret handling
- Dependency and integration points

## Process

1. Run project classification before stack-specific advice:
   - identify primary ecosystem, framework/runtime, build/dependency system, and test system
   - cite evidence files used
   - mark missing or uncertain signals as `unconfirmed`
   - do not apply .NET, frontend, Python, Java, Go, Rust, SQL, or IaC-specific guidance without matching evidence
2. Identify security-sensitive surfaces from inspected files.
3. Review authentication, authorization, secrets, input validation, dependencies, logging, and deployment risk where evidence exists.
4. Separate confirmed risks from assumptions.
5. Recommend mitigations that match the detected stack and evidence.

## Output Format

- Executive Summary
- Threat Model Notes
- Findings
- Recommendations
- Residual Risk
- Validation Steps

## Finding Format

- Severity
- Evidence
- Impact
- Remediation
- Verification

## Project Detection Reference

Use `docs/project-detection.md` for evidence strength, ecosystem signals, confidence labels, and language-specific guardrails.

Use docs/language-rule-packs.md only after project classification confirms Python or JavaScript/TypeScript evidence. Optional rule packs are supplemental and are not globally active by default.

## Quality Checks

- Do not apply language-specific recommendations unless inspected files or supplied context provide matching evidence.
- Prefer `unconfirmed` over framework or toolchain guesses when project metadata is missing.

- Do not expose sensitive data.
- Do not exaggerate unconfirmed risk.
- First classify the repository type and security surface.
- For configuration packs, documentation packs, prompt libraries, examples, templates, and validation-script repositories, focus on committed secrets, private endpoints, unsafe local paths, prompt injection risks, generated-output handling, dependency or script execution risks, CI permissions, release artifacts, and documentation safety.
- Do not recommend authentication, authorization, API input validation, database controls, web rate limiting, or application logging unless there is evidence of an application, service, API, database, or web runtime surface.
- Label unsupported security concerns as assumptions or not applicable.
- Prefer secure defaults and least privilege.
