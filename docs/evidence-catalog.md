# Evidence Catalog

The evidence catalog is the compact index of what has actually been validated.
Use it to avoid turning one successful test into a broader claim than the
project can support.

The machine-readable catalog lives at `config/evidence-catalog.tsv`.

Its machine-readable definition lives at
`config/capability-evidence-contract.json`.

## Capability Evidence Contract v2

Version 2 makes readiness a capability claim instead of a model-wide claim.
The complete key combines surface, surface version, provider, model, operating
system, operation, and validation mode.

Consumers must match every key field. A write result from Continue cannot make
the same model write-ready in Cline, Aider, or another surface. A read result
cannot become plan, review, or write evidence. Windows evidence cannot be
silently inherited on Linux or macOS.

When duplicate rows have the same complete key, consumers select the most
conservative status and retain every unique evidence path. They must not pick
the first or most optimistic row.

## Fields

| Field | Meaning |
| --- | --- |
| `schema_version` | Contract version. Current rows must use `2`. |
| `area` | Validation area, such as model tool use, editor surface, installer profile, or language support. |
| `subject` | The specific model, surface, script, sample, or workflow being summarized. |
| `surface` | The tool or execution surface used for validation. |
| `surface_version` | Exact tested surface version, `not-recorded` when historical evidence omitted it, or a static test identifier. |
| `provider` | Model provider used for validation, or `N/A` for non-model checks. |
| `os` | Operating system or platform scope. Use `Cross-platform` only for static checks or tests that do not depend on a single OS. |
| `model` | Model used for the evidence, or `N/A` when model behavior is not part of the check. |
| `operation` | Exact tested capability, such as read, plan, scoped write, or test harness execution. |
| `validation_mode` | How validation ran, such as editor agent, generated sample, static, or automated tests. |
| `status` | Conservative status label. Do not upgrade a status unless the linked evidence supports it. |
| `evidence` | Repository-relative path to the source evidence or validating script. |
| `notes` | Short sanitized note that explains limits or follow-up work. |

## Status Labels

| Status | Meaning |
| --- | --- |
| `candidate-only` | Useful for consideration only; not validated for local tool use. |
| `plan-review-candidate` | Useful for generated-sample planning or review workflows, but not write-ready. |
| `plan-validated` | The exact capability key produced an evidence-based plan without writing files. |
| `review-validated` | The exact capability key completed the recorded review operation. |
| `read-only-tool-validated` | Read-only tool use worked in the stated surface and environment. |
| `read-only-cli-validated` | CLI/context validation worked, but editor Agent behavior is not proven. |
| `write-smoke-validated` | A minimal disposable-repository write smoke test passed with external Git and file-content verification, but broad approved-write readiness is not claimed. |
| `approved-write-ready` | A scoped write test passed and was verified outside the agent surface. |
| `static-validated` | Static file/script validation passed without model execution. |
| `validated-by-tests` | Repository tests enforce the behavior. |
| `partial-pass` | Useful evidence exists, but recorded limitations or follow-up remain. |

## Rules

- Keep entries sanitized: no private endpoints, private paths, usernames, hostnames, customer names, or raw transcripts.
- Link to committed evidence only.
- Do not mark a model or surface approved-write ready unless external file or git verification passed.
- Use `not-recorded` instead of inventing a historical surface version.
- Do not use `Cross-platform` for a model run that occurred on only one operating system.
- Do not infer one operation from another, even when the model is generally capable.
- Treat online discovery as candidate-only until local model and editor validation passes.
- Prefer adding a conservative entry with limitations over leaving validation knowledge scattered in notes.
