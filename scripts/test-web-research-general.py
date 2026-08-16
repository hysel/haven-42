#!/usr/bin/env python3
"""Focused hostile and end-to-end tests for approved general web research."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "web"))

import web_research_general_transport as GENERAL  # noqa: E402
import server as WEB  # noqa: E402


class Response:
    def __init__(self, body: bytes, content_type: str = "application/json", status: int = 200):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type, "Content-Encoding": "identity"}

    def getheader(self, name: str, default: str = "") -> str:
        return self.headers.get(name, default)

    def read(self, maximum: int) -> bytes:
        return self.body[:maximum]


class Connection:
    def __init__(self, response: Response):
        self.response = response
        self.request_details = None

    def request(self, method: str, path: str, headers: dict) -> None:
        self.request_details = (method, path, headers)

    def getresponse(self) -> Response:
        return self.response

    def close(self) -> None:
        return None


def expect_rejected(callable_value, code: str) -> None:
    try:
        callable_value()
    except GENERAL.GeneralResearchError as error:
        assert str(error) == code, (str(error), code)
    else:
        raise AssertionError(f"expected-{code}")


def main() -> int:
    checks = 0
    assert GENERAL.normalize_query("  recent   GPU models ") == "recent GPU models"
    checks += 1
    for value, code in [
        ("", "query-invalid"),
        ("<script>", "query-invalid"),
        ("api_key=secret", "query-credential-like"),
    ]:
        expect_rejected(lambda value=value: GENERAL.normalize_query(value), code)
        checks += 1
    expect_rejected(lambda: GENERAL.validate_api_key("short"), "api-key-invalid")
    checks += 1

    payload = json.dumps({"web": {"results": [
        {"title": "Safe result", "description": "A bounded public description.", "url": "https://example.com/report"},
        {"title": "Private", "description": "Must be rejected.", "url": "https://127.0.0.1/private"},
    ]}}).encode()
    connection = Connection(Response(payload))
    result = GENERAL.search(
        "recent GPU models", "a" * 32, 5,
        connection_factory=lambda _host: connection,
    )
    assert result["providerId"] == "brave-search-api"
    assert len(result["results"]) == 1
    assert result["results"][0]["displayDomain"] == "example.com"
    assert connection.request_details[2]["X-Subscription-Token"] == "a" * 32
    checks += 5

    html = b"<html><body><h1>Public report</h1><script>steal()</script><p>Useful text.</p><a href='https://tracker.example'>Source</a></body></html>"
    page = GENERAL.fetch_page(
        "https://example.com/report",
        connection_factory=lambda _host: Connection(Response(html, "text/html; charset=utf-8")),
    )
    text = " ".join(page["segments"])
    assert "Public report" in text and "Useful text." in text
    assert "steal" not in text and "tracker.example" not in text
    assert page["activeContentExecuted"] is False and page["filesWritten"] is False
    checks += 4

    citations = result["results"]
    citation_id = citations[0]["citationId"]
    synthesis_calls = []

    def fake_search(query, api_key, limit):
        assert api_key == "b" * 32
        return {**result, "query": query}

    def fake_page(destination):
        assert destination == "https://example.com/report"
        return {"segments": ["A verified fixture fact."], "contentCharacters": 24}

    def fake_synthesis(*args, **kwargs):
        synthesis_calls.append((args, kwargs))
        return {"message": {"content": json.dumps({
            "claims": [{"text": "The fixture reports a public fact.", "citationIds": [citation_id]}]
        })}}

    with tempfile.TemporaryDirectory() as temporary:
        state = WEB.HavenState(
            general_research_search_provider=fake_search,
            general_research_page_provider=fake_page,
            general_research_synthesis_provider=fake_synthesis,
            diagnostic_root=Path(temporary),
        )
        with state.lock:
            state.base_url = "http://127.0.0.1:11434"
            state.models = ("fixture-model:1",)
        prepared = state.prepare_general_web_research(
            "recent GPU models", "b" * 32, "fixture-model:1"
        )
        cancelled = state.prepare_general_web_research(
            "cancelled GPU search", "c" * 32, "fixture-model:1"
        )
        cancellation = state.cancel_research_approval(cancelled["approvalToken"])
        assert cancellation["cancelled"] is True and cancellation["networkUsed"] is False
        assert cancelled["approvalToken"] not in state.pending_research_approvals
        checks += 2
        answer = state.execute_general_web_research(prepared["approvalToken"])
        assert answer["kind"] == "general-web-research-answer"
        assert answer["claims"][0]["citationIds"] == [citation_id]
        assert answer["credentialPersisted"] is False
        assert synthesis_calls and "https://example.com/report" not in repr(synthesis_calls)
        checks += 6
        try:
            state.execute_general_web_research(prepared["approvalToken"])
        except WEB.WebRequestError as error:
            assert str(error) == "research-approval-invalid"
            checks += 1
        else:
            raise AssertionError("approval-token-replay")

    print(f"General web research passed: {checks} focused checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
