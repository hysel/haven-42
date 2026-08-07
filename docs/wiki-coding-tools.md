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

## Download

Open the
[Local LLM IDE Tools development prerelease](https://github.com/hysel/haven-42/releases/tag/local-llm-ide-tools-v0.1.0-development)
and download the ZIP plus its `.sha256` file. This is an unsigned development
package, not a production release.

The expected ZIP SHA-256 is:

```text
da12ab46c26aaf9ea4f4105b927345bfe3d0900a416591ba29b3a33edaf16644
```

Follow the
[package guide](https://github.com/hysel/haven-42/tree/main/packages/local-llm-ide)
to verify the download, extract it, preview setup, and apply only the changes
you approve. You do not need to clone the full repository.
