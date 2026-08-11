# Tested Hardware and AI Engines

This page summarizes the real computers and operating systems used during Haven
42 development. A successful result applies only to the listed combination. It
does not guarantee that every computer with the same GPU family will behave the
same way.

For the current Alpha 2 status of individual models and computer profiles, see
[[Model and Hardware Test Status|Model-And-Hardware-Test-Status]].

## Computers used for testing

| Operating system | Hardware | Environment |
| --- | --- | --- |
| Windows 11 x64 | AMD Radeon RX 7800 XT, 16 GB | Physical machine |
| Windows 11 x64 | Intel Arc B580, 12 GB | Physical machine and Windows-to-Go |
| Ubuntu 26.04 Desktop | Intel Arc B580, 12 GB | Physical machine |
| Windows 11 x64 | NVIDIA Quadro RTX 5000, 16 GB | Proxmox virtual machine |
| Ubuntu 26.04 Desktop | NVIDIA Quadro RTX 5000, 16 GB | Proxmox virtual machine |
| Bazzite Linux | NVIDIA Quadro RTX 5000, 16 GB | Proxmox virtual machine |
| Ubuntu 24.04 | AMD Radeon RX 7800 XT, 16 GB through DXG | WSL2 |
| Ubuntu Linux | Two NVIDIA Tesla V100 GPUs, 32 GB each | Proxmox container and server |
| Proxmox VE 9.2 | Two Tesla V100 32 GB GPUs and one Quadro RTX 5000 16 GB GPU | Physical virtualization host |
| Native macOS | Apple Silicon, 16 GB unified memory | AWS EC2 Mac system |

The public evidence intentionally does not retain private machine addresses,
account names, AWS identifiers, or local file paths.

## Ollama and llama.cpp combinations

| Runtime | Operating system | Hardware | Result |
| --- | --- | --- | --- |
| Ollama with CUDA | Windows 11 x64 | NVIDIA Quadro RTX 5000, 16 GB | Passed Haven 42 Alpha testing |
| Ollama with ROCm | Windows 11 x64 | AMD Radeon RX 7800 XT, 16 GB | Passed Haven 42 Alpha testing |
| Ollama with experimental Vulkan | Windows 11 x64 | Intel Arc B580, 12 GB | Passed the exact Intel Alpha test profile |
| Ollama with CUDA | Ubuntu Linux | NVIDIA 16 GB profile | Passed Q4_K_M and Q8_0 comparison |
| Ollama with CUDA | Ubuntu Linux and Proxmox container | Two NVIDIA Tesla V100 GPUs, 32 GB each | Passed external-server and model testing |
| Ollama | Native macOS | Apple Silicon, 16 GB unified memory | Passed local model workflow testing |
| llama.cpp with CUDA | Ubuntu Linux | NVIDIA Quadro RTX 5000, 16 GB | Passed engine and Haven adapter tests |
| llama.cpp with CUDA | Ubuntu Linux | NVIDIA Tesla V100, 32 GB | Passed the 11-model operational matrix |
| llama.cpp with CUDA | Windows 11 x64 | NVIDIA Quadro RTX 5000, 16 GB | Passed engine, vision, lifecycle, and tool-call tests |
| llama.cpp with HIP and ROCm | Windows 11 x64 | AMD Radeon RX 7800 XT, 16 GB | Passed engine and tool-call tests |
| llama.cpp with Vulkan | Windows 11 x64 | AMD Radeon RX 7800 XT, 16 GB | Partial result; the patch-quality gate failed |
| llama.cpp with HIP and DXG | Ubuntu 24.04 under WSL2 | AMD Radeon RX 7800 XT, 16 GB | Passed the model matrix as candidate evidence only |
| llama.cpp with SYCL | Ubuntu 26.04 Desktop | Intel Arc B580, 12 GB | Functional tests passed, but three upstream tests failed |
| llama.cpp with SYCL | Windows 11 x64 | Intel Arc B580, 12 GB | Failed the native model-loading gate |
| llama.cpp with Metal | Native macOS | Apple Silicon, 16 GB unified memory | Not tested; remains parked |

## What the result labels mean

- **Passed** means the recorded bounded checks succeeded on that exact setup.
- **Candidate evidence** means useful development tests passed, but the
  combination is not available as a supported Haven 42 product route.
- **Partial** means some checks passed and at least one required check failed.
- **Failed** means the combination did not pass its required execution or
  quality gate.
- **Not tested** means no result should be inferred from another operating
  system, GPU, runtime, or model.

For the engineering details behind these results, see
[[Inference Engine Architecture|Inference-Engine-Architecture]],
[[Inference Engine Validation|Inference-Engine-Validation]], and
[[Cross-Accelerator Model Validation|Cross-Accelerator-Model-Validation]].
