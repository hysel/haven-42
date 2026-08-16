# Windows conversation-history per-user ACL validation

Last reviewed: August 15, 2026

This development proof checks one narrow prerequisite for optional encrypted
conversation history: Windows can create a directory whose access list is
limited to the current user and Local System, then let a key file inherit that
same boundary.

The proof passed 24 checks on Windows. It:

- creates a random, test-owned directory beneath the system temporary folder;
- accepts no caller-selected path and verifies the fresh directory is not a
  reparse point before use;
- removes inherited permissions from the directory;
- grants full control only to the current user and Local System;
- creates one fixed-name synthetic key file with exclusive creation and a
  durable flush;
- verifies the inherited file rules contain only those two identities;
- deliberately adds the built-in Users group and proves the verifier refuses
  the widened access list; and
- removes the temporary file and directory after the test.

No conversation, database, application data directory, credential, or user
content was used. The proof is excluded from the package and grants no runtime,
UI, persistence, or production authority.

This is not production ACL admission. Haven 42 still needs to bind the same
checks to its eventual per-user application directory, encrypted database and
wrapped-key atomic creation, recovery and migration paths, and packaged
Windows lifecycle before saved history can be enabled.

The repeatable contract and checks are:

- `config/conversation-history-windows-per-user-acl.json`
- `scripts/conversation-history-windows-per-user-acl.ps1`
- `scripts/test-conversation-history-windows-per-user-acl.py`
