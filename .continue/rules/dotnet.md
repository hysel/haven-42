---
name: .NET Engineering
globs: ["**/*.cs", "**/*.fs", "**/*.vb", "**/*.csproj", "**/*.fsproj", "**/*.vbproj", "**/*.sln", "**/*.slnx", "**/*.props", "**/*.targets"]
---

## Scope

Apply these standards to .NET application, library, and service code.

## Required Practices

- Prefer clear domain and application code over framework-heavy implementation.
- Use dependency injection for infrastructure dependencies.
- Keep public APIs intentional and stable.
- Use async APIs for I/O-bound operations.
- Pass `CancellationToken` through async call chains where appropriate.
- Prefer nullable reference type correctness over defensive noise.
- Keep exception handling purposeful; do not swallow exceptions silently.
- Use options binding and validation for configuration.
- Prefer structured logging over string-concatenated logs.
- Keep tests close to observable behavior.
- For legacy .NET Framework, desktop, add-in, or custom MSBuild projects, preserve project-system and package-management behavior unless migration risk is explicitly assessed.
- Treat PackageReference migration, SDK-style conversion, and custom MSBuild target changes as separate decisions.

## Avoid

- Static service locators.
- Hidden global state.
- Fire-and-forget tasks in request or service flows.
- Blocking on async code with `.Result` or `.Wait()`.
- Leaking persistence models into domain or API contracts by default.
- Recommending SDK-style conversion, project-file renames, or package-management migration as mechanical cleanup without validating custom targets, generated artifacts, packaging, and runtime loading.
- Providing full project-file rewrites for legacy project migrations when the task only asks for a plan.
- Providing complete PackageReference XML replacement blocks when the task asks for a migration plan rather than implementation.
- Deleting `packages.config` before proving restore, build, package output, and runtime loading behavior.

## Review Checklist

- Are dependencies injected at the boundary?
- Are async and cancellation handled consistently?
- Are configuration, logging, and errors production-safe?
- Are tests covering meaningful behavior?
- Do package or project-system changes preserve restore, build, packaging, and runtime loading behavior?
- Are project-system migration assumptions proven by tool support or marked as assumptions?
- Have package build assets, native assets, analyzers, custom targets, and hint paths been inventoried before migration?
## Evidence Gate

Apply this rule only when inspected files or supplied context provide matching .NET evidence, such as `.sln`, `.slnx`, `.csproj`, `.fsproj`, `.vbproj`, `Directory.Build.*`, `packages.config`, `global.json`, `Program.cs`, `Startup.cs`, `appsettings*.json`, or related .NET source files.

If .NET evidence is absent or unreadable, keep recommendations language-neutral and label .NET-specific assumptions as `unconfirmed`.
