# NVIDIA GeForce RTX 3060 12 GB on Ubuntu 26.04

## What this record proves

On August 18, 2026, one Ubuntu 26.04 LTS computer with a GeForce RTX 3060
12 GB completed the Alpha 2 exact-artifact model campaign. The run used Linux
kernel 7.0.0-30, NVIDIA driver 610.43.02, CUDA, and an isolated Ollama 0.32.14
runtime.

All 19 model artifacts passed three samples each for Chat, Writing, and
Summarization. Every sample also passed the required unload check. Each model
then completed its own 30-minute soak with a request every 30 seconds and an
unload after every response.

This is exact-profile engineering evidence. It does not certify every RTX
3060 computer, another operating system or driver, the packaged beginner
workflow, accessibility, or a coding-agent surface. It does not change Haven
42's automatic model choice, runtime admission, or support labels.

## Results

| Model artifact | Task gate | 30-minute soak |
| --- | --- | --- |
| Qwen 3.5 0.8B Q8_0 | Passed | Passed |
| Qwen 3.5 2B Q8_0 | Passed | Passed |
| Qwen 3.5 4B Q4_K_M | Passed | Passed |
| Qwen 3.5 9B Q4_K_M | Passed | Passed |
| Gemma 3 1B Q4_K_M | Passed | Passed |
| Gemma 3 4B Q4_K_M | Passed | Passed |
| Gemma 3 12B Q4_K_M | Passed | Passed |
| Gemma 4 E2B QAT | Passed | Passed |
| Gemma 4 E4B QAT | Passed | Passed |
| Gemma 4 12B QAT | Passed | Passed |
| Granite 4.1 3B Q4_K_M | Passed | Passed |
| Granite 4.1 8B Q4_K_M | Passed | Passed |
| Phi 4 Mini 3.8B Q4_K_M | Passed | Passed |
| Llama 3.2 3B Q4_K_M | Passed | Passed |
| Ministral 3 3B Q4_K_M | Passed | Passed |
| Ministral 3 8B Q4_K_M | Passed | Passed |
| Ornith 10 9B Q4_K_M | Passed | Passed |
| LFM 2.5 8B-A1B Q4_K_M | Passed | Passed |
| MiniCPM V4.6 1B Q4_K_M | Passed | Passed |

## Power evidence

`nvidia-smi` captured 37,443 one-second graphics-board samples. The pre-run
idle window averaged 13.962 W and the post-run idle window averaged 14.175 W.
Across the 19 paced model windows, average board power ranged from 23.577 W
to 32.876 W and the observed peaks ranged from 56.54 W to 139.18 W.

These are GPU-board readings, not wall power. They exclude CPU, system
memory, storage, cooling, display power, and power-supply losses. The test's
deliberate pauses and unloads make these mixed-task averages; they are not a
maximum-load benchmark.

## Why the Windows and Linux rows differ

The separate Windows RTX 3060 campaign stopped five artifacts at explicit
task-contract failures. This Ubuntu campaign passed all 19. The results are
kept as separate evidence cells because operating system, driver, harness,
and runtime behavior can change the outcome. Neither result is generalized
to the other platform.

The sanitized machine-readable result is
[`config/alpha-2-nvidia-rtx3060-linux-qualification-result.json`](https://github.com/hysel/haven-42/blob/main/config/alpha-2-nvidia-rtx3060-linux-qualification-result.json).
