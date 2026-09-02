#!/usr/bin/env python3
"""Bounded, candidate-only search of the public Ollama model catalog."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request


CATALOG_ORIGIN = "https://ollama.com"
MAX_CATALOG_BYTES = 512 * 1024
MAX_QUERY_CHARACTERS = 64
MAX_RESULTS = 20
MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$")
QUERY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._/:+-]{0,63}$")
MACOS_SYSTEM_CA_BUNDLES = (Path("/etc/ssl/cert.pem"),)


class ModelCatalogSearchError(ValueError):
    """A fail-closed public catalog search error."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        del request, file_pointer, code, message, headers, new_url
        return None


class _LibraryLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.models: list[str] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = next((value for name, value in attributes if name.lower() == "href"), None)
        if not href:
            return
        path = urllib.parse.urlsplit(href).path
        if not path.startswith("/library/"):
            return
        candidate = urllib.parse.unquote(path.removeprefix("/library/")).strip("/")
        if (
            not candidate
            or candidate.endswith(":cloud")
            or not MODEL_NAME.fullmatch(candidate)
            or candidate in self.models
        ):
            return
        self.models.append(candidate)


def validate_query(value: object) -> str:
    if not isinstance(value, str):
        raise ModelCatalogSearchError("invalid-model-search-query")
    query = " ".join(value.split())
    if (
        not query
        or len(query) > MAX_QUERY_CHARACTERS
        or len(query.encode("utf-8")) > 256
        or not QUERY.fullmatch(query)
    ):
        raise ModelCatalogSearchError("invalid-model-search-query")
    return query


def parse_ollama_search_html(content: str) -> list[str]:
    parser = _LibraryLinkParser()
    try:
        parser.feed(content)
        parser.close()
    except (UnicodeError, ValueError) as error:
        raise ModelCatalogSearchError("invalid-model-catalog-response") from error
    return parser.models[:MAX_RESULTS]


def _catalog_ssl_context() -> ssl.SSLContext:
    """Use interpreter trust, or the fixed macOS system bundle when it is empty."""
    context = ssl.create_default_context()
    if context.get_ca_certs() or sys.platform != "darwin":
        return context
    for candidate in MACOS_SYSTEM_CA_BUNDLES:
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if resolved.is_file() and resolved.stat().st_size > 0:
            return ssl.create_default_context(cafile=str(resolved))
    raise ModelCatalogSearchError("model-catalog-system-trust-unavailable")


def _fetch_catalog_html(path: str, timeout_seconds: int, query: str | None = None) -> str:
    if not path.startswith("/") or ".." in path or not re.fullmatch(r"/[A-Za-z0-9._/:+-]+", path):
        raise ModelCatalogSearchError("invalid-model-catalog-path")
    url = CATALOG_ORIGIN + path
    if query is not None:
        url += "?" + urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html",
            "User-Agent": "Haven-42-model-catalog-search/1",
        },
        method="GET",
    )
    # Search consent covers the fixed catalog origin, not an inherited proxy.
    try:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=_catalog_ssl_context()),
            _NoRedirect(),
        )
        with opener.open(request, timeout=timeout_seconds) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if (
                final.scheme != "https"
                or final.netloc != "ollama.com"
                or final.path != path
                or response.status != 200
            ):
                raise ModelCatalogSearchError("invalid-model-catalog-response")
            content_type = response.headers.get_content_type()
            declared = response.headers.get("Content-Length")
            if content_type != "text/html" or (
                declared is not None and int(declared) > MAX_CATALOG_BYTES
            ):
                raise ModelCatalogSearchError("invalid-model-catalog-response")
            data = response.read(MAX_CATALOG_BYTES + 1)
            if len(data) > MAX_CATALOG_BYTES:
                raise ModelCatalogSearchError("model-catalog-response-too-large")
    except (OSError, urllib.error.HTTPError, ValueError) as error:
        if isinstance(error, ModelCatalogSearchError):
            raise
        raise ModelCatalogSearchError("model-catalog-search-failed") from error
    return data.decode("utf-8", errors="strict")


def search_ollama_catalog(query: str, timeout_seconds: int = 10) -> list[str]:
    """Return matching families and their bounded official Ollama tag variants."""
    query = validate_query(query)
    if timeout_seconds < 1 or timeout_seconds > 15:
        raise ModelCatalogSearchError("invalid-model-search-timeout")
    models = parse_ollama_search_html(_fetch_catalog_html("/search", timeout_seconds, query))
    normalized_query = query.casefold().replace(" ", "")
    families = [
        model for model in models
        if ":" not in model.rsplit("/", 1)[-1]
        and model.casefold() == normalized_query
    ][:1]
    for family in families:
        encoded = urllib.parse.quote(family, safe="._+-")
        variants = parse_ollama_search_html(
            _fetch_catalog_html(f"/library/{encoded}/tags", timeout_seconds)
        )
        models.extend(model for model in variants if model not in models)
    return models[:MAX_RESULTS]
