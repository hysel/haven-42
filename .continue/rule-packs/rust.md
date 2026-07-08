---
name: Rust Engineering
optional: true
---

## Scope

Use this optional rule pack only when project detection confirms Rust evidence.

Strong Rust evidence includes `Cargo.toml`, `Cargo.lock`, `src/main.rs`, `src/lib.rs`, `crates/`, `benches/`, `examples/`, or inspected Rust source and test files.

If Rust evidence is absent or unreadable, do not apply this rule pack. Keep recommendations language-neutral and mark Rust, Cargo, async runtime, crate layout, and test assumptions as `unconfirmed`.

## Required Practices

- Read `Cargo.toml` before naming crates, features, editions, binaries, workspaces, or test commands.
- Preserve workspace and crate boundaries unless the requested change explicitly includes restructuring.
- Keep ownership, borrowing, lifetimes, and error types understandable at module boundaries.
- Prefer explicit error propagation and domain-specific error types where the project already uses them.
- Match async guidance to inspected runtime evidence such as Tokio, async-std, Axum, Actix, Tonic, or none.
- Treat file paths, deserialization, FFI, unsafe blocks, subprocess calls, network input, and database values as validation boundaries.
- Keep tests deterministic with unit tests, integration tests, fixtures, or property tests only when matching project conventions exist.

## Avoid

- Recommending Tokio, Axum, Actix, Serde, SQLx, anyhow, thiserror, clap, or tracing without repository evidence.
- Adding `unsafe` unless there is no safe alternative and the invariants are documented and tested.
- Overusing cloning, global mutable state, or broad trait abstractions before there is a clear need.
- Treating `cargo check` as full validation when runtime behavior, feature flags, or integration boundaries changed.
- Rewriting modules to an idealized Rust layout without a concrete migration reason.

## Review Checklist

- Which files prove this is a Rust project?
- Which edition, workspace layout, crate type, feature flags, and test approach are confirmed versus `unconfirmed`?
- Are ownership, errors, async runtime usage, and resource lifecycles clear?
- Are unsafe, FFI, file, serialization, network, and database boundaries reviewed?
- Do build and test recommendations match inspected Cargo metadata?
