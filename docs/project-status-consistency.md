# Project Status Consistency

Haven 42 treats public maturity claims as security-relevant evidence. A feature
must not appear complete in one document while remaining proposed, blocked, or
unadmitted elsewhere.

`config/project-status-consistency.json` defines lifecycle classifications for
Milestones 20 through 28. `scripts/verify-project-status-consistency.py` checks
the status tables in `ROADMAP.md`, `README.md`, and the solution architecture
review, plus unique companion markers in `TODO.md` and `PROJECT.md`.

The verifier is read-only. It has no network, process-launch, file-write, or
status-promotion authority. Missing rows, duplicate rows, missing companion
markers, lifecycle mismatches, malformed contracts, or an effect-enabling
contract fail closed. Hostile tests mutate representative documents and prove
that drift is rejected.

The contract classifies lifecycle state; it does not infer completion from test
counts and cannot promote a capability. Evidence and exit criteria remain
authoritative within each milestone.
