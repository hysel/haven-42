# Model Scorecard

## Purpose

The model scorecard summarizes capability readiness from committed evidence. It
groups rows by the complete Capability Evidence Contract v2 key instead of
publishing one global readiness label per model.

Generate it locally:

```powershell
.\scripts\generate-model-scorecard.ps1 -OutputPath .\runtime-validation-output\model-scorecard.json -MarkdownOutputPath .\runtime-validation-output\model-scorecard.md
```

```bash
./scripts/generate-model-scorecard.linux.sh --output-path runtime-validation-output/model-scorecard.json --markdown-output-path runtime-validation-output/model-scorecard.md
```

## Inputs

- `config/evidence-catalog.tsv`
- `config/model-recommendations.tsv`

## Rules

- Approved-write readiness must come from explicit evidence.
- Surface, surface version, provider, OS, operation, and validation mode remain separate.
- Duplicate evidence for one key is aggregated to the most conservative status while provenance is retained.
- Write-smoke validation does not imply real-project approved-write readiness.
- Candidate and partial-pass models stay conservative until stronger evidence exists.
- Models are scored from status labels, not from subjective claims.
- Speed and quality should be added only when validated evidence records them in a structured way.
