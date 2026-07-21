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

All fields must match before evidence can drive a recommendation. Continue write evidence does not make the same model write-ready in Aider, OpenCode, or another agent surface. Read-only evidence does not prove planning, review, or write behavior.

## Conservative Aggregation

When multiple records share the complete key, consumers use the most conservative status and retain all unique evidence paths. They never select the first or most optimistic row.

Historical evidence with no recorded surface version uses `not-recorded`. It does not match a known future version automatically.

## Files

- `config/capability-evidence-contract.json` defines the machine-readable contract.
- `config/evidence-catalog.tsv` contains sanitized evidence records.
- `docs/evidence-catalog.md` documents fields, statuses, and maintenance rules.
- Recommendation, scorecard, and dashboard scripts consume the v2 fields.

## Promotion Rule

Add exact evidence for the target surface, version, provider, operating system, operation, and validation mode before promoting a model or enabling write roles. Missing evidence leaves the corresponding recommendation lane empty.
