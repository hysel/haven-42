# Package Dependency Admission

The unsigned PyInstaller development package has one admitted build graph: Python 3.14.6 plus the eight exact Python distributions in `package/requirements-build.txt`. Every direct and transitive build dependency is explicitly pinned and hash-locked. Platform markers distinguish the Windows and macOS-only packages.

`config/package-dependency-admission.json` records the exact version, license expression, and platform scope. Its test compares that contract with the requirements lock, the package builder's inventory mapping, and the least-privilege packaging workflow. Any added, removed, moved, unpinned, unhashed, or license-divergent dependency fails locally before commit.

This admission applies only to building unsigned development archives. It does not admit npm, Cargo, Tauri, a native installer, signing, updater activation, release publication, or production redistribution. The separate exact runtime-component and Microsoft redistribution reviews remain authoritative for packaged runtime bytes.
