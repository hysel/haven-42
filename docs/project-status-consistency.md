# Project Status Consistency

Public maturity claims are security-relevant in Haven 42, so they must agree
across its documentation. A feature must not appear complete in one document
while remaining proposed, blocked, or unadmitted elsewhere.

`config/project-status-consistency.json` defines lifecycle classifications for
the complete Milestone 1 through 28 roadmap. `scripts/verify-project-status-consistency.py`
checks all 28 status rows in `ROADMAP.md` and the solution architecture review,
the active Milestone 20 through 28 summary in `README.md`, and the complete set
of detailed milestone headings in both `ROADMAP.md` and `TODO.md`. It also
checks unique companion markers in `TODO.md` and `PROJECT.md`.
The closed schema also names stale claims that must remain absent, including
the superseded statement that no hosted attestation has run.

The verifier is read-only. It has no network, process-launch, file-write, or
status-promotion authority. Missing rows, duplicate rows, missing companion
markers, lifecycle mismatches, malformed contracts, or an effect-enabling
contract fail closed. Unknown contract fields, incomplete milestone ranges,
invalid regular expressions, duplicate markers, and malformed marker groups
also fail closed. Hostile tests mutate representative documents and prove that
drift is rejected.

The contract classifies lifecycle state; it does not infer completion from test
counts and cannot promote a capability. Evidence and exit criteria remain
authoritative within each milestone.
