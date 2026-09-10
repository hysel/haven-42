# Quadro P4000 8 GB: Windows and Ubuntu inference results

On September 9, 2026, all five pinned model artifacts below passed Chat,
Writing, and Summarization checks and a separate 30-minute repeated-load soak
on each of two operating-system profiles. Windows passed 699 responses;
Ubuntu passed 735. Every response passed its unload check, with zero failed
samples and a verified final unload on both profiles.

## Tested profiles

| Component | Windows | Ubuntu |
| --- | --- | --- |
| Operating system | Windows 11 Pro, build 26200 | Ubuntu 26.04.1 LTS |
| Kernel | Windows build 26200 | 7.0.0-31-generic |
| NVIDIA driver | 582.78 | 580.178.04 |
| GPU | Quadro P4000, 8 GB | Quadro P4000, 8 GB |
| Detected system RAM | About 128 GiB | About 121 GiB |
| Runtime | Ollama 0.32.14, CUDA | Ollama 0.32.14, CUDA |

The Windows runtime used its CUDA 12 backend after the CUDA 13 backend
rejected Pascal compute capability 6.1. That fallback is not a CUDA 13 pass.

## Model results

Each model passed nine core samples per operating system: three per capability.
The soak cycles those capabilities in three-response groups, with pauses and
unloads. It is not a continuous thermal stress test. Sample counts differ
because each model has its own 30-minute window, not a fixed response count.

| Exact artifact | Windows core / soak samples | Ubuntu core / soak samples | Result on both |
| --- | --- | --- | --- |
| Qwen3.5 9B Q4_K_M | 9 / 123 | 9 / 129 | Passed |
| Qwen3.5 4B Q4_K_M | 9 / 126 | 9 / 135 | Passed |
| Qwen3.5 2B Q8_0 | 9 / 129 | 9 / 135 | Passed |
| Phi-4 Mini 3.8B Q4_K_M | 9 / 138 | 9 / 147 | Passed |
| Llama3.2 3B Q4_K_M | 9 / 138 | 9 / 144 | Passed |

Full manifest digests, per-model durations, counts, and private-source hashes
are recorded in [Windows results](../config/p4000-windows-inference-result.json)
and [Ubuntu results](../config/p4000-ubuntu-inference-result.json).

## Temperature and power checkpoints

The controller queried `nvidia-smi` before each three-response group and at
model preflight. These sparse checkpoints generally follow an unload or pause.
They are not continuous load measurements and may miss the highest temperature
and power draw. The averages below are arithmetic means of those checkpoints,
not time-weighted averages over the run.

| Checkpoint measurement | Windows | Ubuntu |
| --- | --- | --- |
| Samples | 238 | 250 |
| Temperature range | 42–58 °C | 41–57 °C |
| Mean temperature | 51.647 °C | 49.276 °C |
| GPU-board power range | 6.32–35.51 W | 5.93–42.40 W |
| Mean checkpoint power | 17.900 W | 16.185 W |

This is GPU-board power, not wall power. No energy-consumption estimate or
Windows-versus-Linux efficiency ranking is justified by these checkpoints.
The separately collected Windows HWiNFO log remains private. Its SHA-256 and
size are retained for provenance; its continuous readings are not summarized
here and are not the source of this table.

## Scope and missing checks

These results apply to the two tested profiles and exact model digests. They
do not certify the entire Pascal or GTX 10-series family. They do not change
automatic model defaults or support labels. Other model artifacts were not
tested in this run. These were high-system-memory profiles, not tests of an
8 GB system-RAM computer; 8 GB refers to GPU memory.

Coding-agent repository read, planning, review, filename fidelity, scoped edit,
tool-call, bounded-context, timeout-recovery, and unintended-write checks are
all **not-run**. Inference unload passed, but coding-surface unload remains
**not-run**. Interactive packaged-app and accessibility checks are **not-run**.
No coding-agent recommendation follows from these inference results.

Raw logs, HWiNFO data, local paths, network identities, prompts, and responses
are excluded from the public result records. The collected Ubuntu files were
hash-verified against their remote originals, and the Windows HWiNFO copy was
hash-verified before the machine changed operating systems.
