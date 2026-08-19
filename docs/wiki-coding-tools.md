# Coding Tools for Local Models

The Haven 42 app does not require coding tools. If you want to use a local
Ollama model from Aider or OpenCode, use the separate **Haven 42 Local LLM IDE
Tools** package. Continue is legacy evidence only. It is not configured,
recommended, packaged, or requalified by Haven 42.

The package contains one small setup helper for Aider and OpenCode. It does not
contain Continue project configuration, the Haven 42 app, Ollama, models, IDEs,
drivers, maintainer scripts, or third-party installers.

Setup shows a preview first. It writes only after you add `--apply`, stops
before replacing existing settings unless you add `--replace`, and creates a
backup before replacement.

## Availability

The earlier `0.1.0-development` package is retired because it shipped Continue
project configuration that current editor tests did not load or apply
reliably. The corrected package remains source-only until a new package review
passes. Do not use the old ZIP for a new setup.

Follow the
[package guide](https://github.com/hysel/haven-42/tree/main/packages/local-llm-ide)
for the current source status and safety boundaries.
