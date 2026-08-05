# Security Policy

## Clear security information

Haven 42 is designed for people who may be new to local AI. Security messages
must explain the practical consequence and the safe next step in plain
language. Technical detail may be placed under **Advanced**, but warnings,
approval boundaries, uncertainty, and fail-closed behavior must never be hidden
or removed to make the interface appear simpler.

## Supported Versions

Haven 42 is pre-1.0. Only the latest tagged release and the current `main` branch receive security fixes. Contracts marked `runtimeAdmitted: false`, documentation-only candidates, and failed or partial provider profiles are not supported runtime surfaces.

Security review is a standing repository gate. Every enhancement receives a
security check, and large, binary, or security-sensitive staged changes require
a zero-finding review bound to the exact Git index tree before commit. A finding
of any severity stops commit, push, and merge work until the repository owner is
notified, every finding is fixed, and the complete staged tree is reviewed
again. `config/security-review-gate.json` defines the enforced classification;
the pre-commit hook rejects missing or stale review evidence.

The local-web readiness scan is explicit, loopback-only, CSRF-protected, bounded, shell-free, network-free, and read-only. It returns sanitized capability facts rather than identity or raw command output, stores its snapshot only in memory, and builds setup plans only from the exact current server-owned snapshot. Automatic text recommendations require an exact provider digest and capability evidence; name-only matches remain unverified. Provider token and timing values are diagnostic, memory-only, and never represented as billing or remaining context. Event envelopes are fail-closed: sequences must be contiguous and monotonic, contain exactly one result or error terminal, and stop at that terminal. An unverified manual model is visibly warned, failures do not retry automatically, and restored input remains browser-memory-only for a new request.

The trusted loopback service validates and classifies the normalized provider
URL. A successful HTTP connection remains visibly marked as unencrypted:
same-machine loopback HTTP receives a local-transport notice, while
private-network HTTP receives a prominent interception/tampering warning that
recommends a trusted HTTPS endpoint or a loopback tunnel. HTTPS suppresses the
HTTP warning but does not broaden the endpoint, redirect, or provider trust
scope.

Authenticated Ollama connections use only fixed `Authorization: Bearer` or
`X-API-Key` modes. Secrets are bounded visible ASCII, remain in session memory,
are redacted from object representations, and are never returned, logged, or
persisted by Haven 42. Authenticated private-network endpoints require HTTPS;
HTTP authentication is allowed only on same-machine loopback. Blank-key reuse
is limited to the same normalized endpoint and authentication mode within the
current process. Every discovery, chat, model-residency, and cleanup request
uses the same engine-owned authentication object, while redirects, inherited
proxies, arbitrary header names, URL credentials, and query credentials remain
blocked.

The inactive installer foundation does not claim native Ollama TLS. A future
private-network managed profile must keep Ollama loopback-bound behind a
separately acquired and admitted HTTPS gateway. A locally generated
certificate is allowed only with an exact endpoint-IP SAN, explicit trust,
protected non-exported key material, strict verification, negative TLS tests,
rotation, rollback, and exact transaction-owned trust/key cleanup. Certificate
or trust-store modification remains an unadmitted machine effect.

Provider and public-catalog transports explicitly disable inherited OS and
environment proxies, reject redirects, and use exact bounded response shapes.
The loopback API requires exact JSON field types rather than coercing values,
limits provider discovery to 512 models, caps request handling at 32 workers,
and times out stalled sockets after 15 seconds. Assistant Markdown uses only
inert DOM construction and a 2,048-element rendering budget; excess content is
preserved as plain preformatted text instead of expanding the DOM.

Optional public model search requires the user to activate the explicitly labeled **Search public catalog** submit action; changing capability or typing locally never starts it. It sends only a 64-character bounded query to the fixed Ollama HTTPS catalog, rejects redirects and responses over 512 KiB, returns at most 20 strictly normalized names, and persists nothing. Every online result is visibly distinguished from models already installed on the connected Ollama server and remains candidate-only with evidence unverified, hardware fit unknown, and license review required. Selecting an uninstalled candidate cannot execute it: Haven 42 neither calls a pull API nor starts a command. The only installation aid is a copyable `ollama pull` instruction constructed from a validated model name.

The Software view admits only registry-backed `uiReady`, `read-only` plans and
cannot pass arguments or start a process. The Images view is separately limited
to the promoted Linux ComfyUI/SDXL profile through an IP-literal loopback
endpoint. The model and node graph are engine-owned, response size and PNG shape
are bounded, API history is cleared, client delivery stays in browser memory,
and provider-side retention is disclosed before execution. No browser request
can authorize arbitrary download, command, client file write, repository read,
elevation, service change, driver change, or installation. The installation
broker remains simulation-only and not runtime-admitted.

Separate Windows NVIDIA and AMD image-provider evidence is partial and does not
broaden the Images view or provider registry. The Windows NVIDIA cell used an
exact-digest user-local runtime and checkpoint, explicit IPv4 loopback binding,
disabled browser launch, metadata, custom nodes, and external API nodes,
bounded production-adapter I/O, isolated run directories, and exact-owned-
process shutdown. Its generated files, logs, transferred source, harness, and
raw report were removed. Update/rollback, onboarding, idle lifecycle,
uninstall, package parity, and redistribution review remain required before any
admission.

The Validation · Evidence view is read-only and fail-closed. A shared
standard-library engine reads only the bundled sanitized evidence catalog and
surface matrices. The browser receives a bounded schema that omits catalog
notes, machine paths, provider endpoints, and raw validation output. Loading
the view cannot access a network, create a process, read a user repository,
write a file, invoke a provider, modify a machine, or claim that live
validation or production readiness has occurred.

The Evidence page renders committed outcome counts and agent-surface activity
counts locally. Its only external navigation is the fixed
`https://github.com/hysel/haven-42/wiki/Evidence-Dashboard` address. The
renderer cannot supply or change that URL; Haven 42 does not fetch it in the
background, and navigation requires an explicit user click. The link opens a
separate browsing context with `noopener`, `noreferrer`, and a no-referrer
policy.

Unsigned portable development builds preserve this boundary. They verify their allowlisted browser/data resources at startup, bind only to IPv4 loopback, construct only a loopback browser URL, expose no arbitrary process control, and require same-origin session authority plus verified model cleanup for HTTP shutdown. Native smoke tests include read-only-package startup and recovery after abrupt test-owned process termination. Package archives include SHA-256 checksums, dependency inventory, third-party notices, and CycloneDX SBOM evidence. They are not signed, notarized, installer-backed, published releases, or production-ready. The offline installer and updater policy foundations cannot modify a machine or activate an update. The lifecycle simulator rejects raw paths, URLs, commands, arguments, and environment input; models healthy, failed-health, phase-specific interrupted recovery, replay defense, rollback, retention, and disabled paths; and always reports network, writes, download, staging, activation, rollback, cleanup, installation, elevation, service, driver, firewall, process, and user-data effects as false.

The updater trust-handoff foundation does not verify cryptography. It only
checks the strict shape, exact release/asset digest binding, bounded lifetime,
candidate verifier identity, and replay state of a future native verifier
receipt. Raw signatures, certificates, transparency proofs, URLs, and paths are
not accepted. Scenario claims are never authoritative: structural admission
keeps cryptographic verification, trust establishment, evidence promotion,
staging, activation, network, filesystem, trust-store, credential, and
user-data effects false.

The verifier transition foundation similarly accepts no cryptographic material
or authority. It requires consecutive registry versions, bounded validity
overlap, exact verifier and active-root continuity, current-root threshold
claims, and replay defense. Those claims remain non-authoritative; no
authorization is verified and no registry, trust store, runtime verifier,
package, credential, or filesystem state changes.

The post-quantum readiness foundation is also inventory and policy only. It
records current cryptographic boundaries and the standardized ML-KEM, ML-DSA,
and SLH-DSA candidate roles without selecting a parameter set, adding a
dependency, changing TLS policy, handling a key, or verifying a signature. A
future TLS claim requires observation of the exact hybrid negotiation and
certificate signature; HTTP never gains a security claim. Hybrid negotiation
is preferred but not enforced: an observed secure classical fallback is
allowed, must be reported as classical, and cannot receive a PQC claim. A future update
transition must retain classical protection, reject unknown algorithms,
missing signatures, and silent downgrade, and pass independent native and
package review. PQC cannot replace bulk symmetric encryption, OS key
protection, platform code signing, or notarization. All PQC runtime,
cryptographic, trust, package, update, network, and machine-effect authority
remains false.

Portable build dependencies are exact-version and SHA-256 locked for the admitted hosted runner platforms. Evidence generation and verification use an exact reviewed platform/version/license allowlist rather than trusting the caller environment. Native hostile tests reject altered, missing, unexpected, and traversal-manifest resources; shutdown authority failures; unsafe, linked, encrypted, oversized, excessive, duplicate, or case-colliding archive members; incomplete checksums/notices; evidence symlinks; unexpected targets; malformed SBOM/provenance; and archive/file-inventory divergence. Provenance is informational and explicitly unsigned/unattested.

Public-history privacy is enforced before push and in a least-privilege GitHub Actions job. The versioned policy scans reachable commits, commit messages, author and committer identities, unique historical blobs, and every tracked or untracked non-ignored working-tree file for private-network endpoints, machine-specific user paths and SSH command targets, key material, fingerprints, credential-bearing URLs, and likely secrets. GitHub noreply identities and narrowly enumerated hostile-test pattern sources are admitted; ignored recovery evidence and unreachable Git objects remain local and must never be tracked.

The lightweight pack validator uses the same Git-bounded tracked and
non-ignored file inventory instead of recursively walking ignored development
artifacts. It rejects symbolic links and junctions before reading candidate
text while allowing ordinary OneDrive cloud-file metadata. This prevents
inaccessible or unusually large ignored evidence from producing environment-
specific validation failures without weakening pending-file scans.

Task composition is simulation-only. Its admitted planner accepts only registered UI-ready read-only workflows, bounded acyclic dependencies, exact fields, exact metadata-only intermediate records, and engine-consistent fresh/retry/cancel identity. It accepts no renderer arguments or approval grants and cannot create a process, access a filesystem or network, execute a workflow, or modify a machine. A separate inactive execution-admission simulator can validate exact effect disclosure, typed intermediate metadata, digest-bound approval scope, expiry/replay state, and retry/recovery/cancellation consistency for future workflows. It accepts no token secret and never issues, consumes, or accepts an approval for execution. An additional digest-chain simulator binds non-authoritative execution, effect, completion, failure, and cancellation claims to the exact admission and approval identifiers. It rejects reordering, forged completion, cross-admission reuse, unsafe retry, and uncertain recovery but writes no journal and proves no effect. Possible prior effects block recovery; every runtime effect and `ExecutionAllowed` remain false.

The Milestone 27 retrieval engine is offline, deterministic, and memory-only.
It accepts only already validated text records, rejects paths and budget
violations, treats embedded instructions as inert content, discloses selected
source offsets, and clears state on removal, failure, and shutdown. It has no
runtime route, UI control, provider payload, parser, network, process, or
persistent-index authority. Conversation storage remains inactive. Its reviewed
key architecture forbids plaintext, embedded, machine-derived, and
beside-database key fallbacks; an unavailable or locked current-user OS
credential facility must fail closed to write-free Private session.

The Milestone 22 admission-readiness ledger is also non-authoritative for
promotion. It records exact remaining blockers and validates repository-local
evidence references, but every authority flag is fixed false. It rejects any
attempt to admit Tauri/Rust, signing, notarization, publication, online update
activation, production readiness, or machine effects. It also prevents future
promotion work from blocking or weakening the existing unsigned development
package.

The prepared GitHub build-provenance job is isolated from pull-request builds
and runs only after all three native package jobs succeed on a push to `main`.
It revalidates exactly three same-run unsigned artifact sets and attests only
the archive subjects. Its job-scoped OIDC, attestation, and artifact-metadata
write permissions do not include contents, packages, releases, pull requests,
or administration writes. An attestation is not Windows code signing, Apple
Developer ID signing, notarization, updater authorization, or production
readiness.

The future Windows signing policy is public but inactive. It restricts any
eventual request to the project-owned `haven42.exe` at one immutable digest,
requires a fresh manual approval, excludes pull requests and upstream
executables/libraries, and forbids exporting a signing key into GitHub,
artifacts, or maintainer machines. Windows development builds now fail if
their deterministic Haven 42 product/version metadata is absent or mismatched.
The SignPath readiness audit remains blocked by the missing existing public
Release, provider acceptance and signing-service MFA, and exact packaged
dependency/license review. Repository-account MFA was owner-confirmed on
2026-07-27. No certificate or signing workflow is active.

Portable supply-chain evidence now classifies every archived file into an
exact project or runtime component group. Unknown files, unsafe paths,
duplicate records, invalid hashes, incomplete coverage, SBOM divergence, and
missing runtime notice markers fail closed. Every upstream group is explicitly
ineligible for Haven 42 signing, while runtime redistribution clearance and
production promotion remain false. CPython 3.14.6, Apache 2.0, and exact
libffi 3.4.4 license texts are hash-verified artifact evidence. Windows
libffi/OpenSSL source and version provenance is recorded. The builder now
constrains Windows dependency search paths and the classifier rejects
host-derived API-set/UCRT files after a stale local build was found to contain
39 DLLs from an unrelated JDK. The two retained Visual C++ runtime DLLs match
the official Python.org distribution. A clean 31-file local rebuild passes
artifact and native package verification; applicable Microsoft redistribution
terms and clean hosted reproduction remain blocked.

Hosted package jobs use versioned runner labels and accept only the exact
reviewed Python 3.14.6 archive identity for their platform. A missing,
cross-platform, or mutated archive name/digest fails before evidence
generation. Local builds are never reported as hosted-source verified.

New development-only data boundaries remain outside the application. The
conversation-history validator accepts no user content or caller database
path, uses a fixed parameterized SQLite schema only in a fresh temporary
directory, verifies backup/restore and cascade deletion, and fails unless all
database and journal files are removed. The folder inspector returns no
content or absolute path, reads verified regular-file descriptors, detects
changes during read, and rejects recursion without explicit choice, links,
reparse points, hidden and unsupported entries, invalid UTF-8, executable or
archive signatures, binary content, and every resource overrun.

The controlled research query adapter is disabled and has no native transport.
It revalidates the complete fixed-host request, rejects credential-like or
active query content, accepts only finite bounded JSON with exact fields, and
derives inactive citation destinations from numeric identifiers. Live network,
DNS, proxy inheritance, redirects, cookies, credentials, page retrieval,
model tools, UI, persistence, and follow-up remain false. Self-hosted and
multi-query contracts cannot weaken SSRF or citation controls.

Approved public-repository inspection uses ignored bare object stores only.
It rejects checkout-only objects, symlinks, submodules, alternates, reparse
points, config includes, unsafe repository config, replacement objects,
mutable commits, license mismatches, and resource overruns. Lazy network fetch
is disabled during validation, and no target hook, package, build, test, or
source file executes. Passing static inspection cannot promote Aider,
OpenCode, a model, or real-project write access.

The package dependency admission test cross-checks every exact build version,
SHA-256 lock, license expression, and platform marker across the requirements
file, builder inventory, contract, and least-privilege workflow. npm, Cargo,
Tauri, installers, signing, updater activation, release publication, and
production redistribution remain outside that development-only admission.

External provider engines, models, accelerator runtimes, drivers, installers,
and updater payloads are outside the Haven package trust boundary. Haven may
connect only through an admitted endpoint contract to separately acquired
software. Discovery, compatibility evidence, and license audits grant no
download, installation, update, execution, or redistribution authority.

## Windows Alpha setup security boundary

The Alpha text API accepts only `general.chat`, `content.write`, and
`content.summarize`. Images, software workflows, research, and unknown
capability identifiers remain server-blocked regardless of renderer state.
Writing and summarization use the same message, attachment, size, provider,
and memory-only boundaries as chat, with separate server-owned prompts and
typed Markdown results.

Active text generation uses a fresh 128-bit browser request identifier only
for cancellation correlation. The same-origin, CSRF-protected loopback cancel
route accepts exact lowercase hexadecimal identifiers and can affect only the
single request currently tracked by the engine. It sets an in-memory event,
closes the bounded no-proxy/no-redirect Ollama response stream, and unloads the
active model. It exposes no PID, signal, shell, arbitrary process, or stale
request authority, and cancellation restores the prompt without retaining the
partial response.

The managed Alpha state root is the fixed `Haven42-Data` directory beside the
packaged executable, not a caller-controlled environment variable or renderer
path. Hardware selection measures free space on that same portable volume, and
execution rechecks the exact conservative byte requirement before network or
process effects.

The sanitized diagnostic root is the separate fixed sibling directory
`Haven42-Logs`. It accepts only allowlisted event categories, stable codes,
outcomes, timestamps, random references, and the application version; its API
cannot accept arbitrary caller details. Files rotate at fixed bounds, malformed
or linked content fails closed, and reports are created locally only after an
explicit action. Managed-component removal has authority only over validated
marker-owned `Haven42-Data` roots and preserves `Haven42-Logs`. Removing logs
requires a separate confirmation and disables logging for the rest of that
process so shutdown cannot recreate the directory.

The `0.4.0-alpha.1` candidate does not bundle or invoke an Ollama installer.
After an explicit, effect-bound, single-use approval it may download only exact
registered standalone archives over HTTPS, enforce byte length and SHA-256,
reject traversal, links, devices, case collisions, excessive members and
expanded size, then require a valid Ollama Authenticode signer. A content-hash
inventory is generated from the verified extraction and must match before a
managed runtime is reused. It writes only inside the marker-owned portable data
directory and starts `ollama.exe serve` at the fixed loopback endpoint it owns.
Cancellation and any worker failure close only that managed process tree;
model-pull reads use a bounded inactivity timeout rather than waiting
indefinitely.
On later launches, the presence of `Haven42-Data` alone grants no process
authority. Automatic local reconnection requires a valid bounded completion
receipt and fresh verification of the hardware-derived registered plan,
runtime content inventory, Authenticode publisher, exact model manifest,
managed directories, and fixed loopback endpoint. Resume neither downloads nor
installs anything. Any mismatch leaves onboarding visible and stops a process
that could not be connected safely.
On Windows the managed runtime starts suspended, is assigned to a non-inherited
Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, and is resumed only after
assignment succeeds. Windows therefore closes the managed runtime and its
descendants when Haven exits normally, crashes, or is force-terminated. An
external provider is never assigned to this job and remains outside Haven's
process-control authority.
Removal requires an explicit same-origin request and audits the marker-owned
tree before deleting it. On Windows, it enumerates process image paths and
stops only processes whose executable resolves beneath that validated tree,
including orphaned provider children left by an interrupted run. It audits the
tree again before deletion. Links, reparse points, special files, unrecognized
ownership, and excessive entry counts fail closed.
The running application never attempts to delete itself.
Pre-release legacy Local AppData cleanup is admitted only through the same
explicit removal action and only after validating its fixed known-folder path,
Alpha receipt, registered identifiers, bounded layout, and link-free tree.
Drivers, updates, firmware, services, firewall, certificate trust, elevation,
and system runtimes are unconditionally outside its authority.

## Reporting A Vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting for `hysel/haven-42` so reports, proof-of-concept details, credentials, private endpoints, and affected artifacts remain private.

Include the affected commit or release, operating system, entry point, required privileges, impact, reproduction steps, and whether secrets or user data may have been exposed. Remove real credentials, private prompts, repository content, and machine identity from attachments.

## Response Targets

- Acknowledge a credible report within 3 business days.
- Triage severity and affected supported surfaces within 7 business days.
- Immediately block release or runtime promotion when exploitation may affect credentials, arbitrary code execution, update integrity, path-grant escape, or user-data deletion.
- Coordinate a patch and advisory before public disclosure. Timing depends on severity and the safety of available mitigations.

No bounty is currently offered. Good-faith research that avoids privacy violations, persistence, service disruption, social engineering, and access beyond the reporter's own systems is welcome.

## Release And Incident Handling

Security fixes use a new commit and release tag; published tags are not rewritten. A compromised release, signing identity, dependency, model artifact, or provider profile is blocked, documented, and superseded. Required response actions include revoking affected credentials or signing material, disabling automatic acquisition, preserving sanitized evidence, publishing an advisory, and validating a new immutable artifact through the normal promotion gates.

Never send secrets through issue comments, logs, test fixtures, or committed evidence.

Repository governance is fail-closed and recorded in
`config/github-repository-policy.json`. `main` requires the complete
cross-platform validation/package gate plus CodeQL, full-SHA GitHub-owned
Actions, read-only default workflow permissions, linear history, conversation
resolution, and administrator enforcement. See
`docs/github-repository-policy.md`.
