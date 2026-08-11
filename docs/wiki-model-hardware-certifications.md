# Model and Hardware Test Status

_Last reviewed: August 11, 2026._

This page shows which model and computer combinations Haven 42 has actually
tested. It is a record of bounded tests, not a promise that every similar
computer will work. A result applies only to the operating system, AI engine,
model, and hardware profile named here.

Haven 42 does not save private lab addresses, account names, machine names,
keys, or local paths in this tracker.

## How to read the results

- **Verified** means all checks named in that row passed on that exact setup.
- **Engineering pass** means useful native tests passed, but the complete
  beginner setup and release-candidate workflow is not finished.
- **Comparison only** means the model passed quality checks on a controlled
  server. It cannot become an automatic choice from that result alone.
- **Did not pass** means at least one required check failed. Haven 42 excludes
  that model or route from promotion.
- **Not yet verified** means no result should be inferred from another model,
  operating system, or graphics card.

## Alpha 2 computer coverage

| Computer profile | What passed | Current label |
| --- | --- | --- |
| Windows 11 with NVIDIA Quadro RTX 5000, 16 GB | Managed Ollama 0.32.5; Qwen 3.5 0.8B chat, writing, summarization, unload, GPU use, package lifecycle, and graceful shutdown | **Engineering pass**; the distinct Windows Alpha 2 package and final beginner workflow remain open |
| Ubuntu 26.04 with NVIDIA Quadro RTX 5000, 16 GB | Linux package parity; Qwen 3.5 CPU and CUDA task checks; native driver and GPU-use checks | **Engineering pass**; promotion-candidate desktop flow remains open |
| Bazzite 44 with NVIDIA Quadro RTX 5000, 16 GB | Linux package parity; Qwen 3.5 CPU and CUDA task checks; native driver and GPU-use checks | **Engineering pass**; promotion-candidate desktop flow remains open |
| Ubuntu 24.04, Debian 13, Linux Mint 22.3, Pop!_OS 24.04, Fedora 44, CachyOS, and Arch Linux with the 16 GB NVIDIA test profile | Linux package parity; Qwen 3.5 0.8B CPU and CUDA task checks; native driver and GPU-use checks | **Engineering pass**; NVIDIA results are experimental and complete desktop flows remain open |
| Windows 11 with AMD Radeon RX 7800 XT, 16 GB | Earlier Alpha Ollama/ROCm and llama.cpp/HIP checks | **Previously tested**; an Alpha 2 release-candidate pass remains open |
| Windows 11 with Intel Arc B580, 12 GB | Earlier Alpha Ollama/Vulkan and bounded llama.cpp checks | **Previously tested**; an Alpha 2 release-candidate pass remains open |
| Linux with AMD or Intel graphics | No complete native Alpha 2 release-candidate cell | **Not yet verified** |
| macOS on Apple silicon | Earlier local-model workflow testing | **Previously tested**; no Alpha 2 package certification yet |

All nine Linux distributions used the same unsigned candidate archive for the
package-parity checks. Those checks covered archive integrity, relocation,
read-only startup, repeated start and stop, abrupt-exit recovery, occupied
ports, hostile environment handling, and protected-resource integrity. They
did not by themselves certify the complete guided setup, accessibility,
attachments, uninstall, or tester-reporting experience.

## Models eligible for automatic-selection review

These results use the managed Ollama 0.32.5 runtime. Passing a test does not
change Haven 42's default model; that requires a separate owner decision.

| Model | Tested profile | Tasks | Result |
| --- | --- | --- | --- |
| Qwen 3.5 0.8B, Q8_0 | CPU on all nine Linux profiles; CUDA on all nine Linux NVIDIA profiles; separate Windows NVIDIA baseline | Chat, writing, summarization, unload, and execution-device checks | **Verified for the exact tested profiles** |
| Qwen 3.5 2B, Q8_0 | Ubuntu 26.04 and Bazzite with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | **Verified for those two CUDA profiles only** |
| Qwen 3.5 4B, Q4_K_M | Ubuntu 26.04 and Bazzite with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | **Verified for those two CUDA profiles only** |

The evidence includes measured system-memory and usable-GPU-memory floors.
Haven 42 must refuse automatic selection when a computer falls below the
tested floor, even if a model might technically start there.

## Cross-family qualification results

Qualification uses three deterministic samples for chat, writing, and
summarization, followed by a 30-minute soak only after the task checks pass.
Every sample must unload cleanly. Raw prompts and responses are not retained.

| Model | CPU profile | 16 GB CUDA profile | Outcome |
| --- | --- | --- | --- |
| Gemma 3 1B, Q4_K_M | Did not pass task gate | Did not pass task gate | **Did not pass**; no soak |
| Gemma 3 4B, Q4_K_M | Passed tasks and soak | Passed tasks and soak | **Qualified for owner review** |
| Gemma 4 E2B, QAT | Passed tasks and soak | Passed tasks and soak | **Qualified for owner review** |
| Gemma 4 E4B, QAT | Passed tasks and soak | Passed tasks and soak | **Qualified for owner review** |
| Gemma 4 12B, QAT | Not in this CPU profile | Passed tasks and soak | **Qualified for CUDA owner review only** |
| Granite 4.1 3B, Q4_K_M | Passed tasks and soak | Passed tasks and soak | **Qualified for owner review** |
| Granite 4.1 8B, Q4_K_M | Passed tasks and soak | Passed tasks and soak | **Qualified for owner review** |
| Phi 4 Mini 3.8B, Q4_K_M | Passed tasks and soak | Passed tasks and soak | **Qualified for owner review** |
| Llama 3.2 3B, Q4_K_M | Passed tasks and soak | Passed tasks and soak | **Qualified for owner review** |
| Ministral 3 3B, Q4_K_M | Did not pass writing or summarization gate | Did not pass writing or summarization gate | **Did not pass**; no soak |
| Ministral 3 8B, Q4_K_M | Did not pass writing or summarization gate | Did not pass writing or summarization gate | **Did not pass**; no soak |
| Qwen 3.6 27B, Q4_K_M | Not tested on this CPU profile | Passed tasks and 30-minute soak on Windows with at least 31 GB system memory and 16 GB CUDA memory | **Qualified for that exact owner-review profile** |

“Qualified for owner review” is deliberately narrower than “available by
default.” None of these qualification results changes the automatic model
ladder or downloads a model for an end user.

## Comparison-only models

The following models passed chat, writing, summarization, and unload checks on
a controlled external Ollama 0.32.6 provider. The results compare model
behavior; they do not certify an end-user hardware profile.

| Model | Result |
| --- | --- |
| Qwen 3.5 9B | **Comparison only** |
| Gemma 3 12B | **Comparison only** |
| Granite 4 7B | **Comparison only** |
| Mistral Small 3.2 24B | **Comparison only** |

## Open certification work

- Build and natively test the newly separated Windows Alpha 2 archive without
  changing the published Alpha 1 package.
- Complete the beginner guided-setup and daily-use sequence on Windows 11
  NVIDIA, Ubuntu 26.04 NVIDIA, and Bazzite NVIDIA.
- Complete CPU-only desktop sequences on the remaining Linux distributions.
- Run native Alpha 2 AMD and Intel cells on Windows and Linux.
- Test constrained-memory and mixed-GPU computers before assigning those
  labels.
- Test Qwen 3.6 35B only on a computer with at least 48 GB system memory.
- Admit Qwen 3.7 or 3.8 only after an official local artifact is verified.

## Detailed evidence

For the exact boundaries and test design, see
[[Alpha 2 Linux Long-Term Validation|Alpha-2-Linux-Long-Term-Validation]],
[[Tested Hardware and AI Engines|Tested-Hardware-And-AI-Engines]], and
[[Evidence Dashboard|Evidence-Dashboard]]. Engineering records live in the
repository under `config/alpha-2-*` and contain no private lab identity.

If a result looks wrong or incomplete, open a GitHub issue or email
`haven42localai@gmail.com`. Please name the operating system, graphics card,
runtime version, model, and the row you are asking about; do not include keys,
passwords, or private addresses.
