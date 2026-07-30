# Complex-Document Container Review Validation

Date: 2026-07-30

This is offline synthetic security evidence for future Office Open XML and
OpenDocument work. It is not parser, upload, runtime, UI, provider, or package
admission.

The deterministic review corpus contains 16 ignored ZIP/XML containers:
safe `.docx` and `.odt` controls plus traversal, case-insensitive duplicate
members, macro payloads, external relationships, embedded objects, ActiveX,
ZIP symlinks, encryption flags, compression expansion, malformed XML,
DOCTYPE/entity declarations, OpenDocument external links, embedded
OpenDocument objects, and mimetype confusion.

The bounded inspector passed 41 security checks. It validates candidate format
identity, required members, OpenDocument first-member/stored mimetype rules,
entry/member/expanded/XML limits, compression methods and ratios, safe unique
member names, encryption flags, ZIP symlink metadata, macro/ActiveX/embedded
paths, well-formed XML, prohibited DTD/entities, and external relationships.
It reads bytes supplied directly by the review harness, never extracts the
archive, launches an office application, accepts a filesystem path, imports a
third-party document parser, contacts a network, executes formulas or content,
or emits extracted user text.

`.docx`, `.xlsx`, `.pptx`, `.odt`, `.ods`, and `.odp` remain candidate-blocked.
The inspector and contract are absent from the Haven 42 runtime, PyInstaller
specification, and resource-integrity manifest. Independent semantic extraction,
dependency review, worker containment, non-synthetic hostile evidence,
source/package parity, and native Windows/Linux/macOS package evidence remain
required before any format can be considered for admission.
