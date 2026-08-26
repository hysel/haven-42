# Restricted PDF Worker Prototype Validation

Date: 2026-07-30

This sanitized local security-review record is not product or runtime
admission.

## Exact review cell

- Host: Windows x86_64
- Python: 3.14.6
- Candidate: `pypdf` 6.14.2 universal wheel
- Wheel SHA-256:
  `3f07891af76dc002657e04993ab9b4de81de29f9013b9761d0b7968bff12e946`
- Input: 14 deterministic synthetic PDFs from the ignored local-review corpus
- Result: 61 security checks passed across all 14 fixtures
- Static contract: 64 fail-closed checks passed
- Contract/package boundary: 40 parity and exclusion checks passed

The safe control extracted exactly `Haven 42 fixture`. The hostile cases were
rejected for encryption; JavaScript, open, launch, and submit actions; embedded
and associated files; external references; malformed cross-reference or EOF
structures; excessive page metadata; decompression expansion; and recursive
objects.

## Containment exercised

The parent supplies bounded base64 bytes over standard input and receives
bounded JSON over standard output. It never gives the child a document path.
The child starts with isolated Python flags and imports only the exact
digest-verified ignored wheel. Network, child-process, filesystem, and
temporary-file Python APIs are denied after that import.

On Windows the child is created suspended, assigned to a transient Job Object,
and resumed only after the job enforces a 512 MiB memory ceiling, a 10-second
CPU ceiling, one active process, and kill-on-close. The parent also enforces a
15-second wall deadline and streams stdout/stderr into hard bounded buffers.
Dedicated probes verified forced termination of a hung worker, immediate
termination on stdout and stderr flooding, a typed crash outcome, denied effect
APIs, and no fixture-directory residue. Residue snapshots reject links,
directories, excessive entries, and excessive bytes instead of traversing them.

POSIX resource-limit code and the same fail-closed contract are present, but
real parser execution on Linux and macOS has not yet been recorded. The
prototype does not claim OS sandboxing, container isolation, or production-
grade containment.

## Deliberately not admitted

- The wheel is ignored, uninstalled, and absent from repository dependencies.
- No user document, runtime route, UI control, provider payload, package file,
  installer, updater, or release artifact uses this worker.
- Dependency inventory, third-party notices, and CycloneDX data were generated
  deterministically only under ignored local review. None was generated into a
  package or granted package authority.
- Source-versus-package parity and native Windows, Linux, and macOS package
  smoke tests remain required before any later admission decision.
- PDF rendering, OCR, encrypted PDFs, active content, embedded content,
  external references, Office formats, and arbitrary paths remain blocked.
