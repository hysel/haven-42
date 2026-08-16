#!/usr/bin/env python3
"""Hostile offline tests for the explicit native web-research query transport."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import socket


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "web_research_native_transport.py"
SPEC = importlib.util.spec_from_file_location("native_query", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def resolver_for(*addresses: str):
    def resolve(_host, port, *, type, proto):
        assert type == socket.SOCK_STREAM and proto == socket.IPPROTO_TCP
        return [
            (socket.AF_INET6 if ":" in address else socket.AF_INET, type, proto, "", (address, port, 0, 0) if ":" in address else (address, port))
            for address in addresses
        ]
    return resolve


class Response:
    status = 200

    def __init__(self, body: bytes, content_type: str = "application/json", content_encoding: str = ""):
        self.body = body
        self.content_type = content_type
        self.content_encoding = content_encoding

    def getheader(self, name: str, default: str = "") -> str:
        if name.casefold() == "content-type":
            return self.content_type
        if name.casefold() == "content-encoding":
            return self.content_encoding
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


def fixture() -> bytes:
    return json.dumps({
        "batchcomplete": True,
        "continue": {"continue": "-||", "sroffset": 1},
        "query": {
            "searchinfo": {"totalhits": 1},
            "search": [{
                "ns": 0, "pageid": 42,
                "timestamp": "2026-01-01T00:00:00Z",
                "title": "Local artificial intelligence",
            }],
        },
    }, separators=(",", ":")).encode()


def refused(callable_, code: str) -> None:
    try:
        callable_()
    except MODULE.NativeQueryError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"expected refusal: {code}")


def main() -> int:
    checks = 0
    contract = MODULE.load_contract()
    assert contract["authority"]["runtimeRouteAllowed"] is False; checks += 1
    assert contract["authority"]["modelToolAllowed"] is False; checks += 1
    assert contract["authority"]["pageRetrievalAllowed"] is False; checks += 1
    assert contract["authority"]["persistenceAllowed"] is False; checks += 1

    refused(lambda: MODULE.resolve_pinned_address("en.wikipedia.org", 443, resolver_for("127.0.0.1")), "dns-result-not-public"); checks += 1
    refused(lambda: MODULE.resolve_pinned_address("en.wikipedia.org", 443, resolver_for("192.0.2.1")), "dns-result-not-public"); checks += 1
    refused(lambda: MODULE.resolve_pinned_address("en.wikipedia.org", 443, resolver_for("169.254.1.1")), "dns-result-not-public"); checks += 1
    refused(lambda: MODULE.resolve_pinned_address("en.wikipedia.org", 443, resolver_for("::1")), "dns-result-not-public"); checks += 1

    made = []
    def factory(host, port, pinned_ip, timeout, context):
        connection = Connection(host, port, pinned_ip, timeout, context, response=Response(fixture()))
        made.append(connection)
        return connection
    result = MODULE.execute_query(
        "local artificial intelligence", 1,
        resolver=resolver_for("93.184.216.34"), connection_factory=factory,
    )
    assert result["status"] == "development-live-query-validated"; checks += 1
    assert result["networkAuthorityGranted"] is False; checks += 1
    assert result["runtimeAdmissionGranted"] is False; checks += 1
    assert result["pageRetrievalAllowed"] is False; checks += 1
    assert result["additionalResultsAvailable"] is True; checks += 1
    assert len(result["results"]) == 1 and result["results"][0]["activeNavigationAllowed"] is False; checks += 1
    connection = made[0]
    assert connection.created[2] == "93.184.216.34" and connection.created[3] == 10; checks += 1
    method, path, headers = connection.requested
    assert method == "GET" and path.startswith("/w/api.php?"); checks += 1
    assert headers["Host"] == "en.wikipedia.org" and "Authorization" not in headers and "Cookie" not in headers; checks += 1
    assert headers["Connection"] == "close" and headers["Accept-Encoding"] == "identity" and connection.closed; checks += 1

    def oversized_factory(*args):
        return Connection(*args, response=Response(b"x" * 65537))
    refused(lambda: MODULE.execute_query("safe query", 1, resolver=resolver_for("93.184.216.34"), connection_factory=oversized_factory), "provider-response-size"); checks += 1
    def wrong_type_factory(*args):
        return Connection(*args, response=Response(fixture(), "text/html"))
    refused(lambda: MODULE.execute_query("safe query", 1, resolver=resolver_for("93.184.216.34"), connection_factory=wrong_type_factory), "provider-content-type"); checks += 1
    def compressed_factory(*args):
        return Connection(*args, response=Response(fixture(), content_encoding="gzip"))
    refused(lambda: MODULE.execute_query("safe query", 1, resolver=resolver_for("93.184.216.34"), connection_factory=compressed_factory), "provider-content-encoding"); checks += 1

    print(f"Native web-research query transport passed {checks} offline security checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
