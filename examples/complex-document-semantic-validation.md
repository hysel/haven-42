# Complex-Document Semantic Review Evidence

Date: 2026-07-30

This is sanitized source-form review evidence. It does not admit Office or
OpenDocument uploads, dependencies, workers, routes, provider payloads, package
components, or release artifacts.

## Review boundary

The standard-library prototype first requires the existing bounded ZIP/XML
container inspection to pass. It never extracts an archive to disk. It then
reads only fixed semantic XML parts from in-memory synthetic containers:

- DOCX body paragraphs, table cells, headers, footers, and comments with
  part-specific provenance. Tracked changes are rejected rather than
  interpreted.
- XLSX inline strings, shared strings, and literal cell values with
  worksheet/cell provenance.
- PPTX shape text and speaker notes with slide-or-note provenance.
- ODT/ODS/ODP paragraph or heading text with document-content provenance.

Formulas and cached formula values are rejected. Macros, external
relationships, embedded objects, encrypted containers, DTDs/entities, unsafe
member names, unsupported compression, and expansion abuse are rejected by the
container gate before semantics. Selected XML parts, depth, segment count,
segment length, and total output all have fixed ceilings.

## Deterministic evidence

- 17 semantic fixtures: six baseline examples, three richer provenance
  examples, and eight hostile formula, tracked-change, shared-string,
  part-count, or segment-count cases.
- 57 semantic security and exclusion checks.
- Existing 16-container corpus and 41 container-security checks.
- Windows x86_64/Python 3.14.6 source orchestration: passed.
- Ubuntu Linux x86_64/Python 3.14.4 source orchestration: passed.
- macOS source: not run.
- Windows, Linux, and macOS packaged cells: not run and explicitly false.

The ignored native evidence contains no hostname, username, network address,
absolute path, or raw document text.

## Dependency research

`python-docx`, `openpyxl`, `python-pptx`, and `odfpy` remain unselected review
candidates. Their additional XML, image, and helper dependency surfaces require
separate exact-artifact, license, vulnerability, package, and containment
review. The current prototype uses no third-party complex-document dependency.

## Remaining gate

The prototype is reachable only as a test library. Charts, drawings, style
semantics, worksheet names/ordering, relationship-aware slide ordering, comment
thread semantics, and change interpretation remain incomplete. A separate
33-check parity contract proves that the current Windows and Ubuntu source
evidence does not admit any package cell. Runtime admission requires a
separately approved worker boundary, hostile non-synthetic evidence,
source/package parity, and native packaged evidence on every supported OS.
