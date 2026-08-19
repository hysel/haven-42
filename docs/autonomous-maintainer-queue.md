# Autonomous Maintainer Queue

This queue captures work that can usually be done without asking for more product input.

Use it after the repository is clean, tests are passing, and the requested direction is already represented in `TODO.md`, `ROADMAP.md`, `config/workflows.json`, or an existing docs gap.

## Safe Without Prompt

| Task | Boundary | Done when |
| --- | --- | --- |
| Keep workflow docs aligned | Update README, workflow docs, appendix, and tests when registry-backed workflows change. | `scripts/test-pack.ps1` passes and docs reference the guided menu before script details. |
| Keep solution catalogs aligned | Update surface matrices, solution catalog docs, dashboard/menu output, and tests when evidence status changes. | Planned or blocked surfaces are not promoted accidentally. |
| Improve generated reports | Add read-only JSON or Markdown fields sourced from committed catalogs. | Generated output stays sanitized and schema changes are tested. |
| Tighten validation guardrails | Add deterministic checks for leaks, stale docs, missing workflow coverage, or broken references. | The check fails for the bad state and passes for the current repository. |
| Audit evidence freshness | Recompute exact repository input bindings and run publication preflight without changing runtime, model, hardware, or product policy. | Stale, missing, duplicate, escaped, or incomplete evidence remains visibly blocked. |
| Keep recommendation explanations reproducible | Regenerate synthetic recommendation matrices and verify every rejection reason against committed policy and evidence. | No report changes defaults, downloads a model, or infers support across platforms. |
| Keep coding-agent gates explicit | Generate not-run cells for new model/surface/version combinations and audit historical results without claiming current readiness. | Every gate is passed, failed, blocked, or not-run; no missing gate becomes a recommendation. |
| Refine appendix/reference docs | Add exact command references for existing workflows while keeping beginner docs intent-based. | Every workflow remains covered by `docs/script-reference-appendix.md`. |
| Plan script consolidation | Update `docs/script-consolidation-plan.md`, workflow docs, and tests before changing script families. | Shared engines, thin wrappers, and no-consolidate-yet cases are documented. |
| Update roadmap and TODO state | Mark completed, tested work as done and keep remaining work concrete. | Roadmap, TODO, README, and tests agree. |

## Needs Explicit Input

- Validating against a private or real target repository.
- Running a local model test that may pull, unload, or delete models unless the user has already asked for that flow.
- Installing dependencies, extensions, or agent surfaces on the user machine.
- Changing approved-write behavior for real project files.
- Promoting a planned or blocked agent surface to supported.
- Adding a new network-dependent default.

## Operating Loop

1. Start with `git status --short --branch`.
2. Choose the smallest pending item that is already supported by roadmap or TODO.
3. Prefer registry-backed docs, generators, and tests over one-off prose.
4. Run the narrow command first, then `scripts/test-pack.ps1`.
5. Commit and push when tests pass; record the full pushed commit SHA.
6. Run `scripts/verify-hosted-ci.ps1 -CommitSha <full-sha>` or the native Linux/macOS equivalent. The verifier must find the exact-SHA run, use `gh run watch --exit-status`, and check all required hosted jobs.
7. If verification fails, inspect the automatically retrieved failed logs, fix the issue, rerun local validation, push the new commit, and verify the new SHA.
8. Report `Pushed`, `CI running`, `CI passed`, or `CI failed` with the exact commit SHA and run URL. Never call a push successful before `CI passed`.
9. Continue to the next safe item only after the repository is clean and the exact pushed commit has a known hosted conclusion.

See `docs/hosted-ci-verification.md` for the enforced contract and platform commands.

## Current Priority Order

1. Keep the guided menu and appendix aligned with the workflow registry.
2. Add registry-backed reports that reduce script choice for users.
3. Follow `docs/script-consolidation-plan.md` before consolidating repeated command families behind shared engines or dispatchers.
4. Expand evidence dashboard inputs without changing committed sanitized evidence defaults.
5. Document promotion gates for non-Continue agent surfaces.
6. Design the future UI only after script-level workflows stay stable.
