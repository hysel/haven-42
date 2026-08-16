#!/usr/bin/env python3
"""Retrieve one explicitly selected Wikipedia page as bounded inert text."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
from pathlib import Path
import re
import socket
import ssl
import sys
import urllib.parse
from typing import Callable

import offline_research_page_text as PAGE_TEXT
import web_research_native_transport as QUERY


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
CONTRACT_PATH = ROOT / "config" / "web-research-native-page-transport.json"
DESTINATION = re.compile(r"^https://en\.wikipedia\.org/\?curid=([1-9][0-9]{0,18})$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CITATION = re.compile(r"^source-[0-9a-f]{20}$")


class NativePageError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate-json-key")
        result[key] = value
    return result


def _validate_json_shape(value: object, maximum_depth: int, maximum_nodes: int) -> None:
    pending = [(value, 0)]
    nodes = 0
    while pending:
        current, depth = pending.pop()
        if depth > maximum_depth:
            raise NativePageError("page-response-depth")
        if isinstance(current, (dict, list)):
            nodes += 1
            if nodes > maximum_nodes:
                raise NativePageError("page-response-complexity")
            pending.extend(
                (item, depth + 1)
                for item in (current.values() if isinstance(current, dict) else current)
            )


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise NativePageError("invalid-native-page-contract") from error
    network = value.get("network", {})
    selection = value.get("selection", {})
    authority = value.get("authority", {})
    expected_parameters = {
        "action": "query", "exintro": "1", "explaintext": "1",
        "format": "json", "formatversion": "2", "prop": "extracts",
        "redirects": "0",
    }
    if (
        value.get("schemaVersion") != 1
        or value.get("status") != "owner-approved-fixed-provider-runtime"
        or value.get("providerId") != "wikipedia-page-extract"
        or network.get("fixedHost") != "en.wikipedia.org"
        or network.get("fixedPort") != 443
        or network.get("fixedPath") != "/w/api.php"
        or network.get("fixedParameters") != expected_parameters
        or network.get("pageIdParameter") != "pageids"
        or network.get("systemTrustStoreRequired") is not True
        or network.get("dnsPassesRequired") != 2
        or network.get("publicIpOnly") is not True
        or network.get("selectedIpPinnedForConnection") is not True
        or network.get("redirectsAllowed") is not False
        or network.get("responseCompressionAllowed") is not False
        or network.get("proxyEnvironmentInherited") is not False
        or network.get("credentialsAllowed") is not False
        or network.get("cookiesAllowed") is not False
        or network.get("timeoutSeconds") != 10
        or network.get("maximumResponseBytes") != 262144
        or network.get("maximumJsonDepth") != 8
        or network.get("maximumJsonNodes") != 2048
        or network.get("requiredContentType") != "application/json"
        or set(selection) != {
            "exactNormalizedQueryRequired", "trustedCitationIdRequired",
            "exactEngineDerivedDestinationRequired",
            "queryIsRevalidatedBeforePageRetrieval", "oneSelectedPagePerProcess",
            "modelCannotApprove",
        }
        or any(item is not True for item in selection.values())
        or authority.get("explicitDevelopmentCliAllowed") is not True
        or authority.get("selectedPageNetworkAllowed") is not True
        or any(
            authority.get(name) is not True
            for name in (
                "runtimeRouteAllowed", "uiControlAllowed",
                "packageAdmissionAllowed",
            )
        )
        or any(
            authority.get(name) is not False
            for name in (
                "modelToolAllowed", "activeNavigationAllowed",
                "persistenceAllowed", "automaticFollowUpAllowed",
                "pageExecutionAllowed", "downloadAllowed",
            )
        )
    ):
        raise NativePageError("unsafe-native-page-contract")
    return value


def _selected_result(
    query_result: object,
    citation_id: object,
    destination: object,
    expected_query_digest: str,
) -> dict:
    expected_query_fields = {
        "schemaVersion", "status", "queryDigest", "results",
        "additionalResultsAvailable", "networkAuthorityGranted",
        "runtimeAdmissionGranted", "pageRetrievalAllowed", "transport",
    }
    expected_transport = {
        "providerId": "wikipedia-query",
        "tlsSystemTrust": True,
        "dnsRevalidated": True,
        "connectionPinnedToReviewedPublicIp": True,
        "redirectsFollowed": False,
        "credentialsSent": False,
        "cookiesSent": False,
        "proxyEnvironmentInherited": False,
    }
    if (
        not isinstance(citation_id, str)
        or not CITATION.fullmatch(citation_id)
        or not isinstance(destination, str)
        or not DESTINATION.fullmatch(destination)
        or not isinstance(query_result, dict)
        or set(query_result) != expected_query_fields
        or query_result.get("schemaVersion") != 1
        or query_result.get("status") != "development-live-query-validated"
        or not isinstance(query_result.get("queryDigest"), str)
        or not SHA256.fullmatch(query_result["queryDigest"])
        or query_result["queryDigest"] != expected_query_digest
        or not isinstance(query_result.get("additionalResultsAvailable"), bool)
        or query_result.get("networkAuthorityGranted") is not False
        or query_result.get("runtimeAdmissionGranted") is not False
        or query_result.get("pageRetrievalAllowed") is not False
        or not isinstance(query_result.get("results"), list)
        or query_result.get("transport") != expected_transport
    ):
        raise NativePageError("selected-citation-untrusted")
    matches = [
        item for item in query_result["results"]
        if isinstance(item, dict)
        and item.get("citationId") == citation_id
        and item.get("destination") == destination
    ]
    if len(matches) != 1:
        raise NativePageError("selected-citation-untrusted")
    selected = matches[0]
    if (
        set(selected) != {
            "citationId", "title", "displayDomain", "destination", "retrievedAt",
            "contentTrust", "destinationDisclosureRequired", "activeNavigationAllowed",
        }
        or selected.get("displayDomain") != "en.wikipedia.org"
        or selected.get("contentTrust") != "untrusted-metadata-only"
        or selected.get("destinationDisclosureRequired") is not True
        or selected.get("activeNavigationAllowed") is not False
        or not isinstance(selected.get("title"), str)
        or not selected["title"]
    ):
        raise NativePageError("selected-citation-untrusted")
    return selected


def _parse_page_response(data: bytes, page_id: int, title: str, contract: dict) -> dict:
    limits = contract["network"]
    if not isinstance(data, bytes) or not data or len(data) > limits["maximumResponseBytes"]:
        raise NativePageError("page-response-size")
    try:
        payload = json.loads(
            data.decode("utf-8", errors="strict"),
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("non-finite")),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise NativePageError("page-response-json") from error
    _validate_json_shape(payload, limits["maximumJsonDepth"], limits["maximumJsonNodes"])
    if not isinstance(payload, dict) or set(payload) != {"batchcomplete", "query"} or payload["batchcomplete"] is not True:
        raise NativePageError("page-response-fields")
    query = payload["query"]
    if not isinstance(query, dict) or set(query) != {"pages"}:
        raise NativePageError("page-response-fields")
    pages = query["pages"]
    if not isinstance(pages, list) or len(pages) != 1:
        raise NativePageError("page-response-count")
    page = pages[0]
    if not isinstance(page, dict) or set(page) != {"extract", "ns", "pageid", "title"}:
        raise NativePageError("page-response-fields")
    if page["pageid"] != page_id or page["ns"] != 0 or page["title"] != title:
        raise NativePageError("page-response-identity")
    if not isinstance(page["extract"], str):
        raise NativePageError("page-response-extract")
    try:
        return PAGE_TEXT.extract("text/plain", page["extract"].encode("utf-8", errors="strict"))
    except (UnicodeError, PAGE_TEXT.PageRejected) as error:
        raise NativePageError(f"page-extract-{error}") from error


def execute_selected_page(
    query: object,
    result_limit: object,
    citation_id: object,
    destination: object,
    *,
    query_executor: Callable | None = None,
    resolver: Callable = socket.getaddrinfo,
    connection_factory: Callable | None = None,
    contract_path: Path = CONTRACT_PATH,
) -> dict:
    contract = load_contract(contract_path)
    query_request = QUERY.ADAPTER.build_request(query, result_limit)
    normalized_query = query_request["parameters"]["srsearch"]
    if normalized_query != query:
        raise NativePageError("query-not-exactly-normalized")
    execute_query = query_executor or QUERY.execute_query
    query_result = execute_query(query, result_limit)
    expected_query_digest = hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()
    selected = _selected_result(
        query_result, citation_id, destination, expected_query_digest
    )
    match = DESTINATION.fullmatch(destination)
    assert match is not None
    page_id = int(match.group(1))
    if page_id > 2**63 - 1:
        raise NativePageError("selected-citation-untrusted")
    network = contract["network"]
    parameters = dict(network["fixedParameters"])
    parameters[network["pageIdParameter"]] = str(page_id)
    path = network["fixedPath"] + "?" + urllib.parse.urlencode(
        sorted(parameters.items()), quote_via=urllib.parse.quote
    )
    pinned_ip = QUERY.resolve_pinned_address(
        network["fixedHost"], network["fixedPort"], resolver
    )
    context = ssl.create_default_context()
    factory = connection_factory or QUERY._PinnedHttpsConnection
    connection = factory(
        network["fixedHost"], network["fixedPort"], pinned_ip,
        network["timeoutSeconds"], context,
    )
    try:
        connection.request(
            "GET", path,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "identity",
                "Connection": "close",
                "Host": network["fixedHost"],
                "User-Agent": "Haven42-Development-Web-Research/1",
            },
        )
        response = connection.getresponse()
        if response.status != 200:
            raise NativePageError(f"page-provider-http-{response.status}")
        content_type = response.getheader("Content-Type", "").split(";", 1)[0].strip().casefold()
        if content_type != network["requiredContentType"]:
            raise NativePageError("page-provider-content-type")
        encoding = response.getheader("Content-Encoding", "").strip().casefold()
        if encoding not in ("", "identity"):
            raise NativePageError("page-provider-content-encoding")
        body = response.read(network["maximumResponseBytes"] + 1)
        if len(body) > network["maximumResponseBytes"]:
            raise NativePageError("page-response-size")
    except (OSError, ssl.SSLError, http.client.HTTPException) as error:
        raise NativePageError("page-provider-transport-failed") from error
    finally:
        connection.close()
    extracted = _parse_page_response(body, page_id, selected["title"], contract)
    return {
        "schemaVersion": 1,
        "status": "development-live-selected-page-validated",
        "queryDigest": query_result["queryDigest"],
        "source": selected,
        "contentDigest": hashlib.sha256(
            "\n".join(item["text"] for item in extracted["segments"]).encode("utf-8")
        ).hexdigest(),
        "segments": extracted["segments"],
        "contentCharacters": extracted["contentCharacters"],
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


def sanitized_summary(result: object) -> dict:
    if (
        not isinstance(result, dict)
        or result.get("status") != "development-live-selected-page-validated"
        or not isinstance(result.get("source"), dict)
        or not isinstance(result.get("segments"), list)
    ):
        raise NativePageError("page-summary-input")
    source = result["source"]
    return {
        "schemaVersion": 1,
        "status": result["status"],
        "queryDigest": result["queryDigest"],
        "citationId": source["citationId"],
        "title": source["title"],
        "displayDomain": source["displayDomain"],
        "destination": source["destination"],
        "destinationDisclosureRequired": source["destinationDisclosureRequired"],
        "contentDigest": result["contentDigest"],
        "segmentCount": len(result["segments"]),
        "contentCharacters": result["contentCharacters"],
        "developmentNetworkUsed": result["developmentNetworkUsed"],
        "dnsRevalidated": result["dnsRevalidated"],
        "connectionPinnedToReviewedPublicIp": result["connectionPinnedToReviewedPublicIp"],
        "redirectsFollowed": result["redirectsFollowed"],
        "credentialsSent": result["credentialsSent"],
        "cookiesSent": result["cookiesSent"],
        "proxyEnvironmentInherited": result["proxyEnvironmentInherited"],
        "activeNavigationAllowed": result["activeNavigationAllowed"],
        "pageExecutionAllowed": result["pageExecutionAllowed"],
        "automaticFollowUpAllowed": result["automaticFollowUpAllowed"],
        "filesWritten": result["filesWritten"],
        "runtimeAdmissionGranted": result["runtimeAdmissionGranted"],
        "packageAdmissionGranted": result["packageAdmissionGranted"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--citation-id", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    if not args.execute_live:
        parser.error("--execute-live is required for this explicit development network action")
    try:
        result = execute_selected_page(
            args.query, args.limit, args.citation_id, args.destination
        )
    except (NativePageError, QUERY.NativeQueryError, QUERY.ADAPTER.QueryAdapterError) as error:
        print(json.dumps({"status": "refused", "code": str(error)}, sort_keys=True))
        return 1
    output = sanitized_summary(result) if args.summary_only else result
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
