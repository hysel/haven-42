#!/usr/bin/env python3
"""Run one explicit, fixed-host development web-research metadata query."""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
from pathlib import Path
import socket
import ssl
import sys
import urllib.parse
from typing import Callable

import web_research_query_adapter as ADAPTER


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
CONTRACT_PATH = ROOT / "config" / "web-research-native-query-transport.json"


class NativeQueryError(ValueError):
    pass


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise NativeQueryError("invalid-native-query-contract") from error
    authority = value.get("authority", {})
    network = value.get("network", {})
    if (
        value.get("schemaVersion") != 1
        or value.get("status") != "owner-approved-fixed-provider-runtime"
        or value.get("providerId") != "wikipedia-query"
        or authority.get("explicitDevelopmentCliAllowed") is not True
        or authority.get("queryNetworkAllowed") is not True
        or any(
            authority.get(name) is not True
            for name in (
                "runtimeRouteAllowed", "uiControlAllowed",
                "pageRetrievalAllowed", "packageAdmissionAllowed",
            )
        )
        or any(
            authority.get(name) is not False
            for name in (
                "modelToolAllowed", "activeNavigationAllowed",
                "persistenceAllowed", "automaticFollowUpAllowed",
            )
        )
        or network.get("fixedHost") != "en.wikipedia.org"
        or network.get("fixedPort") != 443
        or network.get("fixedPath") != "/w/api.php"
        or network.get("systemTrustStoreRequired") is not True
        or network.get("dnsPassesRequired") != 2
        or network.get("publicIpOnly") is not True
        or network.get("selectedIpPinnedForConnection") is not True
        or network.get("redirectsAllowed") is not False
        or network.get("responseCompressionAllowed") is not False
        or network.get("proxyEnvironmentInherited") is not False
        or network.get("credentialsAllowed") is not False
        or network.get("cookiesAllowed") is not False
        or network.get("requiredContentType") != "application/json"
        or network.get("maximumResponseBytes") != 65536
        or network.get("timeoutSeconds") != 10
    ):
        raise NativeQueryError("unsafe-native-query-contract")
    return value


def _public_addresses(host: str, port: int, resolver: Callable = socket.getaddrinfo) -> set[str]:
    try:
        records = resolver(host, port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    except OSError as error:
        raise NativeQueryError("dns-resolution-failed") from error
    addresses: set[str] = set()
    for record in records:
        try:
            address = ipaddress.ip_address(record[4][0])
        except (IndexError, TypeError, ValueError) as error:
            raise NativeQueryError("dns-result-invalid") from error
        if not address.is_global:
            raise NativeQueryError("dns-result-not-public")
        addresses.add(address.compressed)
    if not addresses:
        raise NativeQueryError("dns-result-empty")
    return addresses


def resolve_pinned_address(host: str, port: int, resolver: Callable = socket.getaddrinfo) -> str:
    first = _public_addresses(host, port, resolver)
    second = _public_addresses(host, port, resolver)
    stable = first & second
    if not stable:
        raise NativeQueryError("dns-revalidation-failed")
    return sorted(stable, key=lambda value: (ipaddress.ip_address(value).version, value))[0]


class _PinnedHttpsConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, pinned_ip: str, timeout: int, context: ssl.SSLContext):
        super().__init__(host, port=port, timeout=timeout, context=context)
        self._pinned_ip = pinned_ip

    def connect(self) -> None:
        raw = socket.create_connection((self._pinned_ip, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def execute_query(
    query: object,
    result_limit: object,
    *,
    resolver: Callable = socket.getaddrinfo,
    connection_factory: Callable | None = None,
    contract_path: Path = CONTRACT_PATH,
) -> dict:
    contract = load_contract(contract_path)
    request = ADAPTER.build_request(query, result_limit)
    network = contract["network"]
    if (
        request["host"] != network["fixedHost"]
        or request["port"] != network["fixedPort"]
        or request["path"] != network["fixedPath"]
        or request["method"] != "GET"
        or request["credentials"] is not None
        or request["redirectsAllowed"] is not False
        or request["proxyEnvironmentInherited"] is not False
    ):
        raise NativeQueryError("query-request-escaped-contract")
    pinned_ip = resolve_pinned_address(request["host"], request["port"], resolver)
    path = request["path"] + "?" + urllib.parse.urlencode(
        sorted(request["parameters"].items()), quote_via=urllib.parse.quote
    )
    context = ssl.create_default_context()
    factory = connection_factory or _PinnedHttpsConnection
    connection = factory(
        request["host"], request["port"], pinned_ip,
        network["timeoutSeconds"], context,
    )
    try:
        connection.request(
            "GET", path,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "identity",
                "Connection": "close",
                "Host": request["host"],
                "User-Agent": "Haven42-Development-Web-Research/1",
            },
        )
        response = connection.getresponse()
        if response.status != 200:
            raise NativeQueryError(f"provider-http-{response.status}")
        content_type = response.getheader("Content-Type", "").split(";", 1)[0].strip().casefold()
        if content_type != network["requiredContentType"]:
            raise NativeQueryError("provider-content-type")
        content_encoding = response.getheader("Content-Encoding", "").strip().casefold()
        if content_encoding not in ("", "identity"):
            raise NativeQueryError("provider-content-encoding")
        payload = response.read(network["maximumResponseBytes"] + 1)
        if len(payload) > network["maximumResponseBytes"]:
            raise NativeQueryError("provider-response-size")
    except (OSError, ssl.SSLError, http.client.HTTPException) as error:
        raise NativeQueryError("provider-transport-failed") from error
    finally:
        connection.close()
    result = ADAPTER.validate_response(request, payload)
    result["status"] = "development-live-query-validated"
    result["transport"] = {
        "providerId": contract["providerId"],
        "tlsSystemTrust": True,
        "dnsRevalidated": True,
        "connectionPinnedToReviewedPublicIp": True,
        "redirectsFollowed": False,
        "credentialsSent": False,
        "cookiesSent": False,
        "proxyEnvironmentInherited": False,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()
    if not args.execute_live:
        parser.error("--execute-live is required for the explicit development network action")
    try:
        result = execute_query(args.query, args.limit)
    except (NativeQueryError, ADAPTER.QueryAdapterError) as error:
        print(json.dumps({"status": "refused", "code": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
