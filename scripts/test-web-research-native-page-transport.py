#!/usr/bin/env python3
"""Hostile offline tests for selected-page native transport."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import socket


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "web_research_native_page_transport.py"
SPEC = importlib.util.spec_from_file_location("native_page", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def resolver_for(*addresses: str):
    def resolve(_host, port, *, type, proto):
        assert type == socket.SOCK_STREAM and proto == socket.IPPROTO_TCP
        return [
            (
                socket.AF_INET6 if ":" in address else socket.AF_INET,
                type, proto, "",
                (address, port, 0, 0) if ":" in address else (address, port),
            )
            for address in addresses
        ]
    return resolve


class Response:
    status = 200

    def __init__(self, body: bytes, content_type: str = "application/json", encoding: str = ""):
        self.body = body
        self.content_type = content_type
        self.encoding = encoding

    def getheader(self, name: str, default: str = "") -> str:
        if name.casefold() == "content-type":
            return self.content_type
        if name.casefold() == "content-encoding":
            return self.encoding
        return default

    def read(self, amount: int) -> bytes:
        return self.body[:amount]


class Connection:
    def __init__(self, host, port, pinned_ip, timeout, context, *, response):
        self.created = (host, port, pinned_ip, timeout, context)
        self.response = response
        self.requested = None
        self.closed = False

    def request(self, method, path, headers):
        self.requested = (method, path, headers)

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


def query_result() -> dict:
    return {
        "schemaVersion": 1,
        "status": "development-live-query-validated",
        "queryDigest": hashlib.sha256(
            b"local artificial intelligence"
        ).hexdigest(),
        "results": [{
            "citationId": "source-" + "b" * 20,
            "title": "Local artificial intelligence",
            "displayDomain": "en.wikipedia.org",
            "destination": "https://en.wikipedia.org/?curid=42",
            "retrievedAt": "2026-01-01T00:00:00Z",
            "contentTrust": "untrusted-metadata-only",
            "destinationDisclosureRequired": True,
            "activeNavigationAllowed": False,
        }],
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


def page_body(**updates) -> bytes:
    page = {
        "pageid": 42, "ns": 0, "title": "Local artificial intelligence",
        "extract": "Local AI runs on a user's device.\nThis is untrusted source text.",
    }
    page.update(updates)
    return json.dumps(
        {"batchcomplete": True, "query": {"pages": [page]}},
        separators=(",", ":"),
    ).encode()


def refused(callable_, code: str) -> None:
    try:
        callable_()
    except (
        MODULE.NativePageError,
        MODULE.QUERY.NativeQueryError,
        MODULE.QUERY.ADAPTER.QueryAdapterError,
    ) as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"expected refusal: {code}")


def main() -> int:
    checks = 0
    contract = MODULE.load_contract()
    for name in ("runtimeRouteAllowed", "uiControlAllowed", "packageAdmissionAllowed"):
        assert contract["authority"][name] is True
        checks += 1
    for name in (
        "modelToolAllowed", "persistenceAllowed", "automaticFollowUpAllowed",
        "pageExecutionAllowed", "downloadAllowed",
    ):
        assert contract["authority"][name] is False
        checks += 1

    made = []
    def query_executor(query, limit):
        assert query == "local artificial intelligence" and limit == 1
        return query_result()
    def factory(host, port, pinned_ip, timeout, context):
        connection = Connection(host, port, pinned_ip, timeout, context, response=Response(page_body()))
        made.append(connection)
        return connection

    result = MODULE.execute_selected_page(
        "local artificial intelligence", 1,
        "source-" + "b" * 20, "https://en.wikipedia.org/?curid=42",
        query_executor=query_executor,
        resolver=resolver_for("93.184.216.34"),
        connection_factory=factory,
    )
    assert result["status"] == "development-live-selected-page-validated"; checks += 1
    assert result["developmentNetworkUsed"] is True; checks += 1
    assert result["runtimeAdmissionGranted"] is False; checks += 1
    assert result["packageAdmissionGranted"] is False; checks += 1
    assert result["activeNavigationAllowed"] is False; checks += 1
    assert result["pageExecutionAllowed"] is False; checks += 1
    assert result["automaticFollowUpAllowed"] is False; checks += 1
    assert result["filesWritten"] is False; checks += 1
    assert [item["text"] for item in result["segments"]] == [
        "Local AI runs on a user's device.", "This is untrusted source text.",
    ]; checks += 1
    assert all(item["trust"] == "untrusted-inert-text" for item in result["segments"]); checks += 1
    summary = MODULE.sanitized_summary(result)
    assert "segments" not in summary and summary["segmentCount"] == 2; checks += 1
    assert summary["contentDigest"] == result["contentDigest"]; checks += 1
    connection = made[0]
    method, path, headers = connection.requested
    assert connection.created[2] == "93.184.216.34" and connection.created[3] == 10; checks += 1
    assert method == "GET" and "pageids=42" in path and path.startswith("/w/api.php?"); checks += 1
    assert headers["Host"] == "en.wikipedia.org" and "Authorization" not in headers and "Cookie" not in headers; checks += 1
    assert headers["Accept-Encoding"] == "identity" and connection.closed; checks += 1

    common = dict(
        query_executor=query_executor,
        resolver=resolver_for("93.184.216.34"),
        connection_factory=factory,
    )
    refused(lambda: MODULE.execute_selected_page(
        " local artificial intelligence ", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42", **common,
    ), "query-not-exactly-normalized"); checks += 1
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "c" * 20,
        "https://en.wikipedia.org/?curid=42", **common,
    ), "selected-citation-untrusted"); checks += 1
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://example.com/?curid=42", **common,
    ), "selected-citation-untrusted"); checks += 1
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=43", **common,
    ), "selected-citation-untrusted"); checks += 1

    bad_query = query_result()
    bad_query["runtimeAdmissionGranted"] = True
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42", query_executor=lambda *_: bad_query,
        resolver=resolver_for("93.184.216.34"), connection_factory=factory,
    ), "selected-citation-untrusted"); checks += 1

    bad_digest = query_result()
    bad_digest["queryDigest"] = "a" * 64
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42", query_executor=lambda *_: bad_digest,
        resolver=resolver_for("93.184.216.34"), connection_factory=factory,
    ), "selected-citation-untrusted"); checks += 1

    bad_transport = query_result()
    bad_transport["transport"] = dict(bad_transport["transport"])
    bad_transport["transport"]["dnsRevalidated"] = False
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42", query_executor=lambda *_: bad_transport,
        resolver=resolver_for("93.184.216.34"), connection_factory=factory,
    ), "selected-citation-untrusted"); checks += 1

    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42", query_executor=query_executor,
        resolver=resolver_for("127.0.0.1"), connection_factory=factory,
    ), "dns-result-not-public"); checks += 1

    def custom_factory(response):
        return lambda *args: Connection(*args, response=response)
    base = dict(
        query_executor=query_executor, resolver=resolver_for("93.184.216.34")
    )
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42",
        connection_factory=custom_factory(Response(b"x" * 262145)), **base,
    ), "page-response-size"); checks += 1
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42",
        connection_factory=custom_factory(Response(page_body(), "text/html")), **base,
    ), "page-provider-content-type"); checks += 1
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42",
        connection_factory=custom_factory(Response(page_body(), encoding="gzip")), **base,
    ), "page-provider-content-encoding"); checks += 1
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42",
        connection_factory=custom_factory(Response(page_body(pageid=43))), **base,
    ), "page-response-identity"); checks += 1
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42",
        connection_factory=custom_factory(Response(page_body(title="Changed"))), **base,
    ), "page-response-identity"); checks += 1
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42",
        connection_factory=custom_factory(Response(page_body(extract=""))), **base,
    ), "page-extract-page-byte-budget"); checks += 1
    duplicate = b'{"batchcomplete":true,"batchcomplete":true,"query":{"pages":[]}}'
    refused(lambda: MODULE.execute_selected_page(
        "local artificial intelligence", 1, "source-" + "b" * 20,
        "https://en.wikipedia.org/?curid=42",
        connection_factory=custom_factory(Response(duplicate)), **base,
    ), "page-response-json"); checks += 1

    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".py", ".js", ".html", ".css", ".json"}
    )
    assert "web_research_native_page_transport" in runtime; checks += 1
    assert "web_research_native_page_transport" in (
        ROOT / "package/haven42.spec"
    ).read_text(encoding="utf-8"); checks += 1

    print(f"Native selected-page transport passed {checks} offline security checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
