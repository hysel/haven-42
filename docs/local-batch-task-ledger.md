# Recovered local-batch task ledger

The recovered conversation plan contains exactly 374 tasks in 18 phases,
numbered 0 through 17. The seven blocker classifications following the Phase 0
mapping instruction are one multiline task, matching the original count.

The authoritative task list is
`config/local-batch-task-ledger.tsv`. Every task has a stable phase-local ID,
status, blocker, evidence field, and note. The companion
`config/local-batch-task-ledger.json` records the source digest, schema,
allowed states, counts, and denied authority.

## Reconciliation rules

- `unverified` means the repository has not yet been checked one-to-one against
  that task. It does not mean complete or incomplete.
- `completed` requires repository-relative evidence or an immutable Git/test
  reference that proves the exact task outcome.
- `partial` records implemented foundations and the remaining gap.
- `blocked` requires a specific blocker category and evidence explaining why
  local progress cannot complete the task.
- `deferred` records an explicit owner or policy decision rather than an
  implementation failure.
- `not-started` is used only after the audit establishes that no qualifying
  implementation exists.
- Passing a broad gate cannot, by itself, mark an individual task complete.
- Classification grants no runtime, network, machine-change, packaging,
  signing, publication, or production authority.

The initial import deliberately left tasks `unverified`. Reconciliation is now
complete in phase order. Phases 0, 2, 3, and 4 are fully reconciled. The owner
deferred Phase 1's seven exact external-runtime licensing gaps on 2026-08-04
because Haven will not bundle or redistribute that provider runtime; the gaps
remain mandatory before any future redistribution. Phase 5 retains six exact
cryptographic-verifier gaps. Phases 6 and 7 are locally reconciled while all
image, audio, video, quantization, conversation-history, and folder-selection
candidates remain unpromoted. Phases 8 through 16 are locally reconciled;
retrieval, complex documents, controlled research, public-repository structure
validation, and additional agent-surface profiles retain their explicit
inactive or unpromoted boundaries. Phase 17 is locally reconciled after the
complete Windows PowerShell 5.1 gate passed 119 tests with zero skipped. The
final instruction remains `partial`: it required the work to remain
uncommitted and unpushed, but commit `3cab2d0` already existed locally when the
recovered ledger was created while the branch remains unpushed. This prevents
the ledger from repeating the earlier unsupported claim that every task was
complete.

Current reconciliation snapshot:

- 360 completed;
- 7 deferred by explicit owner decision;
- 7 partial;
- zero unverified;
- zero runtime, network, machine-change, package-promotion, release, or signing
  authority granted.

## Batch exit criteria

The recovered local batch is complete only when all of the following are true:

1. All 374 task records have been reconciled; none remains `unverified`.
2. Every `completed` record cites exact evidence, every `partial` record states
   its remaining work, and every blocked or deferred record names its blocker.
3. Locally executable work is complete; inactive foundations remain explicitly
   non-authoritative and are not presented as admitted runtime capability.
4. Roadmap, TODO, project status, evidence, security, privacy, architecture,
   package, and wiki-source statements agree with the task ledger.
5. Focused tests pass during each phase and the complete security and validation
   gate passes once against the final review tree.
6. The final diff and privacy boundary are reviewed without signing, release
   publication, installer activation, online update activation, or destructive
   machine effects.
7. The work remains unpushed until owner review and explicit permission.

The local preparation and validation criteria are now met. Seven owner-deferred
external-runtime license records and seven partial prerequisite/review records
remain explicit; they do not grant runtime, redistribution, signing, release,
or production authority. See `docs/roadmap-owner-decisions.md`.

## Phase inventory

| Phase | Tasks | Subject |
|---:|---:|---|
| 0 | 9 | Repository and roadmap closure control |
| 1 | 35 | Image-runtime licensing and supply chain |
| 2 | 20 | Haven 42 portable-package supply chain |
| 3 | 25 | Git, CI, and merge-readiness hardening |
| 4 | 19 | Offline installer and lifecycle foundations |
| 5 | 17 | Offline updater trust foundations |
| 6 | 30 | Windows image-provider preparation |
| 7 | 19 | Audio and video preparation |
| 8 | 16 | Quantization and model lifecycle preparation |
| 9 | 23 | Conversation history database |
| 10 | 20 | Explicit folder-selection foundation |
| 11 | 17 | PDF, Office, and OpenDocument preparation |
| 12 | 12 | Retrieval, embeddings, and knowledge-library preparation |
| 13 | 33 | Controlled web research |
| 14 | 16 | Public real-repository validation |
| 15 | 13 | Additional agent-surface profiles |
| 16 | 22 | Documentation and wiki reconciliation |
| 17 | 28 | Security and validation gate |
