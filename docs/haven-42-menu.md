# Haven 42 Menu

The Haven 42 menu is the primary human-facing navigation for setup, engineering,
validation, evidence, cleanup, and release work. For general local chat, launch the
local web application described in `docs/local-web-mvp.md`.

The menu groups repository scripts by what you want to do:

- First-time setup.
- Health check.
- Model choice.
- Install or configure an agent.
- Validate a model or agent.
- Review evidence.
- Cleanup local artifacts.
- Release readiness.

Generate the menu on Windows:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/show-haven-42-menu.ps1 -MarkdownOutputPath runtime-validation-output/haven-42-menu.md -OutputPath runtime-validation-output/haven-42-menu.json -AsJson
```

Generate the menu on Linux or macOS:

```bash
./scripts/show-haven-42-menu.linux.sh --markdown-output-path runtime-validation-output/haven-42-menu.md --output-path runtime-validation-output/haven-42-menu.json --as-json
./scripts/show-haven-42-menu.macos.sh --markdown-output-path runtime-validation-output/haven-42-menu.md --output-path runtime-validation-output/haven-42-menu.json --as-json
```

Start with this menu before opening individual script docs. The generated agent surface
snapshot comes from `config/agent-surface-solutions.json` and includes only surfaces
whose `showInDefaultMenu` policy is enabled. Documentation-only candidates may remain in
the detailed solution catalog without appearing as setup choices; failed and retired
integrations are removed entirely.

The Linux and macOS wrappers use the native Python 3 renderer and do not
require PowerShell.

For the complete workflow list, including safety levels, commands, and reference docs,
use `docs/workflow-chooser.md`.

For script parameters and troubleshooting, use `docs/script-reference-appendix.md`.

For each agent surface's install, configuration, and test maturity, use
`docs/agent-surface-solutions.md`.
