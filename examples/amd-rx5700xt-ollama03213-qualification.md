# Radeon RX 5700 XT on Ubuntu 26.04

This report covers one Radeon RX 5700 XT 8 GiB running Ollama 0.32.13 through
the Vulkan backend on Ubuntu 26.04. It answers a narrow question: can this exact
RDNA 1 setup run useful local models without quietly falling back to the CPU?

## Hardware and runtime proof

The sanitized hardware attestation observed:

- AMD PCI vendor `0x1002`, device `0x731f`;
- the `amdgpu` kernel driver;
- the RADV Vulkan driver from Mesa 26.0.3;
- 8,573,157,376 bytes of VRAM; and
- Ubuntu 26.04 with the 7.0.0-29 kernel.

The evidence intentionally omits the host name, network address, hardware
serials, and UUIDs. Every accelerated request had to report Vulkan residency.
The final compact-model cells additionally required Ollama's GPU-resident byte
count to equal its total model byte count.

## Test method

For each eligible model, the harness ran three deterministic Chat, Writing, and
Summarization samples. A model that failed any task did not enter the soak. A
model that passed ran a bounded 30-minute mixed-task soak with repeated unloads.
Advertised coding, tools, vision, thinking, and recovery behaviors used
separate checks and did not inherit the core result.

Oversized 12 GiB-class candidates were checked by admission policy and refused
before download on the automatic 8 GiB path. That refusal is a safety pass, not
proof that those models are defective.

## Results

| Exact model | Result | What happened |
| --- | --- | --- |
| Gemma 3 1B Q4_K_M | Failed task gate | Chat and Writing passed; Summarization returned more than the required one sentence. |
| Gemma 3 4B Q4_K_M | Passed core | 42 soak samples passed at 113.089 tokens/s average. |
| Gemma 4 E2B QAT | Passed core | 42 soak samples passed at 146.822 tokens/s average. |
| Gemma 4 E4B QAT | Passed core | 42 soak samples passed at 87.342 tokens/s average. |
| Granite 4.1 3B Q4_K_M | Passed core | 45 soak samples passed at 135.295 tokens/s average. |
| Granite 4.1 8B Q4_K_M | Passed core | 42 soak samples passed at 65.265 tokens/s average. |
| Llama 3.2 3B Q4_K_M | Passed core | 45 soak samples passed at 144.331 tokens/s average. |
| Ministral 3 3B Q4_K_M | Failed task gate | Chat and Summarization passed; Writing returned more than one sentence. |
| Ministral 3 8B Q4_K_M | Failed task gate | Chat passed; Writing and Summarization missed their one-sentence contracts. |
| Phi 4 Mini 3.8B Q4_K_M | Passed core | 45 soak samples passed at 122.392 tokens/s average. |
| Qwen 3.5 0.8B Q8_0 | Failed task gate | Chat and Summarization passed with full GPU residency; Writing missed the required word-count range. |
| Qwen 3.5 2B Q8_0 | Failed task gate | Chat and Summarization passed with full GPU residency; Writing missed the required word-count range. |
| Qwen 3.5 4B Q4_K_M | Passed core | Full GPU residency and 42 soak samples passed at 93.501 tokens/s average. |
| Ornith 1.0 9B Q4_K_M | Passed core and advertised checks | Full residency, 42 soak samples, coding, tools, and recovery passed at 61.112 tokens/s average. |
| LFM 2.5 8B-A1B Q4_K_M | Failed task gate | Full residency was observed, but all three core response contracts failed; license review also remains open. |
| MiniCPM-V 4.6 1B Q4_K_M | Failed | Full residency and timeout/recovery passed, but the base Chat and separate vision-grounding contracts failed. No core soak ran. |

Every passing soak includes a verified unload after each sample. No failed
task-gate model entered a soak. Qwen 3.5 9B, Gemma 3 12B, and Gemma 4 12B
were safely refused before download because their exact model layers alone
exceeded the reviewed 8 GiB headroom envelope.

## Stability boundary

The machine previously had unexplained freezes before its final firmware and
memory configuration. The certification campaign therefore includes a
current-boot hardware-error review and a bounded CPU smoke after model testing.
That cell completed 600 seconds across four workers and found no machine-check,
uncorrected-memory, GPU-reset, CPU-lockup, critical-thermal, or fatal-PCIe
incident in the current boot. The report does not turn an earlier memory-test
result into proof for a later firmware profile. A complete final-profile memory
test is still open, so this remains exact-profile engineering evidence rather
than a general RX 5700 XT support claim.

## Power boundary

Linux exposes the card's `power1_average` board-power sensor. The measurement
keeps GPU-board power separate from whole-system wall power. A failed first
capture remains in the evidence; a corrected retry uses a content-bounded
sysfs reader because sysfs reports a synthetic file size. With Llama 3.2 3B
Q4_K_M, the corrected profile measured 7.575 W idle average, 122.118 W active
average, 242 W peak, and 20.350129 Wh across the 600-second active window. It
produced 43,431 output tokens, or 2,134.188 tokens per active Wh, and verified
model unload. These are GPU-board sensor readings, not whole-computer power.

## What this does not approve

This result does not establish Windows support, ROCm support, every RX 5700 XT
board design, every driver version, package lifecycle behavior, or an automatic
model default. Those are separate evidence cells and decisions.
