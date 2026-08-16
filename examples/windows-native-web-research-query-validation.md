# Native web-research query transport validation

## What was tested

On 2026-08-15, the development-only native query transport sent one explicit
three-result query to the fixed English Wikipedia metadata API from Windows.
The reviewed query was `local artificial intelligence software`; its stored
SHA-256 digest is
`2899f41a1e3a98a39b9c2ea6b5fbc70e361a03d15b90b6f0c8b3b226c76c1a47`.

The transport used the operating system trust store, resolved the fixed host
twice, rejected non-public addresses, pinned the connection to an address
present in both DNS results, preserved the fixed TLS server name and Host
header, requested identity encoding, and followed no redirects. It sent no
credentials or cookies and did not inherit proxy environment settings. The
response was accepted only as bounded JSON metadata and produced three
engine-derived, inactive citation records.

The same code passed 21 hostile offline transport checks, the fixed query
adapter passed 15 security checks, and the separate cited-synthesis boundary
passed 26 checks. No conversation, document, local path, hardware detail,
account identifier, private address, prompt, or response is stored in this
record.

## What this proves

This proves one narrow development capability: an owner-invoked command can
perform one bounded metadata query against one fixed provider while enforcing
the reviewed transport and response boundaries on this Windows source tree.

It does **not** make web research available in Haven 42. There is no runtime
route, user-interface control, model tool, page retrieval, active navigation,
automatic follow-up, persistence, or package admission. Search-result metadata
remains untrusted, and this result does not prove cited-answer correctness.

## Remaining gates

- Add a trusted, keyboard-accessible citation and destination-disclosure UI.
- Bind explicit per-query approval and cancellation to the product runtime.
- Add separately approved page retrieval only after its transport, extraction,
  and residue-cleanup gates pass.
- Complete native package parity and macOS source checks before any promotion;
  the separate native headless Linux source query now has its own evidence
  record.
