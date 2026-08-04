#!/usr/bin/env python3
"""Verify exact, single-use, memory-only controlled-research approvals."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "scripts/offline_research_approval_state.py"
SPEC = importlib.util.spec_from_file_location("research_approval", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def rejected(action, reason):
    try:
        action()
    except MODULE.ApprovalRejected as error:
        assert str(error) == reason
        return
    raise AssertionError(reason)


def main() -> int:
    state = MODULE.OfflineApprovalState()
    state.approve_query("exact approved query")
    state.consume_query("exact approved query")
    rejected(lambda: state.consume_query("exact approved query"), "query-not-approved")
    rejected(lambda: MODULE.OfflineApprovalState().approve_query(" not normalized "), "query-not-normalized")
    state = MODULE.OfflineApprovalState(2)
    state.approve_query("one")
    state.approve_query("two")
    rejected(lambda: state.approve_query("three"), "query-budget")
    state = MODULE.OfflineApprovalState()
    results = [{"citationId": "source-safe", "destination": "https://example.com/page"}]
    state.register_results(results)
    rejected(lambda: state.consume_page("source-safe", results[0]["destination"]), "page-not-approved")
    state.register_results(results)
    rejected(lambda: state.approve_page("source-forged", results[0]["destination"]), "page-not-trusted")
    state.register_results(results)
    rejected(lambda: state.approve_page([], results[0]["destination"]), "page-not-trusted")
    state.register_results(results)
    rejected(lambda: state.consume_page([], results[0]["destination"]), "page-not-approved")
    for method in ("cancel", "fail", "provider_changed", "shutdown"):
        state = MODULE.OfflineApprovalState()
        state.approve_query("approved")
        getattr(state, method)()
        rejected(lambda state=state: state.consume_query("approved"), "query-not-approved")
    state = MODULE.OfflineApprovalState()
    state.register_results(results)
    state.approve_page("source-safe", results[0]["destination"])
    state.consume_page("source-safe", results[0]["destination"])
    rejected(lambda: state.consume_page("source-safe", results[0]["destination"]), "page-not-approved")
    runtime = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "web").rglob("*") if path.is_file() and path.suffix in {".py", ".js", ".html", ".css"})
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert "offline_research_approval_state" not in runtime + package
    print("Offline research approval state passed 17 exact-lifecycle checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
