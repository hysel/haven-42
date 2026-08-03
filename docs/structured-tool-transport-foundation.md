# Structured Tool Transport Foundation

## Status

Haven 42 has an offline, effect-free parser for future structured model tool
calls. It is not imported by the application, included in a package, connected
to a provider, or authorized to execute a tool.

The foundation exists to make malformed or hostile provider output fail closed
before any future runtime integration is considered.

## Supported candidate shapes

The parser recognizes only two exact, review-only response shapes:

- an Ollama assistant message containing one structured function call; and
- an OpenAI-compatible assistant choice containing one identified function
  call whose arguments are strict JSON.

This is transport-shape compatibility, not provider admission. No network
request is made by the parser or its tests.

## Security boundary

Every candidate call must satisfy all of these conditions:

- exactly one call and no mixed assistant prose;
- a bounded tool name present in a trusted caller-owned registry;
- only known argument fields with all required fields present;
- exact scalar types for the current minimal schema;
- bounded encoded size, string length, nesting depth, and node count;
- no duplicate JSON keys, non-finite numbers, cycles, NUL-bearing strings, or
  prototype-related object keys; and
- an exact supported transport shape with no ignored extra fields.

Successful normalization still returns `executionAllowed: false`,
`approvalGranted: false`, and `runtimeAdmissionGranted: false`. Arguments remain
untrusted data. The module has no filesystem, process, network, provider, or
tool-execution API.

## Evidence

Run:

```text
python scripts/test-structured-tool-transport.py
```

The deterministic suite covers both candidate shapes and hostile unknown tools,
parallel calls, mixed content, duplicate keys, invalid JSON values, wrong
types, unknown or missing arguments, dangerous keys, oversized strings, cyclic
objects, and unsupported transports. Static checks also keep the module out of
the product runtime and restrict its imports to JSON and regular-expression
processing.

WSL2 may run this effect-free suite as preliminary cross-environment evidence,
but WSL2 is not native Linux evidence and cannot satisfy a native package or
operating-system isolation gate.

## Promotion blockers

Runtime work remains blocked until a separate design and review defines:

- an engine-owned immutable tool registry and versioned schemas;
- provider-specific streaming and cancellation behavior;
- user-visible intent, argument, destination, and effect disclosure;
- scoped approval receipts bound to the exact call and lifecycle;
- result transport, replay prevention, timeout, retry, and cleanup semantics;
- native hostile tests and source-versus-package parity; and
- an execution broker that remains distinct from model and renderer authority.

This foundation does not weaken the existing rule that a model cannot approve
or execute its own requested action.
