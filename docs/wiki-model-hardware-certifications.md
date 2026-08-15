# Model and Hardware Test Status

_Last reviewed: August 12, 2026._

This page shows which model and computer combinations Haven 42 has actually
tested. It records bounded tests, not a promise that every similar computer
will work. A result applies only to the operating system, AI engine, model, and
hardware profile named in its row.

Haven 42 does not save private lab addresses, account names, machine names,
keys, prompts, responses, or local paths in this tracker.

## Status labels

- **✅ Verified** — every bounded check described in the row passed on that
  exact setup.
- **🧪 Engineering evidence** — useful controlled tests passed, but the result
  does not establish a complete end-user or release-candidate route.
- **⚠️ Partial** — some checks passed and at least one required check is
  incomplete or failed.
- **❌ Did not pass** — the model or route failed a required gate and is not
  promoted.
- **⬜ Not tested** — no result should be inferred from a different model,
  operating system, or graphics card.

These are test-result labels. Roadmap labels describe milestone delivery and
use a different scale.

## How a model becomes a recommendation

Haven 42 uses a staged test path so one successful prompt or one powerful lab
computer cannot become a broad compatibility claim.

1. **Discovered** — an official local artifact exists and its exact tag,
   manifest, license, runtime requirements, size, and quantization are known.
2. **Task qualified** — that exact artifact passes three samples each for
   Chat, Writing, and Summarization, with clean unload evidence.
3. **Soak passed** — it completes its separate 30-minute reliability run.
4. **Hardware verified** — it passes on a named physical hardware class with
   measured CPU, RAM, accelerator memory, acceleration use, latency, and speed.
5. **OS verified** — setup, daily use, recovery, restart, cleanup, and uninstall
   pass on the named operating system and runtime combination.
6. **Recommended** — comparative task quality and reliability support a clear
   use case within the tested limits.
7. **Default candidate** — the evidence is strong enough to propose an
   automatic choice. It is still not a product default without explicit owner
   approval.

**Failed or needs retest** remains a visible result at any stage. A formatting
failure, provider-lifecycle evidence failure, unsupported artifact, or hardware
shortage is recorded separately so it is not misrepresented as the same kind
of failure.

## Hardware tiers still being built

| Test tier | What the evidence must use | Current purpose |
| --- | --- | --- |
| CPU-only | Real low-, medium-, and high-memory computers | Find a usable fallback and refusal floor. |
| 4 GiB graphics | The purchased GTX 1650 Super after it arrives | Validate only the best small candidates with safe overhead. No result exists yet. |
| 8 GiB graphics | The installed Radeon RX 5700 XT RDNA 1 profile | Validate small candidates and safe fallback behavior on separate Windows and Linux cells. Linux ROCm, Windows, and Vulkan results remain distinct. |
| 12 GiB graphics | The purchased RTX 3060 12 GB and current Intel Arc B580 | Validate the 8B-to-14B range on NVIDIA and Intel without relying on a larger card. The RTX 3060 has not arrived yet. |
| 16 GiB graphics | Quadro RTX 5000, Radeon RX 6800 non-XT, and Radeon RX 7800 XT | Compare NVIDIA Turing, AMD RDNA 2, and AMD RDNA 3. The RX 6800 has not arrived yet. |
| 24 GiB graphics | A physical 24 GiB consumer accelerator | Validate 24B-to-35B candidates and runtime overhead. |
| 32 GiB graphics | One physical Tesla V100 32 GB | Validate larger local candidates while clearly labeling the datacenter architecture. |
| 48 GiB or more | Two Tesla V100 32 GB devices in the high-memory lab | Qualify 70B and mixture-of-experts candidates without claiming single-card or consumer equivalence. |

An artificial memory limit is useful for diagnosis but does not certify a
physical memory tier. A measured model footprint is also not its supported
minimum; Haven 42 keeps headroom for context, runtime allocations, the desktop,
and failure recovery.

## Test coverage strategy

Every locally runnable candidate receives the same initial task gate. Every
passing candidate receives its own soak and at least one appropriate hardware
run. The number of models in two hardware campaigns does not need to match.
Each card tests the complete set of credible candidates admitted by its usable
accelerator memory, system memory, runtime support, storage headroom, and safe
execution policy. More capable hardware may therefore have a larger queue and
larger models.

A shared baseline is still run across vendors where possible. That baseline
answers whether the exact same model behaves differently on NVIDIA, AMD, and
Intel. Hardware-specific expansion queues answer a different question: what is
the best model this particular computer can run? Dashboards and reports label
these scopes separately; a campaign count is progress information, not a
quality score or certification ranking.

Operating-system coverage uses small, medium, large, and very-large anchor
models where the machine fits. It does not repeat every model on every
distribution or infer that one distribution proves another.

### How Haven 42 chooses the best model for a computer

Recommendations are made within an exact hardware and software profile, not
from parameter count alone. A candidate must first fit with recovery headroom
and use the intended accelerator without an undisclosed CPU fallback. Haven 42
then compares only candidates that passed the required gates for the requested
task.

The selection order is:

1. Reject an unverified artifact, incompatible runtime, unsafe memory fit, or
   missing accelerator evidence.
2. Match the requested task: Chat, Writing, Summarization, or another separately
   tested capability.
3. Prefer complete task success and reliability over model size.
4. Within equally reliable candidates, prefer measured task quality, then
   responsiveness, memory headroom, and energy efficiency.
5. Keep a smaller verified fallback for startup or resource-recovery failures.
6. Show untested combinations only as clearly labeled manual choices; they
   cannot become an automatic recommendation.

The best model is therefore the highest-quality **verified and responsive**
choice for the exact computer. It is not necessarily the largest model that
can be loaded. Any proposed automatic default remains a separate owner-approved
product decision.

### How Haven 42 chooses the AI engine

A model name alone is not enough. Haven 42 keeps a separate compatibility
route for each engine that can run the model. A route names the engine
(Ollama or llama.cpp), its minimum compatible version, the exact model
artifact, and the platform/backend package needed by the computer.

Before managed setup, Haven 42 must find an admitted route for the engine the
user selected. If it cannot, setup stops and explains which engine and version
are required. It does not silently fall back from llama.cpp to Ollama, from
Ollama to llama.cpp, or from a graphics backend to CPU. A successful test on
one engine does not certify the same model on the other engine.

The new candidate bindings cover Muse Glimmer and Nemotron 3.5 Lightning.
Muse Glimmer requires Ollama 0.32.8 or llama.cpp b10353 or newer. Haven 42's
first conservatively reviewed Nemotron llama.cpp route is b10375; this is a
Haven 42 test floor, not a claim that upstream first supported the model in
that build. The current managed candidates are Ollama 0.32.9 and llama.cpp
b10375. Ollama 0.32.9 now has narrow dual-V100 Nemotron qualification
evidence, and llama.cpp b10375 has narrow Intel Arc B580 Granite 4.1 8B soak
evidence. Those results do not complete native lifecycle or package admission.

WSL2 AMD needs a separate runtime pin. The 11-model b10088 HIP/DXG matrix
passed, while b10375 and b10380 detected the same Radeon RX 7800 XT but exited
before the first benchmark. A b10375 CPU-only control passed. For this exact
WSL candidate route, b10088 remains the last passing evidence; newer builds
must be requalified rather than assumed compatible.

The six models in the current automatic Qwen 3.5 ladder are explicitly bound
to the existing admitted Ollama 0.32.5 portable route. Alpha 2 presents that
engine and version before permission is requested and checks the same binding
again at approval and execution time. It also matches the platform installer's
component IDs, artifact names, sizes, checksums, sources, and versions against
that binding. A disagreement stops setup before permission is requested.
The same comparison runs before Haven 42 reopens a completed managed setup;
an old receipt alone is not enough to start a runtime after policy changes.
Those models do not yet have an admitted
llama.cpp route; choosing or adding a llama.cpp provider for them must remain
blocked until exact GGUF artifacts and compatible llama.cpp builds are recorded
and tested.

Catalog models beyond these recorded routes remain unavailable to the managed
resolver until their exact engine artifacts and versions are recorded and
tested.

The offline hardware-fit report generator applies that policy to completed,
sanitized soak evidence. It compares shared models across cards, reports every
hardware-specific expansion result, calculates measured accelerator-memory
headroom, requires explicit full-offload proof, and identifies the smallest
eligible fallback. It deliberately refuses to name a task winner until at
least two eligible models have sanitized task-quality review evidence. Raw
throughput and the number of tested models cannot substitute for quality.

```text
python scripts/generate-alpha2-hardware-model-fit-report.py --request hardware-fit-request.json --evidence-root . --output-json hardware-fit-report.json --output-markdown hardware-fit-report.md
```

The generator reads local files only. It does not contact a test machine,
download a model, run inference, change hardware state, or modify Haven 42's
automatic model selection.

### Current recommendation outlook

These are conservative engineering recommendations based on completed evidence
as of the review date. Rows marked **candidate** must finish the named work
before they can influence automatic selection.

| Hardware profile | Current recommendation or candidate | Intended role | Evidence boundary / next work |
| --- | --- | --- | --- |
| CPU-only Alpha 2 Linux profiles | Qwen 3.5 0.8B Q8 | Safe chat, writing, and summarization fallback | Verified only on the exact profiles listed below. |
| NVIDIA 16 GiB, Ubuntu 26.04 and Bazzite 44 | Qwen 3.5 4B Q4 | Current approved balanced default | Exact approved evidence exists; keep the 0.8B and 2B records as fallbacks. |
| NVIDIA high-memory lab | Qwen 3.5 27B Q4, Qwen 3.5 35B Q4, Qwen3-Next 80B-A3B Q4, and both tested Nemotron 3.5 Lightning quantizations are candidates | Larger-model quality comparison | The exact Nemotron Q4 and Q8 artifacts passed three task contracts and 30-minute soaks on dual V100s. Exact per-model GPU-board energy is now measured. Comparative human review, remaining capabilities, and exact multi-GPU distribution are still open. |
| AMD Radeon RX 7800 XT 16 GiB | Gemma 3 1B Q4 and Llama 3.2 3B Q4 are completed baseline candidates | Responsive local baseline | The 17-model campaign completed. An Ollama 0.32.9 retry reproduced summarization failures for Granite 4 7B and Ministral 3 3B/8B, so no final AMD recommendation is made. |
| Intel Arc B580 12 GiB | Granite 4.1 8B Q4 is a narrow Linux SYCL candidate | Cross-vendor baseline | The exact artifact passed 15 task samples, a 30-minute soak, full 41-layer offload, cleanup, and card-energy measurement. Other models still have load or task failures, so no final Intel default is proposed. |
| 4 GiB, 8 GiB, NVIDIA 12 GiB, and AMD RDNA 2 tiers | No recommendation yet | New physical tiers | Wait for the purchased or available cards and run their hardware-fit campaigns. |

The quality suite is being expanded beyond format compliance to cover factual
answers, short and long summaries, writing, long context, ambiguous requests,
attachments, multilingual prompts, refusal behavior, and name consistency.
Reliability coverage includes cold starts, multi-turn use, cancellation,
restart, unload and reload, interrupted downloads, low-resource behavior,
provider failure, sleep and wake where supported, system load, and exact
process cleanup. Close recommendation decisions require blind human review.

### How reliability tests are prepared

The reliability suite groups the lifecycle work into eight short campaigns:
three cold starts with multi-turn use; cancellation and cleanup; unload and
reload; runtime restart and provider-failure recovery; interrupted-download
recovery; bounded low-memory and low-disk recovery; sleep and wake; and
concurrent load with final cleanup.

Preparation is deliberately separate from execution. The planner downloads
nothing, runs no model, signals no process, applies no resource pressure, and
does not sleep or restart a computer. Every prepared action remains blocked
until a fresh execution approval confirms that no other campaign owns the
target hardware. Sleep additionally requires the operator to be present.

Low-resource tests do not fill a real disk or exhaust the host. They use a
quota-limited disposable directory and an operating-system memory boundary
such as a job, cgroup, or isolated VM. Process cleanup may address only the
Haven-owned process identifiers recorded for that exact run; wildcard process
termination is forbidden.

Prepare a plan from the example request:

```text
python scripts/plan-alpha2-model-reliability.py --request examples/fixtures/alpha-2-model-reliability-request.json --output reliability-plan.json
```

After an approved native executor produces sanitized evidence, the validator
requires the exact plan binding, current approval reference, minimum attempt
counts, accelerator use, unload evidence, listener closure, and exact process
cleanup. A missing cleanup proof prevents a passing result. This tooling does
not promote a model or change Haven 42's default selection.

## Power use and electricity estimates

Haven 42 will publish measured graphics-card energy for exact model and
hardware combinations. A model does not have one universal power figure: the
graphics card, quantization, task, context, runtime, driver, and operating
system all affect the result.

Each measurement uses a two-minute idle baseline followed by at least five minutes of
the same Chat, Writing, and Summarization workload. Vendor telemetry is sampled
at least every ten seconds and normally every second. The record includes:

- average and peak graphics-card power;
- measured and idle-adjusted watt-hours;
- output speed and output tokens per watt-hour;
- separate power and token-efficiency results for Chat, Writing, and Summarization;
- graphics utilization, memory, and temperature when the card exposes them;
- the exact model digest, runtime, driver, operating system, and graphics card.

NVIDIA telemetry is available through `nvidia-smi` on supported Windows and
Linux drivers. Intel measurements can use a supported `xpu-smi` source or the
card's energy counter. Windows AMD measurements can use an Adrenalin metrics
CSV that includes GPU board power; Linux AMD measurements can use `amd-smi`
when the exact card and driver expose it. The collector refuses to substitute
an unsupported tool silently.

These are **graphics-card or graphics-package readings**, not whole-computer
measurements. They do not include the CPU, RAM, storage, fans, power-supply
losses, displays, or other devices. A wall meter is required for a complete
computer measurement.

### Radeon RX 7800 XT result

The first synchronized AMD result is now recorded for Windows 11, one Radeon
RX 7800 XT 16 GiB, Ollama 0.32.5, and `qwen3.5:9b` Q4_K_M. The 30-minute
Chat, Writing, and Summarization soak passed 50 of 50 cells with full GPU
offload and averaged 65.93 generated tokens per second. Adrenalin's GPU board
power averaged 40.084 W across the full soak, reached a 261 W peak, and
recorded 20.142 Wh. After subtracting the 24.202 W idle baseline, the average
was 15.882 W and the measured energy was 7.981 Wh. See
[the sanitized evidence](Windows-AMD-RX7800XT-Power-Validation).

The low full-run average includes idle gaps and deliberate model unloads. It
is not a card TDP or a whole-computer measurement, and it must not be applied
to another model or graphics card. The controlled rerun met the 120-second
baseline floor and the machine-readable importer accepted it as exact-profile
GPU energy evidence. It still grants no automatic model, runtime, or cost
promotion.

To estimate graphics-card cost for a billing period:

`average watts / 1000 × hours used per day × days × electricity price per kWh`

For example, a measured 120 W average used two hours per day for 30 days at
$0.20 per kWh would be approximately $1.44 for the graphics card. This is an
example of the formula, not a Haven 42 model measurement.

The engineering calculator accepts a measured evidence file, the local rate,
and expected daily use:

```text
python scripts/calculate-model-energy-cost.py evidence.json --rate 0.20 --hours-per-day 2
```

Alpha 2 also provides the same plain-language estimate under **System →
Electricity estimate**. It starts with manual bill-rate entry. A person may
explicitly request an EIA or Eurostat average; Haven 42 shows the selected
country, source period, tax scope, and source currency and keeps the values in
the current browser session. The page never infers location, silently converts
currency, or changes model recommendations. For admitted Eurostat countries,
the currency field follows the country code the person explicitly enters. The
latest calculation also appears as a compact GPU-only summary in the left
navigation; selecting it returns to the full explanation and inputs.

### Electricity prices outside the United States

The calculator works with any country and any three-letter currency code. It
does not convert currencies. The most accurate simple option is to copy the
price per kWh from your own electricity bill and keep the result in that
bill's currency.

Haven 42 does not detect a country from an IP address, operating-system
locale, or device location. If an official average is used, the person using
the app explicitly chooses the country or region. The estimate shows the
country, currency, effective period, tax treatment, and source so an old or
inexact average cannot look like a current utility tariff.

The initial official-source registry includes:

- the U.S. Energy Information Administration's monthly national and state
  residential averages;
- Eurostat's twice-yearly household electricity-price dataset `nrg_pc_204`
  for the countries it reports, including an explicit consumption band and
  tax scope;
- OpenEI's U.S. Utility Rate Database as an advanced opt-in source for
  tariffs with tiers or time-of-use periods.

EIA's residential-price route is state-level and does not publish a ZIP-code
price. OpenEI can locate candidate utility tariffs from an address, but a
tariff may contain tiers, time-of-use schedules, and fixed charges. Haven 42
therefore does not turn either source into a misleading single ZIP-code rate.
ZIP/tariff support remains an advanced future adapter that must preserve the
selected tariff structure.

Official averages are fallbacks, not bill predictions. Utility plans may add
fixed charges, tiers, taxes, subsidies, demand charges, or different prices
at different times. Countries without an admitted official adapter still
receive the complete calculator through manual bill-rate entry; they are not
silently assigned a U.S. rate.

An updater-generated rate profile is local JSON with no address or inferred
location. For example:

```json
{
  "schemaVersion": 1,
  "kind": "haven42-electricity-rate-profile",
  "sourceKind": "manual-bill-rate",
  "sourceId": "manual-user-entry",
  "countryCode": "JP",
  "subdivisionCode": null,
  "currency": "JPY",
  "currencyDecimalPlaces": 0,
  "ratePerKwh": 31,
  "effectivePeriod": "2026-08",
  "taxScope": "user-entered-bill-rate",
  "sourceUrl": null,
  "estimateOnly": true,
  "locationWasInferred": false
}
```

Use it without retyping the rate:

```text
python scripts/calculate-model-energy-cost.py evidence.json --rate-profile electricity-rate.local.json --hours-per-day 2
```

The Alpha 2 updater fetches only after the user explicitly chooses a source,
country, currency, and output file. It never infers location, never stores an
API key, and refuses to replace an existing snapshot unless `--replace` is
provided. EIA uses an API key from the `EIA_API_KEY` environment variable:

```text
python scripts/update-electricity-rate-snapshot.py --source eia --country US --subdivision US-NY --output electricity-rate.local.json
```

Eurostat requires an explicit source currency and defaults to the 2,500–4,999
kWh household band with all taxes and levies included:

```text
python scripts/update-electricity-rate-snapshot.py --source eurostat --country DE --currency EUR --output electricity-rate.local.json
```

These commands create a versioned local snapshot. They do not run
automatically and do not change Haven 42's model or runtime selection.

Source documentation: [EIA Open Data](https://www.eia.gov/opendata/documentation.php),
[Eurostat household electricity prices](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_204/default/table),
and [OpenEI Utility Rates](https://apps.openei.org/services/doc/rest/util_rates/?version=4).

The engineering collector also has a resumable batch runner. It skips existing
evidence records, requires an exact digest for every model, never downloads or
deletes a model, and cannot change Haven 42's automatic model selection.

Externally recorded NVIDIA, Intel, and AMD Adrenalin CSV logs use a separate
importer. The log must be paired with a small manifest that names the exact
model digest, runtime, driver, graphics card, and operating system; supplies
timezone-aware idle and active windows; identifies every Chat, Writing, and
Summarization interval; and supplies output-token counts. If a vendor CSV uses
local timestamps without an offset, the manifest must provide the explicit
`telemetryUtcOffset`; the importer never guesses it. Missing timestamps,
insufficient samples, an identity mismatch, or overlapping windows stop the
import. Raw prompts, responses, provider addresses, and machine names are not
copied into the result.

```text
python scripts/import-alpha2-model-energy-log.py --vendor amd --input metrics.csv --manifest windows.json --output evidence.json
```

Start from
`examples/fixtures/alpha-2-model-energy-import-manifest.json`; replace every
example identity, timestamp, digest, and token count with the measured values.

A separate report generator applies the ordered labels shown above. It rejects
skipped gates, requires evidence references for every passed gate, and requires
an explicit owner-approval reference for `Default candidate`. It produces JSON
and a plain Markdown table but never updates the application's automatic model
selection.

```text
python scripts/generate-alpha2-model-certification-report.py --input certification.json --output-json report.json --output-markdown report.md
```

The report input shape is illustrated by
`examples/fixtures/alpha-2-model-certification-report-input.json`.

Public exact-profile power evidence now exists for the dual-V100 Nemotron
measurements, the Intel Arc B580 Granite measurement, and the admitted RX 7800
XT Qwen 3.5 9B measurement. See the plain-language
[power and electricity evidence page](Model-Power-And-Electricity-Evidence) for the
current numbers and comparison limits.

The current expanded lab campaign covers 41 exact artifacts. Twenty-one passed
the initial Chat, Writing, and Summarization gate and are proceeding through
individual 30-minute soaks; twenty failed at least one gate and remain recorded
for diagnosis or targeted retest. These results do not alter the automatic
model ladder.

## Alpha 2 computer coverage

| Computer profile | Status | Notes |
| --- | --- | --- |
| Windows 11 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Managed Ollama 0.32.5 and Qwen 3.5 0.8B passed chat, writing, summarization, unload, GPU-use, package-lifecycle, and graceful-shutdown checks. The distinct Alpha 2 package and final beginner workflow remain open. |
| Ubuntu 26.04 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Linux package parity, Qwen 3.5 CPU/CUDA task checks, driver checks, and GPU-use checks passed. The promotion-candidate desktop flow remains open. |
| Bazzite 44 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Linux package parity, Qwen 3.5 CPU/CUDA task checks, driver checks, and GPU-use checks passed. The promotion-candidate desktop flow remains open. |
| Ubuntu 24.04 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Debian 13 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Linux Mint 22.3 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Pop!_OS 24.04 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | The corrected identity path passed the full source-candidate managed lifecycle. A rebuilt package and complete desktop flow remain open. |
| Fedora 44 with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | The completion-receipt ordering correction passed the full source-candidate managed lifecycle. A rebuilt package and complete desktop flow remain open. |
| CachyOS with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Arch Linux with NVIDIA Quadro RTX 5000, 16 GB | 🧪 Engineering evidence | Package parity, Qwen 3.5 0.8B CPU/CUDA task checks, driver checks, and GPU-use checks passed. The complete desktop flow remains open. |
| Windows 11 with AMD Radeon RX 7800 XT, 16 GB | 🧪 Engineering evidence | Earlier Alpha Ollama/ROCm and llama.cpp/HIP checks passed. The Alpha 2 hardware-fit campaign completed, but targeted Ollama 0.32.9 summary failures keep release-candidate and recommendation gates open. |
| Ubuntu Linux with Intel Arc B580, 12 GB | ⚠️ Partial | Granite 4.1 8B passed an exact llama.cpp b10375 SYCL 30-minute soak with full offload, cleanup, and card-energy evidence. Other model routes and the complete Alpha 2 package flow remain open. |
| Linux with AMD graphics | ⬜ Not tested | No complete native Alpha 2 release-candidate cell exists. |
| Linux with Intel graphics | ⬜ Not tested | No complete native Alpha 2 release-candidate cell exists. |
| macOS on Apple silicon | 🧪 Engineering evidence | Earlier local-model workflow checks passed. No Alpha 2 package certification exists. |

All nine Linux distributions used the same unsigned candidate archive for the
package-parity checks. Those checks covered archive integrity, relocation,
read-only startup, repeated start and stop, abrupt-exit recovery, occupied
ports, hostile environment handling, and protected-resource integrity. They
did not certify the complete guided setup, accessibility, attachments,
uninstall, or tester-reporting experience.

## Approved automatic choices

These records use the managed Ollama 0.32.5 runtime. The owner approved the
exact records on August 11, 2026. Haven 42 still matches the operating system,
backend, runtime, memory, artifact digest (an exact-file checksum), and
requested tasks before making an
automatic choice. A nearby but untested configuration is not equivalent.

| Model | Tested profile | Tasks | Status | Notes |
| --- | --- | --- | --- | --- |
| Qwen 3.5 0.8B, Q8_0 | CPU on all nine Linux profiles | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for the exact CPU-tested profiles. |
| Qwen 3.5 0.8B, Q8_0 | CUDA on all nine Linux NVIDIA profiles | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved as the tested CUDA fallback for these profiles. |
| Qwen 3.5 0.8B, Q8_0 | Windows NVIDIA baseline | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved only for the exact tested Windows baseline. |
| Qwen 3.5 2B, Q8_0 | Ubuntu 26.04 with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for this exact CUDA profile. |
| Qwen 3.5 2B, Q8_0 | Bazzite 44 with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for this exact CUDA profile. |
| Qwen 3.5 4B, Q4_K_M | Ubuntu 26.04 with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for this exact CUDA profile. |
| Qwen 3.5 4B, Q4_K_M | Bazzite 44 with 16 GB NVIDIA profile | Chat, writing, summarization, unload, and execution-device checks | ✅ Verified | Approved for this exact CUDA profile. |

Haven 42 automatically chooses Qwen 3.5 0.8B Q8 on the exact CPU-tested Linux
profiles. On the exact Ubuntu 26.04 and Bazzite 44 CUDA profiles with 16 GiB
usable GPU memory, it chooses Qwen 3.5 4B Q4. The tested 0.8B and 2B CUDA
records remain fallbacks if the larger model does not pass the free-space
check.
Other Linux CUDA profiles remain evidence-pending even when comparison tests
succeeded.

The evidence includes measured system-memory and usable-GPU-memory floors.
Haven 42 must refuse automatic selection below the tested floor, even if a
model might technically start.

## Cross-family qualification results

Qualification uses three fixed samples for chat, writing, and summarization,
followed by a 30-minute soak test—a continuous run that looks for delayed
failures—only after the task checks pass. `Q4_K_M` and `Q8_0` are quantization
labels for the exact prepared model size; a result for one does not prove the
other. CUDA rows require a compatible NVIDIA GPU and do not apply to Intel Arc
or AMD graphics.
Every sample must unload cleanly. Raw prompts and responses are not retained.

| Model and profile | Status | Notes |
| --- | --- | --- |
| Gemma 3 1B, Q4_K_M on CPU | ❌ Did not pass | Failed the task gate; no soak ran. |
| Gemma 3 1B, Q4_K_M on 16 GB CUDA | ❌ Did not pass | Failed the task gate; no soak ran. |
| Gemma 3 4B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 3 4B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 E2B, QAT on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 E2B, QAT on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 E4B, QAT on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 E4B, QAT on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Gemma 4 12B, QAT on CPU | ⬜ Not tested | This model was not included in the CPU profile. |
| Gemma 4 12B, QAT on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for CUDA use. |
| Granite 4.1 3B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Granite 4.1 3B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Granite 4.1 8B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Granite 4.1 8B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Phi 4 Mini 3.8B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Phi 4 Mini 3.8B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Llama 3.2 3B, Q4_K_M on CPU | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Llama 3.2 3B, Q4_K_M on 16 GB CUDA | 🧪 Engineering evidence | Passed task checks and soak; awaits owner review for any product use. |
| Ministral 3 3B, Q4_K_M on CPU | ❌ Did not pass | Failed writing or summarization; no soak ran. |
| Ministral 3 3B, Q4_K_M on 16 GB CUDA | ❌ Did not pass | Failed writing or summarization; no soak ran. |
| Ministral 3 8B, Q4_K_M on CPU | ❌ Did not pass | Failed writing or summarization; no soak ran. |
| Ministral 3 8B, Q4_K_M on 16 GB CUDA | ❌ Did not pass | Failed writing or summarization; no soak ran. |
| Qwen 3.6 27B, Q4_K_M on CPU | ⬜ Not tested | This model was not tested on the CPU profile. |
| Qwen 3.6 27B, Q4_K_M on Windows with at least 31 GB system memory and 16 GB NVIDIA CUDA memory | 🧪 Engineering evidence | Passed task checks and a 30-minute soak on that exact review profile. This result does not apply to Intel Arc or AMD graphics and does not add the model to automatic selection. |
| Granite 4.1 8B, Q4_K_M on Ubuntu Linux with Intel Arc B580 12 GB | 🧪 Engineering evidence | Passed 15 task samples, a 30-minute llama.cpp b10375 SYCL soak, full 41-layer offload, cleanup, and card-energy measurement. This does not establish Windows support or automatic selection. |
| Nemotron 3.5 Lightning 30B-A3B, Q4_K_M on Ubuntu 24.04 with dual Tesla V100 32 GB | 🧪 Engineering evidence | Ollama 0.32.9 passed 81 samples across nine cycles and a 30-minute soak with reported GPU residency. A separate five-minute workload averaged 155.005 W across both GPU boards and produced 1,524.219 output tokens/Wh. Remaining capability, context, recovery, and product gates are open. |
| Nemotron 3.5 Lightning 30B-A3B, Q8_0 on Ubuntu 24.04 with dual Tesla V100 32 GB | 🧪 Engineering evidence | Ollama 0.32.9 passed 72 samples across eight cycles and a 30-minute soak with reported GPU residency. A separate five-minute workload averaged 141.373 W across both GPU boards and produced 1,274.383 output tokens/Wh. Remaining capability, context, recovery, and product gates are open. |

The same Ollama 0.32.9 NVIDIA profile also retried five exact artifacts that
had failed the task-contract gate on 0.32.8. Gemma 3 1B, Phi 4 Mini 3.8B,
Ministral 3 3B and 8B, and Muse Glimmer 30B all retained the
`soak-task-contract-failed` result. This negative result is kept deliberately:
a runtime update must not turn an unqualified model into a recommendation
without new passing evidence.

Engineering evidence is narrower than availability by default. None of these
qualification results changes the automatic model ladder or downloads a model
for an end user.

## Models queued for testing

These models are planned, not verified. Adding a model here does not download
it, start a test machine, or make it an automatic Haven 42 choice.

To suggest another model, use the
[model test request form](https://github.com/hysel/haven-42/issues/new?template=model-test-request.yml).
The form accepts a simple model name; technical version and hardware details
are optional. Requests are public, so do not include private prompts, files,
addresses, usernames, paths, logs, or credentials.

| Model | Planned test | What must happen first | Status |
| --- | --- | --- | --- |
| [**Muse Glimmer 30B, Q4_K_M**](https://ollama.com/library/muse-glimmer) | Chat, writing, summarization, image understanding, tool use, failure recovery, and a 30-minute soak on a high-memory NVIDIA computer | Use an exact compatible Ollama version (at least 0.32.8), verify the pinned artifact again, meet the conservative 32 GiB system-memory and 24 GiB usable-GPU-memory test floor, and receive an explicit start prompt | ⬜ Not tested |
| [**Muse Glimmer 30B, MLX NVFP4-DFlash**](https://ollama.com/library/muse-glimmer:30b-mlx) | The same capability and soak checks on Apple silicon | **Owner-deferred until suitable Apple Silicon hardware is available.** After that, use an exact compatible Ollama version (at least 0.32.7), verify the pinned artifact again, meet the conservative 48 GiB unified-memory test floor, and receive an explicit start prompt | ⬜ Not tested |
| [**NVIDIA Nemotron 3.5 Lightning 30B-A3B, Q4_K_M**](https://ollama.com/library/nemotron-3.5-lightning:30b-a3b-q4_K_M) | Tool use, thinking-mode behavior, failure recovery, and bounded-context checks | Keep the exact Ollama 0.32.9 and manifest binding, prove the remaining capabilities and exact multi-GPU distribution, and complete human review | 🧪 Chat, writing, summarization, GPU residency, a 30-minute soak, and exact GPU-board energy passed; 81 samples across nine cycles at 62.067 tokens/s |
| [**NVIDIA Nemotron 3.5 Lightning 30B-A3B, Q8_0**](https://ollama.com/library/nemotron-3.5-lightning:30b-a3b-q8_0) | The same remaining checks, plus a quality, speed, memory, and energy comparison with Q4_K_M | Keep the exact Ollama 0.32.9 and manifest binding, prove the remaining capabilities and exact multi-GPU distribution, and complete human review | 🧪 Chat, writing, summarization, GPU residency, and a 30-minute soak passed; 72 samples across eight cycles at 47.574 tokens/s |

The memory figures above are fail-closed admission floors for Haven 42's first
test. They are not claims about the model's absolute minimum requirements.
Nemotron's published one-million-token GGUF context is not treated as tested;
the first plan is deliberately bounded to 8K and 32K context checks. Its 65.9
GB BF16 artifact is outside the current full-offload envelope. The 22.7 GB,
34.0 GB, and 65.8 GB MLX variants are recorded but owner-deferred until suitable
Apple Silicon hardware is available. Muse Glimmer and Nemotron will remain
outside the automatic model ladder unless separate evidence and owner approval
support a later product decision.

## Controlled comparison results

These models passed chat, writing, summarization, and unload checks on a
controlled external Ollama 0.32.6 provider. They compare model behavior; they
do not certify an end-user hardware profile.

| Model | Status | Notes |
| --- | --- | --- |
| Qwen 3.5 9B | 🧪 Engineering evidence | Controlled comparison only. |
| Gemma 3 12B | 🧪 Engineering evidence | Controlled comparison only. |
| Granite 4 7B | 🧪 Engineering evidence | Controlled comparison only. |
| Mistral Small 3.2 24B | 🧪 Engineering evidence | Controlled comparison only. |

## Open certification work

- Build and natively test the separated Windows Alpha 2 archive without
  changing the published Alpha 1 package.
- Complete the beginner guided-setup and daily-use sequence on Windows 11
  NVIDIA, Ubuntu 26.04 NVIDIA, and Bazzite NVIDIA.
- Build a new Linux candidate containing the Pop!_OS identity-path fix and
  repeat its native package/readiness sequence.
- Complete CPU-only desktop sequences on the remaining Linux distributions.
- Run native Alpha 2 AMD on Linux and finish the complete package flow on the
  partially validated Intel Linux route.
- Requalify a newer llama.cpp HIP/DXG build before replacing the passing b10088
  WSL2 AMD candidate pin.
- Test constrained-memory and mixed-GPU computers before assigning labels.
- Test Qwen 3.6 35B only on a computer with at least 48 GB system memory.
- Admit Qwen 3.7 or 3.8 only after an official local artifact is verified.

## Detailed evidence

The canonical engineering records are:

- [[Alpha 2 Linux Long-Term Validation|Eng-Alpha-2-Linux-Long-Term-Validation]]
- [[Tested Hardware and AI Engines|Tested-Hardware-And-AI-Engines]]
- [[Evidence Dashboard|Eng-Evidence-Dashboard]]

If a result looks wrong or incomplete, open a GitHub issue or email
`haven42localai@gmail.com`. Name the operating system, graphics card, runtime
version, model, and row you are asking about. Do not include keys, passwords,
private addresses, prompts, or files.
