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
5. Commit and push when tests pass.
6. After pushing, check the GitHub Actions status for the pushed commit with `gh run list --branch main --limit 5` and, when a new run starts, watch it to completion with `gh run watch <run-id> --exit-status`.
7. Report the commit id and hosted GitHub Actions result before moving on.
8. Continue to the next safe item only after the repo is clean again and the pushed commit status is known.

## Current Priority Order

1. Keep the guided menu and appendix aligned with the workflow registry.
2. Add registry-backed reports that reduce script choice for users.
3. Follow `docs/script-consolidation-plan.md` before consolidating repeated command families behind shared engines or dispatchers.
4. Expand evidence dashboard inputs without changing committed sanitized evidence defaults.
5. Document promotion gates for non-Continue agent surfaces.
6. Design the future UI only after script-level workflows stay stable.
