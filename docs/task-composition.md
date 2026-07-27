# Bounded Task Composition

Haven 42 has a plan-only composition foundation for joining trusted read-only workflows into a small dependency graph. It validates intent and produces metadata-only intermediate artifact references. It does not execute a workflow, create a process, read or write a user file, contact a provider, use an approval grant, or modify a machine.

`config/task-composition-contract.json` is the default-deny contract. A request is limited to six uniquely named steps, five dependencies per step, exact known fields, and workflows that are both `uiReady` and `read-only` in `config/workflows.json`. Engine-owned lifecycle fields distinguish a fresh plan, one bounded retry, and cancellation; retry identity must point to a different earlier composition and attempts cannot exceed two. Unknown workflows, write-capable workflows, arguments, renderer approvals, additional fields, duplicate steps, missing dependencies, self-dependencies, cycles, replayed retry identity, and inconsistent lifecycle state are rejected.

`scripts/simulate-task-composition.py` performs deterministic topological planning. Each planned edge uses an exact metadata-only intermediate record with source and consumer step IDs, classification, and validation state; no content field is admitted. Each step also reports an engine-owned approval posture that cannot grant execution. Cancellation can stop the plan before any step artifact is emitted. In-process results always set `executionAllowed` to false and explicitly report process creation, filesystem access, network access, and machine modification as false. The command-line entry point deliberately logs no request-derived plan data; it emits only a constant acceptance statement after validation.

`scripts/test-task-composition.py` covers 19 ordered-planning, typed metadata-only artifact, fresh/retry/cancel lifecycle, cancellation, unknown-field, size-bound, write-workflow, cycle, missing-dependency, attempt-bound, retry-replay, renderer-approval, and renderer-argument cases.

## Future Execution Admission Simulation

`config/task-execution-admission-contract.json` and
`scripts/simulate-task-execution-admission.py` define the next effect-free
boundary without connecting it to the planner or any dispatcher. The simulator
requires a registered UI-ready workflow, exact sorted effect disclosure,
bounded typed intermediate metadata, a digest-bound engine-issued approval
receipt description, and consistent fresh/retry/recover/cancel lifecycle
state. It accepts no arguments, content, path, URL, environment, token secret,
renderer-issued approval, or prohibited machine/service/driver/firewall/
credential effect.

Intermediate records must match the shared typed-artifact contract by artifact
type and media type and include only a bounded byte count, SHA-256, source step,
and validation status. They contain no content or path and are never read. The
approval scope digest binds the admission, composition, step, workflow,
attempt, full lifecycle state, sorted effects, and every intermediate metadata record. Expired,
revoked, used, wrong-issuer, wrong-audience, effect-mismatched, and replayed
receipt descriptions fail closed. Cancellation and blocked recovery require an
explicitly absent receipt with null metadata, preventing approval material from
crossing a non-execution path. Retry requires a completed prior attempt
with no possible effects. Recovery is visibly blocked whenever prior effects
may have occurred, and cancellation ends before approval evaluation.

The 49-case hostile suite verifies those boundaries. Even when every structural
precondition matches, `ApprovalAcceptedForExecution` and `ExecutionAllowed`
remain false; no approval is issued or consumed and no process, filesystem,
network, artifact, or machine effect occurs.

## Effect Journal Simulation

`config/task-effect-journal-contract.json` and
`scripts/simulate-task-effect-journal.py` model the next recovery boundary
without creating a durable journal or connecting to an executor. Every request
binds the exact admission, composition, step, workflow, attempt, scope digest,
approval receipt identifier, and sorted effect set. Each scenario record is
strictly shaped, timestamp ordered, sequence ordered, and chained by a SHA-256
over the exact admission binding, record metadata, and previous record digest.

The state model covers admission binding, claimed execution/effect starts,
claimed effect completion, cancellation before start, cancellation after a
claimed start, failure, completion, clean retry, and crash recovery. It rejects
missing admission records, chain substitution, cross-admission reuse, duplicate
or reordered events, effects outside the approved set, completion without every
effect record, records after a terminal event, retry after possible effects,
and recovery state that understates possible effects. Even a complete valid
chain is only an untrusted scenario: it does not prove an effect, authorize
retry or recovery, consume an approval, or permit execution. The 46-case suite
also confirms that no journal, artifact, file, process, or network effect
occurs.

This foundation remains intentionally narrower than executable composition.
Future execution still requires a separately admitted native opaque-token
issuer, workflow dispatcher, typed artifact reader, durable atomic effect
journal, bounded runtime cancellation/retry/recovery, rollback evidence, and
cross-platform native validation. None of those authorities are implied by
these simulators.
