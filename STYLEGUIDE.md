# Style Guide

## Purpose

This style guide keeps documentation, prompts, rules, agents, and templates consistent as the pack grows.

The pack should feel like a practical senior engineering toolkit: clear, direct, reviewable, and safe for enterprise use.

## General Writing

- Use plain technical English.
- Prefer short sections with specific headings.
- Avoid marketing language.
- Avoid claiming implemented behavior before it exists.
- State assumptions explicitly.
- Distinguish required behavior from recommended behavior.
- Use examples when they remove ambiguity.

## Markdown Conventions

- Use `#` for the document title.
- Use `##` for primary sections.
- Use `###` only when it improves scanability.
- Use fenced code blocks for file trees, command examples, and structured snippets.
- Use bullets for unordered guidance.
- Use numbered lists for ordered workflows.
- Keep line length readable, but do not force hard wrapping.

## README Style

The README should be user-facing.

It should answer:

- What is this?
- Who is it for?
- What works today?
- How do I use it?
- Where do I go for deeper detail?

The README should not carry detailed implementation planning once that content belongs in `ROADMAP.md` or `TODO.md`.

## Project Documentation Style

Top-level documentation should separate concerns:

- `PROJECT.md` defines scope and intent.
- `ARCHITECTURE.md` explains structure and responsibility boundaries.
- `ROADMAP.md` explains staged delivery.
- `TODO.md` tracks tactical implementation work.
- `DECISIONS.md` records meaningful project decisions.
- `CHANGELOG.md` records released changes.
- `AI.md` guides AI assistants and contributors.

## Prompt Style

Prompt files should include:

- Purpose
- When to use
- Required context
- Process
- Output format
- Quality checks

Prompts should be task-specific. They should not duplicate full rule files.

## Rule Style

Rule files should include:

- Scope
- Required practices
- Avoid
- Review checklist, where useful

Rules should be concise and enforceable. Avoid broad advice that cannot guide a review or implementation decision.

## Agent Style

Agent files should define:

- Role
- Responsibilities
- Operating principles
- Boundaries
- Expected outputs

Agents should describe durable behavior. Task sequences belong in prompts.

## Template Style

Templates should be structured for repeatable outputs.

Prefer sections such as:

- Summary
- Context
- Findings
- Recommendations
- Risks
- Open Questions
- Next Steps

Templates should be easy to paste into issues, pull requests, architecture records, or review documents.

## Tone

- Be precise.
- Be calm.
- Be direct about risk.
- Be respectful of existing code.
- Prefer actionable guidance over abstract criticism.

## Terminology

Use consistent terms:

- "pack" for this repository's Continue configuration bundle
- "agent" for a role-specific assistant definition
- "prompt" for a task-specific workflow
- "rule" for reusable engineering guidance
- "template" for structured output
- "local-first" for the default model and privacy posture
