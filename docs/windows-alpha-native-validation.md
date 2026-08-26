# Windows Alpha native validation

Haven 42 tested the unsigned `0.4.0-alpha.1` candidate on physical Windows 11
x64 Intel, AMD, and NVIDIA GPU cells. This is sanitized evidence, not a public
release, a production-readiness claim, or evidence for every Windows hardware
combination.

## Exact Intel test cell

- Candidate archive: `haven42-0.4.0-alpha.1-windows-x64-unsigned.zip`
- Candidate SHA-256:
  `0157f482fa788272a35c54b4af0fae233e08aea6183e68a14fd9d5a66dc71020`
- Package state: unsigned, uncommitted test tree, distribution not authorized
- Operating system: Windows 11 x64
- Account boundary: dedicated non-administrator test account
- Processor capacity: 24 logical processors
- System memory: 127.9 GiB
- Accelerator: Intel Arc B580, 11.8 GiB detected memory
- Runtime backend: Ollama `0.32.5`, opt-in Vulkan
- Selected model: `qwen3.5:9b`, pinned Q4 catalog entry

## Exact AMD test cell

- Candidate archive and SHA-256: identical to the Intel cell above
- Package state: unsigned, uncommitted test tree, distribution not authorized
- Operating system: Windows 11 x64
- Account boundary: current-user, non-elevated validation
- Processor capacity: 24 logical processors
- System memory: 31.9 GiB
- Accelerator: AMD Radeon RX 7800 XT, 16 GiB detected memory
- Runtime backend: Ollama `0.32.5`, pinned ROCm supplement
- Selected model: `qwen3.5:9b`, pinned Q4 catalog entry

## Exact NVIDIA test cell

- Candidate archive and SHA-256: identical to the Intel cell above
- Package state: unsigned, uncommitted test tree, distribution not authorized
- Operating system: Windows 11 x64
- Account boundary: dedicated non-administrator test account
- Processor capacity: 8 logical processors
- System memory: 31.9 GiB
- Accelerator: NVIDIA Quadro RTX 5000, 16 GiB detected memory
- Runtime backend: Ollama `0.32.5`, CUDA
- Selected model: `qwen3.5:9b`, pinned Q4 catalog entry

No hostname, address, username, SSH material, endpoint, prompt content, model
response, or local filesystem path is retained in this record.

## Fresh Intel portable-closure cell

On 2026-08-06, a fresh 41-file development archive built from the pending
portable-evidence correction passed an additional physical Windows 11 x64
Intel Arc B580 cell under a dedicated non-administrator account:

- archive: `haven42-windows-amd64-unsigned-development.zip`;
- SHA-256:
  `1aefe03183828adea0f21ad9e2c8ee100187142d38158e17578b6aeaa6ed71cf`;
- package identity: unsigned Haven 42 `0.4.0-alpha.1` development evidence,
  not the immutable published Alpha asset and not authorized for distribution;
- managed runtime: pinned portable Ollama `0.32.5`, Intel Vulkan backend; and
- selected model: pinned `qwen3.5:9b` Q4 entry with exact manifest verification.

The isolated extracted package passed:

- transferred-archive digest verification, 41-file extraction, packaged
  resource integrity, security headers, loopback-only reachability, session-
  token shutdown authority, process exit, and port closure;
- explicit single-use setup approval for only network download, portable-
  folder files, one owned process, and local-model validation, while driver,
  service, firewall, certificate, firmware, global-runtime, and elevation
  effects remained forbidden and false;
- fresh current-user setup, Authenticode and runtime-integrity verification,
  exact model digest, required GPU acceleration, and real Chat, Writing, and
  Summarization with positive provider-reported token rates;
- second-launch receipt, runtime-integrity, and publisher revalidation with no
  download, installation, or managed-data growth;
- sanitized support-report creation under `Haven42-Logs`, outside the
  replaceable `Haven42-Data` component tree;
- acceptance of a bounded human filename containing spaces, parentheses, and
  a Unicode en dash as inert memory-only text context, with no temporary file,
  filesystem, tool, or host-execution authority;
- rejection of PowerShell shebang content renamed with a `.txt` suffix;
- verified local-to-private-network-to-local provider switching against
  Ollama `0.32.6`, including the unencrypted trusted-LAN transport state,
  all three text capabilities, no-download local return, and zero externally
  loaded models after cleanup; and
- confirmed uninstall of 7.947 GiB of marker-owned `Haven42-Data`, while the
  application and sanitized logs remained, followed by a package-verified
  relaunch in the empty/setup-ready state.

The remote harnesses were disposable ignored test artifacts. They are not
application, package, workflow, or repository surfaces and grant no ongoing
machine authority.

## AMD, NVIDIA, and replacement-candidate closure

On 2026-08-06, a later unsigned development archive with SHA-256
`2a4ee460744369f3f5dce22579320537d32b06bc7d8971625466996a83e53e0d`
completed fresh managed setup independently on the exact Windows AMD and
Windows NVIDIA cells. Each run verified the package, pinned runtime and model
bytes, Authenticode publisher, exact model manifest, required accelerator use,
real Chat, provider token metrics, explicit model unload, Haven shutdown, and
managed-port closure. The NVIDIA package then passed local-to-trusted-LAN-to-
local switching against Ollama `0.32.6` for Chat, Writing, and Summarization;
the external server had zero loaded models after the run.

That work exposed a relaunch robustness boundary: a transient filesystem or
child-process start error could escape the managed setup abstraction and close
the browser connection. The implementation now converts those failures into
bounded fail-closed setup errors without retrying an unreadable runtime or
weakening any integrity check. The replacement archive has SHA-256
`afe0d31c3055400d036d1cea4008acd4d47c616a3ea00e43f36765e41c1aac02`.
It passed artifact/SBOM/notices verification, native package parity and hostile
lifecycle tests, 432 packaged-browser checks, and exact no-effect native cells
on Windows AMD/ROCm, Windows NVIDIA/CUDA, and Windows Intel/Vulkan. No
`Haven42-Data` was present in that archive or its build output.

## Passed evidence

The native harness verified across the recorded cells:

- exact candidate SHA-256 before extraction;
- packaged resource integrity, unsigned Alpha identity, the admitted text-only
  Chat, Writing, and Summarization boundary, and IPv4 loopback binding;
- read-only hardware detection without network, installation, elevation,
  service, firewall, or driver effects;
- rejection of a forged setup-effect approval without changing setup state;
- hardware-aware selection of the 9B Q4 model, using Vulkan on Intel, the
  pinned ROCm supplement on AMD, and CUDA on NVIDIA;
- current-user runtime download, exact byte length and SHA-256, bounded ZIP
  extraction, and valid Ollama Inc. Authenticode signing;
- a Haven-owned profile, app-data, model, and temporary-directory boundary;
- Ollama cloud and command-history disablement for the managed child process;
- exact model-manifest digest verification while accepting the API's documented
  raw digest representation with or without the literal `sha256:` prefix;
- fixed synthetic inference, exact loaded-model identity, and nonzero model
  VRAM proving Intel Vulkan, AMD ROCm, and NVIDIA CUDA acceleration rather than
  silent CPU fallback;
- a real Chat request plus provider-reported token and local resource data;
- explicit model unload, clean Haven shutdown, managed-port closure, and no
  remaining Haven-managed Ollama process; and
- a second reuse run that reverified runtime file integrity and repeated the
  inference, Chat, unload, and shutdown lifecycle without redownloading the
  runtime or model.

An earlier candidate completed that managed reuse run independently on the
Intel Vulkan, NVIDIA CUDA, and AMD ROCm cells. The later closure candidate
repeated fresh AMD and NVIDIA setup and inference as recorded above. Before
sufficient target space was available, the same AMD cell also passed the native `StorageDenied`
path at 7.4 GiB free: no model or managed plan was selected, the broker stayed
idle, managed-state existence did not change, shutdown was clean, and no user
content was persisted. After unrelated WSL storage was moved off the target
volume, the AMD cell reported 69.6 GiB free and completed the exact 17.8 GiB
preflight, managed inference, Chat, unload, port-closure, and shutdown gates.

The same candidate also passed the local native parity, relocation, read-only
startup, abrupt-exit recovery, repeated lifecycle, occupied-port, hostile
environment, shutdown-authority, and hostile package-integrity suite.

These results support only the pinned Qwen 3.5 9B Q4 artifact for managed
Windows Alpha setup and only on the exact recorded profiles.
The server now refuses to create or register a managed
setup plan for every catalog candidate that still lacks the required evidence;
those entries remain visible as instruction-only candidates.

## Findings resolved during native validation

Native testing found and resolved these fail-closed issues before any candidate
promotion:

1. CPU-only high-memory systems could be offered a GPU-oriented model. Missing
   GPU capacity is now treated as zero, limiting that profile to the admitted
   CPU model.
2. Intel required explicit Ollama Vulkan activation. Backend selection now
   derives from the hardware snapshot and Vulkan is enabled only for Intel.
3. Authenticode verification needed the fixed Windows security-module path and
   an environment-bound internal target rather than a trailing command
   argument.
4. Ollama required a home/profile directory. All child profile, application,
   model, and temporary paths now remain inside Haven's user-scoped state, with
   cloud behavior and history disabled.
5. Ollama `0.32.5` returned raw manifest hex rather than the prefixed digest
   representation. Verification now normalizes only an optional exact prefix
   and still compares all 64 lowercase hexadecimal characters.
6. Qwen placed the deliberately bounded validation tokens in `thinking` rather
   than `response`. Validation accepts either non-empty generated field while
   still requiring completion, a bounded positive token count, exact model
   residency, and GPU VRAM when required.
7. Transient runtime-inventory reads or child-process start failures during a
   later relaunch could escape as a closed browser connection. They now return
   bounded setup errors while retaining fail-closed integrity and process
   ownership checks.
8. A low-end Windows tester showed that selecting CPU mode without enforcing
   Ollama's generic CPU runner could let runtime autodetection choose a native
   runner that crashed during the private model test. Managed CPU mode now sets
   the exact `cpu` library override; the same downloaded model completed the
   bounded validation request under that override.
9. The first successful low-end setup entered Chat without selecting the model
   it had just validated because Chat reapplied the general external-server
   recommendation. Receipt-backed local reconnects now bind the exact installed
   model name and digest to the completed local self-test, select it
   automatically for Chat, Writing, and Summaries, and leave external-server
   recommendations unchanged.

## Remaining boundaries

These cells do not validate low-memory/CPU-only hardware, every supported model
tier, or a fresh managed download after the narrow replacement-candidate
relaunch-error correction; the replacement itself passed exact no-effect cells
on all three accelerator families. The published Alpha remains unsigned.
Signing, stable or production
promotion, installer activation, driver automation, broader system changes,
and production claims remain blocked.
