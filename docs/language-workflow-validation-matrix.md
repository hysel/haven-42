# Language Workflow Validation Matrix

## Purpose

`config/language-workflow-validation-matrix.json` defines the representative
Milestone 18 validation surface for every optional language rule pack.

The matrix separates two facts that must not be confused:

- `fixtureStatus: static-validated` means the generated sample and expected
  evidence files passed deterministic repository tests.
- `pending-model-validation` means no editor/model result has been promoted for
  that operation yet.

## Medium Fixtures

| Sample | Coverage | Intended use |
| --- | --- | --- |
| `python-layered-api` | Python configuration, domain, repository, service, entry point, and tests | Discovery, planning, review, and a two-file scoped validation change |
| `typescript-service-medium` | TypeScript domain, repository, service, config, entry point, and tests | Discovery, planning, review, and a two-file scoped validation change |
| `multi-language-platform` | Java API, Go worker, Rust tool, SQL migrations, Terraform, and Kubernetes | Component-aware discovery and edits that must remain inside one approved boundary |

These are disposable validation fixtures, not production starter projects.

## Required Operations

Every matrix entry must eventually pass:

1. `repository-discovery`
2. `implementation-plan`
3. `code-review`
4. `scoped-write`

Discovery, planning, and review require sanitized saved output that references
real fixture filenames. Scoped writes additionally require external Git diff
verification proving that only the approved files changed.

The runners reject an otherwise filename-complete response when it explicitly
states that the source was unavailable or not inspected. That result receives
the `UNREAD_SOURCE_CLAIM` failure signal and cannot become language evidence.

## Promotion Gate

A rule pack remains optional and evidence-gated until the matrix records a
validated result with the agent surface and version, provider, model, operating
system, sanitized output, and external diff evidence where applicable.

Static fixture success alone never promotes an editor/model combination.

## Local Preparation

Generate the fixtures without installing dependencies:

```powershell
.\scripts\generate-sample-repositories.ps1 -Force
```

```bash
./scripts/generate-sample-repositories.linux.sh --force
```

Then inspect the matrix and choose one ecosystem/operation pair at a time. Use
`examples/language-rule-pack-validation.md` for sanitized evidence and
`docs/runtime-output-verification.md` for deterministic output checks.

## Automated Continue CLI Run

Windows PowerShell can execute selected matrix rows with separate read and
write configurations:

```powershell
.\scripts\run-language-workflow-matrix.ps1 `
  -Ecosystems python,javascript-typescript `
  -ReadConfigPath .\runtime-validation-output\continue-read.yaml `
  -WriteConfigPath .\runtime-validation-output\continue-write.yaml `
  -UnloadAfterRun
```

The runner generates clean fixtures, invokes Continue CLI in read-only or auto
mode, checks operation-specific filenames, verifies scoped writes with Git,
restores the fixture, stores raw output only under ignored runtime output, and
writes a sanitized JSON report. When `-UnloadAfterRun` is used, it retries the
model release and verifies that the model is no longer resident before reporting
success. Use `-Operations` to run a smaller slice and `-DryRun` to validate
orchestration without contacting a model.

Native Linux and macOS runners are available through
`run-language-workflow-matrix.linux.sh` and
`run-language-workflow-matrix.macos.sh`, which delegate to the shared Bash
engine. Native Linux evidence is complete through WSL2 Ubuntu 24.04. Native
macOS evidence is complete for all 28 required cells on Apple Silicon using the
validated Devstral Small 2 lane.

On the 16 GB Apple Silicon validation host, the `qwen3.5:9b` Ollama lane is
appropriate for targeted smoke slices but was not practical for one continuous
24-cell run: the remote command exceeded its 30-minute transport limit before
it produced a report. Do not treat that interrupted attempt as evidence. Run
remaining macOS cells in smaller batches, or use a Mac with more unified memory
and a separately validated model lane. This guidance remains useful for smaller
Mac hosts. The shared runner releases its tested
models on normal completion and on `HUP`, `INT`, or `TERM`; after a connection
loss, check `/api/ps` before starting another run.

The smaller `qwen3.5:9b` lane remains useful for targeted macOS smoke tests,
but it did not consistently reproduce exact root-relative evidence paths in
the TypeScript runner. On 2026-07-17, `devstral-small-2:24b` completed the
full TypeScript matrix and the remaining Java, Go, Rust, SQL, and
Infrastructure as Code matrices in separate bounded runs. Every cell passed
the exact-file and external scoped-write checks, and the model was verified
unloaded after each run.

The Windows and Bash runners refuse to start when Ollama already has a loaded
model. This protects the 64 GB validation budget from accidental concurrent
loads. Unload the existing model first; use `-AllowLoadedModels` on Windows
or `--allow-loaded-models` on Linux/macOS only when concurrent use is
intentional and the available memory has been checked.

## Latest Continue CLI Evidence

Two full Windows runs on 2026-07-15 used Continue CLI `1.5.47` with Ollama.
Each model independently passed 27 of 28 cells; their evidence-backed
language-aware combination validates 28 of 28 required cells.

| Ecosystem | Discovery | Planning | Review | Scoped write |
| --- | --- | --- | --- | --- |
| Python | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 |
| JavaScript / TypeScript | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 | Qwen 3.5 35B |
| Java | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 |
| Go | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 |
| Rust | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 |
| SQL | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 |
| Infrastructure as Code | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 | Devstral Small 2 |

`devstral-small-2:24b` failed only the TypeScript scoped-write final-line
check. `qwen3.5:35b` passed that TypeScript write, but failed the Rust
scoped-write final-line and diff checks. The machine-readable contract records
the selected model for every operation. This is Windows Continue CLI evidence.

## Native Linux Evidence

On 2026-07-15, Continue CLI 1.5.47 ran in Ubuntu 24.04 under WSL2 against
an Ollama server with one model loaded at a time. Devstral Small 2 completed
all 28 required cells across clean runs. Qwen 3.5 35B separately completed the
TypeScript scoped-write override. Each run verified model unload afterward.

This is Linux CLI evidence, not native Linux editor-extension evidence. The
language-aware selector recognizes the validated Linux evidence separately and
must not silently reuse Windows evidence.

## Native macOS Evidence

The macOS validation and test wrappers were run on a native Apple Silicon
macOS host. Validation passed, and the 50 deterministic macOS wrapper checks
passed after the validated-model installer was updated to prefer `python3`
when `python` is unavailable.

On 2026-07-15, Continue CLI `1.5.47` ran against local Ollama on a native
Apple Silicon host with a single `qwen3.5:9b` model. Python
`repository-discovery`, `implementation-plan`, `code-review`, and
`scoped-write` passed. The scoped write changed only its approved file, ended
with the exact required marker, passed `git diff --check`, returned structured
headless output, and the runner confirmed model unload after every run. This is
native macOS CLI evidence only, not editor-extension evidence. It promotes the
Python slice for this exact surface/model/OS combination, not the remaining
language packs.

On 2026-07-17, Continue CLI `1.5.47` ran the complete 28-cell matrix on a
native Apple Silicon host with local Ollama and `devstral-small-2:24b`. Python,
JavaScript/TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code each
passed repository discovery, implementation planning, code review, and scoped
write. The runner verified the constrained external diff for every scoped-write
cell and unloaded the model after every bounded ecosystem run. This is native
macOS CLI evidence only; it does not claim editor-extension validation.
