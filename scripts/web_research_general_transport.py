#!/usr/bin/env python3
"""Bounded Brave Search and public-page text transport for approved research."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import http.client
import ipaddress
import json
import re
import socket
import ssl
import urllib.parse
from datetime import datetime, timezone
from typing import Callable

import web_research_native_transport as FIXED


SEARCH_HOST = "api.search.brave.com"
SEARCH_PATH = "/res/v1/web/search"
MAX_SEARCH_BYTES = 262_144
MAX_PAGE_BYTES = 524_288
MAX_PAGE_CHARACTERS = 12_000
MAX_RESULTS = 5
TIMEOUT_SECONDS = 12
TOKEN = re.compile(r"^[A-Za-z0-9._~-]{20,512}$")
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


class GeneralResearchError(ValueError):
    pass


def normalize_query(value: object) -> str:
    if not isinstance(value, str):
        raise GeneralResearchError("query-type")
    result = " ".join(value.split())
    if not result or len(result) > 256 or CONTROL.search(result) or "<" in result or ">" in result:
        raise GeneralResearchError("query-invalid")
    if re.search(r"(?i)\b(password|passwd|token|secret|api[-_ ]?key|authorization)\s*[:=]", result):
        raise GeneralResearchError("query-credential-like")
    return result


def validate_api_key(value: object) -> str:
    if not isinstance(value, str) or TOKEN.fullmatch(value) is None:
        raise GeneralResearchError("api-key-invalid")
    return value


def _bounded_text(value: object, maximum: int, field: str) -> str:
    if not isinstance(value, str):
        raise GeneralResearchError(f"{field}-type")
    result = " ".join(value.split())
    if not result or len(result) > maximum or CONTROL.search(result) or "<" in result or ">" in result:
        raise GeneralResearchError(f"{field}-invalid")
    return result


def _public_destination(value: object) -> tuple[str, str, str]:
    if not isinstance(value, str) or len(value) > 2048:
        raise GeneralResearchError("destination-invalid")
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise GeneralResearchError("destination-invalid") from error
    if (
        parsed.scheme != "https" or not parsed.hostname or port not in (None, 443)
        or parsed.username is not None or parsed.password is not None
    ):
        raise GeneralResearchError("destination-https-required")
    host = parsed.hostname.casefold().rstrip(".")
    if host == "localhost" or host.endswith((".localhost", ".local")):
        raise GeneralResearchError("destination-public-required")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", host) is None:
            raise GeneralResearchError("destination-host-invalid")
    else:
        if not address.is_global:
            raise GeneralResearchError("destination-public-required")
    canonical = urllib.parse.urlunsplit(("https", host, parsed.path or "/", parsed.query, ""))
    return canonical, host, (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else "")


def _connection(host: str, resolver: Callable = socket.getaddrinfo):
    pinned = FIXED.resolve_pinned_address(host, 443, resolver)
    return FIXED._PinnedHttpsConnection(
        host, 443, pinned, TIMEOUT_SECONDS, ssl.create_default_context()
    )


def search(
    query: object,
    api_key: object,
    result_limit: object = MAX_RESULTS,
    *,
    resolver: Callable = socket.getaddrinfo,
    connection_factory: Callable | None = None,
) -> dict:
    normalized = normalize_query(query)
    key = validate_api_key(api_key)
    if isinstance(result_limit, bool) or not isinstance(result_limit, int) or not 1 <= result_limit <= MAX_RESULTS:
        raise GeneralResearchError("result-limit")
    parameters = urllib.parse.urlencode({"q": normalized, "count": str(result_limit), "safesearch": "moderate"})
    factory = connection_factory or (lambda host: _connection(host, resolver))
    connection = factory(SEARCH_HOST)
    try:
        connection.request("GET", f"{SEARCH_PATH}?{parameters}", headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close",
            "Host": SEARCH_HOST,
            "User-Agent": "Haven42-Web-Research/1",
            "X-Subscription-Token": key,
        })
        response = connection.getresponse()
        if response.status != 200:
            raise GeneralResearchError(f"search-provider-http-{response.status}")
        content_type = response.getheader("Content-Type", "").split(";", 1)[0].strip().casefold()
        if content_type != "application/json":
            raise GeneralResearchError("search-provider-content-type")
        if response.getheader("Content-Encoding", "").strip().casefold() not in ("", "identity"):
            raise GeneralResearchError("search-provider-content-encoding")
        body = response.read(MAX_SEARCH_BYTES + 1)
        if len(body) > MAX_SEARCH_BYTES:
            raise GeneralResearchError("search-provider-size")
    except (OSError, ssl.SSLError, http.client.HTTPException) as error:
        raise GeneralResearchError("search-provider-transport-failed") from error
    finally:
        connection.close()
    try:
        payload = json.loads(body.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise GeneralResearchError("search-provider-json") from error
    raw_results = payload.get("web", {}).get("results") if isinstance(payload, dict) else None
    if not isinstance(raw_results, list):
        raise GeneralResearchError("search-provider-shape")
    retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []
    seen = set()
    for raw in raw_results:
        if len(results) >= result_limit:
            break
        if not isinstance(raw, dict):
            continue
        try:
            destination, domain, _path = _public_destination(raw.get("url"))
            title = _bounded_text(raw.get("title"), 200, "title")
            excerpt = _bounded_text(raw.get("description"), 500, "excerpt")
        except GeneralResearchError:
            continue
        if destination in seen:
            continue
        seen.add(destination)
        citation_id = "source-" + hashlib.sha256(
            f"brave\0{normalized}\0{len(results) + 1}\0{destination}".encode("utf-8")
        ).hexdigest()[:20]
        results.append({
            "citationId": citation_id,
            "title": title,
            "excerpt": excerpt,
            "displayDomain": domain,
            "destination": destination,
            "retrievedAt": retrieved,
            "contentTrust": "untrusted-metadata-only",
            "activeNavigationAllowed": False,
        })
    if not results:
        raise GeneralResearchError("search-provider-no-results")
    return {
        "query": normalized,
        "results": results,
        "providerId": "brave-search-api",
        "networkUsed": True,
        "credentialsSentOnlyToProvider": True,
        "filesWritten": False,
    }


class _TextExtractor(HTMLParser):
    BLOCKED = {"script", "style", "noscript", "svg", "canvas", "template"}
    BREAKS = {"p", "li", "article", "section", "div", "h1", "h2", "h3", "h4", "h5", "h6", "br"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocked = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        value = tag.casefold()
        if value in self.BLOCKED:
            self.blocked += 1
        elif not self.blocked and value in self.BREAKS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        value = tag.casefold()
        if value in self.BLOCKED and self.blocked:
            self.blocked -= 1
        elif not self.blocked and value in self.BREAKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.blocked:
            self.parts.append(data)


def fetch_page(
    destination: object,
    *,
    resolver: Callable = socket.getaddrinfo,
    connection_factory: Callable | None = None,
) -> dict:
    canonical, host, path = _public_destination(destination)
    factory = connection_factory or (lambda name: _connection(name, resolver))
    connection = factory(host)
    try:
        connection.request("GET", path, headers={
            "Accept": "text/html,text/plain;q=0.9",
            "Accept-Encoding": "identity",
            "Connection": "close",
            "Host": host,
            "User-Agent": "Haven42-Web-Research/1",
        })
        response = connection.getresponse()
        if response.status != 200:
            raise GeneralResearchError(f"page-http-{response.status}")
        media_type = response.getheader("Content-Type", "").split(";", 1)[0].strip().casefold()
        if media_type not in {"text/html", "text/plain"}:
            raise GeneralResearchError("page-content-type")
        if response.getheader("Content-Encoding", "").strip().casefold() not in ("", "identity"):
            raise GeneralResearchError("page-content-encoding")
        body = response.read(MAX_PAGE_BYTES + 1)
        if len(body) > MAX_PAGE_BYTES:
            raise GeneralResearchError("page-size")
    except (OSError, ssl.SSLError, http.client.HTTPException) as error:
        raise GeneralResearchError("page-transport-failed") from error
    finally:
        connection.close()
    try:
        decoded = body.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise GeneralResearchError("page-encoding") from error
    if media_type == "text/html":
        parser = _TextExtractor()
        parser.feed(decoded)
        parser.close()
        decoded = "".join(parser.parts)
    segments = []
    total = 0
    for raw in decoded.splitlines():
        text = " ".join(raw.split())
        if not text:
            continue
        remaining = MAX_PAGE_CHARACTERS - total
        if remaining <= 0:
            break
        text = text[: min(2000, remaining)]
        total += len(text)
        segments.append(text)
        if len(segments) >= 100:
            break
    if not segments:
        raise GeneralResearchError("page-empty")
    return {
        "destination": canonical,
        "segments": segments,
        "contentCharacters": total,
        "networkUsed": True,
        "activeContentExecuted": False,
        "remoteReferencesRetained": False,
        "filesWritten": False,
    }
