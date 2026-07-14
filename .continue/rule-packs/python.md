---
name: Python Engineering
optional: true
globs: ["**/*.py", "**/pyproject.toml", "**/requirements*.txt", "**/pytest.ini", "**/tox.ini"]
---

## Scope

Use this optional rule pack only when project detection confirms Python evidence.

Strong Python evidence includes `pyproject.toml`, `requirements*.txt`, `setup.py`, `poetry.lock`, `Pipfile`, `pytest.ini`, `tox.ini`, or clearly inspected Python package/source files.

If Python evidence is absent or unreadable, do not apply this rule pack. Keep recommendations language-neutral and mark Python assumptions as `unconfirmed`.

## Required Practices

- Prefer project metadata such as `pyproject.toml` or `requirements*.txt` before naming package managers, build tools, or test runners.
- Preserve the repository's existing dependency manager unless the requested change explicitly includes migration.
- Keep application code, infrastructure adapters, and test utilities separated by existing package boundaries.
- Use explicit configuration loading and validation for environment-specific settings.
- Treat file paths, shell commands, uploaded files, API input, serialized data, and database values as untrusted input.
- Prefer deterministic tests with clear fixtures; avoid tests that depend on local machine state, network access, or wall-clock timing unless explicitly scoped.
- Match test commands to inspected project metadata. Use `pytest`, `unittest`, `tox`, `nox`, or package-manager scripts only when evidence supports them.
- Keep linting, formatting, and type-checking recommendations tied to observed tools such as Ruff, Black, mypy, Pyright, or project scripts.

## Avoid

- Recommending `pytest`, Poetry, Pipenv, FastAPI, Flask, Django, Ruff, Black, mypy, or Pyright without repository evidence.
- Rewriting project layout to a preferred Python structure without a migration reason.
- Adding global mutable state, import-time side effects, or hidden dependency initialization.
- Swallowing exceptions without preserving useful error context.
- Suggesting live API, database, or filesystem tests when a deterministic unit or integration boundary is available.

## Review Checklist

- Which files prove this is a Python project?
- Which dependency manager, build system, and test runner are confirmed versus `unconfirmed`?
- Are configuration, secrets, and environment-specific settings handled safely?
- Are input parsing, file handling, serialization, and database boundaries validated?
- Do test recommendations match inspected project tooling?
