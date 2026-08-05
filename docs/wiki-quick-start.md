# Quick Start

_For first-time users on Windows, Linux, and macOS. Current packages are
unsigned development software._

This guide assumes you have never used local AI before. You do not need to know
Python, graphics settings, model formats, or server administration to follow
the recommended Windows setup.

## Before you begin

Choose one of these forms:

- **Portable package · Recommended:** extract the ZIP and run `haven42.exe`.
  Use only a package supplied by a trusted Haven 42 test source.
- **Source · Advanced:** for developers who already have Python 3 and a reviewed
  copy of this repository.

Ollama is the local AI engine that runs a model. Guided Windows setup can place
the tested portable Ollama files and a suitable model inside your extracted
Haven 42 folder after showing the downloads and asking your permission.

## Start the portable Windows package · Recommended

1. Extract the complete ZIP into a folder you own. Do not run it from inside
   the ZIP.
2. Keep every extracted file together.
3. Run `haven42.exe`.
4. Choose **Set up this computer · Recommended**.
5. Review the computer check and the list of downloads.
6. Check the permission box only if you agree, then choose **Approve and
   continue**.
7. Wait for every item to say **Complete**, then open Chat.

Windows may display a warning because this Alpha package is not digitally
signed. This is expected for invited testing, but you should stop if the file
did not come from your trusted Haven 42 test source.

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

## Choose the first-run path

- **Set up this computer · Recommended** checks the computer, recommends a
  model, explains the downloads, and asks permission.
- **Use another AI server · Advanced** connects to Ollama that you already run.
- **Look around first** opens Haven 42 without setting up or connecting.

For same-machine Ollama, use `http://127.0.0.1:11434`. Private-network
connections must use a private IP address and will show an unencrypted-HTTP
warning unless you provide a trusted HTTPS endpoint.

For safety, Haven 42 blocks public internet server addresses, passwords placed
inside an address, and unexpected redirects.

## Send a first message

1. Keep **Choose for me · Recommended** selected.
2. Type a message and press **Enter**. Use **Shift+Enter** for a new line.
3. Choose Chat, Write, or Summarize only when you want to select the task
   yourself.
4. Open **Response details · Advanced** only if you want token and timing data.

Public model search never downloads anything. Guided Windows setup downloads
only the exact model shown on the permission screen.

## Stop Haven 42

Close Haven 42 using its launcher window or normal close action. The current
conversation is not saved. A Haven-managed local AI engine stops with Haven 42
and is checked and restarted automatically the next time you open the same
extracted copy.

Continue with [[Using Haven 42|Using-Haven-42]] or open [[Troubleshooting]] if
the server, browser, or provider connection does not behave as expected.
