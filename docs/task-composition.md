# Bounded Task Composition

Haven 42 has a plan-only composition foundation for joining trusted read-only workflows into a small dependency graph. It validates intent and produces metadata-only intermediate artifact references. It does not execute a workflow, create a process, read or write a user file, contact a provider, use an approval grant, or modify a machine.

`config/task-composition-contract.json` is the default-deny contract. A request is limited to six uniquely named steps, five dependencies per step, exact known fields, and workflows that are both `uiReady` and `read-only` in `config/workflows.json`. Unknown workflows, write-capable workflows, arguments, additional fields, duplicate steps, missing dependencies, self-dependencies, and cycles are rejected.

`scripts/simulate-task-composition.py` performs deterministic topological planning. Cancellation can stop the plan before any step artifact is emitted. In-process results always set `executionAllowed` to false and explicitly report process creation, filesystem access, network access, and machine modification as false. The command-line entry point deliberately logs no request-derived plan data; it emits only a constant acceptance statement after validation.

`scripts/test-task-composition.py` covers ordered planning, metadata-only intermediate artifacts, cancellation, unknown fields, empty and oversized plans, write-workflow rejection, cycles, missing dependencies, and renderer-supplied arguments.

This foundation is intentionally narrower than executable composition. Future execution requires separately admitted workflow dispatch, typed intermediate artifact validation, per-effect approval authority outside the renderer, bounded retries, runtime cancellation, crash recovery, and cross-platform native evidence. None of those authorities are implied by a successful plan.
