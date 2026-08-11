# Windows Alpha download and feedback

Haven 42 `0.4.0-alpha.1` is an early, unsigned Windows 11 x64 test build. It is
not a production release. The download must come from the Haven 42 repository
release page, and its SHA-256 value must match the checksum published beside
the archive.

The wiki [Quick Start](https://github.com/hysel/haven-42/wiki/Quick-Start) is
the maintained setup procedure. This page adds release-integrity and reporting
details without maintaining a second setup sequence.

## Before downloading

- Use Windows 11 x64. Windows 10 and other operating systems are outside this
  Alpha's admitted test boundary.
- Expect Windows or security software to warn about an unsigned application.
  Do not disable antivirus, SmartScreen, Secure Boot, or another protection to
  run Haven 42.
- Haven 42 never installs drivers. If a graphics driver needs attention, setup
  stops and provides instructions.
- Keep the extracted folder in a location where your Windows account can write.
  Haven 42 stores managed components in `Haven42-Data` and sanitized support
  records in `Haven42-Logs`, both beside the application.

## Download and verify

Download these two files from the official
[Haven 42 Releases page](https://github.com/hysel/haven-42/releases):

- `haven42-0.4.0-alpha.1-windows-x64-unsigned.zip`
- the published SHA-256 checksum file for that archive

Alpha 1's runtime license and third-party-notice documents are separate hashed
assets on that release page rather than files inside the application ZIP. This
is a known Alpha 1 packaging limitation; future package builds embed them in the
extracted folder.

In Windows PowerShell 5.1 or PowerShell 7, change to the download folder and
run:

```powershell
Get-FileHash -Algorithm SHA256 .\haven42-0.4.0-alpha.1-windows-x64-unsigned.zip
```

Compare all 64 hexadecimal characters with the published value. If they do not
match, delete the download and report the mismatch. Do not run it.

## Start Haven 42

Follow the [Quick Start](https://github.com/hysel/haven-42/wiki/Quick-Start)
from **Start the portable Windows package** through its explicit **Next** link.

Haven 42 opens in the default browser and binds only to IPv4 loopback. Closing
the Haven 42 process stops services it started for that session. The System
page can remove Haven-managed local AI components. After closing Haven 42, the
extracted folder can be deleted to remove the application.

## Report a problem

Use the [Alpha report chooser](https://github.com/hysel/haven-42/issues/new/choose)
for ordinary bugs or experience feedback. The same link is available on the
About page inside Haven 42.

If you need help before opening a public issue, email
[haven42localai@gmail.com](mailto:haven42localai@gmail.com). Do not email
passwords, API keys, private prompts, attached files, or raw logs.

Before submitting a public report, remove prompts, responses, attachment names
and contents, credentials, private addresses, hostnames, usernames, full local
paths, machine identifiers, and screenshots containing personal information.
Never paste raw logs. A support report saved from System > Troubleshooting logs
is designed to be sanitized, but review it before sharing.

Suspected vulnerabilities, exposed credentials, unsafe listening, arbitrary
execution, data loss, or package-integrity problems must be sent through
[private vulnerability reporting](https://github.com/hysel/haven-42/security/advisories/new),
not a public issue.

## Known limits

Read the candidate-bound [known limitations](private-alpha-known-limitations.md)
before testing. This unsigned Alpha publication does not claim production
readiness, activate automatic updates, or authorize signing.
