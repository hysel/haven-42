# Agent Surface Promotion Gates

This document defines what a non-Continue agent surface must prove before the pack can promote install, configure, test, or approved-write support.

Continue remains the supported first path. Other surfaces can move forward only with sanitized evidence recorded in `config/evidence-catalog.tsv`, `config/agent-surface-solutions.json`, and a surface-specific evidence document.

## Milestone 17 Cline And Aider Completion Basis

Milestone 17 has complete Cline and Aider evidence for the current documented scope because at least one non-Continue surface has sanitized read-only validation evidence, Cline has disposable write-smoke evidence, Aider has generated-sample read-only, write-smoke, and scoped-edit evidence, and real-project approved-write remains blocked until explicit non-generated repository validation passes.

Milestone 17 remains partial for full tracked-surface compatibility because Kilo Code and OpenHands do not yet have live validation evidence, and OpenCode has generated-sample-only evidence. Roo Code is retired upstream and not an active target.

Kilo Code remains a live-validation blocker. Its documented command shape, native-Ollama project-local configuration, explicit `code` agent selection, and isolated user-profile execution are scaffolded and statically tested. Renewed generated-sample diagnostics found raw tool-schema-like output from `qwen3.5:9b` and bounded-read non-completion from larger coding models, so no model evidence supports promotion. Roo Code is historical only because its upstream project is retired. OpenCode's generated-sample evidence is recorded separately and still requires non-generated-repository validation.

## Shared Gates

| Gate | Required evidence |
| --- | --- |
| Candidate tracked | Surface name, operating mode, expected local model path, and reason it fits the pack. |
| Read-only validated | The surface discovers the opened repository, lists files, reads specific files, and produces grounded output without modifying files. |
| Plan validated | The surface produces a plan that passes deterministic filename, rollback, test, and unsupported-claim checks. |
| Write smoke validated | The surface changes one minimal file in a disposable repository and passes external `git status`, `git diff --check`, and direct file-content verification. |
| Scoped edit validated | The surface changes only expected source/test files in a generated or disposable repository and passes external behavior verification. |
| Install supported | The install path is repeatable, documented, dry-run safe where possible, and does not assume private machine state. |
| Configure supported | The local model config format is documented, generated output is local-only, and private endpoints stay out of committed files. |
| Approved-write ready | Read-only, plan, smoke, and scoped-edit gates pass for the intended surface, model, OS, and permission mode. |

## Surface-Specific Next Gates

| Surface | Current position | Next gate |
| --- | --- | --- |
| Cline | Read-only and minimal disposable write-smoke evidence exists. A realistic Devstral scoped-edit attempt passed exact file scope and behavior but failed whitespace validation because it introduced mixed line endings; its repair attempt did not complete. | Repeat the generated-sample scoped edit and require external changed-file, behavior, `git diff --check`, line-ending, and unexpected-file verification to pass together. |
| Aider | CLI read-only, disposable write-smoke, and richer generated-sample scoped edits exist. | Explicitly approved non-generated repository validation before real-project approved-write claims. |
| Roo Code | Upstream retired. | Do not promote or add new validation; evaluate a maintained successor separately. |
| Kilo Code | Shared wrapper, npm install plan, native-Ollama project-local config generator, explicit `code` agent selection, and isolated user-profile execution exist; renewed live task execution is blocked. | Resolve model/surface tool-protocol compatibility, then rerun generated-sample read-only, write-smoke, and scoped-edit tests one model at a time, unloading each model after testing. |
| OpenCode | Installed CLI plus generated-sample read/write-smoke and constrained scoped-edit evidence exists for Devstral Small 2 24B. | Run explicitly approved non-generated repository validation. |
| OpenHands | Platform-agent candidate is blocked for install/config generation. | Use the isolated generated-sample boundary in `docs/openhands-validation-boundary.md` before any validation automation. |

## Promotion Rules

Aider and OpenCode have passed the install-supported and configure-supported gates through `scripts/setup-agent-surface.*`. That promotion does not satisfy the separate real-project approved-write gate.

- Do not promote `install.status` or `configure.status` to `supported` without install/config evidence for that surface.
- Do not promote `test.status` to `validated` without a repeatable harness or documented manual validation path.
- Do not promote real-project approved-write support from generated-sample evidence alone.
- Do not reuse Continue config-generation status for another surface.
- Keep private endpoints, usernames, local paths, tokens, private repositories, and raw transcripts out of committed evidence.

- For OpenHands, follow `docs/openhands-validation-boundary.md`; generated-sample validation must remain isolated from host credentials, unrelated directories, privileged containers, and unrestricted network access.

## Evidence Update Checklist

- Update `config/evidence-catalog.tsv`.
- Update `config/agent-surface-solutions.json`.
- Update `docs/agent-surface-solutions.md` if the summary status changes.
- Update the relevant surface evidence doc or example.
- Run `scripts/test-pack.ps1`.
