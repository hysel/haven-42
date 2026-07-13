# Model Scorecard

## Purpose

The model scorecard summarizes model readiness from committed evidence. It is not a benchmark and does not claim that a model is safe in every agent surface.

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
- Write-smoke validation does not imply real-project approved-write readiness.
- Candidate and partial-pass models stay conservative until stronger evidence exists.
- Models are scored from status labels, not from subjective claims.
- Speed and quality should be added only when validated evidence records them in a structured way.
