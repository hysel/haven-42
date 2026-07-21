# Workflow Chooser

The workflow chooser is a complete registry-backed report for users and maintainers who need to compare all stable workflows without reading every script. It is generated from `config/workflows.json`.

Start with `docs/haven-42-menu.md` for the short guided path. Use this chooser when you need the full workflow list with safety levels, commands, and reference docs.

Generate the chooser on Windows:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/show-workflow-chooser.ps1 -MarkdownOutputPath runtime-validation-output/workflow-chooser.md -OutputPath runtime-validation-output/workflow-chooser.json -AsJson
```

Generate the chooser on Linux or macOS:

```bash
./scripts/show-workflow-chooser.linux.sh --markdown-output-path runtime-validation-output/workflow-chooser.md --output-path runtime-validation-output/workflow-chooser.json --as-json
./scripts/show-workflow-chooser.macos.sh --markdown-output-path runtime-validation-output/workflow-chooser.md --output-path runtime-validation-output/workflow-chooser.json --as-json
```

The Linux and macOS wrappers use the native Python 3 renderer and do not
require PowerShell.

The report includes:

- Workflow ID.
- Category.
- Safety level.
- UI readiness.
- Platform-specific command.
- Reference documentation.
- Link back to `docs/script-reference-appendix.md`.

The generator is read-only except for optional output paths.
