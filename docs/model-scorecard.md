# Model Scorecard

Generated from config/evidence-catalog.tsv and config/model-recommendations.tsv.

| Model | Surface | OS | Operation | Mode | Readiness | Evidence count |
| --- | --- | --- | --- | --- | --- | ---: |
| qwen3.5:9b | Continue CLI | macOS | scoped-write | generated-sample | approved-write ready | 1 |
| qwen3.5:9b | Continue Agent | Windows | scoped-write | editor-agent | approved-write ready | 1 |
| qwen3.5:35b | Continue CLI | Windows | scoped-write | generated-sample | approved-write ready | 1 |
| devstral-small-2:24b | Continue CLI | Windows | scoped-write | generated-sample | approved-write ready | 1 |
| mlx-community/Qwen3.5-9B-OptiQ-4bit | Continue CLI | macOS | code-review | generated-sample | review validated | 1 |
| qwen3.5:9b | Continue Agent | Windows | plan | editor-agent | plan validated | 1 |
| mlx-community/Qwen3.5-9B-OptiQ-4bit | Continue CLI | macOS | implementation-plan | generated-sample | plan validated | 1 |
| qwen3.5:9b | Continue CLI | Windows | write-smoke | generated-sample | disposable write-smoke validated | 1 |
| qwen3.5:9b | Aider CLI | Windows | write-smoke | generated-sample | disposable write-smoke validated | 1 |
| qwen3.5:35b | OpenCode CLI | Windows | write-smoke | generated-sample | disposable write-smoke validated | 1 |
| qwen3-coder:30b | Continue CLI | Windows | write-smoke | generated-sample | disposable write-smoke validated | 1 |
| qwen3-coder:30b | Aider CLI | Windows | scoped-write | generated-sample | disposable write-smoke validated | 2 |
| qwen3-coder:30b | Aider CLI | Windows | write-smoke | generated-sample | disposable write-smoke validated | 1 |
| mlx-community/Qwen3.5-9B-OptiQ-4bit | Continue Agent | macOS | scoped-write | editor-agent | disposable write-smoke validated | 1 |
| mlx-community/Qwen3.5-9B-OptiQ-4bit | Continue CLI | macOS | write-smoke | generated-sample | disposable write-smoke validated | 1 |
| mlx-community/Qwen3.5-9B-4bit | Continue CLI | macOS | write-smoke | generated-sample | disposable write-smoke validated | 1 |
| mlx-community/Qwen3.5-4B-4bit | Continue CLI | macOS | write-smoke | generated-sample | disposable write-smoke validated | 1 |
| devstral-small-2:24b | OpenCode CLI | Windows | scoped-write | generated-sample | disposable write-smoke validated | 1 |
| devstral-small-2:24b | Continue CLI | Windows | write-smoke | generated-sample | disposable write-smoke validated | 1 |
| qwen3.5:9b | OpenCode CLI | Windows | read-file | generated-sample | read-only tool validated | 1 |
| qwen3.5:9b | Aider CLI | Windows | read-file | generated-sample | read-only tool validated | 1 |
| qwen3.5:9b | Continue Agent | Windows | read-file | editor-agent | read-only tool validated | 1 |
| qwen3-coder:30b | Continue Agent | Windows | read-file | editor-agent | read-only tool validated | 1 |
| qwen3-coder:30b | Continue Agent | Windows | repository-list | editor-agent | read-only tool validated | 2 |
| qwen3-coder:30b | Aider CLI | Windows | read-file | generated-sample | read-only tool validated | 1 |
| mlx-community/Qwen3.5-9B-OptiQ-4bit | MLX OpenAI-compatible server | macOS | structured-tool-call | local-endpoint | read-only tool validated | 1 |
| mlx-community/Qwen3.5-9B-4bit | MLX OpenAI-compatible server | macOS | structured-tool-call | local-endpoint | read-only tool validated | 1 |
| mlx-community/Qwen3.5-4B-4bit | MLX OpenAI-compatible server | macOS | structured-tool-call | local-endpoint | read-only tool validated | 1 |
| devstral-small-2:24b | Continue Agent | Windows | read-file | editor-agent | read-only tool validated | 1 |
| qwen3.5:9b | Continue CLI | macOS | read-workflows | generated-sample | read-only CLI validated | 1 |
| qwen3.5:9b | Continue CLI | Windows | read-file | generated-sample | read-only CLI validated | 1 |
| qwen3-coder:30b | Continue CLI | Windows | read-file | generated-sample | read-only CLI validated | 1 |
| mlx-community/Qwen3.5-9B-OptiQ-4bit | Continue CLI | macOS | read-file | generated-sample | read-only CLI validated | 1 |
| mlx-community/Qwen3.5-9B-4bit | Continue CLI | macOS | read-file | generated-sample | read-only CLI validated | 1 |
| mlx-community/Qwen3.5-4B-4bit | Continue CLI | macOS | read-file | generated-sample | read-only CLI validated | 1 |
| devstral-small-2:24b | Continue CLI | Windows | read-file | generated-sample | read-only CLI validated | 1 |
| SDXL Base 1.0 | Local image capability adapter | Linux | image-generation | local-endpoint | script/test validated | 1 |
| qwen3.5:9b | LLM intent routing | Windows | intent-routing | local-endpoint | script/test validated | 1 |
| qwen3.5:9b | Local text capability adapter | Windows | general-chat | local-endpoint | script/test validated | 1 |
| qwen3.5:9b | Ollama | Windows | trusted-artifact-comparison | local-endpoint | script/test validated | 1 |
| qwen3.5:9b | Local text capability adapter | Windows | general-summarization | local-endpoint | script/test validated | 1 |
| qwen3.5:9b | Local text capability adapter | Linux | writing-constraint-screen | local-endpoint | script/test validated | 1 |
| qwen3.5:9b | Local text capability adapter | Windows | general-writing | local-endpoint | script/test validated | 1 |
| qwen3.5:9b | Ollama | Linux | trusted-artifact-comparison | local-endpoint | script/test validated | 1 |
| qwen3.5:9b | Pack scripts | Cross-platform | config-recommendation | automated-tests | script/test validated | 1 |
| qwen3.5:9b | Capability availability discovery | Windows | provider-discovery | local-endpoint | script/test validated | 1 |
| no-model | Haven 42 web UI | Headless browser source | inert-destination-disclosure | browser-and-static | script/test validated | 1 |
| no-model | Haven 42 web UI | Headless browser source | explicit-query-page-review | browser-and-static | script/test validated | 1 |
| mistral-small3.2:24b-instruct-2506-q4_K_M | Local text capability adapter | Linux | writing-constraint-screen | local-endpoint | script/test validated | 1 |
| gemma3:12b | Local text capability adapter | Linux | writing-constraint-screen | local-endpoint | script/test validated | 1 |
| Qwen3-Coder-Next:latest | Continue CLI | Windows | workflow-review | generated-sample | plan/review candidate | 1 |
| devstral-small-2:latest | Continue CLI | Windows | workflow-review | generated-sample | plan/review candidate | 1 |
| unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 | llama.cpp server | Linux | backend-validation | local-endpoint | partial pass | 1 |
| unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 | llama.cpp server | Linux | backend-validation | local-endpoint | partial pass | 1 |
| unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 | llama.cpp server | Windows | backend-validation | local-endpoint | partial pass | 1 |
| SDXL Base 1.0 | Local image capability adapter | Windows | image-generation | local-endpoint | partial pass | 3 |
| revision-and-sha256-pinned-follow-on-artifacts | llama.cpp CLI and server | Windows | backend-validation | local-endpoint | partial pass | 1 |
| revision-and-sha256-pinned-11-model-corpus | llama.cpp CLI | Windows and Linux | backend-validation | local-endpoint | partial pass | 1 |
| revision-and-sha256-pinned-11-model-corpus | llama.cpp CLI | WSL2 Ubuntu | backend-validation | local-endpoint | partial pass | 1 |
| qwen3.8:27b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak-tools-thinking-recovery-vision | local-endpoint | partial pass | 1 |
| qwen3.8:27b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | partial pass | 1 |
| qwen3.6:35b-a3b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak-residency | local-endpoint | partial pass | 1 |
| qwen3.6:35b-a3b-q4_K_M | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | partial pass | 1 |
| qwen3.6:27b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak | local-endpoint | partial pass | 1 |
| qwen3.5:9b Q4_K_M | Ollama | Windows 11 | chat-writing-summary-soak-energy | local-endpoint | partial pass | 1 |
| qwen3.5:4b-q4_K_M | Ollama | Ubuntu 26.04 LTS | chat-writing-summary-soak-residency | local-endpoint | partial pass | 1 |
| qwen3.5:4b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | partial pass | 1 |
| qwen3.5:4b | Continue CLI | Windows controller and Ubuntu 26.04 AMD Radeon RX 5700 XT model host | 26-read-review-write-scoped-edit-workflows-cancellation-recovery-residency-unload | generated-sample | partial pass | 1 |
| qwen3.5:4b | Continue CLI | Windows controller and Ubuntu 26.04 AMD Radeon RX 5700 XT model host | api-read-review-write-scoped-edit-full-gpu-residency | generated-sample | partial pass | 1 |
| qwen3.5:4b | VS Code-compatible + Continue | Windows editor and Ubuntu 26.04 AMD Radeon RX 5700 XT model host | read-tools-approved-two-file-write-external-test-bounded-patch-recovery | editor-agent | partial pass | 1 |
| qwen3.5:35b | Continue CLI | Windows | workflow-suite | generated-sample | partial pass | 1 |
| qwen3.5:0.8b Q8_0 | Haven 42 source candidate | Ubuntu 26.04 LTS | setup-inference-reuse-uninstall | local-endpoint | partial pass | 1 |
| qwen3.5:0.8b Q8_0 | Haven 42 source candidate | Ubuntu 24.04.4 LTS | setup-inference-reuse-uninstall | local-endpoint | partial pass | 1 |
| qwen3.5:0.8b Q8_0 | Haven 42 source candidate | Pop OS 24.04 LTS | setup-inference-reuse-uninstall | local-endpoint | partial pass | 1 |
| qwen3.5:0.8b Q8_0 | Haven 42 source candidate | Fedora 44 | setup-inference-reuse-uninstall | local-endpoint | partial pass | 1 |
| qwen3.5:0.8b Q8_0 | Haven 42 source candidate | Debian 13 | setup-inference-reuse-uninstall | local-endpoint | partial pass | 1 |
| qwen3.5:0.8b Q8_0 | Haven 42 source candidate | CachyOS rolling | setup-inference-reuse-uninstall | local-endpoint | partial pass | 1 |
| qwen3.5:0.8b Q8_0 | Haven 42 source candidate | Linux Mint 22.3 | setup-recovery-inference-reuse-uninstall | local-endpoint | partial pass | 1 |
| qwen3.5:0.8b Q8_0 | Haven 42 source candidate | Bazzite 44 | setup-inference-reuse-uninstall | local-endpoint | partial pass | 1 |
| qwen3.5:0.8b Q8_0 | Haven 42 source candidate | Arch Linux rolling | setup-inference-reuse-uninstall | local-endpoint | partial pass | 1 |
| Qwen3-Coder-Next:latest | Continue CLI | Windows | workflow-suite | generated-sample | partial pass | 2 |
| phi4-mini:3.8b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak | local-endpoint | partial pass | 1 |
| ornith-10:9b-q4_K_M | Ollama | Ubuntu 26.04 LTS | chat-writing-summary-soak-coding-tools-recovery-residency | local-endpoint | partial pass | 1 |
| OpenVINO/Qwen3-0.6B-int4-ov@f864c6106efb6c7f7b4ef274a78a98e37210dddd | OpenVINO GenAI | Linux | backend-validation | local-endpoint | partial pass | 1 |
| OpenVINO/Qwen3-0.6B-int4-ov@f864c6106efb6c7f7b4ef274a78a98e37210dddd | OpenVINO GenAI | Windows | backend-validation | local-endpoint | partial pass | 1 |
| north-mini-code:10-30b-a3b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak-tools-context-recovery-coding | local-endpoint | partial pass | 1 |
| north-mini-code-1.0:q4_K_M | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | partial pass | 1 |
| none | Haven 42 development key adapter | Windows | wrap-unwrap-synthetic-key | development-native | partial pass | 1 |
| none | Haven 42 development availability probe | Linux headless container session | session-bus-credential-store-presence-cleanup | development-native | partial pass | 1 |
| none | Haven 42 development availability probe | GitHub-hosted macOS 15 | system-tool-presence | automated-tests | partial pass | 1 |
| none | Haven 42 development ACL proof | Windows | protected-directory-inherited-file-unexpected-principal-cleanup | development-native | partial pass | 1 |
| none | Haven 42 development query transport | Native headless Linux | query-metadata-transport-integrity-cleanup | development-network | partial pass | 1 |
| none | Haven 42 development query transport | Windows | query-metadata | development-network | partial pass | 1 |
| none | Haven 42 development selected-page transport | Windows and native headless Linux | selected-page-text-transport-integrity-cleanup | development-network | partial pass | 1 |
| none | Haven 42 development key persistence adapter | Windows | atomic-write-recover-tamper-missing-cleanup | development-native | partial pass | 1 |
| none | Haven 42 unsigned portable development package | Windows 11 | source-package-lifecycle-browser-accessibility | development-native | partial pass | 1 |
| no-model | Haven 42 Linux host-stability harness | Ubuntu 26.04 LTS | 600-second-four-worker-cpu-smoke-and-hardware-log-review | development-native | partial pass | 1 |
| no-model | Haven 42 source web runtime | Windows | explicit-query-and-selected-page | live-fixed-provider | partial pass | 1 |
| no-model | Haven 42 unsigned portable development package | Windows | explicit-query-and-selected-page | development-native | partial pass | 1 |
| nemotron-3.5-lightning:30b-a3b-q8_0 | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak-energy | local-endpoint | partial pass | 1 |
| nemotron-3.5-lightning:30b-a3b-q8_0 | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak | local-endpoint | partial pass | 1 |
| nemotron-3.5-lightning:30b-a3b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak | local-endpoint | partial pass | 1 |
| nemotron-3.5-lightning:30b-a3b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak-energy | local-endpoint | partial pass | 1 |
| nemotron-3-nano-omni:33b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak-thinking-recovery-tools-vision | local-endpoint | partial pass | 1 |
| muse-glimmer:30b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | partial pass | 1 |
| mlx-community/Qwen3.5-4B-4bit | Continue Agent | macOS | scoped-write | editor-agent | partial pass | 1 |
| llama3.2:3b-instruct-q4_K_M | Haven 42 Linux AMD power profiler | Ubuntu 26.04 LTS | idle-active-peak-energy-throughput-unload | local-endpoint | partial pass | 1 |
| laguna-xs-2.1:q4_K_M | Local text capability adapter | Linux | provider-conformance | local-endpoint | partial pass | 1 |
| granite41-8b-q4_K_M | llama.cpp SYCL | Ubuntu Linux | chat-writing-summary-soak | local-endpoint | partial pass | 1 |
| granite4.1:30b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak-coding-tools-recovery-residency | local-endpoint | partial pass | 1 |
| granite4:7b-a1b-h | Local text capability adapter | Linux | writing-constraint-screen | local-endpoint | partial pass | 1 |
| gemma4:e4b-qat | Ollama | Ubuntu 26.04 LTS | chat-writing-summary-soak-residency | local-endpoint | partial pass | 1 |
| gemma4:e2b-qat | Ollama | Ubuntu 26.04 LTS | chat-writing-summary-soak-residency | local-endpoint | partial pass | 1 |
| gemma3:1b-it-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-soak | local-endpoint | partial pass | 1 |
| devstral-small-2:latest | Continue CLI | Windows | workflow-suite | generated-sample | partial pass | 2 |
| devstral-small-2:24b | OpenCode CLI | Windows | read-and-write | generated-sample | partial pass | 1 |
| devstral-small-2:24b | Continue CLI | Windows | workflow-suite | generated-sample | partial pass | 1 |
| acestep-v15-turbo | ACE-Step REST API | Linux | instrumental-and-vocal-request-generation | local-endpoint | partial pass | 1 |
| 17 exact manifest-pinned models | Ollama | Windows 11 | chat-writing-summary-soak | local-endpoint | partial pass | 1 |
| 16 exact manifest-pinned model profiles | Haven 42 Alpha 2 qualification harness | Ubuntu 26.04 LTS | admission-core-tasks-residency-stability-power | local-endpoint | partial pass | 1 |
| synthetic-bounded-source-envelope | No runtime | Windows and Linux | cited-synthesis-validation | offline-fixture | candidate only | 1 |
| none | Haven 42 admission policy | Cross-platform | eight-gate-private-session-readiness | offline-fixture | candidate only | 1 |
| no-model | No runtime | Windows and Linux | offline-boundary | offline-fixture | candidate only | 1 |
| no-model | No runtime | Cross-platform | offline-boundary | offline-fixture | candidate only | 1 |
| no-model | No runtime | Cross-platform | offline-boundary | offline-fixture | candidate only | 1 |
| no-model | Aider and OpenCode | Cross-platform | dry-run-plan | offline-fixture | candidate only | 1 |
| unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 | llama.cpp completion and benchmark | Windows | backend-validation | local-endpoint | candidate only | 1 |
| none | Haven 42 development availability probe | Linux | session-bus-credential-store-presence | offline-mocked | candidate only | 1 |
| none | Haven 42 development availability probe | macOS | system-tool-presence | offline-mocked | candidate only | 1 |
| none | Haven 42 dependency admission | Cross-platform | dependency-provenance-license-fit | offline-primary-source-review | candidate only | 1 |
| mlx-community/Devstral-Small-2-24B-Instruct-2512-4bit | MLX OpenAI-compatible server | macOS | structured-tool-call | local-endpoint | candidate only | 1 |
| exact-upstream-candidate-records | No runtime | Linux | hardware-and-storage-preflight | offline-metadata | candidate only | 1 |
| qwen3.6:27b-q4_K_M | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| qwen3.5:4b | VS Code-compatible + Continue | Windows editor and Ubuntu 26.04 AMD Radeon RX 5700 XT model host | exact-file-read-edit-tool-availability-external-diff | editor-agent | candidate only | 1 |
| qwen3.5:4b | VSCodium + Continue | Windows editor and Ubuntu 26.04 AMD Radeon RX 5700 XT model host | exact-file-read-agent-edit-fallback-apply-external-diff | editor-agent | candidate only | 1 |
| qwen3.5:2b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| qwen3.5:0.8b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| ornith:9b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| nemotron3:33b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| nemotron-3.5-lightning:30b-a3b-q8_0 | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| nemotron-3.5-lightning:30b-a3b-q4_K_M | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| muse-glimmer:30b-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-gate | local-endpoint | candidate only | 1 |
| ministral-3:8b-instruct-2512-q4_K_M | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| ministral-3:8b-instruct-2512-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-gate | local-endpoint | candidate only | 1 |
| ministral-3:3b-instruct-2512-q4_K_M | Ollama | Ubuntu 24.04.4 | chat-writing-summary-gate | local-endpoint | candidate only | 1 |
| ministral-3:3b-instruct-2512-q4_K_M | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| minicpm-v4.6:1b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| minicpm-v:4.6-1b-q4_K_M | Ollama | Ubuntu 26.04 LTS | chat-vision-recovery-residency | local-endpoint | candidate only | 1 |
| lfm2.5:8b-a1b-q4_K_M | Ollama | Ubuntu 26.04 LTS | chat-writing-summary-gate-residency | local-endpoint | candidate only | 1 |
| lfm2.5:8b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| granite4.1:30b | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| gemma3:1b-it-q4_K_M | Continue CLI | Windows controller and Ubuntu 24.04.4 CUDA model host | api-read-review-write-scoped-edit | generated-sample | candidate only | 1 |
| five exact manifest-pinned models | Ollama | Ubuntu 24.04.4 | chat-writing-summary-gate | local-endpoint | candidate only | 1 |
