# Alpha 2 GPU rotation and soak-test plan

_Prepared: August 12, 2026. Updated: August 15, 2026._

This plan covers the physical graphics cards currently available or purchased
for Haven 42 testing. It separates hardware installation, runtime validation,
model qualification, reliability soaks, power measurement, and product
promotion so that success in one area is not mistaken for success everywhere.

The plan deliberately contains no lab addresses, hostnames, account names,
keys, or other private infrastructure details. It does not authorize a model
download, hardware change, driver change, VM change, or soak run. Each live
phase starts only after the owner approves that phase and confirms the required
hardware is ready.

The owner approved the focused Quadro RTX 5000 qualification described in
Phase 0 on August 12, 2026. That approval permits model downloads and changing
the pinned Ollama and llama.cpp versions inside the designated target VM for
this campaign. It does not authorize a Proxmox configuration change, GPU
remapping, a change to Haven 42's automatic defaults, or changes to another VM.

## What this campaign should prove

For each exact card, operating system, driver, runtime, model artifact, and
quantization tested, collect enough evidence to answer:

- Did Haven 42 identify the hardware and choose only a compatible route?
- Did the intended GPU actually perform inference, with no silent CPU fallback?
- Did Chat, Writing, and Summarization pass their bounded task checks?
- Did the exact model remain stable for its complete soak period?
- Did cancellation, unload, restart, cleanup, and application shutdown work?
- How much GPU or whole-system energy did the same controlled workload use?
- Is the result strong enough for engineering evidence, hardware verification,
  a recommendation proposal, or only a documented failure?

No test in this plan changes an automatic model default. A default or selection
ladder change remains a separate owner-approved product decision.

## Hardware in scope

| Hardware class | Graphics card | Memory | Location during testing | Initial status |
| --- | --- | ---: | --- | --- |
| NVIDIA constrained | GeForce GTX 1650 Super | 4 GiB | Proxmox rotation | Purchased; not yet tested |
| NVIDIA mainstream | GeForce RTX 3060 | 12 GiB | Separate physical dual-boot computer | Windows and Ubuntu 26.04 exact-profile engineering campaigns complete; packaged lifecycle and automatic-selection gates remain open |
| NVIDIA workstation | Quadro RTX 5000 | 16 GiB | Proxmox baseline | Existing evidence |
| NVIDIA datacenter | Tesla V100 | 32 GiB each | Proxmox baseline, two cards | Existing evidence |
| AMD RDNA 1 | Radeon RX 5700 XT | 8 GiB | Separate physical dual-boot computer | Ubuntu Vulkan exact-profile engineering evidence complete; package, Windows, and final-profile memory gates remain open |
| AMD RDNA 2 | Radeon RX 6800, non-XT | 16 GiB | Proxmox rotation | Purchased; not yet tested |
| AMD RDNA 3 | Radeon RX 7800 XT | 16 GiB | This Windows computer | Existing bounded evidence; new soak required |
| Intel | Arc B580 | 12 GiB | Separate physical dual-boot computer | Campaign already in progress |

The RX 5700 XT is the 8 GiB RDNA 1 lane. The Ubuntu 26.04 Ollama 0.32.13
Vulkan/RADV campaign now has bounded exact-profile evidence, including positive
GPU residency, safe oversized-candidate refusal, current-boot stability, and
one board-power measurement. Windows and ROCm remain separate test cells and
inherit no Vulkan result. The final-profile full-memory and complete packaged
lifecycle gates also remain open.

## Rules shared by every phase

1. Record the exact card identity, PCI ID, usable memory, firmware where
   exposed, driver, operating system, runtime, model tag, manifest digest,
   quantization, and test-harness revision before testing.
2. Verify current backups and a recovery path before any physical rotation.
3. Stop every VM or container that owns a GPU before changing assignment or
   hardware. The protected two-V100 service remains stopped whenever its V100s
   are absent.
4. Bind each passed-through card to its own stable, accurately named Proxmox
   resource mapping. Never repoint the existing RTX 5000 mapping to another
   model of card.
5. Start one GPU workload at a time. Establish an uncontended baseline before
   any concurrent test.
6. Fail closed if the requested accelerator is missing, the wrong GPU is used,
   GPU residency cannot be demonstrated, or the runtime falls back to CPU.
7. Run the same deterministic Chat, Writing, and Summarization prompts without
   retaining prompt or response content. Record only sanitized metrics and
   pass/fail evidence.
8. A candidate must pass its task gate before receiving a soak. The normal
   reliability soak is 30 minutes per exact artifact. Longer overnight testing
   is a separate endurance phase, not a substitute for the bounded soak.
9. Include cold start, repeated inference, cancellation, unload/reload,
   application restart, clean shutdown, and post-run process/port cleanup.
10. Measure an idle baseline and the same active workload. Label vendor GPU
    telemetry separately from whole-computer wall measurements.
    Every physical card model in the inventory requires at least one reference
    measurement. Measure single-card and multi-card configurations separately;
    combined telemetry cannot silently substitute for an individual-card row.
11. Keep raw evidence outside tracked source until it is sanitized. Public
    records must not contain machine identities, addresses, accounts, keys,
    prompts, responses, or local paths.
12. Stop for temperature, power, PCIe, filesystem, driver, VM, or host errors.
    Do not continue a soak merely to obtain a complete duration.

## Model selection for each memory tier

Use the exact, digest-pinned candidates already admitted by the Alpha 2 model
inventory. Do not use mutable `latest` tags. Each card receives:

- a small anchor that should fit comfortably;
- a middle anchor appropriate to that physical memory tier;
- the largest candidate with measured runtime and context headroom;
- representatives from every admitted model family that fit the tier; and
- an intentional oversized case that must be refused or use an explicitly
  approved partial-offload route.

The complete candidate list does not need to be repeated on every operating
system. First qualify every eligible artifact on one suitable reference
machine. Then use small, middle, and boundary anchors to establish hardware and
operating-system coverage. Failed candidates remain visible and are not soaked
unless a later, explicitly approved retest addresses the failure.

## Phase 0: preserve and close the current baseline

Finish and sanitize the current RTX 5000, V100, Intel, and model-campaign
evidence before opening the chassis.

### Proxmox slot map

```text
Top / rear I/O

PCIE7  Quadro RTX 5000 16 GiB
PCIE6  empty
PCIE5  empty
PCIE4  Tesla V100 B 32 GiB
PCIE3  empty
PCIE2  shared resources; do not use for this campaign
PCIE1  Tesla V100 A 32 GiB

Bottom / front of chassis
```

### Quadro RTX 5000 16 GiB qualification

Use one representative Ubuntu target for the full qualification and one short
Windows package smoke check. Do not repeat the complete model campaign on every
Linux distribution: the existing operating-system matrix already covers
driver discovery, CUDA use, and the bounded Chat, Writing, and Summarization
path on this exact card.

The focused campaign must:

1. Pin and record the exact Ollama version, llama.cpp build and commit, NVIDIA
   driver, model artifact digests, quantizations, context, and concurrency.
2. Test every admitted model-family representative that fits the single 16 GiB
   card with measured runtime headroom, plus one oversized fail-closed case.
3. Run the deterministic task gates before each 30-minute soak.
4. Prove CUDA residency on the Quadro RTX 5000 and reject silent CPU fallback
   or accidental use of another NVIDIA device.
5. Record generation speed, peak GPU memory, idle and active GPU power,
   temperature, cancellation, unload/reload, restart, and cleanup.
6. Exercise Ollama 0.32.9 or a later explicitly pinned compatible release and
   run the prepared llama.cpp `b10375` regression cell. Runtime changes remain
   isolated to the designated VM and must be reported per model.
7. Finish with a short Windows Alpha 2 package and default-selection smoke test
   using the already configured Windows target; this is not another full soak.

This result establishes a representative NVIDIA Turing 16 GiB tier. It does
not inherit the dual-V100 64 GiB capacity result and does not promote a model or
runtime to an automatic default without a separate owner decision.

### Exit gate

- Existing evidence is checkpointed and reports are sanitized.
- The Quadro RTX 5000 16 GiB Ollama and llama.cpp qualification is complete,
  or every incomplete cell has a specific recorded blocker.
- Backups required for recovery have been verified.
- Every current card, cable, carrier, and original slot is labelled.
- The protected V100 service is stopped before physical removal.

## Phase 1: local RX 7800 XT on this Windows computer

Run the RX 7800 XT soak locally. This avoids virtualization and keeps the exact
physical Windows route that an end user is likely to use.

### Hardware map

```text
This Windows computer

Primary graphics slot  Radeon RX 7800 XT 16 GiB
Other test GPUs         none
Display/desktop load    recorded as part of the profile
```

The readiness audit recorded Windows 11 Pro, an AMD Ryzen 9 5900X, an RX 7800
XT, and AMD display driver `32.0.31035.1003`. Recheck these values at execution
time because drivers and Windows builds can change.

### Tooling prerequisite

The current `alpha2-linux-soak.py` runner admits only CPU and CUDA. Before this
phase runs, provide a tested Windows AMD soak path that:

- accepts only a reviewed `rocm` or `vulkan` backend;
- proves the requested GPU was used and records usable VRAM;
- rejects missing telemetry instead of silently reporting a GPU pass;
- binds every model to its expected manifest digest; and
- produces the same content-free evidence shape as the existing soak.

Use the exact managed Ollama/ROCm route and the already validated llama.cpp HIP
route as separate cells. Vulkan, if tested, remains a distinct result and must
not inherit HIP or ROCm status.

### Test order

1. Re-run system readiness and exact driver/runtime inventory.
2. Run the Alpha 2 setup and lifecycle smoke checks.
3. Run the small, middle, and largest safe 16 GiB anchors.
4. Run eligible admitted families and individual 30-minute soaks.
5. Run cancellation, unload/reload, restart, and cleanup checks.
6. Repeat the fixed energy workload. If supported AMD telemetry is unavailable
   on Windows, record that limitation and use a wall meter for whole-system
   energy rather than inventing GPU-only data.
7. Run one owner-approved overnight endurance test only after the bounded
   results pass.

### Exit gate

The result names the exact backend used, proves GPU execution, distinguishes
Ollama from llama.cpp, and does not generalize to another RDNA generation.

## Phase 2: mixed consumer cards on the Proxmox host

Remove both V100s and the RTX 5000. Install the purchased constrained NVIDIA,
mainstream NVIDIA, and RDNA 2 cards in the same three widely spaced slots.

### Proxmox slot map

```text
Top / rear I/O

PCIE7  GeForce GTX 1650 Super 4 GiB
PCIE6  empty for airflow
PCIE5  empty
PCIE4  GeForce RTX 3060 12 GiB
PCIE3  empty for airflow
PCIE2  shared resources; do not use for this campaign
PCIE1  Radeon RX 6800 non-XT 16 GiB

Bottom / front of chassis
```

### Power and assignment map

| Card | Expected auxiliary power | Test owner |
| --- | --- | --- |
| GTX 1650 Super | Verify the exact HP board before installation | One dedicated VM |
| RTX 3060 | Usually one 8-pin; verify the exact board | One dedicated VM |
| RX 6800 | Two 8-pin | One dedicated VM |

Use only the original, exact-model-compatible Corsair modular cables, with one
dedicated cable per GPU socket and no splitters. The three-card nominal board
power is about 520 W, but wall power and temperature must still be watched.

### Test order

1. Boot the host without starting GPU VMs. Inventory each PCI address, IOMMU
   group, power connector, and idle temperature.
2. Create new mappings named for the real card models.
3. Test each GPU alone: driver, runtime, GPU residency, task gate, bounded soak,
   lifecycle, and energy workload.
4. Keep the other two GPU VMs stopped while each uncontended baseline runs.
5. After all three individual routes pass, run one concurrent stability soak
   with one VM per GPU. This proves coexistence and host stability; it does not
   replace the uncontended performance results.
6. If power limits are used for the concurrent soak, record their exact values
   and do not compare capped results with stock-power results as equivalent.

### Tier emphasis

- **4 GiB GTX 1650 Super:** small models and safe refusal behavior; do not force
  a model that leaves inadequate context/runtime headroom.
- **12 GiB RTX 3060:** small and middle models plus the largest safe boundary
  candidate; compare with the 12 GiB Intel result without merging vendors.
- **16 GiB RX 6800:** RDNA 2 compatibility and 16 GiB model anchors; compare
  with RX 7800 XT results only as separate RDNA-generation evidence.

### Exit gate

Every card has an individual result, the concurrent run has no host or PCIe
errors, and no result depends on an unrecorded CPU fallback or power cap.

## Phase 3: RX 5700 XT native Windows and Linux qualification

Use the separate physical dual-boot computer where the RX 5700 XT is installed.
This phase does not require a Proxmox GPU rotation. Run Windows and Linux
sequentially against the same physical card so operating-system and backend
results remain comparable without pretending that one route proves another.

### Physical map

```text
Separate dual-boot computer

Primary graphics slot  Radeon RX 5700 XT 8 GiB
Operating systems      Windows and Linux, one at a time
Other test GPUs         none active in this test cell
```

### Test boundary

- Use the machine-readable plan in
  `config/alpha-2-rx5700xt-certification-plan.json`. It pins the runtime cells,
  candidate tiers, headroom rule, accelerator proof, and evidence outputs. A
  prepared plan is not authorization to download artifacts or start the soak.
- Pin the exact AMD driver, operating system, runtime, backend, and model
  artifact independently for Windows and Linux.
- Use Vulkan as the primary route. Current Ollama ROCm support tables do not
  list the RX 5700 XT on Linux or Windows, while Ollama documents Vulkan as an
  additional AMD route on both systems.
- Keep any ROCm/HIP attempt explicitly experimental. Test Windows and Linux,
  Ollama and llama.cpp, and Vulkan and ROCm as distinct cells; prove that the
  RX 5700 XT, not the CPU, executes each workload.
- Run only model sizes that leave measured headroom inside 8 GiB.
- Test clear refusal and recovery for oversized candidates.
- Record driver stability, unload/reload behavior, power telemetry availability,
  and clean shutdown on both operating systems.

### Admission order

1. Prove stability with the final firmware settings, DIMMs, and memory profile.
   A freeze, reset, machine-check event, EDAC error, or AMD GPU reset makes the
   cell inconclusive rather than a model failure.
2. Use the reviewed AMD Vulkan identity now admitted by the bounded
   qualification runners. The runner requires positive RX 5700 XT residency
   and rejects CPU fallback; ROCm/HIP remains a separate experimental route.
3. Start with the pinned Ubuntu Ollama Vulkan cell. Require the RX 5700 XT
   device identity, VRAM residency, and requested layer-offload proof; reject
   CPU fallback.
4. Run the small-to-medium model ladder. A model must pass three task samples
   before its 30-minute soak.
5. Admit boundary models only when at least 2 GiB and 25% of physical VRAM
   remain after context allocation. Test oversized candidates as refusal paths,
   without downloading or executing them automatically.
6. Exercise cancellation, unload/reload, runtime restart, and repeat-request
   recovery before collecting synchronized power evidence.
7. Repeat the Windows Vulkan route independently. ROCm/HIP experiments remain
   separate and cannot promote the card into a supported ROCm class. Do not
   inherit a Linux result, even on the same card.

### Planned model tiers

| Tier | Purpose | Exact candidate IDs |
| --- | --- | --- |
| Expected fit | Correctness and useful 8 GiB recommendations | `qwen35-08b-q8`, `gemma3-1b-q4`, `llama32-3b-q4`, `granite41-3b-q4`, `qwen35-2b-q8`, `phi4-mini-38b-q4`, `ministral3-3b-q4`, `gemma3-4b-q4`, `gemma4-e2b-qat`, `qwen35-4b-q4` |
| Measured boundary | Continue only if the headroom gate passes | `gemma4-e4b-qat`, `granite41-8b-q4`, `ministral3-8b-q4` |
| Oversized refusal | Prove a novice is stopped before unsafe download or execution | `qwen35-9b-q4`, `gemma3-12b-q4`, `gemma4-12b-qat` |

Candidate IDs resolve through the pinned model inventory and catalog. Newer
27B-and-larger Qwen candidates remain outside this card's full-offload envelope;
their availability is not evidence that they fit 8 GiB.

### Exit gate

Record a precise pass, partial result, unsupported result, or failure for each
operating-system/backend cell. No result changes automatic selection without a
separate owner decision.

## Phase 4: restore the enterprise NVIDIA baseline

After consumer testing, return every original GPU to its labelled
slot and restore only its original resource mapping.

### Proxmox slot map

```text
Top / rear I/O

PCIE7  Quadro RTX 5000 16 GiB  [original card]
PCIE6  empty
PCIE5  empty
PCIE4  Tesla V100 B 32 GiB     [original labelled card]
PCIE3  empty
PCIE2  shared resources; do not use for this campaign
PCIE1  Tesla V100 A 32 GiB     [original labelled card]

Bottom / front of chassis
```

### Restore gate

- PCI identities and IOMMU groups match the recorded baseline.
- Original mappings point to the original devices.
- A short RTX 5000 smoke test passes.
- Both V100s are visible to their protected service before it is restarted.
- The protected service is restarted only after its own health check passes.

## Phase 5: consolidate evidence and make decisions

Produce one human-readable table with a row for every exact combination and
machine-readable sanitized evidence behind it. Each row must state:

- card, memory, architecture/generation, operating system, driver, runtime,
  backend, exact model and digest;
- task-gate and soak outcomes;
- average/minimum speed, peak VRAM, cancellation and cleanup outcomes;
- idle/active/peak power source and whether it is GPU-only or wall power;
- known limitations and whether the evidence is verified, engineering-only,
  partial, failed, or not tested; and
- the next decision: no action, targeted retest, recommendation proposal, or
  explicit unsupported/refusal behavior.

The final table must also retain a row for every inventory card that has not
yet produced a valid measurement. Label that row `Pending`, `Unsupported`, or
`Failed or needs retest` with a specific reason instead of omitting it.

Update the public hardware and model-certification wiki sources only from
reviewed, sanitized evidence. Do not promote a model or backend automatically.

## Expected physical rotations

| Rotation | Physical work | Main evidence produced |
| --- | --- | --- |
| Baseline | None | Close current RTX 5000/V100 evidence |
| Local RDNA 3 | None on Proxmox | RX 7800 XT native Windows soak |
| Consumer set | Replace V100 A, V100 B, and RTX 5000 | GTX 1650 Super, RTX 3060, and RX 6800 individual plus coexistence results |
| Native RDNA 1 | None on Proxmox | RX 5700 XT Linux ROCm and Windows Vulkan exact-profile evidence |
| Restore | Replace consumer cards with labelled originals | Confirmed RTX 5000/V100 return to service |

This is two major three-card rebuilds. The RX 7800 XT, RX 5700 XT, and separate
Intel phases require no Proxmox GPU swap.
