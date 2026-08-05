# Haven 42 0.4 Alpha 1

This is an unsigned, invited-test-only Windows 11 x64 candidate. It is not a
public release, installer, signed product, or production-readiness claim.

## Alpha boundary

- The browser service remains bound to IPv4 loopback.
- `general.chat`, `content.write`, and `content.summarize` are executable in one
  continuous text workspace. Automatic routing is the default, and the tester
  can explicitly select Chat, Write, or Summarize. Images, software workflows,
  research, and every other future capability remain server-denied.
- The tester may connect an existing Ollama provider or choose a guided,
  current-user setup. Guided setup requires an explicit click on an exact plan.
- Haven 42 does not bundle Ollama, models, drivers, or other external software.
  It downloads versioned official artifacts only after approval.
- Drivers are advisory-only. Haven 42 never installs, changes, or removes a
  driver and never changes Windows Update, firmware, services, firewall rules,
  certificate trust, or system runtimes.

## Hardware and model decision

The provisional minimum is four logical processors, 8 GiB system memory, and
15 GiB available storage. A GPU is optional. A machine below the threshold may
open the UI, but local setup is denied with a human-readable reason.

The model catalog contains immutable Ollama manifest and model-layer digests
for Qwen3.5 0.8B, 2B, 4B, 9B, 27B, and 35B candidates. Haven 42 selects the
largest catalog entry that fits bounded system memory, the memory of the exact
accelerator chosen for the backend, and conservative peak free-storage needs.
The storage calculation includes registered component archives, the maximum
admitted expansion budget for each component, model bytes, and a 2 GiB safety
reserve. On Windows, both recommendation and execution measure the volume
containing the extracted Haven executable; environment variables and renderer
input cannot redirect the fixed `Haven42-Data` managed state root. Setup
rechecks the exact byte requirement before any download or process start. If a
larger model does not fit, selection falls back to the
largest smaller catalog entry that does. Candidate guidance cannot create a
managed plan until that exact Windows model path has native evidence.

All catalog models are already quantized. Alpha 1 therefore selects a smaller
pinned artifact before considering conversion. Automatic local quantization
is intentionally disabled: conversion would add provenance, license, quality,
temporary-storage, recovery, and runtime-compatibility risks without filling a
catalog gap.

## Guided setup effects

The managed path uses pinned standalone Ollama archives rather than invoking a
third-party installer. It verifies exact byte length and SHA-256, validates ZIP
members, verifies the extracted Windows publisher signature, writes a
versioned runtime and model store inside the extracted package folder, and
starts only the exact process it owns on `127.0.0.1:11435`.
It records a relative-path content-hash inventory after verified extraction;
every file must still match before the managed runtime can be reused.
On later launches, a completed receipt is only a candidate: Haven re-runs the
bounded hardware check and revalidates the receipt, runtime file inventory,
publisher signature, registered model, managed paths, and loopback endpoint.
If all checks pass it starts the owned runtime and opens the text workspace
without showing the connection step. Any mismatch fails closed into guided
setup without downloading or replacing files. An external provider can still
be selected later from **Setup · Provider**.

The readiness view identifies Windows 10 or Windows 11, includes the Windows
build and architecture, and shows detected software and driver versions where
the bounded probes can determine them. Every managed download row also shows
its exact pinned component or model version.

The portable Haven archive runs in place: its private Python runtime is inside
the extracted `haven42\_internal` directory and is never installed globally.
After explicit setup approval, managed external components use this fixed
layout beneath `Haven42-Data` beside `haven42.exe`:

```text
runtime\<version>\   verified standalone Ollama and optional AMD supplement
models\              verified Ollama model content
downloads\           transient verified component archives
staging\             transient extraction transaction
home\                 isolated managed-runtime profile
appdata\              isolated managed-runtime application data
temp\                 isolated managed-runtime temporary files
```

Haven does not copy these components into `Program Files`, register them as a
service, add them to the global `PATH`, or install a system-wide Python. An
existing manually installed Ollama remains in its own location and is not moved
or replaced by Haven.

The owned runtime receives a constrained child environment. Its home, profile,
application-data, model, and temporary directories all resolve beneath Haven's
portable Alpha state root. Ollama cloud behavior and command history are
disabled for this managed process, so it cannot create its identity files in
the tester's normal profile or silently activate cloud-backed model behavior.

The backend is derived from one measured accelerator in the read-only hardware
snapshot. On mixed-GPU systems, the accelerator with the greatest measured
usable memory is selected, with a deterministic vendor tie-break, so model
capacity and runtime backend cannot come from different devices. Intel uses
Ollama's opt-in Vulkan path, NVIDIA uses its normal CUDA discovery path, AMD
uses the registered Ollama 0.32.5 support package built with ROCm 7.1, and an
unmeasured or CPU-only machine is
limited to the explicitly CPU-capable model. Setup runs a fixed synthetic
inference after download. When a GPU backend was selected, Ollama must report
nonzero model VRAM before setup can succeed; silent CPU fallback fails closed.

Approval is memory-only, session-bound, plan/effect-bound, expires after 15
minutes, and is single-use. Progress is reported as downloading, verifying,
extracting, starting, model download, validating, complete, failed, or
cancelled. A minimal recovery journal may contain component/model identifiers
and phase only; never prompts, attachments, keys, URLs, usernames, hostnames,
or local paths. Cancellation and unexpected worker failures stop the exact
owned process, and model-pull reads use a bounded inactivity timeout.

The Windows launcher starts the managed provider suspended, assigns it to a
kill-on-close Job Object, and resumes it only after assignment succeeds. If
`haven42.exe` exits normally, crashes, or is killed, Windows terminates that
managed process tree, including provider children. Haven does not assign or
terminate an external Ollama server.

Before approval, the setup view lists every registry-selected runtime package
and model with its version, purpose, and expected download size. During setup,
an overall progress bar and one bar per component distinguish download,
integrity verification, portable extraction, readiness, and local validation.
Model progress aggregates bounded provider-reported layer byte counts so
multi-layer downloads do not make the display jump backward. The status API
contains no component URL, command, filesystem path, credential, or secret.

The System panel can remove all marker-owned managed components after an
explicit destructive-action confirmation. Haven first refuses active setup,
audits the complete data tree, and stops only processes whose executable path
resolves inside that validated tree. This safely covers orphaned provider
children without granting name-based process control. Any link,
reparse point, special file, unknown ownership marker, or excessive entry count
blocks removal. The application never self-deletes; after managed cleanup, the
tester closes Haven and deletes the extracted folder to remove the app itself.
For pre-release builds that used the former Local AppData layout, the same
control can remove that legacy tree only when its fixed operating-system path,
Alpha transaction receipt, registered component/model identifiers, top-level
layout, and complete link-free tree all validate. It never migrates or copies
legacy data.

## Resource information

The chat panel displays local CPU, RAM, GPU/VRAM when the operating system can
measure it, plus provider-reported input/output/session token counts. Missing
measurements say `Unavailable`. Samples are bounded to 60 seconds in memory,
are not telemetry, and are cleared when Haven exits. Session token totals reset
with **New task**.

While Chat, Writing, or Summarization is generating, the Send control becomes
a visible **Stop** control. Stopping closes only that request's provider stream,
unloads the active model, discards partial output, and restores the tester's
message for editing or retry. It does not terminate unrelated software.

## Tester diagnostics requirement

Haven provides bounded sanitized diagnostic logs inside the sibling portable
directory `Haven42-Logs`. Alpha logging is local-only and rotates automatically.
The implemented fixed-schema core records stable event/reference IDs, timestamps,
Haven and managed-component versions, setup phases, integrity outcomes,
hardware-selection decisions, owned-runtime lifecycle, and clean or observed
abnormal shutdown state. Important lifecycle events are flushed promptly so a
tester can report the last completed Haven action after a failure.

Logs and support reports must never contain prompts, responses, attachment
content or filenames, API keys, credentials, full provider endpoints,
usernames, hostnames, personal paths, environment values, commands, or raw
child-process output. Haven never uploads diagnostics automatically. A novice
Troubleshooting view must support viewing recent safe events, copying details
for one error reference, explicitly saving a sanitized support report, and
clearing logs. Removing managed components deletes only `Haven42-Data` and
preserves `Haven42-Logs`. Full uninstall treats logs as a separate user-owned
class and removes them only after an explicit choice. Hostile privacy, rotation, disk-full,
interrupted-write, disk-full, packaged UI parity, and expanded component-decision
tests remain required. Privacy, rotation, unclean-session, report, clear, and
separate-removal hostile tests are implemented.

## Response guardrails

Every Alpha Chat, Writing, and Summarization request receives the same compact
model-behavior policy. It prohibits guessing pronouns or sensitive personal
attributes from names, appearance, writing style, or location; unsupported
stereotypes; invented actions or verification; unnecessary secret repetition;
and conversion of uncertain source claims into facts. It requires explicit
uncertainty, cautious framing for high-stakes guidance, and effect plus
verification guidance before destructive or system-changing commands. Explicit
individual pronouns and personal details supplied by the user or source are
preserved exactly. An explicit pronoun is never replaced with singular
they/them. If no individual pronoun is supplied, the model must use the name or
a neutral noun and must not assign a pronoun or ask for gender merely to word a
response.

These instructions do not grant or enforce filesystem, process, network, tool,
or machine authority. The deterministic server boundary remains responsible
for security. Before invited distribution, every automatically selectable exact
model must pass a fixed Chat, Writing, and Summarization compliance matrix;
repeated critical violations block recommendation even if ordinary inference
works.

## Remaining candidate evidence

Implementation alone does not admit distribution. The exact package still
requires a clean security review, privacy scan, full local gate, native Windows
smoke and lifecycle test for every admitted model tier,
package integrity/checksum/SBOM/notices evidence, clean hosted checks on the
eventual commit, owner review, and an authenticated private delivery decision.
The earlier final13 archive has exact Qwen 3.5 9B managed reuse evidence on
Windows Intel Vulkan, AMD ROCm, and NVIDIA CUDA. The current final18 candidate
adds portable-storage and cleanup hardening and still requires fresh
external-hardware validation. The other catalog tiers remain instruction-only.
Signing, tagging, and public release remain outside this batch.
