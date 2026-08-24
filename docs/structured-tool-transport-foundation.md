# Structured Tool Transport Foundation

## Status

Haven 42 has an offline parser for future structured model tool calls. The
application does not import it, packages do not include it, and it cannot
connect to a provider or execute a tool.

Its current job is to reject malformed or hostile provider output before any
future runtime integration is considered.

## Supported candidate shapes

The parser recognizes two exact, review-only response shapes:

- a complete, non-streaming Ollama 0.32.5 response bound to the requested
  model, a normal `stop`, bounded provider metrics, and one indexed function
  call; and
- an OpenAI-compatible assistant choice containing one identified function
  call whose arguments are strict JSON.

This checks transport shape, not provider support. Neither the parser nor its
tests makes a network request.

## Security boundary

Every candidate call must satisfy all of these conditions:

- exactly one call and no mixed assistant prose;
- for Ollama, an exact final envelope, expected-model match, normal stop,
  bounded nonnegative metrics, no thinking field, a bounded call ID, and
  function index zero;
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

The deterministic suite covers both candidate shapes plus hostile unknown
tools, parallel calls, mixed content, duplicate keys, invalid JSON values,
wrong types, unknown or missing arguments, dangerous keys, oversized strings,
cyclic objects, and unsupported transports. Static checks keep the module out
of the product runtime and limit its imports to JSON and regular-expression
processing.

An explicit manual harness can test the exact Ollama profile with a fixed
synthetic prompt and an installed-model list supplied by the operator. It
requires `--live`, validates the endpoint through the shared IP-literal and
no-redirect policy, never downloads a model, bounds every response, and
attempts to unload each tested model in a `finally` path. Its ignored local
record retains model identifiers and outcome categories only; it does not
retain the endpoint, prompt, response, or tool arguments. Four installed
tool-capable models passed the exact envelope and argument check against Ollama
0.32.5; one installed model was correctly classified as not supporting tools.
This validates transport only, not application integration or execution.

WSL2 may run this offline suite as a preliminary cross-environment check,
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
