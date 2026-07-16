# Script Consolidation Plan

## Purpose

This plan keeps the command surface small for end users while preserving tested scripts for maintainers and automation.

The goal is not to hide behavior. The goal is to move repeated behavior into shared engines, registries, or dispatchers, then keep only thin wrappers where they make the pack easier to use on a specific platform or agent surface.

## Principles

- Treat `config/workflows.json`, `config/workflow-envelope-contract.json`, `scripts/invoke-workflow.ps1`, and the cross-platform `scripts/invoke-workflow.*.sh` wrappers as the stable workflow API for menus, reports, and the future UI.
- Keep repeated business logic in shared engines instead of duplicating it across surface-specific scripts.
- Keep thin wrapper scripts when they improve beginner usability, cross-platform ergonomics, or agent-specific command naming.
- Keep individual script docs in `docs/script-reference-appendix.md` for maintainers, troubleshooting, and automation authors.
- Do not remove a script until README links, workflow registry entries, appendix coverage, tests, release readiness checks, and migration notes agree.
- Do not promote a planned or blocked agent surface while consolidating scripts; promotion still depends on evidence in the surface catalogs.

## Current Families

| Script family | Current direction | Boundary |
| --- | --- | --- |
| Workflow discovery and navigation | Consolidated around `config/workflows.json`, `scripts/OnboardingGuidance.psm1`, `scripts/onboarding-guidance.shared.sh`, the three stable public onboarding commands, and the workflow dispatcher. | Shared mechanics live behind the public commands. Keep registry IDs stable and expose new user flows through the registry first. |
| Validation and release gates | Keep explicit entry points such as `scripts/validate-pack.ps1`, `scripts/test-pack.ps1`, and `scripts/test-release-readiness.ps1`. | These are safety gates and should remain easy to run directly and through the dispatcher. |
| Runtime validation | Keep `scripts/generate-runtime-context.ps1`, `scripts/run-runtime-validation.ps1`, and `scripts/verify-runtime-output.ps1` as separate workflow steps. | Consolidate only report parsing or shared evidence ingestion, not the user-visible validation stages. |
| Model profiling and recommendation | Keep shared recommendation data and config generation as the engine behind local model choices. | Future agent surfaces should reuse the recommendation model instead of adding independent model-selection logic. |
| Agent CLI surface testing | Keep `scripts/test-agent-cli-surface-models.ps1`, shell equivalents, and `config/agent-cli-surface-defaults.json` as the shared engine/default catalog for active Aider, Kilo Code, and OpenCode wrappers. Roo Code metadata is historical only. | PowerShell and Bash surface wrappers should only set surface keys, overrides, or platform-friendly arguments. |
| Continue and Cline validation | Keep separate wrappers while config locations, CLI behavior, and read/write safety checks differ. | Consolidate shared assertions only after behavior matches in evidence. |
| Install, cleanup, and package scripts | Keep direct scripts for safety-sensitive operations and release automation. | Add dispatcher entries and reports, but avoid hiding dry-run and approval boundaries. |

## Consolidation Sequence

1. Add or update the workflow registry entry before changing a user-facing command.
2. Add documentation and tests that describe the intended script boundary.
3. Move repeated logic into a shared engine only when the old and new paths can be tested side by side.
4. Keep wrapper scripts thin and deterministic.
5. Deprecate a script in docs before removing it from the repository.
6. Remove a script only at a release boundary with validation, tests, appendix updates, and changelog coverage.

## Implemented Consolidations

### Onboarding And Navigation

The beginner setup plan, agent pack menu, and workflow chooser retain their
documented entry points. Their PowerShell implementations now share:

- catalog loading and validation;
- workflow lookup;
- platform-specific command rendering;
- JSON and Markdown output handling; and
- output-directory creation.

Their Linux/macOS `.shared.sh` entry points now delegate argument parsing and
view selection to one native dispatcher. Full report rendering still requires
PowerShell; replacing that fallback with a native implementation remains
tracked work and is not represented as complete cross-platform parity.

## Do Not Consolidate Yet

- Surface-specific config generators for planned or blocked agent surfaces.
- Kilo Code live task and tool behavior beyond its documented command, install plan, and local-only configuration. Current remote-Ollama model tests reached the provider but did not execute repository tasks. OpenCode remains subject to non-generated-repository validation. Evaluate a maintained Roo Code successor separately.
- Local model pull, unload, or deletion behavior without explicit user intent.
- Cleanup operations that are not covered by dry-run output and tests.
- Any behavior that would require storing private hostnames, IP addresses, usernames, tokens, local paths, or raw hardware reports.

## Done Criteria

A consolidation change is done when:

- Existing documented entry points still work or have an explicit migration note.
- `docs/script-reference-appendix.md`, `docs/workflow-registry.md`, and README links match the current command surface.
- `scripts/test-pack.ps1` passes.
- `scripts/validate-pack.ps1` passes.
- The roadmap and TODO list state whether consolidation planning or implementation is complete.
