# Intel Arc B580 Inference Engine Validation

## Scope

Validation ran on 2026-07-30 on a physical Linux x86_64 workstation and on
2026-08-02 on the same physical Intel Arc B580 12 GB class under Windows x64.
The Linux profile used the `xe` kernel driver and a 16 GB Resizable BAR. The
machine-specific hostnames, addresses, usernames, GPU identities, local paths,
and raw prompts are intentionally omitted.

This is exact-host development evidence. It does not admit an installer,
driver change, system package, bundled inference runtime, model redistribution,
automatic download, provider route, or production support. Ubuntu 26.04 is
newer than OpenVINO's documented Ubuntu 24.04 support baseline, so its
OpenVINO result remains candidate evidence.

## llama.cpp SYCL

The source build used llama.cpp commit
`5f55650a78f92aff4d48d671423e888fac0469ff`, Intel oneAPI `2026.1.0`, and a
user-local Level Zero development package. The build disabled native CPU
specialization, embedded and prebuilt web UI assets, CURL, and oneDNN. A first
build was rejected after it mixed system oneDNN/SYCL libraries and crashed;
only the isolated no-oneDNN build supplied evidence.

All model files were kept outside the repository and hash-verified before use.
Nine representative text artifacts completed bounded GPU inference with full
offload:

- Qwen 3.5 0.8B Q4 and Q8;
- Qwen 3 4B Q4_K_M and 8B Q8;
- SmolLM3 3B Q4;
- Granite 4.1 3B Q4;
- Gemma 3 1B Q4 and 4B Q4; and
- Phi-3 Mini 4K Q4.

The Qwen 3 8B Q8 artifact also passed 4K- and 8K-token prompt-pressure checks.
Ten repeated load/infer/unload cycles left no model process or listener. A
hardened loopback server passed model discovery, exact chat output, a required
tool call, hostile-Origin handling, closed-port verification, and cleanup.
Haven 42's existing provider discovery and invocation entry points passed
against a temporary lab-only profile; no endpoint or model path was persisted.

On 2026-07-31, the retained exact Qwen 3.5 0.8B Q4 artifact and the same
hash-identified SYCL build completed another bounded full-offload inference
cell. Prompt processing was approximately 3,307 tokens per second and
generation approximately 236 tokens per second. The model process and listener
were absent after cleanup. These host-specific rates are diagnostic only; no
new artifact was downloaded and no raw response was committed.

The exact Qwen 3.5 9B Q4_K_M artifact fully offloaded and generated about
57 tokens per second. Its first reasoning-disabled patch attempt failed.
A bounded reasoning retry with an exact hunk-count instruction produced a
one-line patch that passed `git apply --check`, and its required tool call
passed. This is model-and-mode-specific evidence, not a general approved-write
claim.

Gemma 3 4B Q4 plus its separately verified multimodal projector correctly
identified both colors in a generated red/blue control image on the GPU. The
control image was not user content.

The upstream test suite passed 50 of 53 tests. The three failures were:

- a missing real tokenizer fixture where the checkout contained a Git LFS
  pointer;
- a DeepSeek/GLM architecture numerical-error threshold failure; and
- SYCL backend `CONV_2D` mismatches plus an unsupported quantized-copy case.

No GPU hang, reset, or kernel fault was observed. Because all security findings
are treated as blockers and the upstream suite is not fully green, the SYCL
profile remains `candidate`; it is not selectable or packaged.

## OpenVINO GenAI

The OpenVINO comparison used exact CPython 3.14 Linux wheels for:

- OpenVINO `2026.2.1-21919`;
- OpenVINO Tokenizers `2026.2.1.0`; and
- OpenVINO GenAI `2026.2.1.0`.

The complete 27-wheel environment was downloaded to a user-local wheelhouse,
SHA-256 inventoried, installed offline into an isolated virtual environment,
and passed dependency checks. OpenVINO reported both CPU and GPU devices and
identified the B580 as the selected discrete GPU.

The model was Intel's
`OpenVINO/Qwen3-0.6B-int4-ov` at immutable revision
`f864c6106efb6c7f7b4ef274a78a98e37210dddd`. Its 15 downloaded data and
configuration files contained no source, executable, pickle, native library,
or symlink and were individually hashed. Direct GPU inference loaded in about
3.28 seconds. Five fresh load/generate/unload cycles completed in about
2.45 seconds each, with no surviving model process or GPU fault/reset event.

The small model answered the factual control but did not follow the requested
one-word or exact-output constraint before its token limit. This proves
engine/device execution and cleanup, not task quality, tool use, patch
reliability, provider compatibility, or model admission. OpenVINO GenAI
therefore remains a `candidate` with no Haven 42 provider contract.

### Windows OpenVINO GenAI follow-on

The Windows comparison used the official OpenVINO GenAI `2026.2.0` one-folder
archive and the official CPython `3.13.12` embeddable distribution. Published
hashes were verified before extraction, all 87 native OpenVINO files had valid
Authenticode signatures, and the archive contained no executable program. An
isolated, user-local Python path used exact hash-verified NumPy `2.4.6` and
OpenVINO Telemetry `2025.2.0` wheels without an installer or global Python.
OpenVINO imported with telemetry disabled and identified the B580 as the
selected discrete `GPU` device.

The same immutable Qwen3 model revision was downloaded from an exact file
allowlist. All 16 files matched their declared sizes and SHA-256 or Git blob
hashes before use. Three fresh pipeline load/generate/release cycles completed.
The cold load took about 6.79 seconds; subsequent loads took about 2.58 seconds,
and bounded generation took about 0.32 seconds in each run. No Python or
OpenVINO process remained afterward.

The response contained the requested exact marker on every run but wrapped it
in empty Qwen reasoning tags. The strict-output cell therefore remains failed.
This result proves direct Windows GPU execution, verified portable-runtime
loading, and process cleanup only. It does not admit a provider, installer,
automatic download, package component, task-quality claim, or runtime choice.

## Decision

Representative Intel hardware is no longer a blocker for these two engine
families. Neither engine is promoted:

- llama.cpp SYCL is blocked by upstream test failures and has no consumer
  installation or packaged parity evidence;
- OpenVINO GenAI now has exact Linux and Windows B580 execution evidence, but
  is blocked by strict-output behavior and absent provider/package gates. The
  Linux host also remains outside its documented operating-system baseline.

Both runtimes, their toolchains, models, caches, and raw logs remain outside the
repository. No external Ollama server was contacted and no system package,
driver, service, firewall rule, startup entry, or global Python environment was
changed.
