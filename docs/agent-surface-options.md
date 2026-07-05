# Agent Surface Options

## Purpose

This document tracks possible agent surfaces for the Local Engineering Agent Pack.

Continue is the first supported surface because it is the current validated path for local Ollama workflows, prompt loading, rule loading, and approved-write testing. Other open-source tools may become useful targets, but they must be validated before they are recommended for real project changes.

## What Counts As An Agent Surface

An agent surface is the editor, CLI, or runtime that connects the pack assets to a model and to tools.

Examples:

- An editor extension that can read files, apply diffs, and ask for approval.
- A terminal coding assistant that can inspect a Git repository and propose patches.
- A self-hosted agent platform that can run workflows against a mounted workspace.

## Current Support Position

| Surface | Current position | Why |
| --- | --- | --- |
| Continue | Supported first path | Existing config, install scripts, validation docs, model testing, and approved-write guidance target Continue today. |
| Cline | Candidate to evaluate | Useful editor-agent shape for tool-backed workflows, but this pack has not validated its config, prompt, rule, or apply behavior yet. |
| Aider | Candidate to evaluate | Mature Git-aware CLI workflow, but it would need CLI-specific prompt packaging and validation. |
| Kilo Code | Candidate to evaluate | Possible editor/CLI surface, but needs compatibility and write-safety validation before recommendation. |
| OpenCode | Candidate to evaluate | Possible terminal or IDE agent path, but needs validation against this pack's workflows. |
| OpenHands | Candidate to evaluate | More platform-like than editor-focused; useful for heavier automation only after trust-boundary review. |

Candidate means "worth testing", not "approved for edits".

## Validation Levels

Use the same labels for every surface:

| Level | Meaning |
| --- | --- |
| Candidate | The surface looks relevant, but this pack has not validated it yet. |
| Read-only validated | The surface can discover the opened repository, list files, read target files, and produce grounded output without modifying files. |
| Plan validated | The surface can produce implementation plans that preserve project constraints and pass deterministic output verification. |
| Approved-write ready | The surface can make scoped edits only after approval, target the correct file, avoid duplicate writes, and pass external shell or Git verification. |

Do not mark a surface approved-write ready from model claims alone. Verify the changed files outside the agent surface.

## Portability Rules

- Keep reusable prompts, rules, templates, examples, and validation evidence independent of Continue-specific syntax where practical.
- Keep Continue-specific configuration in `.continue` until another surface has a tested packaging format.
- Do not weaken safety rules to support another tool.
- Do not commit private endpoints, local paths, tokens, raw transcripts, or customer/project names when recording validation evidence.
- Treat local model behavior as surface-specific. A model that works in one editor or CLI may fail in another.

## Recommended Next Evaluation

Start with one non-Continue surface in read-only mode.

Suggested order:

1. Pick a generated local sample repository.
2. Install or configure the candidate surface without write permissions if possible.
3. Run repository discovery.
4. Confirm actual file reads, not guessed summaries.
5. Run deterministic output verification on the generated response.
6. Record sanitized evidence in the wiki and repository docs.
7. Only then test scoped writes against a disposable repository.

## Non-Enterprise Use

The default path should stay friendly for users who are not in a corporate environment:

- Simple local Ollama setup.
- Conservative starter model.
- Short commands for Windows, Linux, and macOS.
- Clear warnings before write mode.
- Optional advanced integrations instead of required enterprise tooling.

Enterprise teams can still layer on MCP, SonarQube, stricter validation evidence, review gates, and release governance.
