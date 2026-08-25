# Evidence Record Index

This index gives every sanitized evidence claim its own page. Each page
states exactly what was tested, what passed or remains limited, and what
must not be inferred from the result.

The pages are generated from `config/evidence-catalog.tsv`. Do not edit
them by hand; update the catalog and run the generator.

## Agent Surface

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Aider CLI disposable write-smoke validation](https://github.com/hysel/haven-42/wiki/Evidence-Record-2853e8649d47ac07) | `write-smoke-validated` | Windows · Ollama · qwen3-coder:30b |
| [Aider CLI model test harness](https://github.com/hysel/haven-42/wiki/Evidence-Record-ef5cd44e633c9e80) | `validated-by-tests` | Cross-platform · N/A · N/A |
| [Aider CLI qwen3.5 9B disposable write-smoke validation](https://github.com/hysel/haven-42/wiki/Evidence-Record-1e8e513a7ede9aeb) | `write-smoke-validated` | Windows · Ollama · qwen3.5:9b |
| [Aider CLI qwen3.5 9B read-only context validation](https://github.com/hysel/haven-42/wiki/Evidence-Record-168923a7d31793f3) | `read-only-tool-validated` | Windows · Ollama · qwen3.5:9b |
| [Aider CLI read-only context validation](https://github.com/hysel/haven-42/wiki/Evidence-Record-3bc3e961aa89d354) | `read-only-tool-validated` | Windows · Ollama · qwen3-coder:30b |
| [Aider CLI realistic scoped-edit validation](https://github.com/hysel/haven-42/wiki/Evidence-Record-eee8463c09ed1a53) | `write-smoke-validated` | Windows · Ollama · qwen3-coder:30b |
| [Aider CLI richer disposable scoped-edit validation](https://github.com/hysel/haven-42/wiki/Evidence-Record-c836e3b6f82ceb6c) | `write-smoke-validated` | Windows · Ollama · qwen3-coder:30b |
| [Aider and OpenCode candidate lifecycle plans](https://github.com/hysel/haven-42/wiki/Evidence-Record-4c8889255c609520) | `static-validated` | Cross-platform · No provider invocation · no-model |
| [Apple M4 16 GB Gemma 4 12B OpenCode coding screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-07f3b51d498ce792) | `failed-validation` | macOS 26.6.2 · Ollama 0.32.15 Metal · gemma4:12b-it-qat@38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3 |
| [Apple M4 16 GB LFM2.5 OpenCode coding screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-ea75c15e208b2be2) | `failed-validation` | macOS 26.6.2 · llama.cpp b10520 Metal · LFM2.5-1.2B-and-2.6B-Q4_K_M-exact-GGUFs |
| [Apple M4 16 GB OpenCode 1.18.19 16-model coding screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-713bc8ce611cbfe3) | `failed-validation` | macOS 26.6.2 · Ollama 0.32.15 Metal · 16-exact-manifest-corpus |
| [Continue CLI model test harness](https://github.com/hysel/haven-42/wiki/Evidence-Record-c48f68ae267ddaeb) | `validated-by-tests` | Cross-platform · N/A · N/A |
| [Gemma 3 1B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-23ddebcd60acad2e) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · gemma3:1b-it-q4_K_M |
| [Granite 4.1 30B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-0c002ac81e91a029) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · granite4.1:30b |
| [LFM 2.5 8B-A1B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-a108eefa61d6f8db) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · lfm2.5:8b |
| [MiniCPM V 4.6 1B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-9f4ed4080a80264a) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · minicpm-v4.6:1b |
| [Ministral 3 3B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-46cf85b53624763d) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · ministral-3:3b-instruct-2512-q4_K_M |
| [Ministral 3 8B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-cec3d35c28ceb7dd) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · ministral-3:8b-instruct-2512-q4_K_M |
| [Muse Glimmer 30B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-864cfafcaa524a47) | `partial-pass` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · muse-glimmer:30b |
| [Nemotron 3 Nano Omni 33B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-17626c4549c81ab9) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · nemotron3:33b |
| [Nemotron 3.5 Lightning Q4 coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-e09950a8ffba61a0) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · nemotron-3.5-lightning:30b-a3b-q4_K_M |
| [Nemotron 3.5 Lightning Q8 coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-5fbb9a96f1c4a37d) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · nemotron-3.5-lightning:30b-a3b-q8_0 |
| [North Mini Code 1.0 30B-A3B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-fd18a0f49cec996b) | `partial-pass` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · north-mini-code-1.0:q4_K_M |
| [OpenCode 1.18.11 19-model disposable-repository screen on RTX 3060](https://github.com/hysel/haven-42/wiki/Evidence-Record-7148c5d475b46ccd) | `partial-pass` | Windows 11 · Ollama 0.32.14 · digest-pinned-19-model-corpus |
| [OpenCode CLI Devstral Small 2 generated-sample scoped edit](https://github.com/hysel/haven-42/wiki/Evidence-Record-1e2f129e7b81d26f) | `write-smoke-validated` | Windows · Ollama · devstral-small-2:24b |
| [OpenCode CLI Devstral Small 2 generated-sample validation](https://github.com/hysel/haven-42/wiki/Evidence-Record-3a97cf812d7ead4b) | `partial-pass` | Windows · Ollama · devstral-small-2:24b |
| [OpenCode CLI qwen3.5 35B write smoke](https://github.com/hysel/haven-42/wiki/Evidence-Record-cba49f1efb99951d) | `write-smoke-validated` | Windows · Ollama · qwen3.5:35b |
| [OpenCode CLI qwen3.5 9B read validation](https://github.com/hysel/haven-42/wiki/Evidence-Record-0077a93bb585cbc8) | `read-only-tool-validated` | Windows · Ollama · qwen3.5:9b |
| [OpenCode CLI wrapper scaffold](https://github.com/hysel/haven-42/wiki/Evidence-Record-b7a23e13a579dff1) | `validated-by-tests` | Cross-platform · N/A · N/A |
| [Ornith 1.0 9B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-fdfbebccf314f75a) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · ornith:9b |
| [Qwen 3.5 0.8B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-5744f686ee69ee9f) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · qwen3.5:0.8b |
| [Qwen 3.5 2B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-3f07eddd1d3c4c51) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · qwen3.5:2b |
| [Qwen 3.5 4B VS Code Continue active-file recovery retest on Radeon RX 5700 XT 8 GiB](https://github.com/hysel/haven-42/wiki/Evidence-Record-fe50ca6d08f51589) | `partial-pass` | Windows editor and Ubuntu 26.04 AMD Radeon RX 5700 XT model host · Ollama 0.32.13 · qwen3.5:4b |
| [Qwen 3.5 4B VS Code Continue controlled editor retest with Python extension](https://github.com/hysel/haven-42/wiki/Evidence-Record-bcc43e041506855b) | `failed-validation` | Windows editor and Ubuntu 26.04 AMD Radeon RX 5700 XT model host · Ollama 0.32.13 · qwen3.5:4b |
| [Qwen 3.5 4B VS Code Continue editor workflow on Radeon RX 5700 XT 8 GiB](https://github.com/hysel/haven-42/wiki/Evidence-Record-8bad8490965fc6d2) | `partial-pass` | Windows editor and Ubuntu 26.04 AMD Radeon RX 5700 XT model host · Ollama 0.32.13 · qwen3.5:4b |
| [Qwen 3.5 4B VS Code Continue explicit two-file retest on Radeon RX 5700 XT 8 GiB](https://github.com/hysel/haven-42/wiki/Evidence-Record-3208bee0b01e1ddd) | `failed-validation` | Windows editor and Ubuntu 26.04 AMD Radeon RX 5700 XT model host · Ollama 0.32.13 · qwen3.5:4b |
| [Qwen 3.5 4B VSCodium Continue editor comparison on Radeon RX 5700 XT 8 GiB](https://github.com/hysel/haven-42/wiki/Evidence-Record-6550349b706f26e4) | `failed-validation` | Windows editor and Ubuntu 26.04 AMD Radeon RX 5700 XT model host · Ollama 0.32.13 · qwen3.5:4b |
| [Qwen 3.5 4B coding reliability soak on Radeon RX 5700 XT 8 GiB](https://github.com/hysel/haven-42/wiki/Evidence-Record-492ea3ff6c97b8c5) | `partial-pass` | Windows controller and Ubuntu 26.04 AMD Radeon RX 5700 XT model host · Ollama 0.32.13 · qwen3.5:4b |
| [Qwen 3.5 4B coding workflow on Radeon RX 5700 XT 8 GiB](https://github.com/hysel/haven-42/wiki/Evidence-Record-93e8cb104f42daa6) | `partial-pass` | Windows controller and Ubuntu 26.04 AMD Radeon RX 5700 XT model host · Ollama 0.32.13 · qwen3.5:4b |
| [Qwen 3.5 4B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-841c8bfeebc76fb4) | `partial-pass` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · qwen3.5:4b |
| [Qwen 3.5 4B native VS Code Chat read-only repository inspection](https://github.com/hysel/haven-42/wiki/Evidence-Record-9bfaa61b1508e210) | `read-only-tool-validated` | Windows · Ollama · qwen3.5:4b |
| [Qwen 3.6 27B Q4 coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-deb665f24d7374ee) | `failed-validation` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · qwen3.6:27b-q4_K_M |
| [Qwen 3.6 35B-A3B Q4 coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-993d371eb43c7b6d) | `partial-pass` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · qwen3.6:35b-a3b-q4_K_M |
| [Qwen 3.8 27B coding workflow screen](https://github.com/hysel/haven-42/wiki/Evidence-Record-743034b6d1e30dc9) | `partial-pass` | Windows controller and Ubuntu 24.04.4 CUDA model host · Ollama 0.32.13 · qwen3.8:27b |
| [Qwen 3.8 27B native VS Code Chat read-only repository inspection](https://github.com/hysel/haven-42/wiki/Evidence-Record-cfa90771bd9c89a4) | `read-only-tool-validated` | Windows · Ollama · qwen3.8:27b |
| [Shared agent CLI model test harness](https://github.com/hysel/haven-42/wiki/Evidence-Record-ef3643c281067618) | `validated-by-tests` | Cross-platform · N/A · N/A |
## Controlled Research

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Explicit research approval review](https://github.com/hysel/haven-42/wiki/Evidence-Record-6fe6a89227168b12) | `validated-by-tests` | Headless browser source · Fixed English Wikipedia review shape · no-model |
| [Live fixed-Wikipedia Alpha 2 package runtime](https://github.com/hysel/haven-42/wiki/Evidence-Record-2403d4a9edd19c95) | `partial-pass` | Windows · Fixed English Wikipedia · no-model |
| [Live fixed-Wikipedia product runtime](https://github.com/hysel/haven-42/wiki/Evidence-Record-db792ade22a7c3ad) | `partial-pass` | Windows · Fixed English Wikipedia · no-model |
| [Offline cited-synthesis source parity](https://github.com/hysel/haven-42/wiki/Evidence-Record-03d2a694b6d22720) | `static-validated` | Windows and Linux · Caller-supplied fixtures · synthetic-bounded-source-envelope |
| [Offline transport and approval guards](https://github.com/hysel/haven-42/wiki/Evidence-Record-1c20a3dfac18ae0a) | `static-validated` | Cross-platform · Caller-supplied receipts · no-model |
| [Trusted citation renderer](https://github.com/hysel/haven-42/wiki/Evidence-Record-19165579f9181386) | `validated-by-tests` | Headless browser source · Fixed English Wikipedia citation shape · no-model |
## Data Protection

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Conversation-history activation readiness policy](https://github.com/hysel/haven-42/wiki/Evidence-Record-91e7db3d8cf9310d) | `static-validated` | Cross-platform · No runtime · none |
| [Conversation-history encryption dependency review](https://github.com/hysel/haven-42/wiki/Evidence-Record-afdeb35698fc13c1) | `candidate-only` | Cross-platform · SQLCipher Community and Python bindings · none |
| [Linux credential-store availability boundary](https://github.com/hysel/haven-42/wiki/Evidence-Record-3032fff46e49e400) | `candidate-only` | Linux · freedesktop credential-store candidate · none |
| [Linux credential-store native headless availability](https://github.com/hysel/haven-42/wiki/Evidence-Record-56ca94fba5185607) | `partial-pass` | Linux headless container session · freedesktop credential-store candidate · none |
| [Physical Apple M4 Keychain command availability boundary](https://github.com/hysel/haven-42/wiki/Evidence-Record-e9f4fda429cdc626) | `partial-pass` | macOS 26.6.2 · Apple Keychain Services candidate · none |
| [Physical Apple M4 unattended synthetic Keychain lifecycle](https://github.com/hysel/haven-42/wiki/Evidence-Record-32a2affd636fbbf9) | `failed-validation` | macOS 26.6.2 · Apple Keychain Services candidate · fixed-validation-item |
| [Windows conversation-history per-user ACL primitive](https://github.com/hysel/haven-42/wiki/Evidence-Record-0005faabe699fcf7) | `partial-pass` | Windows · Windows protected DACL · none |
| [Windows conversation-history synthetic key protection](https://github.com/hysel/haven-42/wiki/Evidence-Record-780b76332e1a0df4) | `partial-pass` | Windows · Windows DPAPI current user · none |
| [Windows wrapped-key temporary persistence](https://github.com/hysel/haven-42/wiki/Evidence-Record-01c8b74c82919604) | `partial-pass` | Windows · Windows DPAPI current user · none |
| [macOS Keychain availability boundary](https://github.com/hysel/haven-42/wiki/Evidence-Record-887cf80b11f5cea2) | `candidate-only` | macOS · Apple Keychain Services candidate · none |
| [macOS Keychain native hosted availability](https://github.com/hysel/haven-42/wiki/Evidence-Record-a7fe3f72fe5a759f) | `partial-pass` | GitHub-hosted macOS 15 · Apple Keychain Services candidate · none |
## Editor Surface

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [VS Code-compatible Continue Agent](https://github.com/hysel/haven-42/wiki/Evidence-Record-9865b9af8dddb72e) | `read-only-tool-validated` | Windows · Ollama · qwen3-coder:30b |
| [VSCodium Continue Agent](https://github.com/hysel/haven-42/wiki/Evidence-Record-3532849d1fcc1eb8) | `read-only-tool-validated` | Windows · Ollama · qwen3-coder:30b |
| [VSCodium Continue Agent Qwen 3.5 4B MLX strict write smoke](https://github.com/hysel/haven-42/wiki/Evidence-Record-e5ae46fbbffbcb08) | `partial-pass` | macOS · MLX · mlx-community/Qwen3.5-4B-4bit |
| [VSCodium Continue Agent Qwen 3.5 9B MLX scoped edit](https://github.com/hysel/haven-42/wiki/Evidence-Record-b0c0bfde405ff09e) | `write-smoke-validated` | macOS · MLX · mlx-community/Qwen3.5-9B-OptiQ-4bit |
## Engineering Validation

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Pinned public repository structure selection](https://github.com/hysel/haven-42/wiki/Evidence-Record-9a6b5c12842514d3) | `static-validated` | Windows · Bare Git object inspection · Click 8.2.1, Express 5.1.0, serde_json 1.0.140 |
## General Capability

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Gemma 3 12B writing constraint matrix](https://github.com/hysel/haven-42/wiki/Evidence-Record-eff6c9e174bbfc81) | `validated-by-tests` | Linux · Ollama · gemma3:12b |
| [Granite 4 7B-A1B-H writing constraint matrix](https://github.com/hysel/haven-42/wiki/Evidence-Record-a6e6ffd682af210d) | `partial-pass` | Linux · Ollama · granite4:7b-a1b-h |
| [Local ComfyUI SDXL image generation](https://github.com/hysel/haven-42/wiki/Evidence-Record-794bb0b437c5bd12) | `validated-by-tests` | Linux · ComfyUI · SDXL Base 1.0 |
| [Local Ollama capability availability discovery](https://github.com/hysel/haven-42/wiki/Evidence-Record-7f4b6f4a0b5c9599) | `validated-by-tests` | Windows · Ollama · qwen3.5:9b |
| [Local Ollama general chat](https://github.com/hysel/haven-42/wiki/Evidence-Record-e2cf27858869b71b) | `validated-by-tests` | Windows · Ollama · qwen3.5:9b |
| [Local Ollama general writing](https://github.com/hysel/haven-42/wiki/Evidence-Record-a661b8ee3cb73a5c) | `validated-by-tests` | Windows · Ollama · qwen3.5:9b |
| [Local Ollama summarization](https://github.com/hysel/haven-42/wiki/Evidence-Record-91816f73fe0522a8) | `validated-by-tests` | Windows · Ollama · qwen3.5:9b |
| [Mistral Small 3.2 writing constraint matrix](https://github.com/hysel/haven-42/wiki/Evidence-Record-9160baf776098a16) | `validated-by-tests` | Linux · Ollama · mistral-small3.2:24b-instruct-2506-q4_K_M |
| [Optional local LLM capability suggestion](https://github.com/hysel/haven-42/wiki/Evidence-Record-e868714f9f8c5344) | `validated-by-tests` | Windows · Ollama · qwen3.5:9b |
| [Qwen 3.5 9B writing constraint matrix](https://github.com/hysel/haven-42/wiki/Evidence-Record-b91e58b8e387a4cc) | `validated-by-tests` | Linux · Ollama · qwen3.5:9b |
## Hardware Qualification

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Radeon RX 5700 XT exact Ubuntu Vulkan profile](https://github.com/hysel/haven-42/wiki/Evidence-Record-07a5bd4578f3108f) | `partial-pass` | Ubuntu 26.04 LTS · Ollama 0.32.13 Vulkan RADV · 16 exact manifest-pinned model profiles |
| [Radeon RX 6800 non-XT exact Ubuntu Vulkan profile](https://github.com/hysel/haven-42/wiki/Evidence-Record-8863732197853ce7) | `partial-pass` | Ubuntu 26.04 LTS · Ollama 0.32.14 Vulkan RADV · digest-pinned-13-model-corpus |
## Hardware Recommendation

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Script-level recommendation and config generation](https://github.com/hysel/haven-42/wiki/Evidence-Record-7c544083b952b24c) | `validated-by-tests` | Cross-platform · N/A · qwen3.5:9b |
## Hardware Stability

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Radeon RX 5700 XT current-boot host stability](https://github.com/hysel/haven-42/wiki/Evidence-Record-27f4eaa91d0b896d) | `partial-pass` | Ubuntu 26.04 LTS · Linux kernel and amdgpu · no-model |
## Inference Engine

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Apple M4 16 GB MLX-LM lifecycle](https://github.com/hysel/haven-42/wiki/Evidence-Record-e3d838e6e2d03596) | `partial-pass` | macOS 26.6.2 · MLX 0.32.1 Metal · mlx-community/Qwen3.5-0.8B-OptiQ-4bit@ef605869 |
| [Apple M4 16 GB llama.cpp lifecycle](https://github.com/hysel/haven-42/wiki/Evidence-Record-6c65da7ee449d0dd) | `partial-pass` | macOS 26.6.2 · llama.cpp Metal · Qwen3.5-0.8B-Q4_0-GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| [Apple M4 16 GB official llama.cpp b10520 distribution boundary](https://github.com/hysel/haven-42/wiki/Evidence-Record-6f7b8eca3bf0cc89) | `partial-pass` | macOS 26.6.2 · llama.cpp Metal · none |
| [OpenVINO GenAI on Intel Arc B580](https://github.com/hysel/haven-42/wiki/Evidence-Record-05d02ca020d00629) | `partial-pass` | Windows · direct library API · OpenVINO/Qwen3-0.6B-int4-ov@f864c6106efb6c7f7b4ef274a78a98e37210dddd |
| [OpenVINO GenAI on Intel Arc B580](https://github.com/hysel/haven-42/wiki/Evidence-Record-13d3451c24d5c713) | `partial-pass` | Linux · direct library API · OpenVINO/Qwen3-0.6B-int4-ov@f864c6106efb6c7f7b4ef274a78a98e37210dddd |
| [llama.cpp 11-model identical-byte AMD/NVIDIA matrix](https://github.com/hysel/haven-42/wiki/Evidence-Record-d2ac550dc4f53937) | `partial-pass` | Windows and Linux · direct process · revision-and-sha256-pinned-11-model-corpus |
| [llama.cpp CUDA on Quadro RTX 5000](https://github.com/hysel/haven-42/wiki/Evidence-Record-599dbc1e05b646b6) | `partial-pass` | Linux · OpenAI-compatible loopback API · unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 |
| [llama.cpp HIP on Radeon RX 7800 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-85720f2f0c014451) | `partial-pass` | Windows · OpenAI-compatible loopback API · unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 |
| [llama.cpp HIP through WSL2 DXG on Radeon RX 7800 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-1a16a98b5cd40e10) | `partial-pass` | WSL2 Ubuntu · direct process · revision-and-sha256-pinned-11-model-corpus |
| [llama.cpp SYCL on Intel Arc B580](https://github.com/hysel/haven-42/wiki/Evidence-Record-3d02244dab060bc7) | `candidate-only` | Windows · direct process · unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 |
| [llama.cpp SYCL on Intel Arc B580](https://github.com/hysel/haven-42/wiki/Evidence-Record-a43711f9d74d1e5f) | `partial-pass` | Linux · OpenAI-compatible loopback API · unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 |
| [llama.cpp Windows NVIDIA and AMD follow-on matrix](https://github.com/hysel/haven-42/wiki/Evidence-Record-d535eb939e00de72) | `partial-pass` | Windows · direct process · revision-and-sha256-pinned-follow-on-artifacts |
| [llama.cpp b10375 Vulkan smoke on Radeon RX 5700 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-ded5fc576317be66) | `partial-pass` | Ubuntu 26.04 LTS · Vulkan RADV · Qwen 3.5 0.8B Q4_0 GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| [llama.cpp b10375 Vulkan task and soak on Radeon RX 5700 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-2ee5449c5143bfd7) | `partial-pass` | Windows 10.0.26200.8973 · Vulkan AMD proprietary 26.7.1 · Qwen 3.5 0.8B Q4_0 GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
## Installer Profile

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Approved-write install profile](https://github.com/hysel/haven-42/wiki/Evidence-Record-61e94680de9075db) | `validated-by-tests` | Cross-platform · N/A · N/A |
| [Read-only install profile](https://github.com/hysel/haven-42/wiki/Evidence-Record-fbf3040ee5b605aa) | `validated-by-tests` | Cross-platform · N/A · N/A |
## Knowledge Context

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Memory lexical retrieval hardening](https://github.com/hysel/haven-42/wiki/Evidence-Record-c730707485ed58be) | `static-validated` | Cross-platform · Caller-supplied validated memory · no-model |
| [Office/OpenDocument unsupported-object boundary](https://github.com/hysel/haven-42/wiki/Evidence-Record-128249f02a932a5d) | `static-validated` | Windows and Linux · Synthetic ZIP/XML fixtures · no-model |
## Language Rule Pack

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Python optional rule pack](https://github.com/hysel/haven-42/wiki/Evidence-Record-fa1c4c4d706dbb95) | `static-validated` | Cross-platform · N/A · N/A |
| [TypeScript optional rule pack](https://github.com/hysel/haven-42/wiki/Evidence-Record-bf0a844bf50dad6c) | `static-validated` | Cross-platform · N/A · N/A |
## Language Workflow Matrix

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Devstral Small 2 medium language matrix](https://github.com/hysel/haven-42/wiki/Evidence-Record-9fe4829db45f23cf) | `partial-pass` | Windows · Ollama · devstral-small-2:24b |
| [Native macOS Python read workflows](https://github.com/hysel/haven-42/wiki/Evidence-Record-ead5ac43339950f8) | `read-only-cli-validated` | macOS · Ollama · qwen3.5:9b |
| [Native macOS Python scoped-write](https://github.com/hysel/haven-42/wiki/Evidence-Record-e9278f1fa33b50ed) | `approved-write-ready` | macOS · Ollama · qwen3.5:9b |
| [Qwen 3.5 35B medium language matrix](https://github.com/hysel/haven-42/wiki/Evidence-Record-e133b0735c64b090) | `partial-pass` | Windows · Ollama · qwen3.5:35b |
| [Rust scoped-write lane](https://github.com/hysel/haven-42/wiki/Evidence-Record-4d55669e8b4fe1d1) | `approved-write-ready` | Windows · Ollama · devstral-small-2:24b |
| [TypeScript scoped-write lane](https://github.com/hysel/haven-42/wiki/Evidence-Record-74a1cb2f558d7e4f) | `approved-write-ready` | Windows · Ollama · qwen3.5:35b |
## Managed Lifecycle

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Alpha 2 managed lifecycle on Arch Linux rolling](https://github.com/hysel/haven-42/wiki/Evidence-Record-64b5695c570a65eb) | `partial-pass` | Arch Linux rolling · Ollama 0.32.5 CUDA · qwen3.5:0.8b Q8_0 |
| [Alpha 2 managed lifecycle on Bazzite 44](https://github.com/hysel/haven-42/wiki/Evidence-Record-6d9b244b1163f0ba) | `partial-pass` | Bazzite 44 · Ollama 0.32.5 CUDA · qwen3.5:0.8b Q8_0 |
| [Alpha 2 managed lifecycle on CachyOS rolling](https://github.com/hysel/haven-42/wiki/Evidence-Record-1d6bdc9189569bea) | `partial-pass` | CachyOS rolling · Ollama 0.32.5 CUDA · qwen3.5:0.8b Q8_0 |
| [Alpha 2 managed lifecycle on Debian 13](https://github.com/hysel/haven-42/wiki/Evidence-Record-367cf17184e6d096) | `partial-pass` | Debian 13 · Ollama 0.32.5 CUDA · qwen3.5:0.8b Q8_0 |
| [Alpha 2 managed lifecycle on Fedora 44](https://github.com/hysel/haven-42/wiki/Evidence-Record-a466eb1da4889753) | `partial-pass` | Fedora 44 · Ollama 0.32.5 CUDA · qwen3.5:0.8b Q8_0 |
| [Alpha 2 managed lifecycle on Linux Mint 22.3](https://github.com/hysel/haven-42/wiki/Evidence-Record-996fb8fe75402f31) | `partial-pass` | Linux Mint 22.3 · Ollama 0.32.5 CUDA · qwen3.5:0.8b Q8_0 |
| [Alpha 2 managed lifecycle on Pop OS 24.04](https://github.com/hysel/haven-42/wiki/Evidence-Record-f15751caa49c9951) | `partial-pass` | Pop OS 24.04 LTS · Ollama 0.32.5 CUDA · qwen3.5:0.8b Q8_0 |
| [Alpha 2 managed lifecycle on Ubuntu 24.04](https://github.com/hysel/haven-42/wiki/Evidence-Record-d3fe8b7c516fde7c) | `partial-pass` | Ubuntu 24.04.4 LTS · Ollama 0.32.5 CUDA · qwen3.5:0.8b Q8_0 |
| [Alpha 2 managed lifecycle on Ubuntu 26.04](https://github.com/hysel/haven-42/wiki/Evidence-Record-2a865071c8c4974a) | `partial-pass` | Ubuntu 26.04 LTS · Ollama 0.32.5 CUDA · qwen3.5:0.8b Q8_0 |
## Media Provider

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [ACE-Step 1.5 Linux CUDA feasibility](https://github.com/hysel/haven-42/wiki/Evidence-Record-c9663d1fe857b9a0) | `partial-pass` | Linux · ACE-Step · acestep-v15-turbo |
| [ComfyUI SDXL on Intel Arc B580](https://github.com/hysel/haven-42/wiki/Evidence-Record-3d3a187ec32169e6) | `partial-pass` | Windows · ComfyUI · SDXL Base 1.0 |
| [ComfyUI SDXL on Quadro RTX 5000](https://github.com/hysel/haven-42/wiki/Evidence-Record-9144ebf0180b2118) | `partial-pass` | Windows · ComfyUI · SDXL Base 1.0 |
| [ComfyUI SDXL on Radeon RX 7800 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-dda5053a14f25d32) | `partial-pass` | Windows · ComfyUI · SDXL Base 1.0 |
| [Local video candidate hardware preflight](https://github.com/hysel/haven-42/wiki/Evidence-Record-4e44f89b53777abb) | `candidate-only` | Linux · HunyuanVideo 1.5, Wan2.2, and LTX-2.3 · exact-upstream-candidate-records |
## Model Provider

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Laguna XS 2.1 Ollama conformance](https://github.com/hysel/haven-42/wiki/Evidence-Record-749f44fc9f8604f4) | `partial-pass` | Linux · Ollama · laguna-xs-2.1:q4_K_M |
## Model Qualification

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Apple M4 16 GB 16-model bounded qualification](https://github.com/hysel/haven-42/wiki/Evidence-Record-71fdc1d4cefe7305) | `partial-pass` | macOS 26.6.2 · Ollama · 16-exact-manifest-corpus |
| [Apple M4 16 GB Gemma 4 12B QAT bounded addendum](https://github.com/hysel/haven-42/wiki/Evidence-Record-058dffd9da155b02) | `partial-pass` | macOS 26.6.2 · Ollama · gemma4:12b-it-qat@38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3 |
| [Apple M4 16 GB Gemma 4 12B QAT reliability soak](https://github.com/hysel/haven-42/wiki/Evidence-Record-58b80062769ba4ad) | `partial-pass` | macOS 26.6.2 · Ollama · gemma4:12b-it-qat@38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3 |
| [Apple M4 16 GB LFM2.5 GGUF bounded qualification](https://github.com/hysel/haven-42/wiki/Evidence-Record-0ef74d64cf30f4b8) | `failed-validation` | macOS 26.6.2 · llama.cpp Metal · LFM2.5-1.2B-and-2.6B-Q4_K_M-exact-GGUFs |
| [Apple M4 16 GB nine-model reliability soak](https://github.com/hysel/haven-42/wiki/Evidence-Record-6a2e6287439189e8) | `partial-pass` | macOS 26.6.2 · Ollama · nine-core-pass-exact-artifacts |
| [Gemma 3 1B Q4 on Ollama 0.32.13 Linux CUDA](https://github.com/hysel/haven-42/wiki/Evidence-Record-b1e852d6e517e410) | `partial-pass` | Ubuntu 24.04.4 · Ollama · gemma3:1b-it-q4_K_M |
| [Gemma 4 E2B QAT on Radeon RX 5700 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-9ee9709513adee19) | `partial-pass` | Ubuntu 26.04 LTS · Ollama Vulkan RADV · gemma4:e2b-qat |
| [Gemma 4 E4B QAT on Radeon RX 5700 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-be0a1992c6629cd9) | `partial-pass` | Ubuntu 26.04 LTS · Ollama Vulkan RADV · gemma4:e4b-qat |
| [Granite 4.1 30B Q4 on dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-16a3a4e63dfc72ca) | `partial-pass` | Ubuntu 24.04.4 · Ollama CUDA · granite4.1:30b-q4_K_M |
| [Granite 4.1 8B on Intel Arc B580](https://github.com/hysel/haven-42/wiki/Evidence-Record-739440533a3f6c7a) | `partial-pass` | Ubuntu Linux · direct process · granite41-8b-q4_K_M |
| [LFM 2.5 8B-A1B Q4 on Radeon RX 5700 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-65346575aa772f5d) | `failed-validation` | Ubuntu 26.04 LTS · Ollama Vulkan RADV · lfm2.5:8b-a1b-q4_K_M |
| [MiniCPM V 4.6 1B Q4 on Radeon RX 5700 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-c3662ac9bec5b4b8) | `failed-validation` | Ubuntu 26.04 LTS · Ollama Vulkan RADV · minicpm-v:4.6-1b-q4_K_M |
| [Ministral 3 3B Q4 on Ollama 0.32.13 Linux CUDA](https://github.com/hysel/haven-42/wiki/Evidence-Record-14e2d57e6336807d) | `failed-validation` | Ubuntu 24.04.4 · Ollama · ministral-3:3b-instruct-2512-q4_K_M |
| [Ministral 3 8B Q4 on Ollama 0.32.13 Linux CUDA](https://github.com/hysel/haven-42/wiki/Evidence-Record-83b23ecb83be18a7) | `failed-validation` | Ubuntu 24.04.4 · Ollama · ministral-3:8b-instruct-2512-q4_K_M |
| [Muse Glimmer 30B Q4 on dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-9374faea1e5a9476) | `failed-validation` | Ubuntu 24.04.4 · Ollama CUDA · muse-glimmer:30b-q4_K_M |
| [NVIDIA GeForce RTX 3060 12 GB 19-model qualification](https://github.com/hysel/haven-42/wiki/Evidence-Record-7f16789ca3e3811c) | `partial-pass` | Windows 11 · Ollama · digest-pinned-19-model-corpus |
| [Nemotron 3 Nano Omni 33B Q4 on dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-d25ff2272d76e84f) | `partial-pass` | Ubuntu 24.04.4 · Ollama CUDA · nemotron-3-nano-omni:33b-q4_K_M |
| [Nemotron 3.5 Lightning Q4 on Ollama 0.32.13 dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-3cde6c27785c5e96) | `partial-pass` | Ubuntu 24.04.4 · Ollama CUDA · nemotron-3.5-lightning:30b-a3b-q4_K_M |
| [Nemotron 3.5 Lightning Q4 on dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-999c817bcb50d175) | `partial-pass` | Ubuntu 24.04.4 · Ollama · nemotron-3.5-lightning:30b-a3b-q4_K_M |
| [Nemotron 3.5 Lightning Q8 on Ollama 0.32.13 dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-cb0f0c4481e7b7f9) | `partial-pass` | Ubuntu 24.04.4 · Ollama CUDA · nemotron-3.5-lightning:30b-a3b-q8_0 |
| [Nemotron 3.5 Lightning Q8 on dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-b4871f9bcbf09daa) | `partial-pass` | Ubuntu 24.04.4 · Ollama · nemotron-3.5-lightning:30b-a3b-q8_0 |
| [North Mini Code 10 30B-A3B Q4 on dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-7180c239d7cf4e2e) | `partial-pass` | Ubuntu 24.04.4 · Ollama CUDA · north-mini-code:10-30b-a3b-q4_K_M |
| [Ollama 0.32.9 five-model task-contract retry on dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-029248b547774d8a) | `failed-validation` | Ubuntu 24.04.4 · Ollama · five exact manifest-pinned models |
| [Ornith 10 9B Q4 on Radeon RX 5700 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-48e4f4c41b8289de) | `partial-pass` | Ubuntu 26.04 LTS · Ollama Vulkan RADV · ornith-10:9b-q4_K_M |
| [Phi 4 Mini 3.8B Q4 on Ollama 0.32.13 Linux CUDA](https://github.com/hysel/haven-42/wiki/Evidence-Record-d7e3b3eddcb87ab3) | `partial-pass` | Ubuntu 24.04.4 · Ollama · phi4-mini:3.8b-q4_K_M |
| [Qwen 3.5 4B Q4 on Radeon RX 5700 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-5647918854ef19ab) | `partial-pass` | Ubuntu 26.04 LTS · Ollama Vulkan RADV · qwen3.5:4b-q4_K_M |
| [Qwen 3.5 9B synchronized power on Radeon RX 7800 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-08bad671d73e509b) | `partial-pass` | Windows 11 · Ollama · qwen3.5:9b Q4_K_M |
| [Qwen 3.6 27B Q4 on Ollama 0.32.13 Linux CUDA](https://github.com/hysel/haven-42/wiki/Evidence-Record-f96c1a3dd255db29) | `partial-pass` | Ubuntu 24.04.4 · Ollama · qwen3.6:27b-q4_K_M |
| [Qwen 3.6 35B-A3B Q4 on dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-6c0d4b52091120fa) | `partial-pass` | Ubuntu 24.04.4 · Ollama CUDA · qwen3.6:35b-a3b-q4_K_M |
| [Qwen 3.8 27B Q4 on dual Tesla V100](https://github.com/hysel/haven-42/wiki/Evidence-Record-6c09cdefc61c0f82) | `partial-pass` | Ubuntu 24.04.4 · Ollama CUDA · qwen3.8:27b-q4_K_M |
| [Radeon RX 7800 XT 17-model Ollama 0.32.9 recertification](https://github.com/hysel/haven-42/wiki/Evidence-Record-ad991e5601c892ec) | `partial-pass` | Windows 11 · Ollama · 17 exact manifest-pinned models |
| [Ubuntu NVIDIA GeForce GTX 1650 Super 4 GB eight-model qualification](https://github.com/hysel/haven-42/wiki/Evidence-Record-65198375e7df9abe) | `partial-pass` | Ubuntu 26.04 LTS · Ollama · digest-pinned-eight-model-corpus |
| [Ubuntu NVIDIA GeForce RTX 3060 12 GB 19-model qualification](https://github.com/hysel/haven-42/wiki/Evidence-Record-f5989f6fc215258e) | `partial-pass` | Ubuntu 26.04 LTS · Ollama · digest-pinned-19-model-corpus |
| [Windows NVIDIA GeForce GTX 1650 Super 4 GB eight-model qualification](https://github.com/hysel/haven-42/wiki/Evidence-Record-a31a3f4055c25ef1) | `partial-pass` | Windows 11 · Ollama · digest-pinned-eight-model-corpus |
## Model Quantization

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Qwen 3.5 9B Q4_K_M versus Q8_0](https://github.com/hysel/haven-42/wiki/Evidence-Record-abbec916eccdc9c2) | `validated-by-tests` | Linux · Ollama · qwen3.5:9b |
| [Qwen 3.5 9B Q4_K_M versus Q8_0 on Radeon RX 7800 XT](https://github.com/hysel/haven-42/wiki/Evidence-Record-66af319217108136) | `validated-by-tests` | Windows · Ollama · qwen3.5:9b |
## Model Tool Use

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Devstral Small 2 MLX endpoint tool call](https://github.com/hysel/haven-42/wiki/Evidence-Record-8a4966fb74923f8b) | `candidate-only` | macOS · MLX · mlx-community/Devstral-Small-2-24B-Instruct-2512-4bit |
| [Qwen 3.5 4B MLX Continue CLI read](https://github.com/hysel/haven-42/wiki/Evidence-Record-a4f5cee50428c764) | `read-only-cli-validated` | macOS · MLX · mlx-community/Qwen3.5-4B-4bit |
| [Qwen 3.5 4B MLX Continue CLI scoped write smoke](https://github.com/hysel/haven-42/wiki/Evidence-Record-5f39cc023ffe9b89) | `write-smoke-validated` | macOS · MLX · mlx-community/Qwen3.5-4B-4bit |
| [Qwen 3.5 4B MLX endpoint tool call](https://github.com/hysel/haven-42/wiki/Evidence-Record-5937518d2dcbae62) | `read-only-tool-validated` | macOS · MLX · mlx-community/Qwen3.5-4B-4bit |
| [Qwen 3.5 9B MLX Continue CLI plan](https://github.com/hysel/haven-42/wiki/Evidence-Record-2281ebc7777a2289) | `plan-validated` | macOS · MLX · mlx-community/Qwen3.5-9B-OptiQ-4bit |
| [Qwen 3.5 9B MLX Continue CLI read](https://github.com/hysel/haven-42/wiki/Evidence-Record-254db10e5008805c) | `read-only-cli-validated` | macOS · MLX · mlx-community/Qwen3.5-9B-OptiQ-4bit |
| [Qwen 3.5 9B MLX Continue CLI review](https://github.com/hysel/haven-42/wiki/Evidence-Record-55a17b5d93fb9c09) | `review-validated` | macOS · MLX · mlx-community/Qwen3.5-9B-OptiQ-4bit |
| [Qwen 3.5 9B MLX Continue CLI scoped write smoke](https://github.com/hysel/haven-42/wiki/Evidence-Record-32993a66ac4b468f) | `write-smoke-validated` | macOS · MLX · mlx-community/Qwen3.5-9B-OptiQ-4bit |
| [Qwen 3.5 9B MLX endpoint tool call](https://github.com/hysel/haven-42/wiki/Evidence-Record-3f7866c9fa36fa50) | `read-only-tool-validated` | macOS · MLX · mlx-community/Qwen3.5-9B-OptiQ-4bit |
| [Qwen 3.5 9B baseline MLX Continue CLI read](https://github.com/hysel/haven-42/wiki/Evidence-Record-de86611b0dd8c860) | `read-only-cli-validated` | macOS · MLX · mlx-community/Qwen3.5-9B-4bit |
| [Qwen 3.5 9B baseline MLX Continue CLI scoped write smoke](https://github.com/hysel/haven-42/wiki/Evidence-Record-ccd5b4bdd03c1ef2) | `write-smoke-validated` | macOS · MLX · mlx-community/Qwen3.5-9B-4bit |
| [Qwen 3.5 9B baseline MLX endpoint tool call](https://github.com/hysel/haven-42/wiki/Evidence-Record-fd71babae537344a) | `read-only-tool-validated` | macOS · MLX · mlx-community/Qwen3.5-9B-4bit |
| [Qwen3-Coder-Next generated workflows](https://github.com/hysel/haven-42/wiki/Evidence-Record-0fd3dc956063fdaa) | `plan-review-candidate` | Windows · Ollama · Qwen3-Coder-Next:latest |
| [devstral-small-2 generated workflows](https://github.com/hysel/haven-42/wiki/Evidence-Record-b0b0a5a9fbafbfd4) | `plan-review-candidate` | Windows · Ollama · devstral-small-2:latest |
| [devstral-small-2:24b Continue CLI read](https://github.com/hysel/haven-42/wiki/Evidence-Record-ebc97e7569950583) | `read-only-cli-validated` | Windows · Ollama · devstral-small-2:24b |
| [devstral-small-2:24b Continue CLI write](https://github.com/hysel/haven-42/wiki/Evidence-Record-2b8fd551abe47dcd) | `write-smoke-validated` | Windows · Ollama · devstral-small-2:24b |
| [devstral-small-2:24b read](https://github.com/hysel/haven-42/wiki/Evidence-Record-460f76e4260d68fd) | `read-only-tool-validated` | Windows · Ollama · devstral-small-2:24b |
| [qwen3-coder:30b Continue CLI read](https://github.com/hysel/haven-42/wiki/Evidence-Record-8cdb147cb46a0942) | `read-only-cli-validated` | Windows · Ollama · qwen3-coder:30b |
| [qwen3-coder:30b Continue CLI write](https://github.com/hysel/haven-42/wiki/Evidence-Record-688536975056f222) | `write-smoke-validated` | Windows · Ollama · qwen3-coder:30b |
| [qwen3-coder:30b read](https://github.com/hysel/haven-42/wiki/Evidence-Record-d2ccbc89525e4a4b) | `read-only-tool-validated` | Windows · Ollama · qwen3-coder:30b |
| [qwen3.5:9b Continue CLI read](https://github.com/hysel/haven-42/wiki/Evidence-Record-e81d875e828d2c8f) | `read-only-cli-validated` | Windows · Ollama · qwen3.5:9b |
| [qwen3.5:9b Continue CLI write](https://github.com/hysel/haven-42/wiki/Evidence-Record-3b61696216f40c39) | `write-smoke-validated` | Windows · Ollama · qwen3.5:9b |
| [qwen3.5:9b plan](https://github.com/hysel/haven-42/wiki/Evidence-Record-2410a7d9b3a44da6) | `plan-validated` | Windows · Ollama · qwen3.5:9b |
| [qwen3.5:9b read](https://github.com/hysel/haven-42/wiki/Evidence-Record-011e7524d4091077) | `read-only-tool-validated` | Windows · Ollama · qwen3.5:9b |
| [qwen3.5:9b write](https://github.com/hysel/haven-42/wiki/Evidence-Record-1c9a5cb51bde73c4) | `approved-write-ready` | Windows · Ollama · qwen3.5:9b |
## Multi Language Workflow

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Generated Python sample workflows](https://github.com/hysel/haven-42/wiki/Evidence-Record-cce994c7b1684c6e) | `partial-pass` | Windows · Ollama · devstral-small-2:latest |
| [Generated Python sample workflows](https://github.com/hysel/haven-42/wiki/Evidence-Record-ddd493cef4288ac4) | `partial-pass` | Windows · Ollama · Qwen3-Coder-Next:latest |
| [Generated TypeScript sample workflows](https://github.com/hysel/haven-42/wiki/Evidence-Record-588241e349f32b95) | `partial-pass` | Windows · Ollama · devstral-small-2:latest |
| [Generated TypeScript sample workflows](https://github.com/hysel/haven-42/wiki/Evidence-Record-dff8d8e0aff407ab) | `partial-pass` | Windows · Ollama · Qwen3-Coder-Next:latest |
## Online Discovery

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Online model discovery](https://github.com/hysel/haven-42/wiki/Evidence-Record-2de3f0726ddaba91) | `candidate-only` | Cross-platform · N/A · N/A |
## Package Lifecycle

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Physical Apple M4 unsigned development update lifecycle](https://github.com/hysel/haven-42/wiki/Evidence-Record-c108ec90b7cbf335) | `partial-pass` | macOS 26.6.2 · two exact self-contained arm64 app archives · none |
## Package Parity

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Physical Apple M4 Alpha 2 development app browser flow](https://github.com/hysel/haven-42/wiki/Evidence-Record-d5ea2428d99b1560) | `partial-pass` | macOS 26.6.2 · Self-contained PyInstaller runtime · none |
| [Physical Apple M4 Alpha 2 portable development package](https://github.com/hysel/haven-42/wiki/Evidence-Record-a3ffc5fb42c08cc4) | `partial-pass` | macOS 26.6.2 · Self-contained PyInstaller runtime · none |
| [Windows Alpha 2 current UI package parity](https://github.com/hysel/haven-42/wiki/Evidence-Record-2589000e63822b5e) | `partial-pass` | Windows 11 · local web runtime · none |
## Platform Compatibility

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Physical Apple M4 exact-source native full suite](https://github.com/hysel/haven-42/wiki/Evidence-Record-e0ff8b838482c84e) | `validated-by-tests` | macOS 26.6.2 · Self-contained test toolchain · none |
## Power Evidence

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Apple M4 16 GB Ministral 3 8B bounded power sample](https://github.com/hysel/haven-42/wiki/Evidence-Record-0ca29f0fa9fbdcdb) | `partial-pass` | macOS 26.6.2 · Ollama 0.32.15 Metal · ministral-3:8b-instruct-2512-q4_K_M@1922accd5827ebe6829e536369195db25eaf664528dc66206d646ea3bb386b71 |
| [Apple M4 16 GB Qwen 3.5 2B bounded power sample](https://github.com/hysel/haven-42/wiki/Evidence-Record-157bfe9c7bf20597) | `partial-pass` | macOS 26.6.2 · Ollama 0.32.15 Metal · qwen3.5:2b@324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df |
| [Apple M4 16 GB Qwen 3.5 4B bounded power sample](https://github.com/hysel/haven-42/wiki/Evidence-Record-f955c93a1ebd4164) | `partial-pass` | macOS 26.6.2 · Ollama 0.32.15 Metal · qwen3.5:4b@2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd |
| [Apple M4 16 GB idle Apple SoC sample](https://github.com/hysel/haven-42/wiki/Evidence-Record-cea92a2e0ac35bf8) | `partial-pass` | macOS 26.6.2 · Ollama 0.32.15 Metal · no-loaded-model |
| [NVIDIA GeForce RTX 3060 12 GB mixed-task model soak power](https://github.com/hysel/haven-42/wiki/Evidence-Record-58d8481eef7a394b) | `partial-pass` | Windows 11 · Ollama 0.32.14 CUDA · 14-model-passed-soak-corpus |
| [Radeon RX 5700 XT Llama 3.2 3B board power](https://github.com/hysel/haven-42/wiki/Evidence-Record-9a9906ccfd247313) | `partial-pass` | Ubuntu 26.04 LTS · Ollama 0.32.13 Vulkan RADV · llama3.2:3b-instruct-q4_K_M |
| [Radeon RX 5700 XT Qwen 3.5 0.8B Windows llama.cpp paced-soak power](https://github.com/hysel/haven-42/wiki/Evidence-Record-0b86ce2eeb867f1f) | `partial-pass` | Windows 10.0.26200.8973 · llama.cpp b10375 Vulkan AMD proprietary 26.7.1 · Qwen 3.5 0.8B Q4_0 GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| [Radeon RX 5700 XT Qwen 3.5 0.8B llama.cpp board power](https://github.com/hysel/haven-42/wiki/Evidence-Record-2aa29208b11bc71d) | `partial-pass` | Ubuntu 26.04 LTS · llama.cpp b10375 Vulkan RADV · Qwen 3.5 0.8B Q4_0 GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| [Ubuntu NVIDIA GeForce GTX 1650 Super 4 GB mixed-task model soak power](https://github.com/hysel/haven-42/wiki/Evidence-Record-60b8a8cd266e76e3) | `partial-pass` | Ubuntu 26.04 LTS · Ollama 0.32.14 CUDA · five-model-passed-soak-corpus |
| [Ubuntu NVIDIA GeForce RTX 3060 12 GB mixed-task model soak power](https://github.com/hysel/haven-42/wiki/Evidence-Record-ad94c1f53c81365c) | `partial-pass` | Ubuntu 26.04 LTS · Ollama 0.32.14 CUDA · 19-model-passed-soak-corpus |
| [Windows NVIDIA GeForce GTX 1650 Super 4 GB mixed-task model soak power](https://github.com/hysel/haven-42/wiki/Evidence-Record-00b72ba071ebf282) | `partial-pass` | Windows 11 · Ollama 0.32.14 CUDA · three-model-passed-soak-corpus |
## Remote Profile

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Remote hardware profiling](https://github.com/hysel/haven-42/wiki/Evidence-Record-77e5fbc983b71597) | `validated-by-tests` | Cross-platform · N/A · N/A |
## Sample Repository

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Python API generated sample](https://github.com/hysel/haven-42/wiki/Evidence-Record-32bd4f913b5ede9d) | `read-only-cli-validated` | Windows · Ollama · local-config |
| [TypeScript frontend generated sample](https://github.com/hysel/haven-42/wiki/Evidence-Record-22701a5715776e0d) | `read-only-cli-validated` | Windows · Ollama · local-config |
## Web Research

| Evidence | Status | Tested environment |
| --- | --- | --- |
| [Native fixed-provider metadata query](https://github.com/hysel/haven-42/wiki/Evidence-Record-01b01f98b537ca75) | `partial-pass` | Windows · Wikipedia metadata API · none |
| [Native fixed-provider metadata query on Linux](https://github.com/hysel/haven-42/wiki/Evidence-Record-7207da1f9eca0995) | `partial-pass` | Native headless Linux · Wikipedia metadata API · none |
| [Native selected-page transport on Windows and Linux](https://github.com/hysel/haven-42/wiki/Evidence-Record-f36876d9cc12face) | `partial-pass` | Windows and native headless Linux · Wikipedia query and extracts APIs · none |

## Automatic-update boundary

`config/evidence-page-registry.json` is the machine-readable input reserved
for future update compatibility checks. Its records are advisory evidence
only and cannot activate an update or change a model default.
