# Language Rule Packs

## Purpose

Language rule packs provide ecosystem-specific guidance without making the default pack noisy or wrong for every repository.

The default `.continue/config.yaml` loads only shared engineering rules. Optional language rule packs live under `.continue/rule-packs/` and should be used only after project detection confirms matching repository evidence.

## Current Optional Packs

| Rule pack | Status | Evidence required before use |
| --- | --- | --- |
| `.continue/rule-packs/python.md` | Added, pending full validation | Python project metadata such as `pyproject.toml`, `requirements*.txt`, `setup.py`, `poetry.lock`, `Pipfile`, `pytest.ini`, `tox.ini`, or inspected Python package/source files. |
| `.continue/rule-packs/typescript.md` | Added, pending full validation | JavaScript/TypeScript metadata such as `package.json`, lock files, `tsconfig.json`, frontend/build configs, or inspected `*.ts` / `*.tsx` source and test files. |

## How Agents Should Use Them

1. Run project classification using `docs/project-detection.md`.
2. Cite the files that prove the ecosystem.
3. Use the matching optional rule pack as supplemental guidance only when evidence is high or medium confidence.
4. Keep recommendations language-neutral when evidence is weak, missing, or unreadable.
5. Label unsupported framework, package-manager, and test-runner assumptions as `unconfirmed`.

## Default Config Behavior

Optional rule packs are intentionally not referenced from `.continue/config.yaml`.

This prevents every installed pack from globally applying Python or TypeScript advice to .NET, SQL, infrastructure, documentation, or mixed repositories. If a future installer profile enables language packs automatically, it must do so through explicit profile selection and evidence-gated documentation.

## Validation Expectations

Before a language rule pack is promoted from optional to validated, test it against generated sample repositories and record sanitized evidence.

Minimum validation:

- repository discovery identifies the ecosystem from exact inspected files
- implementation planning uses language-appropriate guidance without inventing frameworks
- code review avoids unrelated .NET or other ecosystem recommendations
- output verification catches unsupported framework, toolchain, or filename claims
- documentation, TODO, roadmap, changelog, and wiki remain aligned
