# Conversation History Activation Readiness

Status: blocked; Private session remains the only effective mode.

The checked-in readiness policy turns the remaining saved-history work into
eight explicit gates. The evaluator reads only that fixed repository policy,
verifies every referenced evidence file, and emits a bounded public report. It
does not accept a caller-selected path and has no database, filesystem-write,
credential-store, browser-storage, process, network, provider, runtime, or UI
authority.

Current result:

```text
status: blocked
effective mode: private-session
open gates: 8
activation allowed: false
```

The 31-check hostile suite rejects extra fields, missing or reordered gates,
unknown statuses, traversal or missing evidence paths, effect authority, and
an inconsistent or overstated ready/activated state. Even a synthetic policy in which every
gate passes produces only `candidate-ready-not-activated`; a separate reviewed
release decision would still be required before any runtime or UI activation.

This is policy evidence, not encryption or product certification. It does not
open or create a database, persist a key, handle user content, or make saved
history available in Haven 42.
