# Security Threat Model

## Assets and trust boundaries

Haven 42 protects user repositories, local files, prompts, responses, models, credentials, generated artifacts, approvals, update state, and provider endpoints. The desktop renderer and all model output are untrusted input. Native IPC, the workflow dispatcher, provider adapters, filesystem grants, packaged binaries, and update verification are separate trust boundaries.

## Principal threats

- Prompt or model output attempts to select commands, executables, arguments, paths, URLs, providers, or approvals.
- A malicious web page targets a predictable localhost port through cross-site forms, fetches, DNS rebinding, framing, or browser-content injection.
- A hostile inherited environment redirects automatic browser launch to an attacker-selected command, or a renderer supplies a non-loopback launch URL.
- A malicious or compromised renderer repeatedly triggers expensive readiness scans, supplies executable/argument/environment input, forges hardware facts or a snapshot ID, or causes raw probe output, identity, private paths, credentials, or network addresses to cross the engine boundary.
- A setup screen turns a recommendation into installation authority, injects an unregistered component, URL, command, or path, or claims that renderer consent is an OS-level approval.
- A public model search leaks local context, follows a redirect, accepts a hostile model name or command, treats catalog claims as evidence, or turns desired selection into download or execution authority.
- A future research search leaks conversation or file context, lets the model choose a destination, reaches a private service through SSRF or DNS rebinding, follows a hostile redirect, executes page content, forges citations, or turns retrieved prompt injection into additional authority.
- A future history feature accepts renderer/model SQL or paths, stores secrets or attachment bytes, silently mixes conversations, weakens Private session, exposes unencrypted records, mishandles a migration or disk-full failure, incompletely deletes WAL/journal/backups, or restores hostile data.
- A local-web request attempts server-side request forgery through public, link-local, credential-bearing, redirected, hostname-based, or path-bearing provider endpoints.
- A completed, failed, cancelled, switched, or idle text task leaves a model resident beyond the configured bounded warm period and consumes accelerator power after Haven 42 stops using it.
- A compromised renderer sends malformed frames, replays approval tokens, crosses sessions, cancels another request, or binds events to the wrong request.
- Path traversal, symlink or reparse-point swaps, and protected-directory writes escape an approved grant.
- A provider response leaks repository data, endpoint details, process inventories, machine paths, or secrets into committed evidence.
- Model-supplied Markdown or HTML creates active markup, links, remote images, scripts, event handlers, misleading hidden content, or an accessibility-breaking document outline.
- A malicious or stale update manifest or activation journal causes downgrade, target confusion, duplicate-asset ambiguity, checksum bypass, unsigned activation, approval replay, interrupted-state confusion, unsafe retention cleanup, or user-data replacement.
- Forged GitHub release metadata points the update checker at a fork, draft, prerelease, mutable release, mismatched tag, duplicate manifest, credential-bearing URL, or unapproved asset host.
- A renderer or compromised update component forges, replays, expires, or substitutes a verifier receipt; confuses a verifier profile, trust root, release, asset, platform, or digest; or treats a structural receipt as cryptographic proof.
- A verifier-registry transition skips a version, removes every continuity anchor, backdates a candidate, uses a new or retired signer, forges a threshold claim, replays a transition, or treats rotation metadata as authorization to change the trust store.
- A future composition request broadens an approval scope, reuses a token across attempts or lifecycles, substitutes typed intermediate artifacts, retries after possible effects, or treats cancellation and uncertain recovery as execution authority.
- A future effect journal omits or reorders records, substitutes an admission binding, forges completion, records an unapproved effect, resumes after uncertain effects, or treats renderer/runtime claims as durable recovery evidence.
- Retry, resume, timeout, or crash handling repeats a write or leaves an orphan process.
- Cleanup deletes preexisting models, provider data, or user artifacts.
- A renderer forges a validated state, approval, or evidence; supplies a raw endpoint, path, credential, command, or environment; requests public binding; or reuses evidence across capability domains.

## Controls

Policy selects registered operations; prompts never grant authority. IPC is typed, size-bounded, schema-strict, session-bound, and default-deny. Filesystem access requires native canonicalization and narrow expiring grants. Writes require an approval bound to the exact operation and effects. Updates use immutable releases, exact target selection, hashes, provenance, side-by-side staging, health checks, and rollback; the current offline manifest, release-metadata, and lifecycle policies cannot use the network, download, write, stage, activate, roll back, clean, install, elevate, terminate processes, or touch user data. The lifecycle policy rejects raw paths and renderer authority, treats all evidence booleans as untrusted scenario inputs rather than proof, protects the active and previous known-good versions, and deterministically models failed health and interrupted-journal recovery. Reliability rules prevent silent write retries and unrelated process termination. Evidence is sanitized and local data deletion is explicit and ownership-aware.

The structural update-trust handoff accepts only a schema-strict, short-lived,
single-use receipt bound to an exact verifier profile and binary digest, trust
root, repository, immutable release and commit, manifest, asset, and platform.
It rejects raw signatures, certificates, transparency material, paths, URLs,
unknown fields, mismatches, expiry, and replay. The current evaluator performs
no cryptography, establishes no trust, promotes no evidence, and cannot stage or
activate a package; scenario claim booleans remain non-authoritative.

The verifier-transition simulator requires consecutive registry versions,
validity overlap and extension, exact verifier continuity, active trust-root
continuity, current-root threshold descriptions, and replay defense. It accepts
no raw keys, signatures, certificates, proofs, paths, or URLs. Authorization
claims remain non-authoritative, so no transition is accepted and no registry,
trust store, runtime verifier, package, credential, or filesystem state changes.

The future task-execution admission simulator binds a complete approval
lifecycle to an exact admission, composition, step, registered workflow,
attempt, sorted effect disclosure, and metadata-only typed artifact set. It
rejects secrets in approval descriptions, raw token material, artifact content
or paths, prohibited machine effects, cross-attempt reuse, cancellation with
approval data, unsafe retries, and uncertain recovery after possible effects.
Even a structurally valid request cannot accept an approval, execute a workflow,
or produce filesystem, process, network, service, driver, firewall, credential,
or machine effects.

The effect-journal simulator chains strict scenario records to the exact
admission scope and approval identifier. It rejects gaps, reordering, digest
substitution, cross-admission reuse, forged or incomplete completion, effects
outside scope, records after a terminal event, unsafe retry, and understated
recovery risk. Start, completion, failure, and cancellation records remain
untrusted claims: no journal is persisted, no effect is proven, and neither
retry, recovery, approval consumption, nor execution is authorized.

Onboarding settings are schema-bounded and default-deny. The renderer cannot supply state, evidence, approval, commands, raw endpoints, raw paths, or plaintext credentials. It receives and submits opaque references only; the evaluator never resolves or returns them. Existing setups require independent validation, cross-domain admission is rejected, public binding is absent, and settings outside exact passed evidence become unverified rather than inheriting trust.
The admitted local-web application binds only to `127.0.0.1`; validates the exact Host and Origin; requires a random in-memory request token; rejects cross-site fetch metadata; serves bundled assets under a restrictive Content Security Policy; accepts only bounded JSON; and classifies IP-literal provider endpoints through the shared no-redirect policy. Automatic browser launch accepts only the engine-generated IPv4-loopback HTTP origin, uses fixed platform mechanisms without a shell, ignores `BROWSER`, strips unneeded inherited Unix environment authority, and safely falls back to a printed URL. Linux supplies only fixed system-owned application data roots needed for Flatpak, Ubuntu Snap, and base-system browser discovery and rejects inherited `XDG_DATA_DIRS`, preventing a caller-controlled desktop entry from becoming launch authority. An immediate opener error or nonzero exit cannot suppress the manual fallback and advances to the next fixed Linux opener; a zero exit or process that remains active through the bounded confirmation window is required for success. It exposes no repository, generic filesystem, shell, arbitrary process, download, update, or arbitrary provider surface. Recommendation catalog loading rejects unknown fields, unsafe or duplicate model names, invalid or mismatched digests, forged capability/operation bindings, duplicate evidence IDs, traversal-like evidence paths, and evidence rows that do not exactly match committed records. Automatic text selection requires exact name, digest, and capability evidence. Provider-reported metrics use a strict nullable numeric shape and are memory-only.

Public model search is a separately disclosed outbound boundary. It accepts
only a bounded phrase after explicit opt-in, targets one fixed HTTPS origin,
rejects redirects and oversized or malformed HTML, and emits at most 20 strict
model names. The renderer revalidates the exact response shape and reconstructed
copy command. Candidate selection stays in browser memory and cannot reach text
execution until the provider's installed inventory contains that exact name.

The text server accepts only `general.chat`, `content.write`, and
`content.summarize`, each with the same bounded 20-message conversation limit.
The unified browser surface uses a narrow, local-only prefix hint to select a
writing or summarization prompt; the hint grants no authority and no text is
sent while a different-model confirmation is visible. A model change requires
an explicit user action, while keeping the current model remains available.
Software
admits only unique `uiReady`, `read-only` registry records and emits plan
artifacts without arguments or process execution. Images admit only a loopback
ComfyUI endpoint, the promoted SDXL checkpoint, a fixed built-in workflow,
bounded settings, and a capped PNG whose chunk sequence, CRCs, terminal IEND,
absence of trailing bytes, and dimensions are revalidated before delivery. The client cannot supply a model, node,
filename, provider path, or workflow graph. API history is cleared, browser
delivery is memory-only, and unavoidable provider retention is warned.

Event rendering rejects unknown fields, malformed codes, gaps, reordering,
multiple terminals, wrong terminal kinds, and events after a terminal.
Assistant text rendering accepts only a small Markdown block/inline allowlist,
creates every element directly, assigns all model text through `textContent`,
maps model headings below the page heading, and never creates model-supplied
links, images, HTML, scripts, or handlers. Hostile tags remain visible text.
Prompt recall is a bounded task-local browser-memory ring with a 20-entry
default and fixed 50/100-entry options. It stores only submitted user text,
suppresses consecutive duplicates, preserves multiline cursor behavior, and
clears on New task, a direct model/provider change, and shutdown without browser
storage or server persistence.
Advanced unverified model use emits a warning. Provider failures emit typed
errors, never retry automatically, and may restore failed text input only in
browser memory for a new request. Model residency is bounded to immediate, 5-,
15-, or 30-minute policies. Only one session text model stays active;
model/provider changes, New task, failures, idle expiry, and shutdown explicitly
unload and verify cleanup.

Readiness inspection is an explicit CSRF-protected POST with a single concurrent scan, a 15-second whole-scan deadline, three-second per-probe deadlines, and a 64 KiB hard output bound. Only fixed engine-owned probes run with `shell=False`, a minimal environment, no stdin, no network, and no renderer-provided executable or argument. Windows accelerator discovery derives a small allowlisted fact set from a fixed read-only registry location; raw registry values and paths are not returned. The server validates the exact schema and all-false effect declaration before retaining a snapshot in memory. Setup planning accepts only the current unexpired snapshot ID and one registered intent. The strict component registry cannot be extended by the renderer, every install control is disabled, and the simulation-only broker rejects commands, URLs, paths, environment, evidence, unknown fields, and renderer approval.

## Residual risk and promotion gates

Milestone 27 admits only explicit bounded UTF-8 `.txt`/`.md`/`.csv`/`.json`, a narrow `.cs`/`.py`/`.js`/`.jsx`/`.ts`/`.tsx`/`.java`/`.go`/`.rs`/`.sql`/`.tf` source-text allowlist, and browsed-or-pasted PNG screenshots. Source files are normalized to `text/plain`, receive no syntax-validation claim, and are never executed; shell, PowerShell, batch, binary, project, archive, configuration, PDF, Office Open XML, and OpenDocument formats remain blocked. Filename and browser MIME metadata are untrusted: byte preflight and independent server revalidation reject known binary/container signatures, forbidden control bytes, language-shebang mismatches, and high-confidence PowerShell/shell/batch masquerading while preserving ambiguous prose only as inert data. CSV and JSON receive browser and engine syntax/resource validation, but JSON is never evaluated and CSV formulas are never executed. The browser exposes no arbitrary path or background scan authority; the loopback engine revalidates normalized names, media types, byte counts, text and structured-content budgets, PNG signature/chunks/CRCs/dimensions/pixels, duplicates, NUL content, and provider consent. The browser-memory screenshot selector defaults to two and permits one through four without raising the engine's absolute four-image, 8-MiB combined, or 33.5-million combined decoded-pixel ceilings. All attachment content remains untrusted inert reference data and cannot add authority. The runtime exposes no attachment-driven tool, shell, process, filesystem-write, archive-expansion, or model-output execution path and makes no antivirus or perfect language-classification claim. Private-network transfer remains warned and deliberate Send confirms it; state is memory-only and no temporary file is allowed.

A 27-case metadata-only parser-worker foundation covers PDF, `.docx/.xlsx/.pptx`, and `.odt/.ods/.odp` identities while granting no dependency, worker, path, or runtime authority. A separate review-only prototype imports the exact ignored `pypdf` 6.14.2 wheel inside a bounded child and rejects 13 hostile synthetic PDFs while extracting one safe control. It accepts no document path, user document, network, child process, temporary file, runtime route, UI control, provider payload, or package authority. Windows creates the child suspended and assigns CPU, memory, one-process, and kill-on-close Job Object limits before resume; POSIX limits are required by contract. Parent streaming-output limits, wall timeout, forced termination, crash/output-flood handling, effect guards, and bounded non-traversing residue probes passed. The Windows review records 61 corpus security checks, 64 static contract checks, and 40 contract-parity/package-exclusion checks.

Three dependency-inventory, notice, and CycloneDX files are generated deterministically only beneath ignored local review. They are explicitly not package evidence and do not change the committed false generation/admission flags. The wheel remains uninstalled, unpackaged, and absent from dependencies. Windows and Ubuntu Linux source orchestration passed; macOS source, non-synthetic hostile evidence, actual package compliance integration, source/package parity, and native package smoke remain mandatory before admission. The production-isolation assessment also requires a Windows restricted-token/AppContainer-equivalent boundary, Linux namespace/seccomp/Landlock-equivalent controls, and a physical macOS sandbox evaluation. Missing controls fail closed rather than silently weakening isolation. PDF, Office, OpenDocument, archive, rendering, OCR, directory, retrieval-index, embedding, and persistent-index support do not inherit approval from this prototype.

The Office/OpenDocument container prototype adds no extraction authority. Its
41-check synthetic suite rejects traversal and ambiguous member names,
case-insensitive duplicates, ZIP symlinks, encryption, unsupported compression,
member/total/ratio abuse, macros, ActiveX, embedded objects, malformed XML,
DTD/entities, external relationships, and OpenDocument mimetype confusion
before returning metadata-only review output. It never calls `extract` or
`extractall`, accepts no path, launches no office application, executes no
formula or content, and remains absent from the runtime and package manifests.
ZIP/XML inspection alone does not establish safe semantic extraction.

The semantic review prototype remains behind that container gate. It reads
only fixed in-memory XML parts, uses no third-party parser, extracts no image or
archive member to disk, rejects formulas and cached formula values, and bounds
selected parts, XML depth, segments, segment length, and total output. Its
44-check suite across 12 synthetic DOCX/XLSX/PPTX/ODT/ODS/ODP fixtures passed
on Windows and Ubuntu Linux. Unsupported tables, shared strings, comments,
tracked changes, notes, charts, headers, footers, and ordering cannot be
silently treated as complete semantics. No route, provider payload, UI,
dependency, worker, or package authority follows from the review.

Native PDF evidence generation refuses platform mismatch and an absent,
renamed, symlinked, or digest-mismatched ignored wheel. Linux/macOS additionally
require the five configured POSIX resource-limit primitives before the worker
suite starts. The runner executes only fixed repository tests with isolated
Python, a minimal environment, no stdin, bounded time, and exact output markers.
Its sanitized evidence omits machine identity, endpoints, paths, and content.
`--describe` is a plan, not native evidence. The non-synthetic intake boundary
allows no download, retention, or parse until immutable provenance, pre-open
digest, redistribution, privacy, and malware review pass; its accepted list is
empty.

Metadata-only corpus research records source-project pages but no artifact
selection. Repository-level licenses are not assumed to cover every linked
PDF. The offline intake verifier rejects non-HTTPS or credential-bearing URLs,
mutable revisions, malformed digests, unapproved redistribution, incomplete
privacy or malware review, unknown categories, extra path fields, and
repository-retention decisions. It contains no network client and cannot open,
parse, download, or retain a candidate.

The lexical-retrieval core is offline-only and memory-only. It deterministically
chunks already validated text, ranks bounded casefolded terms, discloses every
selected source and offset plus matching, omitted, and truncation counts, and
clears on removal, failure, or shutdown. Its
contract grants no runtime route, UI, provider payload, filesystem path, parser,
network, model-ranking, embedding, temporary-file, or persistent-index
authority. Embedded commands and tool requests remain inert text.

The structured tool-transport parser remains runtime-inactive. Its Ollama
profile validates the exact complete 0.32.5 envelope, binds the response to the
requested model, requires a normal stop, rejects thinking and extra fields,
and bounds provider metrics, call identity, and function index. Exact Ollama
and OpenAI-compatible candidate shapes may be normalized only when they contain one
allowlisted call with bounded, schema-matched arguments and no mixed assistant
content. Duplicate JSON keys, unknown tools or fields, parallel calls,
prototype-related keys, non-finite values, cycles, and resource-limit failures
are rejected. Successful normalization still grants no approval, execution,
provider, package, or runtime authority; model output remains untrusted data.
A separate explicit live harness uses only a fixed synthetic prompt, performs
no download, retains no endpoint/prompt/response/argument content, and attempts
model unload after every installed-model cell. Live transport success does not
connect the parser to the product or authorize a tool.

The conversation-history contract is also simulation-only. Its logical
SQLite-compatible schema includes no executable SQL, and its planner does not
import SQLite, open or create a database, read or write a file, invoke a
provider, or expose a runtime route. Exact typed requests reject SQL, queries,
paths, filenames, URLs, endpoints, credentials, commands, environment values,
unknown fields, cross-conversation context, unvalidated summaries, schema
downgrades, attachment bytes, and unverified or active-content restores. Pure
plans model atomic upgrade/rollback, retention, bounded metadata-only context
selection, complete deletion scope, busy/locked, interrupted-write, corruption,
disk-full, backup, and restore behavior with every effect false. Private session
remains the write-free default. Standard SQLite is treated as unencrypted at
rest; runtime persistence stays blocked until encryption/key management,
least-privilege per-user storage, deletion/recovery, and native package evidence
pass separate approval.

Milestone 26 Intel inference evidence grants no runtime admission. The physical
Arc B580 review kept oneAPI, Level Zero development files, llama.cpp source and
builds, OpenVINO wheels and portable archives, models, caches, and raw logs
outside the repository and application package. Inputs were immutable or
exact-versioned and
SHA-256-inventoried; model snapshots were revision-pinned and rejected code,
executables, native extensions, pickle files, and symlinks. The first mixed
oneDNN/SYCL build crashed and was rejected. The isolated llama.cpp SYCL build
still failed 3 of 53 upstream tests. OpenVINO then passed exact Windows B580
GPU execution from a hash-verified user-local portable runtime, but its small
model missed strict output constraints on both operating systems and the Linux
host remains outside the documented support baseline. Both engines therefore
remain candidate-only with no installer, automatic download, active registry
selection, provider route, package component, service, driver change, or
silent CPU fallback. A functional GPU
result cannot override a failed security, correctness, supply-chain, quality,
cleanup, or package-parity gate.

Milestone 28 controlled web research remains proposed and unadmitted. Its
offline contracts, hostile fixtures, and caller-fixture validator cannot open a
socket, resolve DNS, fetch a URL, automate a browser, execute a page, download
content, persist state, or expose a model tool. The validator rejects
credential-like queries, unsafe URLs and IP literals, active markup, malformed
or oversized result shapes, forged citation identifiers, and incomplete source
accounting while keeping every destination inactive. Its promotion gate still
requires explicit reviewed queries, an engine-owned live adapter, DNS and
resolved-IP revalidation, redirect and content limits, no page execution,
trusted citation UI, hostile-content prompt isolation, exact source accounting,
and residue-free memory cleanup. A separate caller-bytes-only extractor rejects
non-allowlisted HTML, malformed nesting, doctypes, processing instructions,
invalid UTF-8, NULs, and resource-budget violations while retaining no
attributes or remote references. Its 26 offline checks do not add URL fetching,
transport, filesystem, runtime, UI, package, or model authority. The admitted fixed Ollama catalog search does
not grant or imply general research-search authority.

The local-web admission applies to read-only readiness inspection, zero-effect setup planning, status, exact-digest Ollama discovery and text, plan-only registered read-only software workflows, and the exact promoted Linux ComfyUI/SDXL image profile through loopback. It does not admit workflow process execution, arbitrary provider profiles, client persistence, installation, elevation, service or driver changes, updates, remote UI access, or Tauri packaging. No optional desktop runtime ships until actual Windows, Linux, and macOS binaries pass renderer, IPC, canonical-path, lifecycle, update, rollback, packaging, uninstall, privilege, and security tests. Unsupported or failed provider cells remain documentation-only and leave no executable integration.
