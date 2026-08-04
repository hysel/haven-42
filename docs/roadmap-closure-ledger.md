# Roadmap closure ledger

The machine-readable ledger at `config/roadmap-closure-ledger.json` prevents unfinished work from being lost when implementation moves between milestones. It classifies every unchecked item in `TODO.md` exactly once.

The categories distinguish work that genuinely depends on new evidence, an
external machine or platform, a suitable repository, an upstream release,
signing or release authority, successful admission of an earlier gate, or a
runtime/external gate whose local foundation is now complete. Classification
does not mark an item complete and grants no runtime, network, package,
machine-change, signing, or release authority.

The parent-roadmap ledger leaves no unchecked `TODO.md` item unclassified.
That statement does not claim the finer-grained recovered conversation plan is
complete. Its separate 374-task evidence audit is now in progress, and any
`unverified` task remains unresolved until reconciled one to one.

The original blocker vocabulary maps to the parent ledger as follows:

- `locally completable`: currently zero parent items; newly discovered work
  must remain open and be added explicitly;
- `locally implementable but inactive`: prerequisite-dependent items and local
  foundations that still require runtime or external admission;
- `external-machine dependent`: `external-machine-or-platform`;
- `external-service dependent`: recorded only when a service is the actual
  blocker rather than being folded into signing or release policy;
- `upstream blocked`: `upstream-or-unadmitted-runtime`;
- `owner deferred`: conditional evidence and owner/repository-input items; and
- `signing/release prohibited`: `signing-release-or-production-policy`.

This mapping is a status classification, not authority to perform an effect.

`scripts/test-roadmap-closure-ledger.py` hashes normalized checkbox text and fails if an item is added, removed, edited, duplicated, or omitted without updating the ledger. This makes roadmap drift visible before a commit instead of after a merge.

The separate recovered conversation plan is tracked task by task in
`config/local-batch-task-ledger.tsv`; see
`docs/local-batch-task-ledger.md`. Its validator preserves all 374 stable task
records and requires evidence before any record can be marked complete. The
roadmap ledger classifies current open parent items, while the recovered-task
ledger audits the finer-grained work that originally appeared only in chat.
