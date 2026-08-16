# Tested Hardware and AI Engines

_Last reviewed: August 13, 2026._

This page summarizes the real operating systems, hardware, and AI engines used
during Haven 42 development. A result applies only to the row shown. It does
not prove that every computer with the same GPU family will behave the same
way.

Haven 42 does not retain private lab addresses, account names, cloud
identifiers, keys, or local file paths in this public record.

For model-specific Alpha 2 results, see [[Model and Hardware Test
Status|Model-And-Hardware-Test-Status]].

## Status labels

- **✅ Verified** — every bounded check described in the row passed on that
  exact setup.
- **🧪 Engineering evidence** — useful controlled tests passed, but the result
  does not establish a complete end-user or release-candidate route.
- **⚠️ Partial** — some checks passed and at least one required check is
  incomplete or failed.
- **❌ Did not pass** — the setup failed a required execution or quality gate.
- **⬜ Not tested** — no result should be inferred from a different operating
  system, GPU, runtime, or model.

These are test-result labels. Roadmap labels describe milestone delivery and
use a different scale.

## Tested combinations

This table combines the former computer inventory and runtime-combination
tables so each result can be read without matching rows by hand.

| Operating system and environment | Hardware | AI engine | Status | Notes |
| --- | --- | --- | --- | --- |
| Windows 11 x64, physical machine | AMD Radeon RX 7800 XT, 16 GB | Ollama with ROCm | ✅ Verified | Passed the bounded Windows Alpha checks. |
| Windows 11 x64, physical machine | AMD Radeon RX 7800 XT, 16 GB | Ollama 0.32.9 with ROCm, 17-model recertification | ⚠️ Partial | Fourteen exact models passed full-offload three-task soaks; Granite 4 7B and Ministral 3 3B/8B failed Summarization before soak. No final recommendation is made. |
| Windows 11 x64, physical machine | AMD Radeon RX 7800 XT, 16 GB | llama.cpp with HIP and ROCm | ✅ Verified | Passed engine and tool-call checks. |
| Windows 11 x64, physical machine | AMD Radeon RX 7800 XT, 16 GB | llama.cpp with Vulkan | ⚠️ Partial | Runtime checks ran, but the patch-quality gate failed. |
| Ubuntu 24.04 under WSL2 | AMD Radeon RX 7800 XT, 16 GB through DXG | llama.cpp with HIP and DXG | 🧪 Engineering evidence | Passed the model matrix as candidate evidence; this is not a supported product route. |
| Windows 11 x64, physical and Windows-to-Go profiles | Intel Arc B580, 12 GB | Ollama with experimental Vulkan | ✅ Verified | Passed the exact bounded Intel Alpha profile. |
| Windows 11 x64, physical machine | Intel Arc B580, 12 GB | llama.cpp with SYCL | ❌ Did not pass | Failed the native model-loading gate. |
| Ubuntu 26.04 Desktop, physical machine | Intel Arc B580, 12 GB | llama.cpp with SYCL | ⚠️ Partial | Functional checks passed, but three upstream tests failed. |
| Windows 11 x64, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | ✅ Verified | Passed the bounded Windows Alpha checks. |
| Windows 11 x64, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | llama.cpp with CUDA | ✅ Verified | Passed engine, vision, lifecycle, and tool-call checks. |
| Ubuntu 26.04 Desktop, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | ✅ Verified | Passed Alpha 2 package, task, driver, and GPU-use checks for the exact profile. |
| Bazzite 44, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | ✅ Verified | Passed Alpha 2 package, task, driver, and GPU-use checks for the exact profile. |
| Linux Mint 22.3, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | 🧪 Engineering evidence | Source-candidate managed lifecycle passed, including interrupted-setup recovery; packaged desktop repetition remains open. |
| Ubuntu 24.04, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | 🧪 Engineering evidence | Source-candidate managed lifecycle passed; packaged desktop repetition remains open. |
| Debian 13, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | 🧪 Engineering evidence | Source-candidate managed lifecycle passed; packaged desktop repetition remains open. |
| Pop!_OS 24.04, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | 🧪 Engineering evidence | The corrected system identity path passed the source-candidate managed lifecycle; packaged desktop repetition remains open. |
| Fedora 44, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | 🧪 Engineering evidence | The completion-receipt ordering correction passed the source-candidate managed lifecycle; packaged desktop repetition remains open. |
| CachyOS, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | 🧪 Engineering evidence | Source-candidate managed lifecycle passed through an explicit Bash launcher; packaged desktop repetition remains open. |
| Arch Linux, Proxmox virtual machine | NVIDIA Quadro RTX 5000, 16 GB | Ollama with CUDA | 🧪 Engineering evidence | Source-candidate managed lifecycle passed through an explicit Bash launcher; packaged desktop repetition remains open. |
| Ubuntu Linux, controlled server | NVIDIA Quadro RTX 5000, 16 GB | llama.cpp with CUDA | ✅ Verified | Passed the bounded engine and Haven adapter checks. |
| Ubuntu Linux, Proxmox container and server | Two NVIDIA Tesla V100 GPUs, 32 GB each | Ollama with CUDA | ✅ Verified | Passed external-server and model checks. |
| Ubuntu Linux, controlled server | NVIDIA Tesla V100, 32 GB | llama.cpp with CUDA | ✅ Verified | Passed the 11-model operational matrix. |
| Native macOS, AWS EC2 Mac system | Apple silicon, 16 GB unified memory | Ollama | ✅ Verified | Passed the bounded local-model workflow checks. |
| Native macOS | Apple silicon | llama.cpp with Metal | ⬜ Not tested | Hardware-specific validation remains parked. |
| Proxmox VE 9.2, physical host | Two Tesla V100 32 GB GPUs and one Quadro RTX 5000 16 GB GPU | Virtualization and passthrough host | 🧪 Engineering evidence | Used as test infrastructure; this does not establish an end-user runtime route. |

## Detailed records

The canonical engineering documents are:

- [[Inference Engine Architecture|Eng-Inference-Engine-Architecture]]
- [[Inference Engine Validation|Eng-Inference-Engine-Validation]]
- [[Cross-Accelerator Model Validation|Eng-Cross-Accelerator-Model-Validation]]

If a result looks wrong or incomplete, open a GitHub issue or email
`haven42localai@gmail.com`. Name the operating system, graphics card, runtime
version, and row you are asking about. Do not include keys, passwords, private
addresses, prompts, or files.
