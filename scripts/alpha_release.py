#!/usr/bin/env python3
"""Fail-closed release identity shared by source and packaged Alpha builds."""

from __future__ import annotations

import os
import sys


ALPHA_1_VERSION = "0.4.0-alpha.1"
ALPHA_2_VERSION = "0.4.0-alpha.2"
PACKAGED_VERSION_ENVIRONMENT = "HAVEN42_PACKAGED_VERSION"


class AlphaReleaseError(ValueError):
    """Raised when a packaged build has no valid embedded release identity."""


def platform_default_version() -> str:
    return ALPHA_2_VERSION if sys.platform.startswith("linux") else ALPHA_1_VERSION


def application_version() -> str:
    """Return source default or the identity forced by a packaged runtime hook."""
    default = platform_default_version()
    if not getattr(sys, "frozen", False):
        return default
    selected = os.environ.get(PACKAGED_VERSION_ENVIRONMENT, "")
    allowed = {ALPHA_2_VERSION} if sys.platform.startswith("linux") else {
        ALPHA_1_VERSION,
        ALPHA_2_VERSION,
    }
    if selected not in allowed:
        raise AlphaReleaseError("invalid-packaged-release-identity")
    return selected


def display_version(version: str) -> str:
    if version == ALPHA_1_VERSION:
        return "Haven 42 0.4 Alpha 1"
    if version == ALPHA_2_VERSION:
        return "Haven 42 0.4 Alpha 2"
    raise AlphaReleaseError("invalid-release-version")
