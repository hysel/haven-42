# Hardware Compatibility

_Last reviewed: August 21, 2026._

Use this page to find configurations similar to your computer. Each row names
the operating system, graphics hardware, and AI engine that were tested
together. A result applies only to that row; it does not prove that every
computer with the same graphics-card family will behave the same way.

Haven 42 does not retain private lab addresses, account names, cloud
identifiers, keys, or local file paths in this public record.

For model choices, see [[Model Compatibility|Model-And-Hardware-Test-Status]].

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

These labels describe only the named test result.

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
| Ubuntu 26.04 LTS, physical machine | AMD Radeon RX 5700 XT, 8 GB | Ollama 0.32.13 with Vulkan and Mesa RADV | 🧪 Engineering evidence | Nine exact profiles passed the core task gate, three oversized candidates were refused before download, full-residency checks passed where requested, and a bounded current-boot stability and board-power profile completed. Seven profiles failed required task contracts; final-profile full-memory and packaged lifecycle testing remain open. |
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
| Native macOS 26.6.2, physical Mac | Apple M4, 16 GB unified memory | Ollama 0.32.15 with Metal | 🧪 Engineering evidence | Seventeen exact artifacts completed the bounded five-gate test set; ten passed and then completed independent 30-minute soaks with no failures. All 17 OpenCode 1.18.19 cells failed at least one required coding-agent gate. The separately approved Gemma 4 12B QAT addendum is included; no default or support promotion is granted. |
| Native macOS 26.6.2, physical Mac | Apple M4, 16 GB unified memory | llama.cpp `b10520` commit cd644c395 with Metal | ⚠️ Partial | The pinned Qwen 3.5 0.8B GGUF passed full-layer Metal offload, authenticated loopback inference, recovery, restart, unload, and cleanup. Exact LFM2.5 1.2B and 2.6B Q4_K_M files also proved full Metal offload, but both failed bounded core gates and timed out in the OpenCode coding screen without changing files, so neither soaked or earned a recommendation. The official arm64 archive passed integrity and relocation checks but remains ad-hoc signed and rejected by Gatekeeper. |
| Native macOS 26.6.2, physical Mac | Apple M4, 16 GB unified memory | MLX-LM 0.31.3 | ⚠️ Partial | The pinned Qwen 3.5 0.8B artifact passed offline native generation, Metal-memory proof, timeout recovery, and cleanup. A production server boundary, self-contained packaging, and a maintained coding surface remain open. |
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
