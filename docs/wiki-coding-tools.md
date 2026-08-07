# Coding Tools for Local Models

The Haven 42 app does not require coding tools. If you want to use a local
Ollama model from Continue, Aider, or OpenCode, use the separate **Haven 42
Local LLM IDE Tools** package.

The package contains one small setup helper and the Continue prompt/rule
bundle. It does not contain the Haven 42 app, Ollama, models, IDEs, drivers,
maintainer scripts, or third-party installers.

Setup shows a preview first. It writes only after you add `--apply`, stops
before replacing existing settings unless you add `--replace`, and creates a
backup before replacement.

See the [package guide](https://github.com/hysel/haven-42/tree/main/packages/local-llm-ide)
for build and setup commands. No public coding-tools release is claimed until
its exact package and hosted checks are approved.
