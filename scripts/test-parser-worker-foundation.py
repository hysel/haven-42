#!/usr/bin/env python3
"""Run the restricted parser-worker hostile admission suite."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "restricted_parser_worker",
    ROOT / "scripts" / "evaluate-parser-worker-admission.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


if __name__ == "__main__":
    raise SystemExit(MODULE.self_test())
