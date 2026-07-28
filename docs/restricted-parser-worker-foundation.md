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

The hostile suite is deliberately metadata-only. A later parser review must
add pinned dependency identity, license and vulnerability evidence, native
packaging, a genuinely isolated worker, cancellation and forced termination,
malformed real documents, residue-free cleanup, and source/package parity
before one format can move beyond `candidate-blocked`.
