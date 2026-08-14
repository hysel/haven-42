# Cross-Accelerator Portable Model Validation

## Scope

This development-only batch compares identical, hash-pinned GGUF bytes through
the same llama.cpp build on Windows AMD/HIP and Linux NVIDIA/CUDA. It does not
compare an Ollama blob with a llama.cpp artifact, transfer evidence between
accelerators, admit a provider route, authorize model redistribution, or claim
production support.

The public manifest is
`examples/cross-accelerator-model-matrix.json`. It pins llama.cpp build
`b10088` at commit `67b9b0e7f6ce45d929a4411907d3c48ec719e81c`,
11 text-model artifacts, and one Gemma multimodal projector. The projector is
verified separately and is reserved for a later vision cell; it is not counted
as a text model.

The runner:

- performs no download and opens no listener;
- passes the runtime's explicit offline option and strips home-directory
  variables from the child environment;
- rejects absolute paths, parent traversal, symlinks, size drift, and SHA-256
  drift before execution;
- rejects relaxed security policy, unknown test names, unbounded execution
  values, and insufficient free space;
- invokes exact binaries without a shell;
- uses an explicit accelerator index and fails on a backend mismatch;
- requires every model layer to be reported as GPU-offloaded;
- runs one model at a time with bounded process time;
- checkpoints only sanitized metrics through an exclusive, no-follow atomic
  temporary file and never stores raw prompts, responses, endpoints,
  hostnames, usernames, or local paths; and
- treats functional quality separately from engine execution.

OpenVINO's Qwen3 0.6B INT4 IR files are Intel-engine-specific and cannot be
executed by llama.cpp CUDA or HIP. The portable comparison therefore uses the
revision-pinned Qwen3 0.6B Q4_0 GGUF counterpart. This is a related model, not
byte-equivalent evidence for the OpenVINO artifact.

## Windows AMD/HIP Result

The Windows x86_64 AMD cell completed on an RX 7800 XT 16 GB using the
hash-verified official b10088 HIP archive. All 11 artifacts matched their
manifest size and SHA-256, identified the ROCm backend and expected GPU,
completed the fixed 128-token prompt and 64-token generation benchmark,
reported full model-layer offload, exited within the per-process limit, and
left no llama.cpp process or listener.

| Artifact | Prompt tokens/s | Generation tokens/s | Exact 48-token response |
| --- | ---: | ---: | --- |
| Qwen3 0.6B Q4_0 | 7,147.02 | 272.20 | Miss |
| Qwen3.5 0.8B Q4_0 | 7,438.82 | 225.62 | Miss |
| Qwen3.5 0.8B Q8_0 | 7,434.84 | 205.60 | Miss |
| Gemma 3 1B Q4_K_M | 5,911.08 | 178.61 | Pass |
| SmolLM3 3B Q4_K_M | 2,749.30 | 139.06 | Miss |
| Granite 4.1 3B Q4_K_M | 2,505.14 | 128.05 | Pass |
| Phi-3 Mini 4K Q4 | 2,819.63 | 118.14 | Pass |
| Gemma 3 4B Q4_K_M | 2,677.37 | 111.06 | Pass |
| Qwen3 4B Q4_K_M | 2,186.77 | 116.78 | Miss |
| Qwen3.5 9B Q4_K_M | 1,285.95 | 69.27 | Miss |
| Qwen3 8B Q8_0 | 1,511.90 | 60.44 | Miss |

The exact-output gate gives each model only 48 generated tokens. The Qwen
reasoning models remained inside their reasoning phase at that boundary; this
is a bounded-task miss, not an engine or offload failure. Four unrelated model
artifacts returned the exact marker after the llama-cli conversation wrapper
was removed by a tested parser. SmolLM3 also missed the exact-output gate.

These throughput values are one controlled development run, not a general
performance guarantee. Patch, tool-call, context-pressure, repeated lifecycle,
and vision tests listed in the manifest remain separate follow-on cells and
must not be inferred from the benchmark.

A complete Windows AMD repeat on 2026-07-31 reverified all 11 artifact hashes,
the exact b10088 runtime commit, ROCm backend identity, full model-layer
offload, bounded exit, and cleanup. All 11 operational checks passed, and the
same four exact-output cells passed while the same seven missed. No artifact
was downloaded and no raw prompt, response, endpoint, username, hostname, or
local path was retained. Repeat throughput varied within the expected
host-specific diagnostic range and does not replace the original paired
AMD/NVIDIA comparison.

## Linux NVIDIA/CUDA Result

The Linux x86_64 NVIDIA cell completed on one explicitly isolated Tesla V100
SXM2 32 GB. The runtime was built from the pinned b10088 source commit for
compute capability 7.0 with its build number explicitly bound to 10088. It
contained no downloaded or embedded server UI. A dedicated, restricted
non-root lab identity staged the already verified corpus; host-specific
connection details and credentials remain outside the repository.

All 11 artifacts independently matched the same manifest sizes and SHA-256
values used by the AMD cell. Every model identified CUDA and the expected GPU,
completed the fixed benchmark, reported full model-layer offload, and exited
within its bound. The selected GPU was idle before the run and returned to zero
memory use afterward. No llama.cpp process or test listener remained.

| Artifact | Prompt tokens/s | Generation tokens/s | Exact 48-token response |
| --- | ---: | ---: | --- |
| Qwen3 0.6B Q4_0 | 6,997.26 | 407.78 | Miss |
| Qwen3.5 0.8B Q4_0 | 5,807.23 | 311.79 | Miss |
| Qwen3.5 0.8B Q8_0 | 7,307.49 | 283.08 | Miss |
| Gemma 3 1B Q4_K_M | 5,979.65 | 261.43 | Pass |
| SmolLM3 3B Q4_K_M | 2,375.61 | 197.65 | Miss |
| Granite 4.1 3B Q4_K_M | 1,998.84 | 166.10 | Pass |
| Phi-3 Mini 4K Q4 | 1,921.38 | 189.57 | Pass |
| Gemma 3 4B Q4_K_M | 1,864.81 | 145.80 | Pass |
| Qwen3 4B Q4_K_M | 1,757.30 | 156.77 | Miss |
| Qwen3.5 9B Q4_K_M | 1,045.86 | 97.01 | Miss |
| Qwen3 8B Q8_0 | 1,398.57 | 80.43 | Miss |

## Cross-Accelerator Comparison

The artifact hash, build number, source commit, full-offload result,
operational result, and exact-output result agree for every AMD/NVIDIA row.
The same four artifacts passed the strict exact marker on both accelerators;
the same seven missed. This consistency supports the conclusion that those
literal-output misses reflect the fixed task/model behavior rather than an
AMD- or NVIDIA-specific engine fault.

Generation throughput was higher on the V100 in every row in this single
controlled run. Prompt throughput varied: the RX 7800 XT was faster in nine
rows, while the V100 was slightly faster for both Gemma 3 1B and Qwen3.5 0.8B
Q8. These measurements are hardware-profile evidence, not a ranking promise
for other drivers, runtimes, models, quantizations, prompts, or devices.

## WSL2 AMD/HIP Candidate Result

A separate Windows-hosted WSL2 Ubuntu 24.04.4 cell exercised the same pinned
llama.cpp b10088 commit and the same 11 hash-pinned artifacts on an RX 7800 XT
16 GB. The clean source build used ROCm 7.2 with its server UI and prebuilt UI
disabled, curl disabled, and no downloaded UI, `node_modules`, or UI build
stamp. The runtime reported commit `67b9b0e` and build number `10088`.

This is WSL2 candidate evidence, not native Linux evidence. GPU access used the
Windows-hosted `/dev/dxg` bridge and ROCDXG 1.2.0 rather than a native Linux
`amdgpu` device. It therefore cannot validate native Linux driver installation,
desktop behavior, package lifecycle, or shutdown behavior.

The runner requires an explicit `--wsl-dxg` switch for this path. It rejects a
non-HIP backend, a Windows process, a non-WSL kernel, a missing device, a
symlink, or anything other than the real `/dev/dxg` character device. The child
receives a fixed `HSA_ENABLE_DXG_DETECTION=1`; inherited values are stripped
and cannot enable the mode.

All 11 artifacts passed SHA-256 and size verification, HIP/DXG device identity,
the fixed benchmark, full model-layer offload, bounded exit, and cleanup in one
coherent rerun. The same four artifacts passed the strict exact-output gate as
on the native Windows AMD and Linux NVIDIA cells.

| Artifact | Prompt tokens/s | Generation tokens/s | Exact 48-token response |
| --- | ---: | ---: | --- |
| Qwen3 0.6B Q4_0 | 7,387.72 | 255.57 | Miss |
| Qwen3.5 0.8B Q4_0 | 6,216.54 | 201.39 | Miss |
| Qwen3.5 0.8B Q8_0 | 1,866.58 | 198.83 | Miss |
| Gemma 3 1B Q4_K_M | 2,582.64 | 190.72 | Pass |
| SmolLM3 3B Q4_K_M | 2,983.81 | 149.50 | Miss |
| Granite 4.1 3B Q4_K_M | 2,322.79 | 132.76 | Pass |
| Phi-3 Mini 4K Q4 | 2,631.65 | 145.59 | Pass |
| Gemma 3 4B Q4_K_M | 2,474.54 | 88.88 | Pass |
| Qwen3 4B Q4_K_M | 2,292.34 | 123.87 | Miss |
| Qwen3.5 9B Q4_K_M | 999.70 | 74.98 | Miss |
| Qwen3 8B Q8_0 | 315.42 | 62.05 | Miss |

The first full pass encountered a transient failure in the final Qwen3 8B Q8
benchmark. The isolated cell and a complete coherent rerun both passed. This
is retained as a stability observation and prevents promotion beyond candidate
status. Throughput is diagnostic for this exact run and is not a platform
ranking.

An initial upstream-default build path attempted to install web-UI dependencies
and reported dependency vulnerabilities. That path was rejected. Only the
separate clean offline build described above was used for recorded inference
evidence; no web UI or dependency tree is admitted or packaged.

### Newer-runtime regression check

On August 12, 2026, the same WSL2/DXG profile compared newer exact llama.cpp
builds against the passing b10088 baseline. Builds b10375 and b10380 detected
the RX 7800 XT but exited before producing the first benchmark result. For
b10375, disabling HIP graphs and requesting zero, one, or all GPU layers did
not change the failure. An exact-commit CPU-only b10375 build passed the same
Gemma 3 1B artifact, which isolates the observed regression to loading the HIP
backend on this WSL2/DXG route rather than to the GGUF or core CPU path.

Haven 42 therefore retains b10088 as the last passing version for this exact
candidate route. The newer failures do not invalidate the historical b10088
matrix, do not establish native Linux AMD behavior, and do not authorize an
automatic runtime downgrade or selection change.

## Windows NVIDIA And Follow-On Results

An independent Windows x86_64 NVIDIA cell used the same b10088 source commit,
the official CUDA 12.4 runtime archives, and a Quadro RTX 5000 16 GB profile.
Both runtime archives matched the SHA-256 digests published with the release.
Only the three hash-pinned artifacts required by the declared follow-on cells
were staged, preserving the 40 GiB free-space floor. No Ollama runtime,
listener, service, global PATH entry, installer, or administrator access was
used.

Qwen 3.5 9B Q4_K_M passed build identity, CUDA device identity, full model-layer
offload, bounded exit, and cleanup. Its fixed baseline generated 58.979 tokens
per second and retained the known 48-token exact-output miss. The separate
strict patch cell passed, and three independent lifecycle starts each loaded,
generated the bounded marker, fully offloaded, exited, and left no process or
listener.

| Artifact and cell | Windows NVIDIA | Windows AMD | Decision |
| --- | --- | --- | --- |
| Qwen 3.5 9B repeated lifecycle | Pass, 3/3 | Pass, 3/3 | Operational evidence only |
| Qwen 3.5 9B strict one-token patch | Pass | Fail | Do not inherit patch evidence across accelerators |
| Qwen 3 8B 4K ordered-marker recall | Fail | Fail | No context-quality promotion |
| Qwen 3 8B 8K ordered-marker recall | Fail | Fail | No context-quality promotion |
| Qwen 3 8B repeated lifecycle | Pass, 3/3 | Pass, 3/3 | Operational evidence only |
| Qwen 3 8B strict one-token patch | Fail | Fail | No patch promotion |
| Gemma 3 4B synthetic PNG vision | Pass | Pass | Candidate vision evidence only |

The vision fixture was generated inside a temporary directory, required the
model to distinguish a red left half from a blue right half, and was deleted
after each run. Both platforms reported full offload and zero temporary
residue. Context validation required all three distant synthetic values,
exactly once and in order, inside a bounded response; formatting was tracked
separately and could not turn a recall failure into a pass.

The reusable follow-on runner downloads nothing, opens no listener, invokes no
shell, verifies every artifact before execution, uses only synthetic prompts,
stores no raw prompt or response, writes atomic sanitized checkpoints, and
deletes temporary prompt and image files. A separate bounded manual Ollama
0.32.5 run passed provider-envelope transport for four tool-capable installed
models and classified one model as unsupported, but it is not direct
accelerator-specific llama.cpp evidence.

On 2026-08-03, a separate ignored development harness exercised the pinned
`llama-server` OpenAI-compatible route directly on Windows NVIDIA/CUDA and
Windows AMD/HIP. Both cells used the identical hash-verified Qwen 3.5 9B
Q4_K_M artifact and exact b10088 runtime. Each reported its intended device,
fully offloaded all model layers, bound an ephemeral authenticated endpoint to
`127.0.0.1` only, returned one exact `inspect_file` call with the required
synthetic path, passed the existing fail-closed untrusted-argument policy,
executed no tool, retained no raw content, stopped its exact process, and
closed its listener. This closes the declared direct tool-call cells only for
these two Windows accelerator profiles. A later physical Windows Intel/SYCL
baseline passed artifact preflight but failed native model loading, so its
follow-on tool-call cell remains blocked. These results add no
provider route, automatic selection, model activation, package, or production
authority.

## Current Decision

The shared HIP/CUDA baseline is complete for these exact development profiles.
It does not replace the previously admitted Qwen3.5 9B HIP cell, widen
automatic selection, or inherit to another CUDA/HIP device, SYCL, Vulkan,
Ollama, or OpenVINO. It also does not admit either direct llama.cpp runtime as
a product route. The declared Windows NVIDIA/AMD patch, context-pressure,
repeated-lifecycle, and vision cells now have explicit pass/fail evidence.
The bounded Ollama provider-envelope transport cell and the direct Windows
NVIDIA/AMD llama.cpp tool-call cells are complete. Runtime integration remains
open, and failed quality cells remain non-promoting. The WSL2 AMD cell adds
bounded candidate evidence only; native Linux AMD validation remains open.
The physical Windows Intel baseline is attempted rather than untested, but the
official b10088 SYCL runtime's zero-free-memory report, tensor-load failure,
and OpenCL fallback fast-fail prevent any operational or quality evidence.
