# Quick Start

_For first-time Windows Alpha users and developers starting from source on
Windows, Linux, or macOS. Current packages are unsigned development software._

The public beginner package currently supports Windows 11 x64. You won't need
Python, graphics tuning, model-format knowledge, or server administration.
Linux and macOS do not yet have a public beginner package; those steps run
reviewed source with Python 3 and are for developers.

## Before you begin

Pick one route:

- **Windows portable package · Recommended:** download
  [`haven42-0.4.0-alpha.1-windows-x64-unsigned.zip`](https://github.com/hysel/haven-42/releases/download/v0.4.0-alpha.1/haven42-0.4.0-alpha.1-windows-x64-unsigned.zip)
  and its [published checksum file](https://github.com/hysel/haven-42/releases/download/v0.4.0-alpha.1/haven42-0.4.0-alpha.1-windows-x64-unsigned.zip.sha256)
  from the official Alpha 1 release. Get both files from the Haven 42
  repository, not a mirror.
- **Source · Advanced:** for developers who already have Python 3 and a reviewed
  copy of this repository.

Ollama is the local AI engine that runs the model. Windows guided setup can put
the tested portable Ollama files and a suitable model inside the extracted
Haven 42 folder, but it lists the downloads and waits for approval first.

## Start the portable Windows package · Recommended

1. In PowerShell, check the ZIP before opening it:

   ```powershell
   Get-FileHash -Algorithm SHA256 .\haven42-0.4.0-alpha.1-windows-x64-unsigned.zip
   ```

   The complete SHA-256 value must be
   `d1648667807dde37c645beb2199503b8a4852a585a2f62eb4ebe2c0b90465106`.
   Stop and delete the ZIP if it differs.
2. Extract the complete ZIP into a folder you own. Do not run it from inside
   the ZIP.
3. Keep every extracted file together.
4. Run `haven42.exe`.
5. Choose **Set up this computer · Recommended**.
6. Review the computer check and the list of downloads.
7. Check the permission box only if you agree, then choose **Approve and
   continue**.
8. Wait for every item to say **Complete**, then open Chat.

Windows will warn that this Alpha package isn't digitally signed. That's
expected for invited testing; stop if the file didn't come from your trusted
Haven 42 test source.

## Start from source

Download or clone the reviewed source from the
[Haven 42 repository](https://github.com/hysel/haven-42), install a working
Python 3 interpreter, and open a terminal in the repository root. This path is
for developers and won't install Ollama or a model for you.

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

Haven 42 starts at `http://127.0.0.1:4242` and asks the operating system to open
your default browser. If nothing opens, copy the exact loopback URL from the
terminal into the browser yourself.

## Choose the first-run path

- **Set up this computer · Recommended** checks the computer, recommends a
  model, lists the downloads, and waits for your approval.
- **Use another AI server · Advanced** connects to Ollama that you already run.
- **Look around first** opens Haven 42 without setting up or connecting.

For Ollama on the same machine, use `http://127.0.0.1:11434`. A server elsewhere
on your private network must use a private IP address. Expect an unencrypted
HTTP warning unless that server has a trusted HTTPS endpoint.

On a Mac, macOS asks whether Haven 42 may find devices on local networks when
you connect to Ollama on another computer. Choose **Allow** only if you intend
to use the address you entered. Haven 42 doesn't scan for nearby devices, and
same-computer setup at `127.0.0.1` doesn't need private-network access.

Try a public internet address, put a password in the URL, or let the server
redirect somewhere unexpected and Haven 42 will refuse the connection. That's
intentional.

## Send a first message

1. Keep **Choose for me · Recommended** selected.
2. Type a message and press **Enter**. Use **Shift+Enter** for a new line.
3. Choose Chat, Write, or Summarize only when you want to select the task
   yourself.
4. Open **Response details · Advanced** only if you want token and timing data.

Public model search doesn't download a result when you click it. You first get
a review with the exact model and destination; the download begins only after
you choose **Approve and install**. Guided Windows setup follows the same rule
for the components on its approval screen.

After connecting, Haven 42 remembers the last main section and returns there
after a browser refresh. It doesn't store the conversation, server address,
credentials, research words, or model-install approval. If it can't confirm a
working connection after restart, it opens setup again.

## Stop Haven 42

Close Haven 42 from its launcher window or with the normal close action. The
current conversation isn't saved. A Haven-managed local AI engine stops with
Haven 42; the next time you open the same extracted copy, Haven 42 checks and
restarts it automatically.

**Next:** [[Using Haven 42|Using-Haven-42]]
