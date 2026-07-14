---
name: Go Engineering
optional: true
globs: ["**/*.go", "**/go.mod", "**/go.sum"]
---

## Scope

Use this optional rule pack only when project detection confirms Go evidence.

Strong Go evidence includes `go.mod`, `go.sum`, `*.go` files, `cmd/`, `internal/`, `pkg/`, or inspected Go tests such as `*_test.go`.

If Go evidence is absent or unreadable, do not apply this rule pack. Keep recommendations language-neutral and mark Go module, framework, command, and test assumptions as `unconfirmed`.

## Required Practices

- Read `go.mod` before naming module paths, Go versions, dependencies, or framework assumptions.
- Preserve existing package layout, especially `cmd/`, `internal/`, and API boundary packages.
- Keep exported APIs small and documented when they are part of the repository's public surface.
- Pass `context.Context` through request, database, network, and long-running operation boundaries where the project already uses it.
- Handle errors explicitly with useful context while preserving sentinel or typed error behavior where present.
- Match tests to inspected Go conventions and commands. Prefer deterministic `go test ./...` guidance only when Go module evidence exists.
- Treat file paths, HTTP input, environment variables, JSON/YAML, SQL, subprocess calls, and concurrency channels as validation and failure boundaries.

## Avoid

- Recommending Gin, Echo, Fiber, Cobra, GORM, sqlx, Wire, or other libraries without repository evidence.
- Introducing goroutines without cancellation, ownership, and error propagation.
- Using package-level mutable state for configuration or clients unless the project already owns that lifecycle.
- Hiding errors with blank identifiers or string-only checks when typed behavior exists.
- Adding broad abstractions before package boundaries or interfaces demonstrate real pressure.

## Review Checklist

- Which files prove this is a Go project?
- Which module path, Go version, package layout, and test approach are confirmed versus `unconfirmed`?
- Are context cancellation, error propagation, and resource cleanup handled?
- Are concurrency, I/O, serialization, HTTP, and database boundaries validated?
- Do build and test recommendations match inspected module metadata?
