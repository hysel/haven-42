# Restricted Parser-Worker Foundation

Milestone 27 does not admit PDF or Office parsing yet.
`config/restricted-parser-worker-contract.json` and
`scripts/evaluate-parser-worker-admission.py` define the default-deny boundary
that a future parser dependency and isolated worker must pass first.

The evaluator reads only JSON metadata fixtures. It never opens the proposed
document, imports a parser, expands an archive, starts a worker, reads a
filesystem path, contacts a network, writes a temporary file, or grants runtime
authority. PDF, DOCX, PPTX, and XLSX remain candidate formats with zero admitted
parser dependencies.

## PDF dependency review

`config/pdf-parser-candidate-review.json` records `pypdf` 6.14.2 as the
preferred candidate for a later restricted text-only PDF gate. It is not an
admitted dependency. The exact universal wheel, embedded metadata, and license
text were verified and digest-locked in
`config/pdf-parser-artifact-lock.json`, but the wheel is not retained in the
repository and no package install, parser import, document open, worker, route,
or UI control is allowed. A 10-case hostile artifact suite rejects renamed or
digest-tampered wheels, traversal/absolute/drive/backslash names, native
binaries, excessive entries, and excessive per-entry expansion. The verifier
checks a fixed size ceiling before reading and hashes the wheel in bounded
chunks.

`config/pdf-parser-hostile-corpus.json` and
`scripts/create-pdf-parser-review-fixtures.py` add a deterministic 14-file
synthetic PDF corpus under the ignored local-review directory. The files cover
a safe control plus encryption, JavaScript, open/launch/submit actions,
embedded and associated files, external references, malformed cross-reference
and EOF structures, excessive page metadata, compressed expansion, and
recursive objects. A 78-check suite locks every byte digest, marker, category,
and size; refuses symlink or mixed-directory writes; and proves the generator
imports no parser, network, or process API.

## Offline restricted-worker prototype

`config/pdf-parser-worker-prototype-contract.json`,
`scripts/restricted-pdf-worker.py`, and
`scripts/run-restricted-pdf-worker.py` now exercise the exact ignored wheel
against that synthetic corpus for security review only. The parent accepts only
the fixed fixture names and locked digests, reads the selected fixture itself,
and sends bounded base64 over standard input; no path crosses into the child.
The child uses Python `-I -S`, strict PDF parsing, bounded JSON output, and
fail-closed checks for classic cross-reference integrity, encryption, active
actions, embedded or associated content, external references, page/object/
depth/expansion/output budgets, and recursive objects.

After the exact artifact is verified and imported, Python network, process,
filesystem, and temporary-file APIs are denied. POSIX workers require CPU,
address-space, file-size, descriptor, and process resource ceilings. Windows
workers are created suspended, assigned to a transient Job Object with CPU,
memory, single-process, and kill-on-close limits, and resumed only after the
assignment succeeds. The parent independently applies a wall timeout, bounded
stdout/stderr, forced termination, and residue checks. These controls reduce
risk but do not constitute a production-grade operating-system sandbox.

On 2026-07-30, the Windows x86_64/Python 3.14.6 review cell passed 61 security
checks across all 14 synthetic PDFs plus 64 static fail-closed contract checks.
The safe control extracted its expected text; hostile cases were rejected for
encryption, active actions, embedded content, external references, malformed
structure, resource expansion, or recursion. See
`examples/restricted-pdf-worker-validation.md`.

`config/pdf-parser-prospective-package-evidence.json` describes the exact
future dependency-inventory, third-party-notice, and CycloneDX component
records. A deterministic generator created all three only beneath the ignored
local-review directory and passed 10 non-admission checks. The committed plan's
package-generation and package-authority flags remain false.
The wheel remains ignored, uninstalled, absent from repository dependencies,
and unavailable to the application, package, installer, updater, or UI.

The review parks PyMuPDF because its AGPL-or-commercial licensing and bundled
native MuPDF wheels increase licensing, supply-chain, and per-platform
packaging complexity. It also parks `pdfminer.six`: although the reviewed
current release includes the fix, its recent unsafe-pickle CMap advisory
requires a higher security-review bar before reconsideration.

Before `pypdf` can be admitted, inventory, notices, and SBOM evidence must be
generated into the candidate package; optional and conditional dependencies
must remain excluded or separately locked; non-synthetic hostile-corpus review
must complement the deterministic corpus; and source/package parity plus native
Windows, Linux, and macOS package smoke tests must pass. Production-grade
worker isolation remains a separate admission decision. OCR and PDF rendering
remain separate unadmitted capabilities.

Candidate metadata is rejected for:

- raw paths, URLs, commands, arguments, environment values, credentials,
  secrets, or tokens;
- unsupported or mismatched formats and media types;
- excessive input, object, nesting, expanded-size, expansion-ratio, memory,
  CPU, wall-time, or output budgets;
- encryption, active content, macros, external relationships, or embedded
  objects;
- renderer/model path claims;
- non-exact network, filesystem, or child-process denial limits; and
- any parser dependency not explicitly admitted by a future reviewed contract.

The original admission suite remains deliberately metadata-only and now has 27
cases after adding `.odt`, `.ods`, and `.odp` beside the Office Open XML
candidates. The
separate worker prototype adds exact candidate execution against synthetic
documents without changing the runtime decision. Native packaging, stronger OS
isolation, non-synthetic hostile review, generated package compliance evidence,
and source/package parity still must pass before PDF can move beyond
`candidate-blocked`.

## Office and OpenDocument position

The machine-readable boundary lists `.docx`, `.xlsx`, `.pptx`, `.odt`, `.ods`,
and `.odp` only so their identities and media types fail closed consistently.
No Office or OpenDocument parser has been selected or imported. These formats
remain unavailable in the picker, runtime, package, and provider payload.
Future work must review Open XML and OpenDocument independently, even though
both use ZIP/XML containers. It must reject macros, external relationships,
embedded/OLE objects, formulas as executable instructions, unsafe or duplicate
archive members, traversal, encryption, excessive parts or expansion, and
unsupported presentation semantics without launching Microsoft Office,
LibreOffice, OpenOffice, or an OS-associated application.

The next offline foundation now uses
`config/complex-document-container-review.json` and a deterministic 16-file
ignored synthetic corpus. A bounded standard-library ZIP/XML inspector passed
41 security checks covering traversal, duplicates, ZIP symlinks, encryption
flags, unsupported compression and expansion, macros, ActiveX, external
relationships, embedded objects, malformed XML, DTD/entities, OpenDocument
external links, and mimetype confusion. It never extracts an archive, accepts
a path, launches an office application, imports a third-party document parser,
or returns document text. Runtime, UI, provider, dependency, worker, and package
authority remain false. See
`examples/complex-document-container-validation.md`.

## Native PDF review lane

`scripts/run-native-pdf-worker-validation.py` and the Linux wrapper provide one
bounded source-form review command. The runner refuses platform mismatch,
requires the exact ignored wheel digest, verifies POSIX resource-limit
availability on Linux/macOS, runs the six fixed review suites with isolated
Python and a minimal environment, and writes only sanitized ignored JSON.
Its 33-check bounded offline contract records Windows and Ubuntu Linux source
evidence only after native execution and keeps macOS source, every packaged
cell, and source/package promotion false.

The Windows x86_64/Python 3.14.6 and Ubuntu Linux x86_64/Python 3.14.4
orchestration cells passed locally. macOS remains pending physical hardware.
No platform result is inferred from `--describe`, a container, WSL, or another
operating system.

The non-synthetic corpus intake policy currently accepts zero artifacts. It
requires immutable HTTPS identity, pre-open SHA-256, explicit redistribution
permission, privacy and malware review, bounded category assignment, and manual
retention. Automatic download, automatic retention, and intake-time parser
execution are denied.

The production-isolation assessment keeps successful source review separate
from arbitrary-document admission. Windows still lacks a restricted-token or
AppContainer-equivalent capability boundary; Linux lacks admitted
namespace/seccomp/Landlock-equivalent controls; macOS lacks physical evidence
and an admitted sandbox. The source/package parity contract therefore records
only Windows and Ubuntu Linux source cells as true and keeps macOS source and
all packaged cells false. A 32-check pure OS-isolation evidence gate now
requires five exact controls per platform, enforcement and hostile-escape
tests, and exact parity without granting runtime authority or allowing a
fallback.

Office/OpenDocument semantic review remains behind the container gate and uses
only the standard library. Seventeen deterministic fixtures cover all six
candidate formats, richer DOCX/XLSX/PPTX provenance, formulas, tracked changes,
invalid shared strings, and part/text budget failures. Fifty-seven semantic
checks passed on Windows and Ubuntu Linux. A separate 33-check parity contract
keeps every packaged cell false, so no dependency, worker, route, provider
payload, UI, package component, user-document parsing, or unsupported fidelity
claim is admitted.
