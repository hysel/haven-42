# Alpha 2 Linux long-term validation

This page records the long-running test campaign for the unsigned Haven 42
`0.4.0-alpha.2` Linux package. Reading it does not grant access to a test
machine, start or stop a virtual machine, assign a graphics card, download
software, or mean that Alpha 2 passed.

## Current campaign status

As of August 11, 2026, the restricted controller is deployed with status,
start, and graceful-shutdown authority for the approved campaign guests. A
guarded stop is exposed only after the latest matching graceful shutdown failed
or was interrupted and the same logical VM is still running. It has no
container-management, storage, snapshot, package-installation, shell, or guest-
configuration authority. The protected Ollama container remained outside the
campaign and was not changed.

On August 13, a later source-candidate managed-lifecycle pass completed on all
nine Linux profiles with the Quadro RTX 5000 CUDA path. Fresh setup, exact
Ollama 0.32.5 and Qwen 3.5 0.8B Q8 identity, inference, normal shutdown,
process and port closure, zero-download reuse, and marker-owned uninstall all
passed. Mint also passed recovery from an interrupted marker-owned setup. This
is source-candidate evidence, not a packaged Alpha 2 result; see
`docs/linux-managed-lifecycle-validation.md`.

An August 11 exact-candidate sweep repeated the checksum, relocation,
read-only startup, abrupt-recovery, lifecycle, occupied-port, shutdown,
hostile-environment, and integrity checks on all nine Linux distributions.
Every distribution passed that package suite. Pop!_OS also exposed a readiness
bug: its fixed `/etc/os-release` link resolves to
`/etc/pop-os/os-release`, which the original fixed-path allowlist did not
recognize. The source fix admits only that exact system path and continues to
reject arbitrary links; it passed the real Pop!_OS 24.04 readiness check. A
new exact candidate still needs to be built and repeated on Pop!_OS before the
fix can count as release-candidate evidence.

After reviewing the sanitized results, the owner approved the first narrow
automatic-selection boundary on August 11. The selector now admits Qwen 3.5
0.8B Q8 on the exact CPU profiles tested across the nine distributions. On
the exact Ubuntu 26.04 and Bazzite 44 CUDA profiles with at least the measured
system-memory floor and 16 GiB usable GPU memory, it admits the tested 0.8B,
2B, and 4B records and chooses Qwen 3.5 4B Q4 as the largest comfortable fit.
The smaller CUDA records remain validated fallbacks when storage fit excludes
the larger model. This does not extend approval to other NVIDIA distribution
profiles, lower memory, AMD or Intel acceleration, other runtimes, or other
model families.

The same unsigned Linux candidate passed package integrity, relocation,
read-only startup, abrupt-exit recovery, repeated lifecycle, occupied-port,
shutdown-authority, hostile-environment, and protected-resource integrity tests
on all nine distributions. This is package-parity evidence. It is not the
complete guided-setup, desktop, capability, accessibility, or long-duration
soak evidence required for a Supported Alpha label.

A read-only NVIDIA preflight confirmed that every guest sees the four functions
of the owner-assigned graphics card. After owner-assisted, distribution-native
driver installation, all nine exact Linux profiles passed a fresh native CUDA
validation pass. The scoped installation helpers were removed afterward; Haven
itself did not install or repair a driver during application setup.

Fresh current-policy CPU evidence covers the exact Qwen 3.5 0.8B artifact on
all nine distributions. The post-driver CUDA matrix adds 27 passing capability
cells, 81 passing samples, and 81 unload checks for that exact artifact across
all nine profiles, with nonzero GPU residency in every cell. Earlier 2B and 4B
CUDA evidence remains limited to Ubuntu 26.04 and Bazzite. No committed
automatic default has changed. Arch and CachyOS report `BUILD_ID=rolling`
rather than `VERSION_ID`, so Alpha 2 normalizes only those two reviewed
distributions to the stable identifiers `arch-rolling` and `cachyos-rolling`.

The separate Windows 11 NVIDIA baseline also passed the exact managed Ollama
0.32.5 and Qwen 3.5 0.8B Chat, Writing, and Summarization cells: nine samples,
nine unload proofs, and nonzero CUDA residency. A later graceful shutdown with
the QEMU guest agent active completed in approximately 75 seconds; the guarded
fallback was not needed for that attempt.

The protected comparison provider was reached only through a verified,
no-command loopback tunnel. A separate comparison-only contract admitted its
exact Ollama 0.32.6 version without changing the managed 0.32.5 runtime or the
selector policy. Qwen 3.5 9B, Gemma 3 12B, Granite 4 7B, and Mistral Small 3.2
24B passed 12 capability cells, 36 samples, and 36 unload checks. Those results
are comparison evidence only; they cannot promote a model or authorize a
client-hardware profile. The tunnel was closed after the run, and the protected
provider was not reconfigured or used to download models.

A separate version inventory now tracks official local artifacts, hosted-only
or preview releases, and versions for which no official local artifact was
found. It explicitly covers Qwen 3.5 through 3.8, Gemma 3 and 4, Granite 4.0
and 4.1, Phi 4 Mini, Llama 3.2, Ministral 3, and Mistral Small 3.2 and 4.
Exact manifest digests are required before a local candidate can run. The
current qualification queue contains Gemma 3 1B/4B, Gemma 4 E2B/E4B QAT,
Granite 4.1 3B/8B, Phi 4 Mini 3.8B, Llama 3.2 3B, and Ministral 3 3B/8B on
CPU and 16 GiB CUDA profiles. Gemma 4 12B QAT is limited to the 16 GiB CUDA
profile. Qwen 3.6 27B is admitted to a separate review-only profile requiring
at least 31 GiB measured system memory and 16 GiB usable CUDA memory, with its
native run scheduled for the Windows NVIDIA VM. Qwen 3.6 35B remains deferred
to a machine with at least 48 GiB system memory. Qwen 3.7/3.8 remains outside
local execution until an official local artifact is verified. This inventory
is not the product model ladder and grants no default-selection authority.

Automatic-selection evidence now includes the minimum tested system-memory and
usable-accelerator-memory measurements. A client below either tested floor
cannot inherit the result even when the model catalog's nominal fit threshold
is lower. This prevents the present roughly 16 GiB VM evidence from being used
to authorize an untested 8 GiB client.

The selector also recomputes the canonical digest of its active policy and
requires every evidence record to carry that exact digest. Report generation
keeps results from different policy revisions in separate groups. Missing,
malformed, or stale-policy evidence is rejected before selection.

Offline selection exercises using the native evidence produced the expected
fail-closed decisions: every tested CPU profile selected the evidenced 0.8B
artifact; the two tested CUDA profiles selected the evidenced 2B artifact at
their measured memory floor and the 4B artifact at 16 GiB or more of system
memory; 8 GiB CUDA and untested Fedora CUDA profiles selected nothing. These
results do not change a product default.

The public, effect-free campaign contract is
`config/alpha-2-linux-long-term-validation.json`. It intentionally contains no
IP address, hostname, username, SSH key, host fingerprint, Proxmox VM number,
PCI address, or private test result. Those details belong in an ignored local
deployment profile on the test controller.

## Coverage

Every distribution receives a CPU or virtual-graphics package and lifecycle
sequence. The sequence covers package integrity, hardware detection, automatic
model selection, Chat, Writing, Summarization, cancellation and retry,
attachments, resource metrics, model unload, process cleanup, loopback-only
binding, logs, support reports, uninstall separation, and privacy.

The NVIDIA resource mapping is preconfigured by the lab owner and is immutable
to the campaign controller. Only one test VM runs at a time, so only that VM
can own the card. CPU cells force and verify CPU execution inside the guest;
they never detach or reconfigure passthrough. Ubuntu 26.04
and Bazzite are the only NVIDIA promotion candidates in the current roadmap.
NVIDIA results from Ubuntu 24.04, Debian, Mint, Pop!_OS, Fedora, CachyOS, and
Arch are useful experimental evidence but cannot promote those profiles.

The planned order is:

1. Read-only host, storage, VM, SSH, and package preflight.
2. Start the next approved guest and finish its CPU and NVIDIA cells.
3. Verify process cleanup and request a graceful guest shutdown.
4. Advance to the next guest only after the shutdown is proved.
5. Build the sanitized summary after every guest is complete.

The restartable queue contains 72 operating-system/package cells and 57 model
cells. Each model cell runs three bounded samples, for 171 planned samples:

- the 0.8B low-memory candidate on the CPU path for all nine distributions;
- the 0.8B, 2B, and 4B candidates on the exclusive Quadro path for Ubuntu
  26.04 and Bazzite;
- Qwen 9B, Gemma 12B, Granite 7B, and Mistral 24B as comparison-only models
  on the protected external Ollama service, but only when already installed.

The completed comparison queue is followed by a distinct qualification queue.
Every new candidate must pass deterministic, sanitized checks for Chat,
Writing, and Summarization before it becomes eligible for a 30-minute soak.
The task checks retain no response text, require three samples and three unload
proofs, and remain incapable of changing an automatic default.

The external-provider lane cannot create automatic client-hardware evidence,
download a missing model, change the container, or promote a default. The 9B,
27B, and 35B automatic-selection tiers remain deferred because the current VM
profiles do not provide their required system-memory and GPU-memory combinations.

The offline planner can be reviewed without contacting a machine:

```console
python scripts/plan-alpha2-linux-long-term-validation.py
```

The pure control-policy engine is
`scripts/alpha2-proxmox-control-policy.py`. It has no process, shell, network,
or Proxmox imports. Its hostile tests prove that unknown actions and targets,
multiple GPU owners, low storage, changed node identity, unexpected
passthrough configuration, and unverified forced stops are refused. The pure
module still cannot change a machine; only the separately deployed restricted
wrapper has the bounded authority described below.

The effect-free live-state parser is
`scripts/alpha2-proxmox-live-state.py`. It consumes a private read-only
inventory snapshot and resolves the reviewed resource mapping to one NVIDIA
index by PCI address. It inventories every VM and container, recognizes only
the exact mapped-device form on an approved target, and reports raw or unknown
passthrough as a stop condition. The private policy binds both the mapping name
and the SHA-256 of its canonical definition, so repointing a familiar name to
other hardware is refused.

The root-side read-only collector is
`scripts/alpha2-proxmox-readonly-collector.py`. It accepts no command-line
arguments, runs only fixed absolute Proxmox and NVIDIA inventory commands with
`shell=False`, limits runtime and output size, and inventories every listed VM
and container. It cannot change power, configuration, storage, or hardware.
The collector reports current state; only the separate policy engine may decide
whether a requested operation is safe.

The Alpha 2 model ladder is platform-neutral in
`config/alpha-2-model-catalog.json`; Alpha 1's frozen Windows catalog remains
unchanged. The first shared model-selection core is
`scripts/alpha2_model_selector.py`. It cannot download a model, contact a
provider, inspect a computer, or run a command. A platform setup planner must
first admit storage for each candidate. The selector then requires an exact
match for the selector-policy digest, model digest, normalized
operating-system/version, architecture, execution backend, Ollama version, and
every requested capability. If any measurement or evidence is missing or stale,
or the client has less RAM or usable accelerator memory than the evidence
profile, it returns no automatic selection and does not fall back silently. The
committed comparison list is a validation queue, not a list of new defaults.

Synthetic cases in
`examples/fixtures/alpha-2-model-selection-cases.json` exercise CPU-only,
Intel/Vulkan, NVIDIA/CUDA, and AMD/ROCm profiles from 8 GiB through 64 GiB of
system memory. They also prove storage fallback and the no-evidence refusal.
These fixtures are deliberately marked as non-product evidence; only native
results from the exact client profile can authorize an automatic choice.

## Deployed controller boundary

The deployed design uses a dedicated SSH identity restricted on the host to a
root-owned command wrapper. The wrapper accepts only these reviewed operations
for an exact private allowlist:

- read status for the approved Linux test VMs;
- start one approved VM;
- request a graceful shutdown and wait for a bounded time;
- use a guarded force stop only after the graceful timeout;
- confirm the owner-configured PCI resource mapping without changing it;
- confirm that no second VM or protected container uses that graphics card.

It does not provide an interactive shell or authority over users, storage,
snapshots, disks, networks, ISO files, containers, Windows guests, other PCI
devices, repository publication, or deletion. The owner reviewed the live
inventory and deployed this exact boundary before native testing began.

The existing Ollama container is explicitly outside lifecycle and GPU control,
as is the future controller container itself. The host wrapper has no container
management command path. Both containers must appear in every trusted live-state
check, and graphics-card use by either one blocks assignment to a test VM. The
existing Ollama service may be used later as a separately validated
external-provider endpoint without changing its role or using its storage for
managed-local test data.

The private policy has two deployment states. `inventory-only` permits review
of sanitized status decisions but refuses every mutation. The owner reviewed
the inventory, target mapping, storage admission, and wrapper before enabling
the bounded VM operations. The enabled policy still denies every operation
except status, start, and graceful shutdown for an approved Linux guest. The
protected service was not changed.

## Stop conditions

The controller must stop the campaign and preserve its checkpoint when:

- the Proxmox host key or guest host key differs from the private allowlist;
- a target VM, GPU mapping, package digest, or expected operating system differs;
- more than one GPU owner exists or an unapproved passthrough entry is present;
- the active guest cannot shut down or release the GPU safely;
- local ZFS free space drops below 16 percent;
- the host reports unsafe temperature, storage, or memory pressure;
- a required SSH or guest-agent connection fails repeatedly;
- an unresolved security or privacy finding is discovered;
- raw prompts, responses, credentials, or machine identity would enter evidence.

The live inventory and storage admission are checked before every bounded VM
operation. A failed preflight stops the next start rather than weakening the
threshold.

## Persistence and evidence

A chat session is not a durable scheduler. The controller therefore needs a
restartable local service with an atomic checkpoint. After a reboot or network
interruption, it must resume at a safe preflight boundary instead of blindly
repeating a machine-changing action.

The effect-free checkpoint implementation is
`scripts/alpha2-linux-campaign-checkpoint.py`. It records only the bounded task
state and sanitized measurements allowed by the campaign contract. A passing
model cell must record all three samples as passed and all three unload checks
as successful.

The effect-free scheduler is
`scripts/alpha2-linux-campaign-scheduler.py`. It advances one bounded step at a
time and never executes that step itself. Only the current test VM may run. A
GPU task cannot begin while the protected Ollama container owns the card, and
the scheduler has no operation that can start, stop, or modify a container. A
test result is saved before cleanup begins; after an interruption, cleanup is
re-proved rather than discarding or repeating that result. The result becomes
final only after the target VM is stopped. The static GPU mapping remains
present and unchanged throughout the campaign.

The root-side wrapper is deployed, but the checkpoint and scheduler remain
effect-free planning modules. They gain no machine authority merely because
the wrapper exists; every live action still passes through the private
allowlist, one-time request journal, and current-state checks.

The sanitized report builder is
`scripts/alpha2-linux-campaign-report.py`. A passing model cell must bind its
result to the current selector-policy digest, exact model manifest, exact
operating-system identifier, architecture, backend, Ollama version, measured
memory floors, storage admission, and tested capability. The report exports an
automatic-selector evidence record only when Chat, Writing, and Summarization
all pass three samples and three unload checks with the same exact profile.
Comparison-only results are reported separately and always retain
`automaticPromotionAllowed: false`. Promotion still requires owner review.

The bounded live soak runner is `scripts/alpha2-linux-soak.py`. It accepts an
owner-approved duration from 5 minutes through 12 hours, contacts only the
reviewed IPv4-loopback Ollama endpoint, rotates through Chat, Writing, and
Summarization, and leaves a quiet interval between cells to exercise idle
recovery. Each cell performs three samples and three unload checks. The runner
never prints model output, downloads a model, starts a service, or promotes a
selector result. Its sanitized JSON includes only the exact runtime profile,
duration, aggregate performance, capability counts, and unload/residency
proofs. The legacy filename is retained for compatibility, but the evidence
engine now requires an explicit `linux` or `windows` platform family and emits
distinct Linux and Windows soak kinds. The offline reporter keeps platform in
its grouping key and rejects a soak kind/platform mismatch, so Windows parity
cannot be mislabeled as or combined with Linux evidence. Compatibility for
task records created before this field existed is limited to the exact reviewed
Bazzite operating-system identifier; a platform-less Windows or unknown record
is refused rather than inferred.

`scripts/alpha2-model-task-qualification.py` handles the separate cross-family
quality gate. It accepts only exact candidates and CPU/CUDA profiles from
`config/alpha-2-model-qualification-matrix.json`, requires the matching
`config/alpha-2-model-version-inventory.json` digest, contacts only IPv4
loopback, and validates task constraints without retaining or printing the
response. Its evidence is labeled qualification-only and cannot be grouped as
selector evidence. Failed checks emit the stable violated-constraint code and
the reviewed model/profile bindings, but no prompt, response, endpoint, or
private machine identity.

`scripts/alpha2-model-qualification-report.py` validates these task and soak
records offline. Supply one `--evidence-dir` for a combined evidence directory,
or repeat the option when task cells and soak records are deliberately kept in
separate, non-overlapping directories. The reporter accepts no more than eight
roots and 1,024 JSON records, and refuses duplicate, nested, or otherwise
overlapping roots so one record cannot be counted twice. It reports a
model/profile as passed only when
all three task gates and a complete 30-minute soak pass with sample/unload
parity. Missing evidence remains incomplete, and any failed task or soak keeps
the cell failed. For each passed task, the summary retains only validated
aggregate sample, unload, output-token, throughput, and accelerator-residency
measurements. It contains no filenames or private source paths and cannot
authorize automatic selection. By default the reporter binds evidence to the
current inventory and matrix. Historical evidence can be reproduced with a
preserved metadata pair by passing both `--inventory` and `--matrix`; supplying
only one is refused, and the matrix must cryptographically bind the supplied
inventory. This keeps older exact evidence reviewable after new candidates are
added without allowing stale evidence to mix with the current qualification
set. Every included record is also rechecked against that metadata for its
exact manifest, provider and version, task check, CPU/CUDA profile, memory
floor, sample-to-unload parity, capability coverage, and accelerator residency.
Failed task records may omit measurements that were never produced, but they
must retain the exact identity binding and can never enter a ranking.

`scripts/alpha2-model-qualification-ranking.py` converts a current, complete
qualification summary into an owner-review ranking per operating-system,
hardware profile, and capability. It ranks only models that passed every task
gate and soak, using the sanitized task throughput with soak throughput as a
tie-breaker. The result explicitly prohibits automatic selection and default
changes; it is decision support for the separate owner-approval gate, not a
product policy. It uses the current metadata by default and accepts the same
paired `--inventory` and `--matrix` snapshot options as the reporter for a
historical summary; a mixed or partially supplied snapshot is refused.

`scripts/alpha2-model-artifact-download.py` is the matching exact-artifact
preparation gate. Its default action is a read-only plan. A download requires
the explicit `--apply-download` flag, an exact inventory candidate, the pinned
loopback provider version, and post-download manifest verification. It reports
only bounded progress totals and never retains raw provider output. An existing
tag with the wrong digest stops the operation rather than being overwritten.

A serialized multi-model run must also pass a batch capacity gate before its
first download. The gate sums every not-yet-present candidate's reviewed
`downloadBytes` and adds at least 8 GiB of working reserve; a per-model free-
space check is not sufficient. Cleanup may remove only exact test artifacts
whose task and soak evidence is already complete and verified. Removal must use
the provider's model-removal operation, confirm that each exact tag is gone,
and recheck capacity before the next queue starts. An incomplete model, partial
evidence file, or failed prior batch is never eligible for automatic cleanup.

Committed evidence may contain only the release and package digests, sanitized
target profile, test identifiers, timestamps, durations, bounded measurements,
outcome, and stable error code. Raw prompts and responses, IP addresses,
hostnames, usernames, personal paths, secrets, keys, and private controller logs
must remain outside the repository.

## Approval gates still open

The owner approved 30-minute soaks, the isolated Ollama 0.32.6 comparison
contract, and qualification of additional model families and newer versions.
Current-package lifecycle and parity checks passed on all nine planned Linux
distributions, and the Windows NVIDIA lane passed its package lifecycle checks
and graceful-shutdown proof. Qwen 3.6 27B also passed its separate Windows CUDA
task gates and 30-minute qualification soak. On August 15, 2026, the exact
Gemma 3 1B, Phi 4 Mini 3.8B, and Qwen 3.6 27B Q4 artifacts then passed the
current three-task contract and separate 30-minute soaks on Ubuntu 24.04.4
CUDA with Ollama 0.32.13. The sanitized report explicitly denies automatic
selection and default authority. These results remain evidence for owner
review: physical memory-tier evidence, full guided-setup promotion, package
publication, and support-label promotion remain separate gates.

On August 16, the exact Ministral 3 3B and 8B Q4 artifacts were retried on the
same Ollama 0.32.13 Ubuntu/CUDA review environment. Both passed Chat with three
samples, three unload proofs, and nonzero CUDA residency. The 3B artifact also
passed Summarization, but both failed Writing's one-sentence constraint and the
8B artifact also failed the same Summarization constraint. The fail-closed
runner therefore started no soak. This newer negative result remains bound to
the exact runtime, task contract, artifacts, and profile.
