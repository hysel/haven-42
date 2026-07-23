# AI Contributor Guide

## Purpose

This file defines how AI assistants and human contributors should work in this repository.

Haven 42 is a local-first AI workbench. Continue is the first supported runtime surface, but most value lives in structured guidance, validation, and reusable workflow assets rather than executable code.

## Required Workflow

Before making changes:

1. Read `README.md`.
2. Read `PROJECT.md`.
3. Read `ARCHITECTURE.md`.
4. Read `ROADMAP.md`.
5. Read `STYLEGUIDE.md`.
6. Read `TODO.md`.
7. Inspect the relevant files under `.continue`.

When editing:

- Keep changes scoped to the requested files or workflow.
- Do not modify unrelated files.
- Preserve the separation between agents, prompts, rules, and templates.
- Do not claim a capability is implemented until the corresponding config, prompt, rule, or template exists.
- Prefer concise markdown that can be reviewed in a pull request.

## Repository Rules

- `config.yaml` wires the pack together.
- Agents define durable role behavior.
- Prompts define task-specific workflows.
- Rules define reusable engineering standards.
- Templates define structured outputs.
- Top-level docs define project intent, governance, and delivery plans.

## AI Output Expectations

AI-assisted work in this repository should:

- Explain assumptions.
- Identify uncertainty.
- Prefer practical engineering guidance that works for individuals, small teams, and enterprise teams.
- Keep local-first and privacy-sensitive workflows in mind.
- Avoid introducing secrets, tokens, private URLs, or organization-specific confidential details.
- Suggest validation steps when behavior changes.

## Review Checklist

Before finishing a change, verify:

- The edited files match their documented responsibilities.
- New prompt content does not duplicate full rule content.
- New rule content is reusable outside a single prompt.
- New agent content does not encode a full task workflow.
- README claims match implemented behavior.
- TODO and ROADMAP remain consistent with the actual state.

## Push Completion Contract

After every push, run the platform-specific `verify-hosted-ci` script for the
full pushed commit SHA. Do not report success until the exact-SHA `Validate
Pack` run concludes successfully and all required Windows, Linux, and macOS
jobs pass. Report the SHA, run URL, and one of `Pushed`, `CI running`, `CI
passed`, or `CI failed`. On failure, inspect failed logs and fix the new commit
before continuing. See `docs/hosted-ci-verification.md`.
