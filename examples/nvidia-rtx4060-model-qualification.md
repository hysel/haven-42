# GeForce RTX 4060 8 GB: Windows and Ubuntu inference results

Five exact model artifacts passed Chat, Writing, Summarization, and separate
30-minute repeated-load soaks on each profile. Each operating system recorded
717 passed responses, zero failed responses, 717 unload passes, and a verified
final unload. Windows ran on September 8, 2026; Ubuntu ran on September 9.

## Tested profiles

| Component | Windows | Ubuntu |
| --- | --- | --- |
| Operating system | Windows 11 Pro, build 26200 | Ubuntu 26.04.1 LTS |
| Kernel | Windows build 26200 | 7.0.0-31-generic |
| NVIDIA driver | 616.64 | 610.57.04 |
| GPU | GeForce RTX 4060, 8188 MiB reported | GeForce RTX 4060, 8188 MiB reported |
| Detected system RAM | About 128 GiB | About 121 GiB |
| Runtime | Ollama 0.32.14, CUDA | Ollama 0.32.14, CUDA |

These are high-system-memory profiles. The GPU's 8 GB does not mean these
tests ran on computers with 8 GB of system RAM.

## Model results

Each core gate used three responses per capability, nine responses per model.
Soaks cycled those capabilities in three-response groups with pauses and unloads.
Counts vary within the fixed-duration windows; this is not continuous thermal stress.

| Exact artifact | Windows core / soak samples | Ubuntu core / soak samples | Result on both |
| --- | --- | --- | --- |
| Qwen3.5 9B Q4_K_M | 9 / 126 | 9 / 129 | Passed |
| Qwen3.5 4B Q4_K_M | 9 / 132 | 9 / 132 | Passed |
| Qwen3.5 2B Q8_0 | 9 / 132 | 9 / 132 | Passed |
| Phi-4 Mini 3.8B Q4_K_M | 9 / 141 | 9 / 138 | Passed |
| Llama3.2 3B Q4_K_M | 9 / 141 | 9 / 141 | Passed |

Full model digests, durations, and source hashes are in the
[Windows record](../config/rtx4060-windows-inference-result.json) and
[Ubuntu record](../config/rtx4060-ubuntu-inference-result.json).

## Telemetry and collection

Both runs have 244 sparse `nvidia-smi` checkpoints before test groups and at
model preflight. Windows recorded 41–66 °C; Ubuntu recorded 42–58 °C. These
are observed checkpoints, not continuous peaks. Driver power was unavailable
at every checkpoint on both systems; it is recorded as unavailable, never zero.
No GPU energy or wall-power claim follows from these data.

The Windows HWiNFO file remains private, represented by its SHA-256 and size.
Its readings are not summarized here. All copied Ubuntu run files and the Windows
HWiNFO file were hash-verified against their sources before hardware was released.
The Windows reboot occurred after completion, not during the retained run.
An earlier attempt stopped before inference because its telemetry parser did
not accept unavailable power readings; that attempt is not counted as a model failure.

## Scope and missing checks

This is evidence for these exact profiles and model digests, not the whole Ada
family, other drivers, or all RTX 4060 computers. It changes no automatic default
or support label. Coding-agent read, planning, review, filename fidelity, scoped
edit, tool-call, bounded-context, timeout-recovery, coding-surface unload, and
unintended-write gates are all **not-run**. Interactive packaged-app and
accessibility checks are **not-run**. No coding recommendation is implied.
