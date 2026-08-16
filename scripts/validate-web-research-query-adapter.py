#!/usr/bin/env python3
"""Validate a fixed query adapter through a caller-supplied inert transport."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
import re
from typing import Callable
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "web-research-query-adapter.json"
QUERY_CREDENTIAL = re.compile(r"(?i)\b(password|passwd|token|secret|api[-_ ]?key|authorization)\s*[:=]")


class QueryAdapterError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate-json-key")
        result[key] = value
    return result


def _contains_unsafe_text(value: str) -> bool:
    return (
        "<" in value
        or ">" in value
        or any(unicodedata.category(character).startswith("C") for character in value)
    )


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise QueryAdapterError("invalid-query-adapter-contract") from error
    if value.get("schemaVersion") != 1 or value.get("status") != "development-disabled-transport-unbound":
        raise QueryAdapterError("invalid-query-adapter-contract")
    authority = value.get("authority", {})
    if not authority or any(flag is not False for flag in authority.values()):
        raise QueryAdapterError("unsafe-query-adapter-contract")
    provider = value.get("provider", {})
    if (
        provider.get("method") != "GET"
        or provider.get("scheme") != "https"
        or provider.get("host") != "en.wikipedia.org"
        or provider.get("port") != 443
        or provider.get("path") != "/w/api.php"
    ):
        raise QueryAdapterError("unsafe-query-adapter-contract")
    transport = value.get("transportRequirements", {})
    if transport.get("redirectsAllowed") is not False or transport.get("proxyEnvironmentInherited") is not False:
        raise QueryAdapterError("unsafe-query-adapter-contract")
    return value


def _bounded_query(value: object, maximum: int) -> str:
    if not isinstance(value, str):
        raise QueryAdapterError("query-type")
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > maximum:
        raise QueryAdapterError("query-size")
    if _contains_unsafe_text(value):
        raise QueryAdapterError("query-active-content")
    if QUERY_CREDENTIAL.search(normalized):
        raise QueryAdapterError("query-credential-like")
    return normalized


def build_request(query: object, result_limit: object, contract_path: Path = CONTRACT_PATH) -> dict:
    contract = load_contract(contract_path)
    limits = contract["limits"]
    normalized = _bounded_query(query, limits["maximumQueryCharacters"])
    if isinstance(result_limit, bool) or not isinstance(result_limit, int) or not 1 <= result_limit <= limits["maximumResults"]:
        raise QueryAdapterError("result-limit")
    provider = contract["provider"]
    parameters = dict(provider["fixedParameters"])
    parameters[provider["queryParameter"]] = normalized
    parameters[provider["limitParameter"]] = str(result_limit)
    return {
        "schemaVersion": 1,
        "providerId": provider["id"],
        "method": provider["method"],
        "scheme": provider["scheme"],
        "host": provider["host"],
        "port": provider["port"],
        "path": provider["path"],
        "parameters": parameters,
        "headers": {"Accept": "application/json"},
        "credentials": None,
        "redirectsAllowed": False,
        "proxyEnvironmentInherited": False,
    }


def _validate_json_shape(value: object, maximum_depth: int, maximum_nodes: int) -> None:
    pending = [(value, 0)]
    nodes = 0
    while pending:
        current, depth = pending.pop()
        if depth > maximum_depth:
            raise QueryAdapterError("response-depth")
        if isinstance(current, (dict, list)):
            nodes += 1
            if nodes > maximum_nodes:
                raise QueryAdapterError("response-complexity")
            pending.extend((item, depth + 1) for item in (current.values() if isinstance(current, dict) else current))


def validate_response(request: dict, response: object, contract_path: Path = CONTRACT_PATH) -> dict:
    contract = load_contract(contract_path)
    limits = contract["limits"]
    if not isinstance(request, dict):
        raise QueryAdapterError("request-shape")
    try:
        parameters = request["parameters"]
        query_value = parameters[contract["provider"]["queryParameter"]]
        result_limit = int(parameters[contract["provider"]["limitParameter"]])
    except (KeyError, TypeError, ValueError) as error:
        raise QueryAdapterError("request-shape") from error
    if request != build_request(query_value, result_limit, contract_path):
        raise QueryAdapterError("request-shape")
    if not isinstance(response, bytes) or len(response) > limits["maximumResponseBytes"]:
        raise QueryAdapterError("response-size")
    try:
        payload = json.loads(
            response.decode("utf-8", errors="strict"),
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("non-finite-number")),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise QueryAdapterError("response-json") from error
    _validate_json_shape(payload, limits["maximumJsonDepth"], limits["maximumJsonNodes"])
    if (
        not isinstance(payload, dict)
        or set(payload) not in ({"batchcomplete", "query"}, {"batchcomplete", "continue", "query"})
        or payload["batchcomplete"] is not True
    ):
        raise QueryAdapterError("response-fields")
    continuation = payload.get("continue")
    if continuation is not None and (
        not isinstance(continuation, dict)
        or set(continuation) != {"continue", "sroffset"}
        or continuation["continue"] != "-||"
        or isinstance(continuation["sroffset"], bool)
        or not isinstance(continuation["sroffset"], int)
        or not 1 <= continuation["sroffset"] <= 2**63 - 1
    ):
        raise QueryAdapterError("response-continuation")
    query = payload.get("query")
    if not isinstance(query, dict) or set(query) != {"searchinfo", "search"}:
        raise QueryAdapterError("response-query-fields")
    search_info = query["searchinfo"]
    if (
        not isinstance(search_info, dict)
        or set(search_info) != {"totalhits"}
        or isinstance(search_info["totalhits"], bool)
        or not isinstance(search_info["totalhits"], int)
        or not 0 <= search_info["totalhits"] <= 2**63 - 1
    ):
        raise QueryAdapterError("response-search-info")
    raw_results = query.get("search")
    requested_limit = int(request["parameters"][contract["provider"]["limitParameter"]])
    if not isinstance(raw_results, list) or len(raw_results) > requested_limit:
        raise QueryAdapterError("response-result-count")
    results = []
    seen: set[int] = set()
    for index, item in enumerate(raw_results, 1):
        if not isinstance(item, dict) or set(item) != {"ns", "pageid", "timestamp", "title"}:
            raise QueryAdapterError("response-result-fields")
        page_id = item["pageid"]
        if isinstance(page_id, bool) or not isinstance(page_id, int) or not 1 <= page_id <= 2**63 - 1 or page_id in seen:
            raise QueryAdapterError("response-page-id")
        title = item["title"]
        if not isinstance(title, str) or not title or len(title) > limits["maximumTitleCharacters"]:
            raise QueryAdapterError("response-title")
        if _contains_unsafe_text(title):
            raise QueryAdapterError("response-title-active-content")
        if (
            isinstance(item["ns"], bool)
            or item["ns"] != 0
        ):
            raise QueryAdapterError("response-result-values")
        if not isinstance(item["timestamp"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", item["timestamp"]):
            raise QueryAdapterError("response-timestamp")
        try:
            datetime.strptime(item["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as error:
            raise QueryAdapterError("response-timestamp") from error
        seen.add(page_id)
        citation = hashlib.sha256(f"{request['parameters']['srsearch']}\0{index}\0{page_id}".encode()).hexdigest()[:20]
        results.append({
            "citationId": f"source-{citation}",
            "title": title,
            "displayDomain": "en.wikipedia.org",
            "destination": f"https://en.wikipedia.org/?curid={page_id}",
            "retrievedAt": item["timestamp"],
            "contentTrust": "untrusted-metadata-only",
            "destinationDisclosureRequired": True,
            "activeNavigationAllowed": False,
        })
    return {
        "schemaVersion": 1,
        "status": "development-transport-shape-validated",
        "queryDigest": hashlib.sha256(request["parameters"]["srsearch"].encode()).hexdigest(),
        "results": results,
        "additionalResultsAvailable": continuation is not None,
        "networkAuthorityGranted": False,
        "runtimeAdmissionGranted": False,
        "pageRetrievalAllowed": False,
    }


def exercise_fixture_transport(query: object, result_limit: object, transport: Callable[[dict], bytes]) -> dict:
    if not callable(transport):
        raise QueryAdapterError("fixture-transport-required")
    request = build_request(query, result_limit)
    return validate_response(request, transport(request))


if __name__ == "__main__":
    print(json.dumps({"status": "development-disabled-transport-unbound", "networkAuthority": False}))
