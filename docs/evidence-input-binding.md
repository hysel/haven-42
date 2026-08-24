# Evidence input binding

Each Haven 42 result should identify the exact catalogs, policies, validators,
harnesses, and runtime artifacts used for the run. A result without those
bindings may still be a useful historical observation, but it is not current
certification evidence.

Use `scripts/alpha2-evidence-binding.py` to generate a small JSON binding beside
a sanitized evidence export. Inputs use `role=hash-mode=repository/path`, for
example:

```text
python scripts/alpha2-evidence-binding.py \
  --evidence-id example-run \
  --input model-catalog=canonical-json=config/alpha-2-model-version-inventory.json \
  --input validator=file-bytes=scripts/alpha2-linux-model-validation.py
```

The resulting structure is:

```json
{
  "schemaVersion": 1,
  "kind": "haven42-evidence-input-binding",
  "evidenceId": "example-run",
  "inputs": [
    {
      "role": "model-catalog",
      "path": "config/alpha-2-model-version-inventory.json",
      "hashMode": "canonical-json",
      "sha256": "<lowercase SHA-256>"
    },
    {
      "role": "validator",
      "path": "scripts/alpha2-linux-model-validation.py",
      "hashMode": "file-bytes",
      "sha256": "<lowercase SHA-256>"
    }
  ]
}
```

Run `python scripts/alpha2-evidence-freshness.py --binding <file>`. The checker
reports `fresh` only when every declared input still matches. It always leaves
product admission false: freshness is necessary evidence, not proof that the
underlying test passed or that a model should be promoted.
