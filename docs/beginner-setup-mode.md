# Beginner Setup Mode

> **Advanced contributor tool:** This page describes a command-line planning
> utility for repository contributors. It is not the beginner setup shown in
> the Haven 42 application. New users should follow the wiki
> [Quick Start](Quick-Start) instead.

Beginner setup mode builds an ordered local setup plan from the workflow registry.

It generates a plan; it does not install anything. The output shows which
commands to run, which workflow each command uses, and where the workflow moves
from read-only checks to a write preview.

Use `docs/setup-paths.md` to compare this quick path with team or enterprise
review and audit requirements.

Generate the Windows plan:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/get-beginner-setup-plan.ps1 -MarkdownOutputPath runtime-validation-output/beginner-setup-plan.md -OutputPath runtime-validation-output/beginner-setup-plan.json -AsJson
```

Generate a Linux or macOS plan:

```bash
./scripts/get-beginner-setup-plan.linux.sh --markdown-output-path runtime-validation-output/beginner-setup-plan.md --output-path runtime-validation-output/beginner-setup-plan.json --as-json
./scripts/get-beginner-setup-plan.macos.sh --markdown-output-path runtime-validation-output/beginner-setup-plan.md --output-path runtime-validation-output/beginner-setup-plan.json --as-json
```

Linux and macOS use the native Python 3 renderer behind these wrappers; they do
not require PowerShell. Python 3 is the only renderer prerequisite.

The generated plan covers:

- Health check.
- Hardware and installed-model profile.
- Evidence dashboard.
- Model scorecard.
- Hardware-aware recommendation.
- Dry-run local config preview.
- Dry-run pack install preview.
- Local model API testing with unload-after-test behavior.

Review any step marked `RequiresReviewBeforeApply` before removing dry-run flags or applying changes to a target project.
