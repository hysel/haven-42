# Beginner Setup Mode

Beginner setup mode creates an ordered local setup plan from the workflow registry.

It is intentionally a plan generator, not an installer. The first output shows exactly which commands to run, which workflow each command uses, and where the workflow boundary changes from read-only to previewing a write.

Use `docs/setup-paths.md` when you need to compare the quick beginner path with team or enterprise review and audit expectations.

Generate the Windows plan:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/get-beginner-setup-plan.ps1 -MarkdownOutputPath runtime-validation-output/beginner-setup-plan.md -OutputPath runtime-validation-output/beginner-setup-plan.json -AsJson
```

Generate a Linux or macOS plan:

```bash
./scripts/get-beginner-setup-plan.linux.sh --markdown-output-path runtime-validation-output/beginner-setup-plan.md --output-path runtime-validation-output/beginner-setup-plan.json --as-json
./scripts/get-beginner-setup-plan.macos.sh --markdown-output-path runtime-validation-output/beginner-setup-plan.md --output-path runtime-validation-output/beginner-setup-plan.json --as-json
```

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
