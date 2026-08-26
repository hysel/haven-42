# Retrieval Expansion Foundations

Status: local research and architecture only; inactive and download-free.

The current baseline is bounded, deterministic, memory-only lexical retrieval.
It rejects exact duplicate UTF-8 content, discloses source/chunk accounting, and
removes retained context after failure, removal, provider changes, task
boundaries, or shutdown. Retrieval results remain untrusted data and cannot
invoke a provider, process, filesystem, or network.

Three small embedding candidates are recorded for later comparison. None is
selected or downloaded. Their licenses, approximate parameter/artifact sizes,
prospective runtimes, and missing immutable or native evidence are explicit in
`config/embedding-candidate-evaluation.json`. Selection requires exact artifact
digests, dependency/SBOM/notices review, explicit consent, capacity checks,
native measurements, quality comparison with the lexical baseline, cleanup,
and source/package parity.

The persistent knowledge-library design remains separate and inactive. It
requires an admitted full-database encryption engine, a current-user OS
credential store, per-user permissions, atomic migrations with rollback,
read-only corruption recovery, encrypted backup/restore, complete deletion,
version-bound indexes, and an explicit uninstall choice. It forbids plaintext
fallback, caller-selected paths, shared or network locations, live file
references, automatic reset, and silent overwrite. No database, key, index,
route, UI control, provider payload, or package component is authorized.
