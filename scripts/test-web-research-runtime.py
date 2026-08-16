#!/usr/bin/env python3
"""Hostile offline checks for the product web-research approval runtime."""

from __future__ import annotations

import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("haven42_web_runtime_test", ROOT / "web/server.py")
assert SPEC is not None and SPEC.loader is not None
WEB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WEB)


def citation(query: str, title: str = "Local artificial intelligence") -> dict:
    page_id = 42
    value = hashlib.sha256(f"{query}\0{page_id}".encode()).hexdigest()[:20]
    return {
        "citationId": f"source-{value}",
        "title": title,
        "displayDomain": "en.wikipedia.org",
        "destination": f"https://en.wikipedia.org/?curid={page_id}",
        "retrievedAt": "2026-01-01T00:00:00Z",
        "contentTrust": "untrusted-metadata-only",
        "destinationDisclosureRequired": True,
        "activeNavigationAllowed": False,
    }


def query_result(query: str, *, selected: dict | None = None) -> dict:
    return {
        "schemaVersion": 1,
        "status": "development-live-query-validated",
        "queryDigest": hashlib.sha256(query.encode()).hexdigest(),
        "results": [selected or citation(query)],
        "additionalResultsAvailable": False,
        "networkAuthorityGranted": False,
        "runtimeAdmissionGranted": False,
        "pageRetrievalAllowed": False,
        "transport": {
            "providerId": "wikipedia-query",
            "tlsSystemTrust": True,
            "dnsRevalidated": True,
            "connectionPinnedToReviewedPublicIp": True,
            "redirectsFollowed": False,
            "credentialsSent": False,
            "cookiesSent": False,
            "proxyEnvironmentInherited": False,
        },
    }


def page_result(query: str, selected: dict) -> dict:
    segments = [
        {"index": 1, "text": "Local AI runs on a user's device.", "trust": "untrusted-inert-text"},
        {"index": 2, "text": "This is untrusted source text.", "trust": "untrusted-inert-text"},
    ]
    joined = "\n".join(item["text"] for item in segments)
    return {
        "schemaVersion": 1,
        "status": "development-live-selected-page-validated",
        "queryDigest": hashlib.sha256(query.encode()).hexdigest(),
        "source": selected,
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


def refused(callable_, code: str) -> None:
    try:
        callable_()
    except WEB.WebRequestError as error:
        assert error.code == code, (error.code, code)
        return
    raise AssertionError(f"expected refusal: {code}")


def main() -> int:
    checks = 0
    query_calls: list[tuple[str, int]] = []
    page_calls: list[tuple[str, int, str, str]] = []

    def query_provider(query, limit):
        query_calls.append((query, limit))
        return query_result(query)

    def page_provider(query, limit, citation_id, destination):
        page_calls.append((query, limit, citation_id, destination))
        return page_result(query, citation(query))

    with tempfile.TemporaryDirectory() as temporary:
        state = WEB.HavenState(
            research_query_provider=query_provider,
            research_page_provider=page_provider,
            diagnostic_root=Path(temporary),
        )
        try:
            prepared = state.prepare_research_query("  local   artificial intelligence  ", 5)
            assert query_calls == []; checks += 1
            assert prepared["singleUse"] is True and prepared["persisted"] is False; checks += 1
            assert prepared["review"]["normalizedQuery"] == "local artificial intelligence"; checks += 1
            assert prepared["review"]["networkAuthorityGranted"] is False; checks += 1
            assert prepared["review"]["modelApprovalAccepted"] is False; checks += 1

            result = state.execute_research_query(prepared["approvalToken"])
            assert query_calls == [("local artificial intelligence", 5)]; checks += 1
            assert result["status"] == "succeeded" and result["networkUsed"] is True; checks += 1
            assert result["queryPersisted"] is False and result["contentPersisted"] is False; checks += 1
            assert result["modelToolAllowed"] is False and result["automaticFollowUpAllowed"] is False; checks += 1
            assert result["citations"]["runtimeAdmissionGranted"] is True; checks += 1
            selected = result["citations"]["citations"][0]
            refused(
                lambda: state.execute_research_query(prepared["approvalToken"]),
                "research-approval-invalid",
            ); checks += 1
            assert len(query_calls) == 1; checks += 1

            refused(
                lambda: state.prepare_research_page(result["resultId"], "source-" + "0" * 20),
                "research-selection-invalid",
            ); checks += 1
            page_prepared = state.prepare_research_page(result["resultId"], selected["citationId"])
            assert page_calls == []; checks += 1
            assert page_prepared["review"]["citation"] == selected; checks += 1
            page = state.execute_research_page(page_prepared["approvalToken"])
            assert len(page_calls) == 1; checks += 1
            assert page["source"] == selected and page["contentCharacters"] > 0; checks += 1
            assert page["contentPersisted"] is False and page["pageExecutionAllowed"] is False; checks += 1
            refused(
                lambda: state.execute_research_page(page_prepared["approvalToken"]),
                "research-approval-invalid",
            ); checks += 1

            expired = state.prepare_research_query("expiry check", 1)
            state.pending_research_approvals[expired["approvalToken"]]["expiresAt"] = 0
            refused(
                lambda: state.execute_research_query(expired["approvalToken"]),
                "research-approval-invalid",
            ); checks += 1

            wrong_kind = state.prepare_research_page(result["resultId"], selected["citationId"])
            refused(
                lambda: state.execute_research_query(wrong_kind["approvalToken"]),
                "research-approval-invalid",
            ); checks += 1
            refused(
                lambda: state.execute_research_page(wrong_kind["approvalToken"]),
                "research-approval-invalid",
            ); checks += 1

            malicious = dict(query_result("bad response"))
            malicious["unexpected"] = True
            state.research_query_provider = lambda *_: malicious
            bad = state.prepare_research_query("bad response", 1)
            refused(
                lambda: state.execute_research_query(bad["approvalToken"]),
                "research-provider-response-invalid",
            ); checks += 1

            bad_citation = citation("bad title", "<script>alert(1)</script>")
            state.research_query_provider = lambda *_: query_result("bad title", selected=bad_citation)
            bad = state.prepare_research_query("bad title", 1)
            refused(
                lambda: state.execute_research_query(bad["approvalToken"]),
                "research-provider-response-invalid",
            ); checks += 1

            state.clear_research()
            assert state.pending_research_approvals == {} and state.research_results == {}; checks += 1
        finally:
            state.diagnostics.close()

    api_query_calls: list[tuple[str, int]] = []
    def api_query_provider(query, limit):
        api_query_calls.append((query, limit))
        return query_result(query)
    with tempfile.TemporaryDirectory() as temporary:
        api_state = WEB.HavenState(
            research_query_provider=api_query_provider,
            research_page_provider=lambda query, _limit, _citation_id, _destination: page_result(query, citation(query)),
            diagnostic_root=Path(temporary),
        )
        server_instance = WEB.HavenWebServer(("127.0.0.1", 0), api_state)
        thread = threading.Thread(target=server_instance.serve_forever, daemon=True)
        thread.start()
        try:
            port = server_instance.server_port
            origin = f"http://127.0.0.1:{port}"
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", "/api/bootstrap", headers={"Host": f"127.0.0.1:{port}"})
            response = connection.getresponse()
            bootstrap = json.loads(response.read())
            connection.close()
            assert response.status == 200 and bootstrap["sessionToken"] == api_state.csrf_token; checks += 1

            def post(path: str, body: dict, token: str | None = None) -> tuple[int, dict]:
                payload = json.dumps(body, separators=(",", ":")).encode()
                client = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                client.request(
                    "POST", path, payload,
                    headers={
                        "Host": f"127.0.0.1:{port}",
                        "Origin": origin,
                        "Sec-Fetch-Site": "same-origin",
                        "Content-Type": "application/json",
                        "Content-Length": str(len(payload)),
                        "X-Haven-Token": token if token is not None else api_state.csrf_token,
                    },
                )
                api_response = client.getresponse()
                value = json.loads(api_response.read())
                status = api_response.status
                client.close()
                return status, value

            status, denied = post(
                "/api/research/query/prepare", {"query": "local AI", "resultLimit": 5}, "wrong"
            )
            assert status == 403 and denied == {"error": "invalid-session-token"}; checks += 1
            status, api_prepared = post(
                "/api/research/query/prepare", {"query": "local AI", "resultLimit": 5}
            )
            assert status == 200 and api_query_calls == []; checks += 1
            status, api_result = post(
                "/api/research/query/execute",
                {"approvalToken": api_prepared["approvalToken"], "confirmed": True},
            )
            assert status == 200 and api_result["kind"] == "wikipedia-research-query-result"; checks += 1
            assert api_query_calls == [("local AI", 5)]; checks += 1
            status, replay = post(
                "/api/research/query/execute",
                {"approvalToken": api_prepared["approvalToken"], "confirmed": True},
            )
            assert status == 409 and replay == {"error": "research-approval-invalid"}; checks += 1
            status, cleared = post("/api/research/clear", {})
            assert status == 200 and cleared["cleared"] is True; checks += 1
        finally:
            server_instance.shutdown()
            thread.join(timeout=5)
            server_instance.server_close()

    server = (ROOT / "web/server.py").read_text(encoding="utf-8")
    app = (ROOT / "web/static/app.js").read_text(encoding="utf-8")
    spec = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    for route in (
        "/api/research/query/prepare", "/api/research/query/execute",
        "/api/research/page/prepare", "/api/research/page/execute",
        "/api/research/clear",
    ):
        assert route in server and route in app
        checks += 1
    assert "innerHTML" not in app[app.index("function renderResearchQueryResult"):app.index("function updatePromptHistoryStatus")]; checks += 1
    assert "web_research_native_transport" in spec and "web_research_native_page_transport" in spec; checks += 1
    assert "validate-web-research-query-adapter.py" in spec; checks += 1

    print(f"Product web-research runtime passed {checks} hostile offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
