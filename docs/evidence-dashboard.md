# Evidence Dashboard

The evidence dashboard generator creates a local JSON and Markdown summary from the committed evidence catalog, agent surface capability matrix, and agent surface solution catalog.

Use it when deciding which model or agent surface is ready for a workflow:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/generate-evidence-dashboard.ps1 -OutputPath runtime-validation-output/evidence-dashboard.json -MarkdownOutputPath runtime-validation-output/evidence-dashboard.md -AsJson
```

The dashboard reports:

- Evidence row counts by readiness status, area, and surface.
- Known agent surface readiness from `config/agent-surface-capabilities.json`.
- Install/configure/test solution status from `config/agent-surface-solutions.json`.
- Distinct model names present in `config/evidence-catalog.tsv`.

For more detail on install/configure/test solution status by agent, use `docs/agent-surface-solutions.md`.

The generator is read-only except for the optional output paths. Output files belong in ignored local folders such as `runtime-validation-output/`; committed shared files stay sanitized and machine-neutral.
