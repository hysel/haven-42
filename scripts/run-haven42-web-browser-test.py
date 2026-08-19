#!/usr/bin/env python3
"""Launch the source browser fixture with process-isolated diagnostics."""

from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web"))
import server as haven_web  # noqa: E402


def research_citation(query: str) -> dict:
    page_id = 42
    digest = hashlib.sha256(f"{query}\0{page_id}".encode()).hexdigest()[:20]
    return {
        "citationId": f"source-{digest}",
        "title": "Local artificial intelligence",
        "displayDomain": "en.wikipedia.org",
        "destination": "https://en.wikipedia.org/?curid=42",
        "retrievedAt": "2026-01-01T00:00:00Z",
        "contentTrust": "untrusted-metadata-only",
        "destinationDisclosureRequired": True,
        "activeNavigationAllowed": False,
    }


def research_query(query: str, _limit: int) -> dict:
    return {
        "schemaVersion": 1,
        "status": "development-live-query-validated",
        "queryDigest": hashlib.sha256(query.encode()).hexdigest(),
        "results": [research_citation(query)],
        "additionalResultsAvailable": False,
        "networkAuthorityGranted": False,
        "runtimeAdmissionGranted": False,
        "pageRetrievalAllowed": False,
        "transport": {
            "providerId": "wikipedia-query", "tlsSystemTrust": True,
            "dnsRevalidated": True, "connectionPinnedToReviewedPublicIp": True,
            "redirectsFollowed": False, "credentialsSent": False,
            "cookiesSent": False, "proxyEnvironmentInherited": False,
        },
    }


def research_page(query: str, _limit: int, _citation_id: str, _destination: str) -> dict:
    segments = [
        {"index": 1, "text": "Local AI runs on a user's device.", "trust": "untrusted-inert-text"},
        {"index": 2, "text": "This browser fixture is inert source text.", "trust": "untrusted-inert-text"},
    ]
    joined = "\n".join(item["text"] for item in segments)
    return {
        "schemaVersion": 1,
        "status": "development-live-selected-page-validated",
        "queryDigest": hashlib.sha256(query.encode()).hexdigest(),
        "source": research_citation(query),
        "contentDigest": hashlib.sha256(joined.encode()).hexdigest(),
        "segments": segments,
        "contentCharacters": sum(len(item["text"]) for item in segments),
        "developmentNetworkUsed": True,
        "dnsRevalidated": True,
        "connectionPinnedToReviewedPublicIp": True,
        "redirectsFollowed": False,
        "credentialsSent": False,
        "cookiesSent": False,
        "proxyEnvironmentInherited": False,
        "activeNavigationAllowed": False,
        "pageExecutionAllowed": False,
        "automaticFollowUpAllowed": False,
        "filesWritten": False,
        "runtimeAdmissionGranted": False,
        "packageAdmissionGranted": False,
    }


def software_updates() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "haven42-managed-software-update-check",
        "checkedBecauseUserRequested": True,
        "automaticChecksEnabled": False,
        "configurationPersisted": False,
        "userContentSent": False,
        "components": [{
            "id": "ollama-runtime",
            "displayName": "Ollama local AI engine",
            "managedVersion": "0.32.14",
            "latestStableVersion": "0.32.14",
            "newerOfficialVersionAvailable": False,
            "managedVersionIsLatest": True,
            "availableForManagedSetup": True,
            "releaseUrl": "https://github.com/ollama/ollama/releases/tag/v0.32.14",
            "artifactName": "ollama-windows-amd64.zip",
            "downloadBytes": 1459874325,
            "sha256": "5ae5bca5f0d297f5e35665e01db399a69a8eac3f8fad89cd9d2531fd495c9457",
        }],
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="haven42-browser-diagnostics-") as temporary:
        state = haven_web.HavenState(
            diagnostic_root=Path(temporary) / "Haven42-Logs",
            managed_setup_state_root=Path(temporary) / "Haven42-Data",
            research_query_provider=research_query,
            research_page_provider=research_page,
            software_update_provider=software_updates,
        )
        try:
            app = haven_web.HavenWebServer(("127.0.0.1", 0), state)
        except OSError as error:
            state.diagnostics.close()
            print(f"Could not start Haven 42 local web test server: {error}", file=sys.stderr)
            return 1
        print(f"Haven 42 is available at {app.expected_origin}", flush=True)
        try:
            app.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
        finally:
            app.shutdown()
            app.server_close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
