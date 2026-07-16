# Agent Surface Options

## Purpose

This document tracks possible agent surfaces for the Local Engineering Agent Pack.

Continue is the first supported surface because it is the current validated path for local Ollama workflows, prompt loading, rule loading, shared asset installation, and approved-write testing. Other open-source tools may become useful targets, but they must be validated before they are recommended for real project changes.

## What Counts As An Agent Surface

An agent surface is the editor, CLI, or runtime that connects the pack assets to a model and to tools.

Examples:

- An editor extension that can read files, apply diffs, and ask for approval.
- A terminal coding assistant that can inspect a Git repository and propose patches.
- A self-hosted agent platform that can run workflows against a mounted workspace.

## Compatibility Matrix

This matrix is a support boundary, not a popularity ranking. A surface can be a good candidate and still be blocked for real edits until this pack has evidence that it reads the right workspace, targets the right files, and passes external verification.

The install/configure/test parity view is tracked separately in `config/agent-surface-capabilities.json` and explained in `docs/agent-surface-capability-parity.md`. Promotion gates for non-Continue surfaces are tracked in `docs/agent-surface-promotion-gates.md`.

## Milestone 14 Positioning Completion Basis

Milestone 14 is complete for positioning and support-boundary documentation because the pack now presents itself as a local-first engineering agent pack rather than a Continue-only or enterprise-only bundle. Continue is the first supported surface, while every other surface stays evidence-gated through the compatibility matrix, `docs/agent-surface-promotion-gates.md`, `docs/surface-specific-config-bundles.md`, and `config/agent-surface-capabilities.json`.

Milestone 14 is complete for its portability and audience scope. It defines the support boundary, records comparable status visibility for tracked surfaces, and keeps non-Continue support evidence-gated. Full live validation parity belongs to Milestone 17, and full install/configure/test implementation parity belongs to Milestone 19.

The non-Continue validation requirement is satisfied by the documented Cline read-only path in `docs/cline-readonly-validation.md` and the related sanitized evidence references. Beginner and team setup expectations are covered by `docs/setup-paths.md`, while approved-write readiness remains blocked for non-Continue surfaces until external verification proves scoped edits in the target surface.

| Surface | Surface type | Current validation level | Current pack support | Approved-write position | Notes |
| --- | --- | --- | --- | --- | --- |
| Continue | VS Code-compatible extension, VSCodium extension, and CLI | Approved-write ready for the validated local editor setup; CLI harness validated by tests | Supported first path plus CLI automation harness | Allowed only after the read-only, read-content, current-folder, and scoped write smoke tests pass in the user's actual setup | Existing config, install scripts, shared asset mode, validation docs, model testing, approved-write guidance, and `docs/continue-cli-model-testing.md` target Continue today. |
| Cline | VS Code-compatible editor agent plus CLI | Read-only validated and disposable write-smoke validated for generated Python sample with `qwen3-coder:30b` at 16k context; CLI harness validated by tests | Read/write validation guide, CLI automation guide, and sanitized evidence available | Real-project approved-write blocked | Use `docs/cline-readonly-validation.md`, `docs/cline-cli-model-testing.md`, and `examples/cline-readonly-validation.md`; a minimal README write smoke test passed, but real-project approved-write remains blocked until a realistic scoped edit passes external verification. |
| Aider | Git-aware CLI coding assistant | Generated-sample read-only, plan, write-smoke, and scoped-edit evidence; adapter tests validated | Supported isolated install, local-only Ollama config, health, and CLI test adapter | Blocked for real-project approved write | Use `scripts/setup-agent-surface.*`, `docs/aider-cli-model-testing.md`, and `examples/aider-validation.md`; explicitly approved non-generated-repository validation remains pending. |
| Kilo Code | VS Code-compatible editor agent | Configuration scaffolded; live generated-sample task execution blocked | The unified adapter generates a local-only `.kilo.local.json` and provides an npm install plan; the shared CLI wrapper has documented defaults | Blocked | The tested remote-Ollama provider reaches models, but current models returned generic greetings or configuration output instead of executing repository tasks or tools. |
| OpenCode | Terminal or IDE-oriented coding agent | Candidate; shared CLI wrapper scaffolded for future command validation | Shared CLI harness wrapper available, live validation pending | Blocked | Needs repository discovery, local model/tool behavior, and deterministic output verification against generated samples. |
| OpenHands | Self-hosted/platform-style agent runtime | Candidate | Not packaged yet | Blocked | More platform-like than editor-focused; needs workspace mount, sandbox, secret, and trust-boundary review before write mode. |
| Roo Code | Archived VS Code-compatible editor agent | Retired upstream | Historical wrapper metadata only; no new setup or validation work | Blocked | The official project was archived and the extension shut down in May 2026. Do not use it for new setups; evaluate a maintained successor separately. |

Candidate means "worth testing", not "approved for edits".

## Validation Levels

Use the same labels for every surface:

| Level | Meaning | Minimum evidence |
| --- | --- | --- |
| Candidate | The surface looks relevant, but this pack has not validated it yet. | Surface name, expected operating mode, and reason it may fit the pack. |
| Read-only validated | The surface can discover the opened repository, list files, read target files, and produce grounded output without modifying files. | Sanitized transcript or summary with exact inspected filenames, model/provider, OS, tool permission state, and failure signals. |
| Plan validated | The surface can produce implementation plans that preserve project constraints and pass deterministic output verification. | Read-only evidence plus a plan output checked for filename fidelity, no unsupported claims, rollback, tests, and docs impact. |
| Write smoke-test validated | The surface can make one minimal approved edit in a disposable repository and pass external verification. | Read-only evidence plus a minimal disposable-repo write test showing exactly one changed file through `git status`, `git diff --check`, and direct file-content verification outside the agent surface. |
| Approved-write ready | The surface can make realistic scoped edits only after approval, target the correct file, avoid duplicate writes, and pass external shell or Git verification. | Read-only, plan, and write-smoke evidence plus a realistic disposable-repo scoped edit showing changed files through `git status`, `git diff --check`, and direct file-content verification outside the agent surface. |

Do not mark a surface approved-write ready from model claims alone. Verify the changed files outside the agent surface.

## Evidence Fields

Every surface validation record should capture:

- Surface name and version.
- Editor, CLI, or runtime host.
- Operating system.
- Model name, provider, endpoint type, and whether the model supports tools in that surface.
- Config source: project-local assets, centralized shared assets, global config, or generated local config.
- MCP state, if any.
- Prompt or workflow tested.
- Tool permissions: read-only, ask-before-write, approved write, or unavailable.
- Exact files inspected or changed, sanitized when necessary.
- External verification commands and results.
- Failure signal, using the documented labels when possible.

## Portability Rules

- Keep reusable prompts, rules, templates, examples, and validation evidence independent of Continue-specific syntax where practical.
- Keep Continue-specific configuration in `.continue` until another surface has a tested packaging format.
- Do not weaken safety rules to support another tool.
- Do not commit private endpoints, local paths, tokens, raw transcripts, or customer/project names when recording validation evidence.
- Treat local model behavior as surface-specific. A model that works in one editor or CLI may fail in another.
- Treat approved-write support as surface plus model plus editor/runtime plus operating-system specific.

## Recommended Next Evaluation

Start with one active non-Continue surface in read-only mode. Cline has a recorded editor evidence path in `docs/cline-readonly-validation.md`; Aider has the first supported non-Continue setup adapter through `docs/aider-cli-model-testing.md`; shared CLI-surface screening is documented in `docs/agent-cli-surface-model-testing.md`. Roo Code is historical only because its upstream project is retired.

Use `docs/agent-surface-promotion-gates.md` before changing support status for any non-Continue surface.

Suggested order:

1. Generate a local sample repository with `docs/sample-repository-factory.md`.
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
