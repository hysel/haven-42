---
name: TypeScript Engineering
optional: true
globs: ["**/*.js", "**/*.jsx", "**/*.mjs", "**/*.cjs", "**/*.ts", "**/*.tsx", "**/package.json", "**/tsconfig*.json"]
---

## Scope

Use this optional rule pack only when project detection confirms JavaScript or TypeScript evidence.

Strong JavaScript or TypeScript evidence includes `package.json`, lock files, `tsconfig.json`, `vite.config.*`, `webpack.config.*`, `next.config.*`, source files such as `*.ts` or `*.tsx`, or inspected test files such as `*.test.ts`, `*.spec.ts`, or Playwright tests.

If JavaScript or TypeScript evidence is absent or unreadable, do not apply this rule pack. Keep recommendations language-neutral and mark frontend, Node, package-manager, and test-runner assumptions as `unconfirmed`.

## Required Practices

- Read `package.json` before naming scripts, dependencies, frameworks, package managers, or test runners.
- Preserve the repository's package manager and lockfile strategy unless migration is explicitly requested.
- Keep browser, server, shared, and test code separated according to existing project boundaries.
- Validate external input at API, form, command, file, and serialization boundaries.
- Prefer typed interfaces at boundaries where the project already uses TypeScript.
- Keep asynchronous behavior explicit; avoid hidden fire-and-forget work unless the framework owns the lifecycle.
- Match test commands to inspected scripts and dependencies. Use Vitest, Jest, Playwright, Cypress, Node's test runner, or framework commands only when evidence supports them.
- For frontend projects, consider accessibility, state management, loading, error, and empty states when the change touches user-facing behavior.

## Avoid

- Recommending React, Vite, Next.js, Vue, Svelte, Jest, Vitest, Playwright, Cypress, npm, pnpm, or yarn without repository evidence.
- Replacing the package manager or lockfile because of preference alone.
- Treating TypeScript compile success as full runtime validation.
- Adding broad snapshots or brittle DOM assertions when behavior-focused tests are practical.
- Assuming browser code, Node services, and full-stack frameworks have the same architecture or security boundaries.

## Review Checklist

- Which files prove this is a JavaScript or TypeScript project?
- Which framework, package manager, build tool, and test runner are confirmed versus `unconfirmed`?
- Are dependency, script, and lockfile recommendations grounded in `package.json` and lock files?
- Are UI states, API boundaries, async behavior, and input validation covered where relevant?
- Do test recommendations match inspected project tooling?
