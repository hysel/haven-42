# AMD Radeon RX 6800 16 GB Windows model qualification

## What this evidence answers

On August 22–23, 2026, Haven 42 tested 19 exact local model artifacts on one
Windows 11 computer with an AMD Radeon RX 6800 non-XT 16 GB. The run used an
isolated Ollama 0.32.14 qualification runtime with its ROCm backend.

This evidence applies only to that exact operating-system, runtime, hardware,
and model-digest set. The graphics-driver version was not captured in the
sanitized campaign evidence, so it is reported as unknown rather than inferred.
No automatic default, support label, managed-runtime choice, or another
hardware or operating-system result changes because of this run.

## Result at a glance

- All 19 exact artifacts passed Chat, Writing, and Summarization: 513 bounded core samples in total.
- All 19 artifacts passed independent 30-minute reliability soaks: 699 bounded soak samples and 699 unload proofs.
- The aggregate measured soak duration was 9.51 hours.
- Every one of the 429 local review files was scanned. None of those raw files is published.
- Raw HWiNFO telemetry is represented only by its byte count and SHA-256 digest.

## Model outcomes

| Exact artifact | Manifest SHA-256 | Core gate | 30-minute soak | Average generation | Peak GPU memory |
| --- | --- | --- | --- | ---: | ---: |
| qwen3.5:0.8b | `f3817196d142eaf72ce79dfebe53dcb20bd21da87ce13e138a8f8e10a866b3a4` | Passed, 27 samples | Passed, 45 samples | 227.204 tok/s | 1.01 GiB |
| qwen3.5:2b | `324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df` | Passed, 27 samples | Passed, 42 samples | 149.675 tok/s | 2.20 GiB |
| qwen3.5:4b | `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd` | Passed, 27 samples | Passed, 42 samples | 112.371 tok/s | 2.92 GiB |
| qwen3.5:9b | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | Passed, 27 samples | Passed, 42 samples | 75.740 tok/s | 5.12 GiB |
| gemma3:1b-it-q4_K_M | `8648f39daa8fbf5b18c7b4e6a8fb4990c692751d49917417b8842ca5758e7ffc` | Passed, 27 samples | Passed, 42 samples | 248.839 tok/s | 0.82 GiB |
| gemma3:4b-it-q4_K_M | `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a` | Passed, 27 samples | Passed, 36 samples | 133.742 tok/s | 2.70 GiB |
| gemma3:12b-it-q4_K_M | `f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a` | Passed, 27 samples | Passed, 27 samples | 56.089 tok/s | 7.51 GiB |
| gemma4:e2b-it-qat | `07ea59a474013479c8b6b802bef095c40e964a1d776ba02f264c0e30e1aede0c` | Passed, 27 samples | Passed, 36 samples | 102.832 tok/s | 1.55 GiB |
| gemma4:e4b-it-qat | `ee665637121887cf3befff38abbb1be4ee117c7db867d97a67e29049ecd7e15f` | Passed, 27 samples | Passed, 33 samples | 98.414 tok/s | 2.89 GiB |
| gemma4:12b-it-qat | `38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3` | Passed, 27 samples | Passed, 30 samples | 59.831 tok/s | 7.13 GiB |
| granite4.1:3b-q4_K_M | `6fd349357287c7ffc9e38189a93b48ea175d24fc566b38f09cfc564fb7f303eb` | Passed, 27 samples | Passed, 39 samples | 159.098 tok/s | 2.33 GiB |
| granite4.1:8b-q4_K_M | `444af1c4b2fedd6b54041aca558e7300b0b3d5c0468c44619126240323ba2852` | Passed, 27 samples | Passed, 33 samples | 84.157 tok/s | 5.48 GiB |
| phi4-mini:3.8b-q4_K_M | `78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753` | Passed, 27 samples | Passed, 39 samples | 151.625 tok/s | 2.88 GiB |
| llama3.2:3b-instruct-q4_K_M | `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72` | Passed, 27 samples | Passed, 39 samples | 177.486 tok/s | 2.37 GiB |
| ministral-3:3b-instruct-2512-q4_K_M | `f04aa1c738f64e13c625b82ae92504fc0260fa6723b509ed1ece0fa188179b1d` | Passed, 27 samples | Passed, 36 samples | 145.184 tok/s | 2.53 GiB |
| ministral-3:8b-instruct-2512-q4_K_M | `1922accd5827ebe6829e536369195db25eaf664528dc66206d646ea3bb386b71` | Passed, 27 samples | Passed, 30 samples | 78.614 tok/s | 5.25 GiB |
| ornith:9b | `a75697c145891910e312c95e4a9fc1ccb8653e5ef543b23b0403a4665b82fd91` | Passed, 27 samples | Passed, 33 samples | 79.421 tok/s | 4.97 GiB |
| lfm2.5:8b | `9cf756159fc2f3b9128c6a3f544ec90c5e9b8afdbb4179a57b8aea9de589cfb2` | Passed, 27 samples | Passed, 33 samples | 218.781 tok/s | 4.89 GiB |
| minicpm-v4.6:1b | `e95583acac773b45d95469c069db44808c87295f924183f4c942d52616b2d132` | Passed, 27 samples | Passed, 42 samples | 311.047 tok/s | 0.63 GiB |

Every core and soak result above was cross-checked against the campaign summaries,
the pinned model inventory, and the per-model result records. A passing synthetic
soak is reliability evidence for this profile; it is not a human quality score or a
coding-agent recommendation.

## Filtered graphics-board power summary

HWiNFO recorded 29,634 rows, including 20,920
rows covering the qualification soak. Across all soak rows, the GPU ASIC sensor
averaged 10.393 W. The 437
rows meeting the fixed active-sample rule averaged 85.114 W.
Observed GPU ASIC power ranged from 5.0 W to
220.0 W. Average GPU temperature was
36.83 C; the highest GPU temperature was
51.0 C and the highest hot-spot temperature
was 64.0 C.

These are aggregate GPU ASIC sensor readings, not per-model readings and not wall
power. CPU, memory, storage, cooling, display, and power-supply losses are excluded.
The source memory-usage column was physically impossible and was excluded. This
power evidence is therefore not eligible for an end-user electricity-cost estimate.

## Privacy and provenance

The private source set contained 429 files and
58,062,183 bytes. The sanitizer scanned every
file and produced this report through an allow list: only fixed public profile labels,
validated model IDs and digests, pass counts, and aggregate measurements could enter
the published result. Raw prompts, responses, local paths, network identities, host
names, user names, and device identifiers were not copied.

The raw telemetry file is not committed. Its provenance is retained only as:

- Size: 57,595,855 bytes
- SHA-256: `36607f7d608efbf6ab4efabf55abd6d0e6c6e6a3223356fa1ad0a16823ee7583`

The machine-readable summary is
[`config/alpha-2-amd-rx6800-windows-qualification-result.json`](https://github.com/hysel/haven-42/blob/main/config/alpha-2-amd-rx6800-windows-qualification-result.json).
