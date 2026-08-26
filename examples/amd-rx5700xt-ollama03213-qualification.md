# Radeon RX 5700 XT qualification evidence

This report tests one Radeon RX 5700 XT 8 GiB on Ubuntu 26.04 and Windows.
The Ubuntu cells use Ollama 0.32.13 and llama.cpp through Vulkan RADV. The
Windows cell uses a hash-pinned llama.cpp Vulkan build with AMD's proprietary
driver. The question is narrow: can these exact RDNA 1 configurations run
the tested local models without quietly falling back to the CPU?

## Hardware and runtime proof

The sanitized hardware record contains:

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

The admission policy refused oversized 12 GiB-class candidates before download
on the automatic 8 GiB path. That refusal is a safety pass, not proof that those
models are defective.

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

## llama.cpp Vulkan engine smoke

A separate engine cell used upstream llama.cpp `b10375` at commit
`ba360efe1`. The 31.10 MiB Ubuntu Vulkan archive matched the plan-pinned
SHA-256 before extraction. The test used the already-present Qwen 3.5 0.8B
Q4_0 GGUF with SHA-256
`57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`.

The runtime identified `AMD Radeon RX 5700 XT (RADV NAVI10)`, assigned all 25
model layers to `Vulkan0`, and returned the exact bounded response at 277.092
generated tokens per second. Board VRAM rose from 109,457,408 bytes to
756,559,872 bytes and returned to exactly 109,457,408 bytes after exit. No
llama.cpp process remained, and the existing Ollama process stayed active.

An initial invocation generated successfully but reached its timeout because
llama.cpp automatically entered interactive conversation mode and waited for
another prompt. The corrected run used explicit single-turn mode and disabled
reasoning. The initial timeout is retained as harness evidence and is not
classified as a model or GPU failure.

This Ubuntu result is only a bounded engine smoke. It does not certify the full
llama.cpp model ladder, package lifecycle, server adapter, sustained operation,
ROCm, or automatic runtime selection.

## Windows llama.cpp Vulkan task and soak

A separate Windows cell used upstream llama.cpp `b10375` at commit `ba360efe1`
and the same hash-pinned Qwen 3.5 0.8B Q4_0 GGUF. The Windows Vulkan archive
matched SHA-256
`1fef77a8b7742485c3f9f0acd16b68330ca9d5f447b73eb80d32862e4b2c7cfa`
before extraction. The runtime identified the RX 5700 XT through AMD's
proprietary Vulkan driver 26.7.1 and assigned all 25 model layers to the GPU.

The task gate passed all nine required samples: three Chat, three Writing, and
three Summarization. No reasoning leakage was detected. The following
30-minute soak passed 1,602 of 1,602 requests, evenly split across the three
tasks, and produced 31,506 completion units. Device proof, full offload, and
process cleanup all passed.

Two earlier launch attempts are retained as harness findings, not model or GPU
failures. One detached process ended when its SSH session closed; one
interactive-only scheduled task never launched. The valid soak used a
persistent foreground process and ended cleanly.

This is an exact Windows engine-and-model cell. It does not establish Windows
Ollama behavior, managed installation or update behavior, other models,
automatic model selection, or the full packaged Haven 42 lifecycle.

## Stability boundary

The machine had unexplained freezes before its final firmware and memory
configuration. The owner reports that disabling Global C-state control resolved
the freezes and has accepted the current exact profile as operationally stable.
This setting is owner-reported because the running operating system cannot
independently attest the BIOS value.

At the evidence review, the current boot reported 78,782 seconds of uptime
(21 hours 53 minutes), zero failed systemd units, and no matching machine-check,
uncorrected-memory, GPU-reset, CPU-lockup, critical-thermal, or fatal-PCIe
incident. A separate bounded CPU smoke had already completed 600 seconds across
four workers with no detected incident. The machine-reported current boot had
not yet reached 24 hours, so this report does not claim a verified 24-hour
current-boot duration.

The report also does not turn an earlier memory-test result into proof for a
later firmware profile. A complete final-profile memory test remains open.
Accordingly, the profile is accepted as exact-profile operationally stable,
not as a general certification of every RX 5700 XT system or firmware setting.

## Power boundary

Linux exposes the card's `power1_average` board-power sensor. The measurement
keeps GPU-board power separate from whole-system wall power. A failed first
capture remains in the evidence; a corrected retry uses a content-bounded
sysfs reader because sysfs reports a synthetic file size. With Llama 3.2 3B
Q4_K_M, the corrected profile measured 7.575 W idle average, 122.118 W active
average, 242 W peak, and 20.350129 Wh across the 600-second active window. It
produced 43,431 output tokens, or 2,134.188 tokens per active Wh, and verified
model unload. These are GPU-board sensor readings, not whole-computer power.

A separate hash-pinned llama.cpp `b10375` Vulkan profile used Qwen 3.5 0.8B
Q4_0. It measured 6.448 W idle average, 167.242 W active average, 180 W peak,
and 27.931213 Wh across 601.238 active seconds. The server completed 1,195
bounded requests and produced 152,960 output tokens, or 5,476.311 tokens per
active Wh. All 25 model layers were assigned to the GPU. VRAM rose from
107,360,256 bytes to 821,579,776 bytes and returned exactly to baseline after
exit. An independent post-run check found no test-process residue, no failed
systemd units, and no matching recent GPU-reset, machine-check, uncorrected
hardware, critical-thermal, or lockup incident; the existing Ollama service
remained active.

The two power profiles use different models, request shapes, and output sizes.
They are useful reference measurements for their exact cells, but they are not
a controlled Ollama-versus-llama.cpp efficiency comparison. Neither result is
whole-system wall power or an electricity-bill estimate.

The Windows soak also captured HWiNFO64 software sensors across 898 valid
samples at an observed interval of about two seconds. Across the full paced
30-minute workload, `GPU ASIC Power` averaged 23.322 W on a time-weighted basis
and integrated to 11.666022 Wh; its median was 7 W, 95th percentile was 154 W,
and maximum was 168 W. A five-minute post-soak idle window averaged 6.322 W.
When GPU utilization exceeded 10 percent, the conditional ASIC-power samples
averaged 113.633 W and reached 168 W. This conditional number is not a
time-integrated workload average.

The GPU reached 58 C, the hotspot reached 65 C, and memory junction reached
54 C. The raw CSV is retained outside version control and is bound by SHA-256
`3ad7633999e0b9434b80f3672e4cac8a0289088ff03a4622c5163792cf14e1d0`.
The exact HWiNFO executable version was not independently captured, so the
telemetry remains partial evidence. These are software-reported ASIC and PPT
sensors, not wall power and not necessarily total board input. The roughly
two-second sampling interval may miss short peaks.

## What this does not approve

This result does not establish broad Windows or ROCm support, every RX 5700 XT
board design, every driver version, package lifecycle behavior, or an automatic
model default. The Windows result applies only to the exact llama.cpp runtime,
driver, model artifact, task gate, and soak described above. Those broader
claims remain separate evidence cells and decisions.
