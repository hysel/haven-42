# Language-Aware Model Lanes

Use the language-aware lane selector after project classification when you want an evidence-backed model recommendation for one workflow operation.

The selector reads repository filenames through the project classifier and matches selected optional language rule packs against `config/language-workflow-validation-matrix.json`. It does not read source-file contents and does not record the target path in its result.

## Current Evidence

| Workflow operation | Default lane | Override |
| --- | --- | --- |
| Repository discovery | devstral-small-2:24b | None |
| Implementation plan | devstral-small-2:24b | None |
| Code review | devstral-small-2:24b | None |
| Scoped write | devstral-small-2:24b | TypeScript uses qwen3.5:35b |

The selector recognizes Windows and Linux Continue CLI evidence separately.
Linux requests use the validated WSL2 Ubuntu 24.04 evidence, while macOS still
returns `no-validated-lane` until native macOS validation is recorded. This
avoids recommending a model from the wrong platform.

## Commands

Windows: `.\\scripts\\recommend-language-model-lane.ps1 -TargetRepo "C:\\work\\example" -Operation scoped-write -AsJson`

Linux: `./scripts/recommend-language-model-lane.linux.sh --target-repo "$HOME/work/example" --operation scoped-write --as-json`

macOS: `./scripts/recommend-language-model-lane.macos.sh --target-repo "$HOME/work/example" --operation code-review --as-json`

## Configuration Boundary

The result includes `ContinueModelProfiles`, which can be incorporated into an agent configuration. The selector does not modify configuration files. Supported editor and CLI surfaces still require a user or surface-specific workflow to select a model/profile; this pack does not claim silent runtime model switching.

Use `docs/language-workflow-validation-matrix.md` for evidence and `docs/project-profile-classification.md` for project detection.
