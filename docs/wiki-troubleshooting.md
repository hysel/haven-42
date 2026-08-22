# Troubleshooting

_For Haven 42 users. Begin here before using the engineering diagnostics._

## Haven 42 does not open

- Keep the launcher terminal open while using Haven 42.
- If the browser does not open automatically, copy the exact
  `http://127.0.0.1:4242` address printed by the launcher into your browser.
- If the launcher reports that the port is already in use, close the older
  Haven 42 process before starting another copy.
- Do not substitute a LAN address. The Haven 42 interface is loopback-only.

## The AI server does not connect

1. If you used guided local setup, close and reopen the same extracted Haven 42
   copy. Haven 42 will check and restart its local AI engine automatically.
2. If you chose an advanced external server, confirm Ollama is running on that
   computer.
3. Confirm the address and port. Same-machine Ollama normally uses
   `http://127.0.0.1:11434`.
4. For another machine, use its private-network numeric address and the
   port on which Ollama is listening.
5. Check that the two machines can reach each other under the network policy
   you manage.

Haven 42 blocks public addresses, credentials in URLs, redirects, and unsupported
hostnames. A private-network HTTP connection also displays an encryption warning;
that warning is expected until you use trusted HTTPS or a loopback tunnel.

### A Mac says Local Network access is not allowed

macOS asks for Local Network access only when Haven 42 connects to an AI server
on another computer. If you trust that server, open **System Settings → Privacy
& Security → Local Network** and enable **Haven 42**, then try the connection
again. Leave it disabled when you use only Ollama on the same Mac. Haven 42
uses the server address you enter and does not scan for nearby devices.

## Chat is unavailable

- Connect Ollama first.
- Wait for Haven 42 to load the installed-model list.
- If the selected model was removed from the server, reconnect and choose an
  installed model.
- Start a **New task** only when you intend to clear the current memory-only
  conversation.

## A model is missing

Open **Models**, search the public catalog, and choose the result. Haven 42
shows the exact model and connected destination before anything downloads.
Choose **Approve and install** only if those details are correct. The model is
not offered for chat until Ollama confirms that the exact model is installed.
An advanced manual command remains available as a fallback for server owners.

## Research stops safely

Use **Open troubleshooting logs** directly below the research error. Haven 42
opens System, expands the log area, refreshes the sanitized events, and moves
keyboard focus there. Search words and retrieved page text are not recorded.

If Wikipedia reports an unexpected response, retry once. Haven 42 rejects
unrecognized fields or destinations rather than guessing. For broader results,
choose **Wider web with a cited answer** to let Haven 42 retrieve a bounded set
of approved public pages, or **Private browser search** to open the exact query
in your browser without importing the results.

## Setup stops while testing a downloaded model

If setup reaches 95%, the model download is complete and Haven 42 is running a
short private local test. Open **View troubleshooting logs** if that test stops.
Keep `Haven42-Data`: retrying the local test reuses the verified model instead
of downloading it again. When Haven 42 selects processor compatibility mode,
it explicitly uses Ollama's most-compatible CPU runner rather than relying on
automatic acceleration detection.

## An attachment is rejected

The current product accepts bounded UTF-8 text, CSV, JSON, admitted source-code
files, and PNG screenshots. It rejects renamed executable content, unsupported
types, excessive file sizes or counts, malformed structured text, and files
that fail signature or content checks.

PDF, Office, OpenDocument, archives, and executables are not currently admitted
chat attachments.

## The response is slow

- Compare the timing shown under **Response details · Advanced**.
- Try a smaller installed model.
- Reduce attachment size or start a focused new task.
- Check the Ollama machine for competing model or GPU workloads.

If the Haven 42 page responds quickly but the answer appears slowly, the AI
model or the computer running it is usually the slow part.

## Still stuck?

Record the operating system, Haven 42 version, exact user-visible error, and the
steps that caused it. Remove private endpoints, paths, prompts, and attachments
before sharing a report.

You can also open System and choose the full-width **Open troubleshooting
logs** button. The collapsible technical log region below it remains available
for repeat checks and saving a sanitized support report.

Developer, Continue, configuration, and repository diagnostics are in
[[Engineering Troubleshooting|Eng-Troubleshooting]]. Security issues
should be reported privately using the repository's
[security policy](https://github.com/hysel/haven-42/security/policy).

**Next:** [[Common Words|Glossary]]
