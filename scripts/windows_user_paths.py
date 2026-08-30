#!/usr/bin/env python3
"""Trusted current-user Windows paths without environment-variable authority."""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path


CSIDL_LOCAL_APPDATA = 0x001C
MAX_WINDOWS_PATH_CHARS = 32768


class WindowsUserPathError(ValueError):
    """Raised when Windows cannot provide a safe current-user known folder."""


def portable_install_root() -> Path:
    """Return the directory containing the portable app, never an env override."""
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        candidate = executable.parent
        if (
            sys.platform == "darwin"
            and executable.parent.name == "MacOS"
            and executable.parent.parent.name == "Contents"
            and executable.parent.parent.parent.name == "Haven 42.app"
        ):
            # A macOS .app executable lives below Contents/MacOS.  Portable
            # mutable state belongs beside the bundle, never inside its signed
            # seal where a normal launch would invalidate package integrity.
            candidate = executable.parents[3]
    else:
        candidate = Path(__file__).resolve().parents[1]
    try:
        root = candidate.resolve(strict=True)
    except OSError as error:
        raise WindowsUserPathError("portable-install-root-unavailable") from error
    if not root.is_dir() or not root.is_absolute():
        raise WindowsUserPathError("portable-install-root-unavailable")
    return root


def portable_data_root() -> Path:
    """Keep every managed Alpha component inside the extracted app folder."""
    return portable_install_root() / "Haven42-Data"


def windows_local_app_data() -> Path:
    """Return the current user's local app-data folder from the Windows shell."""
    if os.name != "nt":
        raise WindowsUserPathError("windows-known-folder-unavailable")
    buffer = ctypes.create_unicode_buffer(MAX_WINDOWS_PATH_CHARS)
    try:
        result = ctypes.windll.shell32.SHGetFolderPathW(
            None, CSIDL_LOCAL_APPDATA, None, 0, buffer,
        )
    except (AttributeError, OSError) as error:
        raise WindowsUserPathError("windows-known-folder-unavailable") from error
    value = buffer.value
    path = Path(value)
    if (
        result != 0
        or not value
        or "\x00" in value
        or value.startswith("\\\\")
        or not path.is_absolute()
        or not path.drive
        or not path.is_dir()
    ):
        raise WindowsUserPathError("unsafe-windows-known-folder")
    return path.resolve(strict=True)
