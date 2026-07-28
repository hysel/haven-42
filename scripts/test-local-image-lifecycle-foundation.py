#!/usr/bin/env python3
"""Run the effect-free local image lifecycle hostile suite."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "local_image_lifecycle",
    ROOT / "scripts" / "simulate-local-image-lifecycle.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


if __name__ == "__main__":
    raise SystemExit(MODULE._self_test())
