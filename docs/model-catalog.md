# Security-Aware Model Catalog

## Purpose

Haven 42 assembles a read-only model catalog from public discovery metadata,
local hardware-fit estimates, and committed validation evidence. The catalog is
an engine-side product contract for future beginner and advanced model views.
It does not download models, modify runtime configuration, execute model code,
or turn public claims into validation.

The source contract is `config/model-catalog-contract.json`. The assembler is
`scripts/build-model-catalog.py`, reached through OS-aware PowerShell, Linux,
and macOS wrappers.

## Two Product Views, One Policy Decision

The catalog emits the same admission decision for both product modes:

- Beginner mode receives `recommendedForThisComputer` and a plain-language
  reason. Only an exact artifact that passes every gate can be recommended.
- Advanced mode receives reported runtimes, formats, quantization signals,
  provenance, license-review state, hardware-fit confidence, and exact
  operation evidence. Advanced controls cannot bypass a blocker.

The future renderer may filter and explain these records. It may not recompute
license, provenance, hardware, or evidence state.

## Fail-Closed Admission

Automatic promotion is denied when any of these conditions applies:

- no license is reported;
- a noncommercial or proprietary-use signal is present;
- a custom or unknown license has not completed explicit review;
- no immutable hexadecimal revision is recorded;
- artifact access is gated;
- no approved safe artifact format is recorded;
- the supplied hardware estimate says the model does not fit; or
- exact model and operation validation is incomplete.

A reported MIT, Apache-2.0, BSD, ISC, or 0BSD identifier clears only the
catalog's initial license-policy check. It is not legal advice, provenance
proof, permission to use trademarks, or permission to redistribute a
derivative. Model licenses are evaluated per exact artifact, not inherited
from a family name.

## Security Boundary

The assembler:

- accepts bounded JSON and TSV inputs only;
- rejects control characters, path-like artifact identifiers, oversized
  candidates, missing fields, and malformed immutable revisions;
- allows only recorded GGUF, SafeTensors, MLX, or Ollama-manifest formats past
  the initial format check;
- always records `remoteCodeAllowed` as false;
- creates its output exclusively and refuses to overwrite an existing file;
- retains no local endpoint, credential, prompt, repository content, hardware
  identifier, or raw validation transcript; and
- never contacts Ollama, Hugging Face, or any other network service.

SafeTensors identifies a weight container, not safe executable model code.
Runtime loaders must continue to disable remote code and enforce their own
dependency and artifact checks.

## Usage

First create a candidate-only discovery report. This step may use the network,
so review its disclosure separately:

```powershell
.\scripts\discover-online-model-candidates.ps1 `
  -Sources huggingface `
  -Families "tool calling" `
  -OutputPath .\runtime-validation-output\candidates.json
```

Then assemble the catalog without network access:

```powershell
.\scripts\build-model-catalog.ps1 `
  -DiscoveryReportPath .\runtime-validation-output\candidates.json
```

Linux or macOS:

```bash
./scripts/build-model-catalog.linux.sh \
  --discovery-report runtime-validation-output/candidates.json
```

The macOS command uses `build-model-catalog.macos.sh`. An explicit output path
must not already exist.

## Lifecycle

Discovery, catalog assembly, download, runtime validation, tool validation, and
promotion remain separate stages. A catalog blocker can be remediated only by
new exact evidence or an explicit policy review. It cannot be dismissed by the
renderer or by selecting advanced mode.
