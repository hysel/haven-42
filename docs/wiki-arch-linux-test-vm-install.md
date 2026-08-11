# Arch Linux Test VM Installation

_For contributors preparing an isolated Arch Linux virtual machine for Haven 42 testing._

This page documents the automated Archinstall path used for the Haven 42 test
lab. It is not required to use Haven 42. The procedure deliberately keeps a
final human confirmation because starting the installation erases the selected
virtual disk.

## Before loading the configuration

Confirm all of the following from the Arch installation environment:

```bash
archinstall --version
lsblk -b -d -o NAME,SIZE,TYPE,MODEL
ip -4 -br address
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

- Verify the expected Archinstall version.
- Match the target path and exact byte size to the isolated virtual disk.
- Do not continue if the target disk is ambiguous.
- Verify the displayed SSH host fingerprint before transferring files.

Keep general settings and credentials in separate files. The credentials file
should contain a password hash, not a plaintext password. Restrict it to the
root account while the live installer uses it:

```bash
chmod 600 /root/haven42-arch-credentials.json
```

Do not commit credentials, host addresses, SSH keys, or a locally generated
installation profile to the Haven 42 repository.

## Archinstall 4.4 configuration notes

Archinstall 4.4 can load a general configuration and a separate credentials
file:

```bash
archinstall \
  --config /root/haven42-archinstall.json \
  --creds /root/haven42-arch-credentials.json
```

The 4.4 example configuration and runtime parser differ in several important
places. A working disk definition must account for the runtime behavior:

- Every partition `start` and `size` needs a `sector_size` object such as
  `{"value": 512, "unit": "B"}`. A `null` value causes the parser to stop.
- Each new partition needs `"dev_path": null`.
- An EFI system partition should include both `boot` and `esp` flags.
- Do not use `Percent` as a size unit with this runtime. Calculate a fixed,
  aligned size and leave room for the backup GPT data at the end of the disk.
- The graphics value accepted by the runtime is `All open-source`. The menu may
  display the friendlier label `All open-source (default)`, but that display
  label is not a valid JSON value.

These parsing failures occur before partitioning starts. Read the full error
and confirm that no installation or disk operation began before retrying with a
corrected file.

## Starting the installation

Loading the two files opens a populated review screen. It does not start
installation automatically. This is intentional: review the target disk,
wipe setting, hostname, desktop, filesystem, bootloader, and user before
selecting **Install**.

After selecting **Install**, Archinstall performs the configured installation
without requiring the same settings to be entered again.

## If the save-directory screen appears

The prompt **Enter a directory for the configuration(s) to be saved** means
**Save configuration** was selected instead of **Install**.

1. Press `Esc` to return to the main screen.
2. Select **Install**.
3. Review the destructive-operation confirmation before continuing.

If the dialog does not close, `/root` is a valid directory. Saving again is
normally unnecessary when the two JSON files are already present in `/root`.

## If configuration loading fails

Do not repeatedly change unrelated fields. Work from the first exception in
the traceback, correct that field, and reload the configuration. Archinstall
records its diagnostic log at:

```text
/var/log/archinstall/install.log
```

Before retrying, validate the JSON syntax and recheck the target disk:

```bash
python -m json.tool /root/haven42-archinstall.json >/dev/null &&
python -m json.tool /root/haven42-arch-credentials.json >/dev/null &&
lsblk -b -d -o NAME,SIZE,TYPE,MODEL
```

Never upload the credentials file. Review the installer log for passwords,
addresses, paths, or other private information before sharing it.
