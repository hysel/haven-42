# Publishing hardware qualification evidence

This workflow turns a completed lab campaign into a human-readable result
without exposing the lab or overstating what was tested.

## 1. Export only the evidence boundary

Export the sanitized profile, event timeline, task/soak summaries, and board
telemetry described by
`config/alpha-2-hardware-qualification-evidence-contract.json`. Do not export
host names, addresses, accounts, keys, machine identifiers, or raw model text.

## 2. Build the exact environment result

Run `scripts/alpha2-hardware-qualification-evidence.py`. The importer refuses
unexpected models, changed execution order, incomplete results claiming
completion, malformed telemetry, unknown profile fields, and missing failure
cells. An unfinished campaign remains `in-progress-local-review-only`.

## 3. Compare environments

Run `scripts/alpha2-hardware-cross-os-report.py` only for the same accelerator
and qualification profile. A missing result is `not-run`, not a failure or a
platform divergence. Results never transfer automatically between operating
systems, drivers, runtimes, or editor surfaces.

## 4. Produce the review copy

Run `scripts/alpha2-hardware-qualification-report.py` to create the readable
comparison and failure-triage bundle. Without `--allow-incomplete`, it refuses
to render an unfinished comparison. That override is for ignored local review
only and must not be used to publish final evidence.

Older records that did not capture exact validator, orchestrator, and runtime
artifact bindings may be passed through
`scripts/alpha2-hardware-result-normalizer.py` for a local comparison preview.
Normalization never upgrades them to complete evidence. Run
`scripts/alpha2-hardware-report-preflight.py` before publication; every cell
must be complete, freshly bound, and free of not-run comparison cells.

## 5. Review before publishing

Confirm the exact environment, artifact and runtime digests, failure cells,
soak duration, power scope, omissions, and privacy declarations. Decide
separately whether the evidence justifies a support label, default, runtime, or
download-policy change; the evidence itself authorizes none of those actions.

## 6. Synchronize the documentation journey

After owner approval, add the final result and human report to the main
repository, add exact claims to the evidence catalog, and regenerate the
engineering evidence pointers. If generated wiki content changes, run the wiki
synchronization check, review both repositories for drift and private data,
commit and push the wiki first, then validate and publish the main repository.

Keep the public wiki navigation small. Detailed hardware records belong behind
the Engineering and Validation Index rather than in the primary user sidebar.
