# Optional Online Model Discovery

## Purpose

This guide defines how the pack discovers newer candidates from multiple public
metadata sources without weakening the local-first setup or hard-coding one
model family.

Online discovery is optional. It records candidate metadata only. It does not
replace local hardware profiling, local runtime inventory, provenance and
license review, tool validation, or approved-write smoke tests.

The local web Models panel provides a smaller interactive slice of this
contract. Installed-name filtering is offline. A public Ollama catalog search
requires activating the explicitly labeled **Search public catalog** action and
sends only a bounded phrase to the fixed `https://ollama.com/search` origin.
Changing the target capability or typing in the local filter does not make a
network request. Redirects are rejected, HTML is
capped, and at most 20 normalized names return. An uninstalled result remains
candidate-only with unverified capability evidence, unknown hardware fit, and
license review required. Selecting it records browser-memory intent only.
Haven 42 may copy an engine-constructed `ollama pull <validated-name>` command,
but it never executes that command, calls `/api/pull`, or changes configuration.
After external installation, reconnect to verify provider inventory and digest.

`config/model-discovery-contract.json` defines the normalized candidate record.
`config/model-discovery-sources.json` defines source adapters, reviewed
publisher namespaces, and independent seed queries. The adapters cover the
Ollama library, general Hugging Face Hub search, and direct modification-time
feeds for reviewed publisher namespaces. Queries are search inputs, not an
allowlist of model families.

The publisher feed is deliberately independent of search rank. It polls each
configured namespace by modification time and retains the immutable Hub
revision. This closes a real discovery gap found on 2026-08-16: Qwen 3.8 had
official public local weights, but a popularity/trending search did not return
them promptly. Search engines and mutable `latest` tags are therefore useful
signals, not release evidence.

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

- Query configured public Ollama and Hugging Face metadata when explicitly requested.
- Poll configured official publisher namespaces by modification time so a new
  repository does not have to become popular before it is reviewed.
- Search arbitrary names, publishers, capabilities, formats, or families.
- Record immutable revisions, publisher identity, license tags, gated status,
  task tags, formats, quantization signals, and possible runtimes when a source provides them.
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

## Model Candidate Updater

Use the discovery script as Haven 42's model candidate updater. It checks the
configured public sources, compares the normalized results with
`config/alpha-2-model-version-inventory.json`, and writes both an engineering
JSON report and a short Markdown review queue. It distinguishes an exact
artifact already tracked by Haven 42 from a new tag in a tracked model
repository and a new upstream model candidate.

The updater runs only when a person starts it. It does not edit the
certification inventory, download a model, prepare or start a soak, change an
automatic model choice, or contact a test machine.

`config/model-release-watch.json` is the smaller human-reviewed queue produced
after discovery. It keeps high-value local candidates, runtime and license
gaps, realistic hardware positions, and oversized-but-not-runnable releases
visible without adding them to automatic selection.

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
default. The JSON retains bounded public metadata and comparison status for
engineering review. The matching Markdown file explains only the review queue
and next actions in plain language. Neither report contains private repository
content, hardware profiles, local endpoints, usernames, hostnames, or local
paths from a public request.

To show only candidates that appeared since an earlier check, provide that
earlier JSON report:

```powershell
.\scripts\discover-online-model-candidates.ps1 `
  -PreviousReportPath .\runtime-validation-output\online-model-candidates-previous.json
```

```bash
./scripts/discover-online-model-candidates.linux.sh \
  --previous-report-path runtime-validation-output/online-model-candidates-previous.json
```

`NewTestCandidates` contains everything not represented by an exact inventory
artifact. `NewSincePreviousReport` is the smaller delta from the optional
previous report. A mutable `latest` tag is blocked until an immutable,
version-pinned artifact is resolved.

To limit discovery to a small set of families:

Windows PowerShell:

```powershell
.\scripts\discover-online-model-candidates.ps1 -Families qwen3.5,devstral,gpt-oss
```

Linux or macOS:

```bash
./scripts/discover-online-model-candidates.linux.sh --families qwen3.5,devstral,gpt-oss
```

The legacy `Families` name is retained as an alias for queries. It does not
restrict discovery to the built-in seed families. To select sources explicitly:

```powershell
.\scripts\discover-online-model-candidates.ps1 `
  -Sources ollama,huggingface `
  -Queries "agentic coding","tool calling","GGUF"
```

```bash
./scripts/discover-online-model-candidates.linux.sh \
  --sources ollama,huggingface \
  --queries "agentic coding,tool calling,GGUF"
```

Hugging Face discovery uses public Hub model search metadata. Its normalized
record distinguishes a Hub repository from a direct Ollama pull, retains the
reported immutable revision when present, and marks every result
`candidate-only`. See the official [Hugging Face Hub API documentation](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api#huggingface_hub.HfApi.list_models).

The `official-publishers` source instead calls the same public API once per
configured namespace with `sort=lastModified`. A rolling 45-day window is the
minimum lookback. `--publisher-since-utc` can widen that window for an
investigation, but it cannot narrow it; this prevents older repository metadata
from hiding a newly announced or newly relevant family. Records without a
license or immutable revision remain blocked. Pipeline types outside Haven
42's configured assistant capability lanes remain visible only in
`SkippedCandidates`.

The `ollama-newest` source reads the fixed newest-first registry index and then
checks each visible family page for local tags. It does not need to know the
family name in advance. Cloud-only tags remain skipped, and a family with no
versioned local tag remains an unresolved review record rather than becoming a
pull command. The older seeded Ollama source remains useful for deep tag review
of already known families.

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

Use `-HuggingFaceJsonPath` or `--hugging-face-json-path` with a captured,
sanitized Hub API fixture to validate the Hugging Face adapter without network
access. Offline fixtures never promote a model.

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

The terminal output identifies each queried source and summarizes candidates,
skips, and source errors. The report adds `VramRecommendation` to each
candidate. This remains a low-confidence name-and-tag estimate until exact
artifact metadata and measured runtime evidence exist. Cloud tags and
platform-incompatible Ollama tags are written to `SkippedCandidates`.
Hugging Face GGUF or Ollama application tags indicate possible import/runtime
paths only; they never become direct Ollama pull references automatically.

## Safe Workflow

Use this sequence if online discovery is added later:

1. Run local hardware profiling.
2. Run optional multi-source discovery with an explicit command such as `discover-online-model-candidates`.
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

## Trust And Normalization Boundary

The normalized record deliberately separates discovery from admission:

- A publisher name is source metadata, not verified ownership.
- A revision is retained when present, but its contents still require artifact verification.
- A license tag is not legal approval; a missing license blocks automatic promotion.
- GGUF, MLX, AWQ, GPTQ, FP8, or INT4 tags are compatibility clues, not runtime evidence.
- Tool-calling, reasoning, coding, security, or multimodal tags are claims until tested.
- Community quantizations require independent provenance, checksum, license, and quality review.
- Results never pull models, rewrite config, or inherit readiness from another source or artifact.

## Related Docs

- `docs/local-model-selection.md`
- `docs/local-agent-model-testing.md`
- `docs/model-tool-use-validation.md`
- `docs/local-config-safety.md`
