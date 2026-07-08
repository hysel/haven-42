# Evidence Catalog

The evidence catalog is the compact index of what has actually been validated.
Use it to avoid turning one successful test into a broader claim than the
project can support.

The machine-readable catalog lives at `config/evidence-catalog.tsv`.

## Fields

| Field | Meaning |
| --- | --- |
| `area` | Validation area, such as model tool use, editor surface, installer profile, or language support. |
| `subject` | The specific model, surface, script, sample, or workflow being summarized. |
| `surface` | The tool or execution surface used for validation. |
| `os` | Operating system or platform scope. Use `Cross-platform` only for static checks or tests that do not depend on a single OS. |
| `model` | Model used for the evidence, or `N/A` when model behavior is not part of the check. |
| `status` | Conservative status label. Do not upgrade a status unless the linked evidence supports it. |
| `evidence` | Repository-relative path to the source evidence or validating script. |
| `notes` | Short sanitized note that explains limits or follow-up work. |

## Status Labels

| Status | Meaning |
| --- | --- |
| `candidate-only` | Useful for consideration only; not validated for local tool use. |
| `plan-review-candidate` | Useful for generated-sample planning or review workflows, but not write-ready. |
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
- Treat online discovery as candidate-only until local model and editor validation passes.
- Prefer adding a conservative entry with limitations over leaving validation knowledge scattered in notes.
