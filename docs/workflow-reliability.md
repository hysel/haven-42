# Workflow Reliability

Haven 42 workflow execution fails closed when completion is uncertain. `config/workflow-reliability-contract.json` contains the versioned rules, which extend workflow-envelope schema version 1 without silently changing it.

Every executable request has a bounded timeout and exactly one terminal event. Cancellation is bound to the request and session, starts cooperatively, and may escalate only against a process created and tracked by that request. Haven 42 never terminates unrelated applications to make capacity available.

Retries are conservative. Reads may retry only recognized transient failures, with a maximum of three attempts. Writes do not retry by default. A retried effect needs an idempotency key covering the session, workflow, request, and effect digest. A known completed effect returns its prior result; an ambiguous effect stops for manual recovery.

Parent cancellation propagates to owned children, orphan execution is forbidden, and child failures are aggregated explicitly. Resume is opt-in, version-bound, approval-bound, and allowed only at a verified boundary. Checkpoints exclude secrets, raw output, endpoints, and machine-specific values.

Required tests cover timeout, cooperative cancellation, owned-process escalation, unrelated-process preservation, transient read retry, write non-retry, duplicate-effect replay, ambiguous effects, parent/child cancellation, event ordering, and resume-version or approval mismatch.
