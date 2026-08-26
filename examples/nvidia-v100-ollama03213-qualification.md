# Ollama 0.32.13 NVIDIA Qualification

Status: exact-profile engineering evidence; no automatic selection or default
change.

On August 15, 2026, three immutable Ollama artifacts completed the current
Chat, Writing, and Summarization qualification contract and separate
30-minute reliability soaks on Ubuntu 24.04.4 with CUDA. The test computer
had 128 GiB of system memory and 64 GiB of aggregate usable GPU memory from two
Tesla V100 32 GiB cards. Ollama was pinned to `0.32.13` and contacted only over
IPv4 loopback.

The evidence retains only bounded aggregate measurements. It contains no
prompts, responses, endpoints, machine identity, account information, or
filesystem paths.

## Results

| Exact model | Qualification lane | Task checks | 30-minute soak | Peak reported GPU residency |
| --- | --- | --- | --- | ---: |
| `gemma3:1b-it-q4_K_M` | `cuda-16gib` | 3/3 Chat, 3/3 Writing, 3/3 Summarization; all nine unload proofs passed | 42/42 samples and unload proofs; 182.075 tokens/s average | 937,070,427 bytes |
| `phi4-mini:3.8b-q4_K_M` | `cuda-16gib` | 3/3 Chat, 3/3 Writing, 3/3 Summarization; all nine unload proofs passed | 42/42 samples and unload proofs; 155.504 tokens/s average | 3,209,345,105 bytes |
| `qwen3.6:27b-q4_K_M` | `cuda-32gib-system-16gib` | 3/3 Chat, 3/3 Writing, 3/3 Summarization; all nine unload proofs passed | 30/30 samples and unload proofs; 33.527 tokens/s average | 16,482,859,743 bytes |

The task-specific rates were:

| Exact model | Chat | Writing | Summarization |
| --- | ---: | ---: | ---: |
| `gemma3:1b-it-q4_K_M` | 179.776 tokens/s | 180.540 tokens/s | 198.665 tokens/s |
| `phi4-mini:3.8b-q4_K_M` | 149.402 tokens/s | 155.109 tokens/s | 160.070 tokens/s |
| `qwen3.6:27b-q4_K_M` | 35.215 tokens/s | 33.164 tokens/s | 32.757 tokens/s |

Within the shared `cuda-16gib` lane, the owner-review ranking places Gemma 3
1B ahead of Phi 4 Mini for all three tasks on throughput after both models
passed the same deterministic task and soak gates. Qwen 3.6 27B is the only
candidate in its larger-memory lane and is not compared directly with the
smaller lane.

## Interpretation

This result supersedes neither older runtime evidence nor evidence from other
hardware. In particular, earlier failures remain valid for their exact Ollama
version, contract, operating system, and hardware profile. The new records show
that these three exact artifacts pass the current contract on Ollama 0.32.13
and this exact Ubuntu/CUDA environment.

The measured memory values came from a 64 GiB aggregate GPU environment. A
qualification lane's 16 GiB admission floor is not proof that the same model
will behave identically on a physical 16 GiB card. Physical memory-tier tests,
other accelerator vendors, package lifecycle, recovery, context pressure,
energy, and human comparative quality review remain separate gates.

The sanitized report and ranking explicitly set automatic selection and
automatic default changes to false. These results support engineering review;
they do not download a model for an end user or change Haven 42's model ladder.
