---
name: documentation
description: Improve or create documentation while keeping claims aligned with implemented behavior.
invokable: true
---

## Purpose

Create, review, or improve engineering documentation while keeping recommendations tied to implemented behavior.

## Required Context

- Target audience
- Current docs
- Implemented behavior
- Known limitations
- Related project files

## Process

1. Run project classification before stack-specific advice:
   - identify primary ecosystem, framework/runtime, build/dependency system, and test system
   - cite evidence files used
   - mark missing or uncertain signals as `unconfirmed`
   - do not apply .NET, frontend, Python, Java, Go, Rust, SQL, or IaC-specific guidance without matching evidence
2. Inspect existing docs and repository structure.
3. Identify missing setup, usage, validation, architecture, contribution, and troubleshooting documentation.
4. Match documentation recommendations to the detected project type and audience.
5. Separate required documentation from optional polish.

## Filename Fidelity Gate

- Treat the inspected repository context as the only source of truth for existing filenames.
- Use exact filenames only when they appear in inspected files, tool output, or supplied context.
- Do not invent, normalize, or substitute conventional filenames such as `CHANGELOG.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, CI workflow names, migration names, Kubernetes manifests, or `.continue/config.yaml`.
- Do not assume this engineering pack's own files, rules, prompts, docs, `.continue/config.yaml`, or workflow names exist in the repository being reviewed.
- If a useful file is missing, label it as `recommended new file: <path>` or `missing file recommendation: <path>` instead of describing it as an existing file.
- If a filename is uncertain, write `unconfirmed filename` and describe the evidence needed before naming the file exactly.
## Output Format

- Summary
- Proposed Documentation Structure
- Content Draft or Review Findings
- Gaps
- Follow-up Tasks

## Project Detection Reference

Use `docs/project-detection.md` for evidence strength, ecosystem signals, confidence labels, and language-specific guardrails.

Use docs/language-rule-packs.md only after project classification confirms Python or JavaScript/TypeScript evidence. Optional rule packs are supplemental and are not globally active by default.

## Quality Checks

- Do not apply language-specific recommendations unless inspected files or supplied context provide matching evidence.
- Prefer `unconfirmed` over framework or toolchain guesses when project metadata is missing.

- Do not invent functionality.
- Keep scaffold-stage language explicit when appropriate.
- Prefer links and references over duplicated detail.
