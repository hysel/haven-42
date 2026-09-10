# GeForce RTX 5050 8 GB — retained inference evidence

Ollama 0.32.14, CUDA. Windows 11 Pro 10.0.26200 used driver 616.64; Ubuntu 26.04 LTS / kernel 7.0.0-30-generic used driver 610.43.02.

| Model inventory ID | Windows core / soak samples | Ubuntu core / soak samples | Manifest SHA-256 |
| --- | ---: | ---: | --- |
| qwen35-9b-q4 | 9 / 126 | 9 / 132 | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` |
| qwen35-4b-q4 | 9 / 132 | 9 / 135 | `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd` |
| qwen35-2b-q8 | 9 / 132 | 9 / 135 | `324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df` |
| phi4-mini-38b-q4 | 9 / 141 | 9 / 147 | `78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753` |
| llama32-3b-q4 | 9 / 144 | 9 / 144 | `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72` |

Every recorded sample passed its bounded inference check and per-sample unload check. Three capabilities were exercised: Chat, Writing and Summarization. These counts are not human quality scores or coding-agent qualification.

Each model used a 30-minute repeated-load/inference/unload window, not continuous thermal stress. The original Windows 9B elapsed field is 1783.88 seconds (last-sample timing); preserved probes show a 1800.003349-second first-soak-to-next-model interval. This is a wall-clock reconstruction, not a recovered monotonic field. The original result is unchanged.

The first Windows controller stopped during the next model download because its status file was locked. The completed 9B record was retained; the other four models were tested in a separate resumed run. Per-sample unload proofs are present for 9B; its original whole-controller finalUnload field is unverified. The resumed Windows run and Ubuntu run each record a verified final unload.

Ubuntu package integrity, effect-free readiness and shutdown passed in a separate diagnostic probe. Managed setup did not complete and packaged inference was not run. Coding-agent checks remain not run. No default, support label, or release approval changes.

Raw HWiNFO and numerical telemetry remain private. The accompanying JSON retains source SHA-256 and byte counts only. No per-model power, energy-cost, or continuous peak claim is made.

## Scope and source record

The [sanitized result](../config/rtx5050-inference-result.json) retains the
separate original and resumed controller cleanup states, exact model digests,
source hashes, and the timing reconstruction. Windows passed 720 responses
across its two runs; Ubuntu passed 738. These results do not certify every
Blackwell card or an 8 GB system-RAM computer. Both profiles used approximately
128 GB of installed system RAM.

Coding-agent repository read, planning, review, filename fidelity, scoped edits,
structured tool calls, bounded context, timeout recovery, coding-surface unload,
and unintended-write checks remain **not-run**. No inference result substitutes
for those gates. The Ubuntu diagnostic package result is separate from the
failed managed-setup attempt and does not establish interactive packaged setup.
