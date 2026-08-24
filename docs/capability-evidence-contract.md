# Capability Evidence Contract

Capability Evidence Contract v2 prevents one successful model test from becoming a broader compatibility claim.

## Complete Key

Every capability record is keyed by:

- Agent surface
- Surface version
- Provider
- Model
- Operating system
- Operation
- Validation mode

Every field must match before a recommendation can use the result. A Continue write result does not make the same model write-ready in Aider, OpenCode, or another agent surface. A read-only result does not prove planning, review, or write behavior.

## Conservative Aggregation

When multiple records share the complete key, consumers use the most conservative status and retain all unique evidence paths. They never select the first or most optimistic row.

Historical results with no recorded surface version use `not-recorded` and do not automatically match a known future version.

## Files

- `config/capability-evidence-contract.json` defines the machine-readable rules.
- `config/evidence-catalog.tsv` contains sanitized evidence records.
- `docs/evidence-catalog.md` documents fields, statuses, and maintenance rules.
- Recommendation, scorecard, and dashboard scripts consume the v2 fields.

## Promotion Rule

Before promoting a model or enabling write roles, add exact results for the target surface, version, provider, operating system, operation, and validation mode. If any result is missing, the corresponding recommendation lane stays empty.
