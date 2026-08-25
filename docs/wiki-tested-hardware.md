# Tested Hardware and AI Engines

_Last reviewed: August 22, 2026._

This page records the operating system, accelerator, and AI engine tested
together. Use it to check whether that exact route has been exercised. To see
which models passed, use [[Model and Hardware Test Status|Model-And-Hardware-Test-Status]].

A row does not cover an entire hardware family. The driver, runtime version,
model artifact, backend, memory behavior, and task can change the result even
when the GPU name looks similar.

Haven 42 does not retain private lab addresses, account names, cloud
identifiers, keys, or local file paths in this public record.

## How to use this table

- Match the operating system, GPU, and engine before relying on a row.
- Treat Windows, native Linux, WSL2, virtual machines, and containers as
  different environments.
- Treat CUDA, Vulkan, ROCm/HIP, SYCL, and Metal as different accelerator routes.
- Follow the linked engineering record when you need exact versions, artifacts,
  checks, or failure details.
- Do not use this page as a hardware shopping leaderboard.

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

Each row combines the computer and runtime details needed to read the result
without cross-referencing another table.

| Operating system and environment | Hardware | AI engine | Status | Notes |
| --- | --- | --- | --- | --- |
| Windows 11 x64, physical machine | AMD Radeon RX 7800 XT, 16 GB | Ollama with ROCm | ✅ Verified | Passed the bounded Windows Alpha checks. |
| Windows 11 x64, physical machine | AMD Radeon RX 7800 XT, 16 GB | Ollama 0.32.9 with ROCm, 17-model recertification | ⚠️ Partial | Fourteen exact models passed full-offload three-task soaks; Granite 4 7B and Ministral 3 3B/8B failed Summarization before soak. No final recommendation is made. |
| Windows 11 x64, physical machine | AMD Radeon RX 7800 XT, 16 GB | llama.cpp with HIP and ROCm | ✅ Verified | Passed engine and tool-call checks. |
| Windows 11 x64, physical machine | AMD Radeon RX 7800 XT, 16 GB | llama.cpp with Vulkan | ⚠️ Partial | Runtime checks ran, but the patch-quality gate failed. |
| Ubuntu 24.04 under WSL2 | AMD Radeon RX 7800 XT, 16 GB through DXG | llama.cpp with HIP and DXG | 🧪 Engineering evidence | Passed the model matrix as candidate evidence; this is not a supported product route. |
| Ubuntu 26.04 LTS, physical machine | AMD Radeon RX 6800 non-XT, 16 GB | Ollama 0.32.14 with Vulkan and Mesa RADV | 🧪 Engineering evidence | Thirteen exact model artifacts were checked. Ten passed the Chat, Writing, and Summarization gate and independent 30-minute soaks; three failed required Writing or Summarization contracts. No automatic default, managed-runtime choice, or support label changed. |
| Ubuntu 26.04 LTS, physical machine | AMD Radeon RX 5700 XT, 8 GB | Ollama 0.32.13 with Vulkan and Mesa RADV | 🧪 Engineering evidence | Nine exact profiles passed the core task gate, three oversized candidates were refused before download, full-residency checks passed where requested, and a bounded current-boot stability and board-power profile completed. Seven profiles failed required task contracts; final-profile full-memory and packaged lifecycle testing remain open. |
| Ubuntu 26.04 LTS, physical machine | AMD Radeon RX 5700 XT, 8 GB | llama.cpp `b10375` with Vulkan and Mesa RADV | ⚠️ Partial | A hash-pinned Qwen 3.5 0.8B GGUF passed device discovery, exact-response generation, full 25-layer GPU offload, VRAM recovery, and process cleanup. This was a bounded one-model engine smoke, not a full model or package qualification. |
| Windows 11 x64 build 10.0.26200.8973, physical machine | AMD Radeon RX 5700 XT, 8 GB | llama.cpp `b10375` with Vulkan and AMD driver 26.7.1 | ⚠️ Partial | A hash-pinned Qwen 3.5 0.8B GGUF passed nine of nine task samples, 1,602 of 1,602 requests during a 30-minute soak, full 25-layer GPU offload, device proof, and cleanup. Other models, packaged lifecycle, and automatic selection remain open. |
| Windows 11 x64, physical and Windows-to-Go profiles | Intel Arc B580, 12 GB | Ollama with experimental Vulkan | ✅ Verified | Passed the exact bounded Intel Alpha profile. |
| Windows 11 x64, physical machine | Intel Arc B580, 12 GB | llama.cpp with SYCL | ❌ Did not pass | Failed the native model-loading gate. |
| Ubuntu 26.04 Desktop, physical machine | Intel Arc B580, 12 GB | llama.cpp with SYCL | ⚠️ Partial | Functional checks passed, but three upstream tests failed. |
| Ubuntu 26.04 LTS, physical machine | Intel Arc B580, 12 GB | OpenVINO GenAI 2026.2.1 | ⚠️ Partial | The immutable Qwen3 0.6B INT4 model passed GPU discovery and five fresh load, generate, unload, and cleanup cycles. Strict output behavior failed, the host OS is outside OpenVINO's documented support baseline, and no Haven 42 provider or package is available for this route. |
| Windows 11 x64, physical machine | Intel Arc B580, 12 GB | OpenVINO GenAI 2026.2.0 | ⚠️ Partial | A hash-verified portable runtime and immutable Qwen3 0.6B INT4 model passed GPU discovery, three direct inference lifecycles, and process cleanup. Strict output behavior failed, and no provider, installer, automatic download, or package support is available for this route. |
| Windows 11 x64, physical machine | NVIDIA GeForce GTX 1650 Super, 4 GB | Ollama 0.32.14 with CUDA | 🧪 Engineering evidence | Eight exact model artifacts were checked. Three passed the Chat, Writing, and Summarization gate and independent 30-minute soaks; five larger candidates stopped at the full-CUDA-residency gate. No automatic default or support label changed. |
| Ubuntu 26.04 LTS, physical machine | NVIDIA GeForce GTX 1650 Super, 4 GB | Ollama 0.32.14 with CUDA | 🧪 Engineering evidence | Eight exact model artifacts were checked. Five passed the Chat, Writing, and Summarization gate and independent 30-minute soaks; three larger candidates stopped at the full-CUDA-residency gate. No automatic default or support label changed. |
| Windows 11 x64, physical machine | NVIDIA GeForce RTX 3060, 12 GB | Ollama 0.32.14 with CUDA | 🧪 Engineering evidence | Fourteen of 19 exact model artifacts passed the core task gate and independent 30-minute soaks. Five stopped at explicit task-contract failures. One OpenCode workflow passed, but the complete coding-policy gate remains incomplete and no coding recommendation is granted. |
| Ubuntu 26.04 LTS, physical machine | NVIDIA GeForce RTX 3060, 12 GB | Ollama 0.32.14 with CUDA | 🧪 Engineering evidence | All 19 exact model artifacts passed the Chat, Writing, and Summarization gate, unload checks, and independent 30-minute soaks. This exact-profile result does not establish another operating system, automatic default, or general support label. |
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
| Native macOS 26.6.2, physical Mac | Apple M4, 16 GB unified memory | llama.cpp `b10520` commit cd644c395 with Metal | ⚠️ Partial | Pinned Qwen 3.5 0.8B passed lifecycle and full-layer Metal checks. Exact LFM2.5 1.2B and 2.6B Q4_K_M files also proved full Metal offload, but failed bounded core and OpenCode coding gates. The official arm64 archive passed integrity and relocation checks but remains ad-hoc signed and rejected by Gatekeeper. |
| Native macOS 26.6.2, physical Mac | Apple M4, 16 GB unified memory | MLX-LM 0.31.3 | ⚠️ Partial | Pinned Qwen 3.5 0.8B passed offline native generation, Metal-memory proof, timeout recovery, and cleanup. Production server, packaging, and maintained coding-surface gates remain open. |
| Proxmox VE 9.2, physical host | Two Tesla V100 32 GB GPUs and one Quadro RTX 5000 16 GB GPU | Virtualization and passthrough host | 🧪 Engineering evidence | Used as test infrastructure; this does not establish an end-user runtime route. |

## Detailed card-by-card records

Use these reports for the exact models, software versions, test duration,
failures, speeds, or power measurements for one graphics card. Windows and
Ubuntu results are separate because success on one operating system does not
prove success on the other.

| Graphics hardware | Operating system | What the detailed record contains |
| --- | --- | --- |
| GeForce GTX 1650 Super, 4 GB | Windows 11 | [Models tested and their results](Eng-NVIDIA-GTX1650-Super-Windows-Model-Qualification) |
| GeForce GTX 1650 Super, 4 GB | Ubuntu 26.04 | [Models tested and their results](Eng-NVIDIA-GTX1650-Super-Linux-Model-Qualification) |
| GeForce RTX 3060, 12 GB | Windows 11 | [Models tested and their results](Eng-NVIDIA-RTX3060-Windows-Model-Qualification) |
| GeForce RTX 3060, 12 GB | Ubuntu 26.04 | [Models tested and their results](Eng-NVIDIA-RTX3060-Linux-Model-Qualification) |
| Quadro RTX 5000, 16 GB | Ubuntu 26.04 | [Measured model power use](Eng-NVIDIA-Quadro-RTX5000-Power-Validation); model and operating-system coverage is summarized in the table above |
| One or two Tesla V100 cards, 32 GB each | Ubuntu 24.04 | [Ollama 0.32.13 models](Eng-NVIDIA-V100-Ollama-03213-Qualification), [Nemotron models](Eng-NVIDIA-V100-Nemotron-Validation), and [single-card power use](Eng-NVIDIA-Tesla-V100-Single-Power-Validation) |
| Radeon RX 5700 XT, 8 GB | Ubuntu 26.04 and Windows 11 | [Models, accelerator use, and failures](Eng-AMD-RX5700XT-Ollama-03213-Qualification) |
| Radeon RX 6800, 16 GB | Ubuntu 26.04 | [Models tested and their results](Eng-AMD-RX6800-Linux-Model-Qualification) |
| Radeon RX 7800 XT, 16 GB | Windows 11 | [Models tested and their results](Eng-AMD-RX7800XT-Windows-Ollama-0329-Recertification) and [measured model power use](Eng-AMD-RX7800XT-Windows-Power-Validation) |
| Intel Arc B580, 12 GB | Ubuntu and Windows | [Inference-engine and accelerator results](Eng-Intel-B580-Inference-Engine-Validation) |
| Apple M4, 16 GB unified memory | macOS 26.6.2 | [Models, Metal acceleration, soaks, and coding checks](Eng-Apple-M4-16GiB-Model-Qualification) |

## Other local AI workloads

Image and audio generation use different qualification gates from text
inference. Their exact hardware and runtime results are kept in separate
records:

| Workload | Tested configurations | Current result | Detailed records |
| --- | --- | --- | --- |
| Local image generation | ComfyUI on Windows 11 with AMD Radeon RX 7800 XT, Intel Arc B580, and NVIDIA Quadro RTX 5000 | ⚠️ Partial | [AMD result](Eng-Windows-AMD-Image-Provider-Validation), [Intel result](Eng-Windows-Intel-Image-Provider-Validation), and [NVIDIA result](Eng-Windows-NVIDIA-Image-Provider-Validation) |
| Local audio generation | ACE-Step 1.5 on Linux with NVIDIA Tesla V100 and Quadro RTX 5000 | ⚠️ Partial | [Audio-provider results](Eng-Local-Audio-Provider-Validation) |

For broader engineering detail, see:

- [[Inference Engine Architecture|Eng-Inference-Engine-Architecture]]
- [[Inference Engine Validation|Eng-Inference-Engine-Validation]]
- [[Cross-Accelerator Model Validation|Eng-Cross-Accelerator-Model-Validation]]

If a result looks wrong or incomplete, open a GitHub issue or email
`haven42localai@gmail.com`. Name the operating system, graphics card, runtime
version, and row you are asking about. Do not include keys, passwords, private
addresses, prompts, or files.
