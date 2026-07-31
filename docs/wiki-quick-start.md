# Quick Start

> **Audience:** first-time Haven 42 users<br>
> **Availability:** unsigned development software<br>
> **Platforms:** Windows, Linux, and macOS

This guide starts Haven 42 without installing a system service, changing a
firewall, requiring administrator access, or enabling an updater.

## Before you begin

Choose one of these forms:

- **Source:** requires Python 3 and a reviewed Haven 42 repository checkout.
- **Portable development package:** includes its own Python runtime and requires
  no global Python installation. Use only an exact artifact from a trusted
  workflow run and verify its supplied checksum.

Ollama is optional while exploring the interface. It is required for chat,
writing, summarization, and installed-model discovery.

## Start from source

Open a terminal in the Haven 42 repository root.

Windows PowerShell:

```powershell
.\scripts\start-haven42-web.ps1
```

Linux:

```bash
./scripts/start-haven42-web.linux.sh
```

macOS:

```bash
./scripts/start-haven42-web.macos.sh
```

Haven 42 starts on `http://127.0.0.1:4242` and asks the operating system to
open its default browser. If the browser does not open, copy the exact loopback
URL printed in the terminal into your browser.

## Start the portable package

Extract the complete archive to a user-owned directory and keep the entire
one-folder bundle together. Verify the checksum supplied with the artifact,
then run the Haven 42 executable inside the extracted bundle.

The package is unsigned development software. It is not an installer and does
not add a service, driver, startup entry, firewall rule, or global Python
runtime. See [[Portable Development Package|Portable-Development-Package]] for
artifact verification and packaging details.

## Choose the first-run path

- **Explore Haven 42** opens the interface without scanning or connecting.
- **Connect existing setup** connects to an Ollama server you already manage.
- **Guided setup** performs a bounded read-only readiness scan and creates a
  disabled setup plan. It does not install anything.

For same-machine Ollama, use `http://127.0.0.1:11434`. Private-network
connections must use a private IP address and will show an unencrypted-HTTP
warning unless you provide a trusted HTTPS endpoint.

Haven 42 blocks public provider addresses, credentials in URLs, redirects, and
unsupported hostnames.

## Send a first message

1. Connect Ollama and wait for the installed-model list.
2. Keep the automatic evidence-backed model or deliberately choose an advanced
   installed model.
3. Enter a prompt and press **Enter**. Use **Shift+Enter** for a new line.
4. Expand run details if you want provider-reported token and timing data.

Haven 42 never downloads a model automatically. If a model is missing, follow
the displayed guidance in the Ollama environment you manage, then reconnect.

## Stop Haven 42

Close the Haven 42 browser tab and stop the launcher in its terminal with
**Ctrl+C**. The current application state is memory-only and is not restored on
the next launch.

Continue with [[Using Haven 42|Using-Haven-42]] or open [[Troubleshooting]] if
the server, browser, or provider connection does not behave as expected.
