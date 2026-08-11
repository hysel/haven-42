# Model and Hardware Test Status

_Last reviewed: August 11, 2026._

This page shows which model and computer combinations Haven 42 has actually
tested. It records bounded tests, not a promise that every similar computer
will work. A result applies only to the operating system, AI engine, model, and
hardware profile named in its row.

Haven 42 does not save private lab addresses, account names, machine names,
keys, prompts, responses, or local paths in this tracker.

## Status labels

- **✅ Verified** — every bounded check described in the row passed on that
  exact setup.
- **🧪 Engineering evidence** — useful controlled tests passed, but the result
  does not establish a complete end-user or release-candidate route.
- **⚠️ Partial** — some checks passed and at least one required check is
  incomplete or failed.
- **❌ Did not pass** — the model or route failed a required gate and is not
  promoted.
- **⬜ Not tested** — no result should be inferred from a different model,
  operating system, or graphics card.

These are test-result labels. Roadmap labels describe milestone delivery and
use a different scale.

## Alpha 2 computer coverage

| Computer profile | Status | Notes |
| --- | --- | --- |
| Windows 11 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Managed Ollama 0.32.5 and Qwen 3.5 0.8B passed chat, writing, summarization, unload, GPU-use, package-lifecycle, and graceful-shutdown checks. The distinct Alpha 2 package and final beginner workflow remain open. |
| Ubuntu 26.04 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Linux package parity, Qwen 3.5 CPU/CUDA task checks, driver checks, and GPU-use checks passed. The promotion-candidate desktop flow remains open. |
| Bazzite 44 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Linux package parity, Qwen 3.5 CPU/CUDA task checks, driver checks, and GPU-use checks passed. The promotion-candidate desktop flow remains open. |
| Ubuntu 24.04 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Debian 13 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Linux Mint 22.3 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Pop!_OS 24.04 with NVIDIA Quadro RTX 5000, 16 GB | ⚠️ Partial | Package checks exposed a fixed-path operating-system identity issue. A source-level correction passed natively, but a new exact package must still pass. |
| Fedora 44 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| CachyOS with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Arch Linux with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Windows 11 with AMD Radeon RX 7800 XT, 16 GB | 🧪 Engineering evidence | Earlier Alpha Ollama/ROCm and llama.cpp/HIP checks passed. An Alpha 2 release-candidate pass remains open. |
| Windows 11 with Intel Arc B580, 12 GB | ⚠️ Partial | Ollama with experimental Vulkan passed the exact Intel Alpha profile, but native llama.cpp with SYCL failed its model-loading gate. An Alpha 2 release-candidate pass remains open. |
| Linux with AMD graphics | ⬜ Not tested | No complete native Alpha 2 release-candidate cell exists. |
| Linux with Intel graphics | ⬜ Not tested | No complete native Alpha 2 release-candidate cell exists. |
| macOS on Apple silicon | 🧪 Engineering evidence | Earlier local-model workflow checks passed. No Alpha 2 package certification exists. |

All nine Linux distributions used the same unsigned candidate archive for the
package-parity checks. Those checks covered archive integrity, relocation,
read-only startup, repeated start and stop, abrupt-exit recovery, occupied
ports, hostile environment handling, and protected-resource integrity. They
did not certify the complete guided setup, accessibility, attachments,
uninstall, or tester-reporting experience.

## Approved automatic choices

These records use the managed Ollama 0.32.5 runtime. The owner approved the
exact records on August 11, 2026. Haven 42 still matches the operating system,
backend, runtime, memory, artifact digest (an exact-file checksum), and
requested tasks before making an
automatic choice. A nearby but untested configuration is not equivalent.

| Model | Tested profile | Tasks | Status | Notes |
| --- | --- | --- | --- | --- |
| Qwen 3.5 0.8B, Q8_0 | CPU on all nine Linux profiles | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for the exact CPU-tested profiles. |
| Qwen 3.5 0.8B, Q8_0 | CUDA on all nine Linux NVIDIA profiles | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved as the tested CUDA fallback for these profiles. |
| Qwen 3.5 0.8B, Q8_0 | Windows NVIDIA baseline | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved only for the exact tested Windows baseline. |
| Qwen 3.5 2B, Q8_0 | Ubuntu 26.04 with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for this exact CUDA profile. |
| Qwen 3.5 2B, Q8_0 | Bazzite 44 with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for this exact CUDA profile. |
| Qwen 3.5 4B, Q4_K_M | Ubuntu 26.04 with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for this exact CUDA profile. |
| Qwen 3.5 4B, Q4_K_M | Bazzite 44 with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for this exact CUDA profile. |

Haven 42 automatically chooses Qwen 3.5 0.8B Q8 on the exact CPU-tested Linux
profiles. On the exact Ubuntu 26.04 and Bazzite 44 CUDA profiles with 16 GiB
usable GPU memory, it chooses Qwen 3.5 4B Q4. The tested 0.8B and 2B CUDA
records remain fallbacks if the larger model does not pass the free-space
check.
Other Linux CUDA profiles remain evidence-pending even when comparison tests
succeeded.

The evidence includes measured system-memory and usable-GPU-memory floors.
Haven 42 must refuse automatic selection below the tested floor, even if a
model might technically start.

## Cross-family qualification results

Qualification uses three fixed samples for chat, writing, and summarization,
followed by a 30-minute soak test—a continuous run that looks for delayed
failures—only after the task checks pass. `Q4_K_M` and `Q8_0` are quantization
labels for the exact prepared model size; a result for one does not prove the
other. CUDA rows require a compatible NVIDIA GPU and do not apply to Intel Arc
or AMD graphics.
Every sample must unload cleanly. Raw prompts and responses are not retained.

| Model and profile | Status | Notes |
| --- | --- | --- |
| Gemma 3 1B, Q4_K_M on CPU | ❌ Did not pass | Failed the task gate; no soak ran. |
| Gemma 3 1B, Q4_K_M on 16 GB CUDA | ❌ Did not pass | Failed the task gate; no soak ran. |
| Gemma 3 4B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 3 4B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 E2B, QAT on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 E2B, QAT on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 E4B, QAT on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 E4B, QAT on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 12B, QAT on CPU | ⬜ Not tested | This model was not included in the CPU profile. |
| Gemma 4 12B, QAT on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for CUDA use. |
| Granite 4.1 3B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Granite 4.1 3B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Granite 4.1 8B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Granite 4.1 8B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Phi 4 Mini 3.8B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Phi 4 Mini 3.8B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Llama 3.2 3B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Llama 3.2 3B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Ministral 3 3B, Q4_K_M on CPU | ❌ Did not pass | Failed writing or summarization; no soak ran. |
| Ministral 3 3B, Q4_K_M on 16 GB CUDA | ❌ Did not pass | Failed writing or summarization; no soak ran. |
| Ministral 3 8B, Q4_K_M on CPU | ❌ Did not pass | Failed writing or summarization; no soak ran. |
| Ministral 3 8B, Q4_K_M on 16 GB CUDA | ❌ Did not pass | Failed writing or summarization; no soak ran. |
| Qwen 3.6 27B, Q4_K_M on CPU | ⬜ Not tested | This model was not tested on the CPU profile. |
| Qwen 3.6 27B, Q4_K_M on Windows with at least 31 GB system memory and 16 GB NVIDIA CUDA memory | 🧪 Engineering evidence | Passed task checks and a 30-minute soak on that exact review profile. This result does not apply to Intel Arc or AMD graphics and does not add the model to automatic selection. |

Engineering evidence is narrower than availability by default. None of these
qualification results changes the automatic model ladder or downloads a model
for an end user.

## Controlled comparison results

These models passed chat, writing, summarization, and unload checks on a
controlled external Ollama 0.32.6 provider. They compare model behavior; they
do not certify an end-user hardware profile.

| Model | Status | Notes |
| --- | --- | --- |
| Qwen 3.5 9B | 🧪 Engineering evidence | Controlled comparison only. |
| Gemma 3 12B | 🧪 Engineering evidence | Controlled comparison only. |
| Granite 4 7B | 🧪 Engineering evidence | Controlled comparison only. |
| Mistral Small 3.2 24B | 🧪 Engineering evidence | Controlled comparison only. |

## Open certification work

- Build and natively test the separated Windows Alpha 2 archive without
  changing the published Alpha 1 package.
- Complete the beginner guided-setup and daily-use sequence on Windows 11
  NVIDIA, Ubuntu 26.04 NVIDIA, and Bazzite NVIDIA.
- Build a new Linux candidate containing the Pop!_OS identity-path fix and
  repeat its native package/readiness sequence.
- Complete CPU-only desktop sequences on the remaining Linux distributions.
- Run native Alpha 2 AMD and Intel cells on Windows and Linux.
- Test constrained-memory and mixed-GPU computers before assigning labels.
- Test Qwen 3.6 35B only on a computer with at least 48 GB system memory.
- Admit Qwen 3.7 or 3.8 only after an official local artifact is verified.

## Detailed evidence

The canonical engineering records are:

- [[Alpha 2 Linux Long-Term Validation|Eng-Alpha-2-Linux-Long-Term-Validation]]
- [[Tested Hardware and AI Engines|Tested-Hardware-And-AI-Engines]]
- [[Evidence Dashboard|Eng-Evidence-Dashboard]]

If a result looks wrong or incomplete, open a GitHub issue or email
`haven42localai@gmail.com`. Name the operating system, graphics card, runtime
version, model, and row you are asking about. Do not include keys, passwords,
private addresses, prompts, or files.
