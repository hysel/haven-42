# Optional Online Model Discovery

## Purpose

This guide defines how the pack may evaluate newer Ollama model candidates in
the future without weakening the local-first setup.

Online discovery is optional. It is for finding candidate model names only. It
does not replace local hardware profiling, local Ollama inventory, Continue
tool validation, or approved-write smoke tests.

## Default Posture

The default workflow stays offline:

1. Use the committed starter model examples.
2. Run the local hardware profile helper.
3. Check models already installed on the local Ollama server.
4. Use `config/model-recommendations.tsv` for curated local recommendations.
5. Validate the selected model in Continue before tool-backed work.

No setup, validation, or install script should require internet access for the
normal path.

## What Online Discovery May Do

An online discovery helper may:

- Query public Ollama model catalog pages or APIs when explicitly requested.
- List newer candidate model names, families, sizes, or tags.
- Compare candidate names with local recommendation tiers.
- Produce a suggestion report for human review.
- Tell the user which model still needs to be pulled and validated locally.

## What Online Discovery Must Not Do

An online discovery helper must not:

- Run by default.
- Replace the committed starter model automatically.
- Rewrite `.continue/config.yaml`.
- Rewrite `.continue/config.local.yaml` without a separate explicit install step.
- Pull models automatically unless the user separately chooses a specific model.
- Mark a model as tool-safe because it appears online.
- Send private repository content, local paths, endpoints, hostnames, usernames,
  tokens, or hardware reports to a public service.
- Depend on private or unstable scraped content for release validation.

## Dry-Run Discovery Script

Use the discovery script when you want to look for newer public model tags
without changing local configuration or pulling models.

Windows PowerShell:

```powershell
.\scripts\discover-online-model-candidates.ps1
```

Linux:

```bash
./scripts/discover-online-model-candidates.linux.sh
```

macOS:

```bash
./scripts/discover-online-model-candidates.macos.sh
```

The script writes a sanitized report to `runtime-validation-output/` by
default. The report records only candidate names, source category, status, and
next-step guidance. It does not send repository content, hardware profiles,
local endpoints, usernames, hostnames, or local paths to the public model
catalog.

To limit discovery to a small set of families:

Windows PowerShell:

```powershell
.\scripts\discover-online-model-candidates.ps1 -Families qwen3.5,devstral,gpt-oss
```

Linux or macOS:

```bash
./scripts/discover-online-model-candidates.linux.sh --families qwen3.5,devstral,gpt-oss
```

For offline parser validation, use a local HTML fixture instead of the network:

Windows PowerShell:

```powershell
.\scripts\discover-online-model-candidates.ps1 `
  -SourceHtmlPath .\runtime-validation-output\sample-model-page.html
```

Linux or macOS:

```bash
./scripts/discover-online-model-candidates.linux.sh \
  --source-html-path ./runtime-validation-output/sample-model-page.html
```

## VRAM-Aware Candidate Annotation

Online discovery can read a local or remote model profile from disk and annotate candidates with estimated VRAM fit. The profile is used only on the machine running the script; it is not uploaded to the online model source, and the report keeps `HardwareProfileSent` set to `false`.

Windows example using a remote hardware profile:

```powershell
.\scripts\discover-online-model-candidates.ps1 `
  -Families qwen3.5,devstral `
  -ModelProfilePath .\runtime-validation-output\remote-model-profile.json `
  -VramSelectionMode TotalDedicated
```

Linux or macOS:

```bash
./scripts/discover-online-model-candidates.linux.sh \
  --families qwen3.5,devstral \
  --model-profile-path runtime-validation-output/remote-model-profile.json \
  --vram-selection-mode TotalDedicated
```

The terminal output shows each family being checked, how many tags were found, each discovered model name, whether that model fits the local VRAM estimate, and any source error for a family that could not be read. The report adds `VramRecommendation` to each candidate. If a model is estimated to exceed available VRAM, its status becomes `online candidate above vram estimate`, and the next step tells the user not to pull it by default. Cloud tags and platform-incompatible tags are written to `SkippedCandidates` instead of pullable `Candidates`; cloud tags are never local pull targets, and MLX tags are only pullable when the detected model host platform is macOS. Use `-IncludeOversizedModels` or `--include-oversized-models` only when intentionally testing beyond the estimate.

## Safe Workflow

Use this sequence if online discovery is added later:

1. Run local hardware profiling.
2. Run optional online discovery with an explicit command such as `discover-online-model-candidates`.
3. Review the candidate list.
4. Pull one chosen model locally.
5. Run API-level model preflight.
6. Run Continue read-only tool validation.
7. Run approved-write smoke testing only when the model needs write access.
8. Install the validated model into `.continue/config.local.yaml` with the
   post-validation installer.
9. Record sanitized validation evidence before updating shared guidance.

## Candidate Status

Online results are only candidates.

A discovered model can move through these states:

| Status | Meaning |
| --- | --- |
| Online candidate | The model appears in a public catalog or public source. |
| Local candidate | The model is installed on the local Ollama server. |
| API preflight candidate | The model passed local Ollama API checks. |
| Read-only validated | The model used Continue tools to inspect files. |
| Approved-write ready | The model passed scoped edit/apply validation and external file checks. |

Only the last two statuses should influence Agent tool-use guidance.

## Updating The Catalog

Do not add a model to `config/model-recommendations.tsv` just because it is new
or popular.

Before updating the catalog:

- Confirm it can be pulled from Ollama.
- Confirm it runs on at least one realistic hardware tier.
- Record sanitized validation results.
- Keep ordering conservative.
- Keep one concrete fallback model per tier.
- Avoid private model names and local-only tags.

## Related Docs

- `docs/local-model-selection.md`
- `docs/local-agent-model-testing.md`
- `docs/model-tool-use-validation.md`
- `docs/local-config-safety.md`
