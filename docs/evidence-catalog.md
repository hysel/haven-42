# Evidence Catalog

The evidence catalog indexes what has actually been validated. Use it to keep
one successful test from becoming a broader claim than the project supports.

The machine-readable catalog lives at `config/evidence-catalog.tsv`.

The v2 aggregation rules live at
`config/capability-evidence-contract.json`.

Every catalog row also has a generated, plain-language wiki page. Browse them
through [[Evidence Record Index|Evidence-Record-Index]]. The stable mapping
between claims and pages lives in `config/evidence-page-registry.json`.

Regenerate the pages and registry after changing the catalog:

```text
python scripts/generate-evidence-wiki-pages.py
```

Check that committed pages are current without changing files:

```text
python scripts/generate-evidence-wiki-pages.py --check
```

The automatic-updates work on the roadmap may read this registry in the future.
The registry cannot start a download, install a runtime, promote a model, or
change a default. Any future updater must still require signed update metadata,
an exact capability match, user policy, compatibility and health checks, and
rollback.

## Capability Evidence Contract v2

Version 2 records readiness for a specific capability rather than an entire
model. Its complete key combines surface, surface version, provider, model,
operating system, operation, and validation mode.

Consumers must match every key field. A write result from Continue does not make
the same model write-ready in Aider, OpenCode, or another surface. A read result
does not prove plan, review, or write behavior. Windows results do not transfer
to Linux or macOS.

When duplicate rows share a complete key, consumers use the most conservative
status and retain every unique evidence path rather than selecting the first or
most optimistic row.

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
- Do not add failed agent candidates to this active catalog. Record only a concise sanitized decision in the removed-integrations documentation and keep detailed evaluation artifacts outside the shipped repository.
- Do not mark a model or surface approved-write ready unless external file or git verification passed.
- Use `not-recorded` instead of inventing a historical surface version.
- Do not use `Cross-platform` for a model run that occurred on only one operating system.
- Do not infer one operation from another, even when the model is generally capable.
- Treat online discovery as candidate-only until local model and editor validation passes.
- Prefer adding a conservative entry with limitations over leaving validation knowledge scattered in notes.
