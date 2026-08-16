#!/usr/bin/env python3
"""Exercise the admitted fixed-Wikipedia product runtime with sanitized output."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web"))
import server as haven_web  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="local artificial intelligence")
    parser.add_argument("--result-limit", type=int, default=3)
    arguments = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="haven42-live-research-") as temporary:
        state = haven_web.HavenState(diagnostic_root=Path(temporary) / "logs")
        try:
            prepared = state.prepare_research_query(arguments.query, arguments.result_limit)
            query_result = state.execute_research_query(prepared["approvalToken"])
            citations = query_result["citations"]["citations"]
            if not citations:
                raise RuntimeError("live-query-returned-no-citations")
            selected = citations[0]
            page_prepared = state.prepare_research_page(
                query_result["resultId"], selected["citationId"]
            )
            page_result = state.execute_research_page(page_prepared["approvalToken"])
            if page_result["source"] != selected:
                raise RuntimeError("selected-source-binding-failed")
            if page_result["contentCharacters"] <= 0:
                raise RuntimeError("selected-page-returned-no-text")
            receipt = {
                "schemaVersion": 1,
                "kind": "haven42-sanitized-live-wikipedia-runtime-validation",
                "provider": "fixed-English-Wikipedia",
                "queryDigest": hashlib.sha256(
                    query_result["normalizedQuery"].encode("utf-8")
                ).hexdigest(),
                "resultCount": len(citations),
                "selectedDisplayDomain": selected["displayDomain"],
                "contentDigest": hashlib.sha256(
                    "\n".join(item["text"] for item in page_result["segments"]).encode("utf-8")
                ).hexdigest(),
                "contentCharacters": page_result["contentCharacters"],
                "queryApprovalSingleUse": prepared["singleUse"],
                "pageApprovalSingleUse": page_prepared["singleUse"],
                "activeNavigationAllowed": page_result["activeNavigationAllowed"],
                "pageExecutionAllowed": page_result["pageExecutionAllowed"],
                "automaticFollowUpAllowed": page_result["automaticFollowUpAllowed"],
                "contentPersisted": page_result["contentPersisted"],
                "modelToolAllowed": page_result["modelToolAllowed"],
            }
            print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
            state.clear_research()
        finally:
            state.diagnostics.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
