#!/usr/bin/env python3
"""Import the reviewed query adapter from its compatibility script name.

The original validator keeps its public hyphenated filename for existing
workflows.  This importable shim lets the packaged runtime reuse that exact
implementation without maintaining a second parser.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
ADAPTER_PATH = ROOT / "scripts" / "validate-web-research-query-adapter.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location(
        "haven42_reviewed_web_query_adapter", ADAPTER_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError("query-adapter-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ADAPTER = _load_adapter()
QueryAdapterError = _ADAPTER.QueryAdapterError
build_request = _ADAPTER.build_request
exercise_fixture_transport = _ADAPTER.exercise_fixture_transport
load_contract = _ADAPTER.load_contract
validate_response = _ADAPTER.validate_response

__all__ = [
    "QueryAdapterError",
    "build_request",
    "exercise_fixture_transport",
    "load_contract",
    "validate_response",
]
