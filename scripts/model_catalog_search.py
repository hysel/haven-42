#!/usr/bin/env python3
"""Bounded, candidate-only search of the public Ollama model catalog."""

from __future__ import annotations

from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request


CATALOG_ORIGIN = "https://ollama.com"
MAX_CATALOG_BYTES = 2 * 1024 * 1024
MAX_QUERY_CHARACTERS = 64
MAX_RESULTS = 200
MAX_FAMILIES = 256
MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$")
QUERY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._/:+-]{0,63}$")
MACOS_SYSTEM_CA_BUNDLES = (Path("/etc/ssl/cert.pem"),)


class ModelCatalogSearchError(ValueError):
    """A fail-closed public catalog search error."""


class CatalogResults(list):
    """Catalog matches with an explicit notice when tag expansion was partial."""

    def __init__(self, values: list[str], incomplete: bool = False):
        super().__init__(values)
        self.incomplete = incomplete


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
        url = urllib.parse.urlsplit(href)
        if url.netloc and (url.scheme != "https" or url.netloc != "ollama.com"):
            return
        path = urllib.parse.unquote(url.path).strip("/")
        if path.startswith("library/"):
            candidate = path.removeprefix("library/")
        else:
            # Community model cards use /publisher/model rather than /library/model.
            # Require a model-card marker (or a tag link), not arbitrary site navigation.
            parts = path.split("/")
            classes = next((value or "" for name, value in attributes if name == "class"), "").split()
            if (
                len(parts) != 2
                or parts[0] in {"docs", "blog", "settings", "account", "api", "signin", "search"}
                or not ("group" in classes and "w-full" in classes or ":" in parts[1])
            ):
                return
            candidate = path
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


def parse_ollama_search_html(content: str, limit: int | None = 20) -> list[str]:
    parser = _LibraryLinkParser()
    try:
        parser.feed(content)
        parser.close()
    except (UnicodeError, ValueError) as error:
        raise ModelCatalogSearchError("invalid-model-catalog-response") from error
    return parser.models if limit is None else parser.models[:limit]


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
    normalized_query = query.casefold()

    # A tag-like query must be admitted by the official family tag page. The
    # general search page may echo an unknown tag in navigation markup, which
    # is not evidence that Ollama can actually pull it.
    requested_leaf = normalized_query.rsplit("/", 1)[-1]
    if ":" in requested_leaf:
        family = query.rsplit(":", 1)[0]
        encoded = urllib.parse.quote(family, safe="._+-/")
        tag_path = f"/{encoded}/tags" if "/" in family else f"/library/{encoded}/tags"
        variants = parse_ollama_search_html(
            _fetch_catalog_html(tag_path, timeout_seconds), None,
        )
        return [model for model in variants if model.casefold() == normalized_query][:1]

    # Format terms describe tags, not family names. Search families first and
    # inspect their tags before applying the output bound or the format filter.
    terms = normalized_query.split()
    formats = {
        term for term in terms
        if term in {"mlx", "nvfp4", "mxfp8", "bf16", "fp16", "f16", "fp32", "f32"}
        or re.fullmatch(r"q[2-8](?:_[a-z0-9]+)+|[0-9]+(?:\.[0-9]+)?[bm]", term)
    }
    family_query = " ".join(term for term in terms if term not in formats)
    models = parse_ollama_search_html(
        _fetch_catalog_html("/search", timeout_seconds, family_query)
        if family_query else _fetch_catalog_html("/library", timeout_seconds), None,
    )
    families = [
        model for model in models
        if ":" not in model.rsplit("/", 1)[-1]
    ][:MAX_FAMILIES]
    expanded: list[str] = []
    exact_family = next(
        (family for family in families if family.casefold() == family_query),
        None,
    )
    selected_families = [exact_family] if exact_family else families
    def family_variants(family: str) -> tuple[list[str], bool]:
        encoded = urllib.parse.quote(family, safe="._+-/")
        tag_path = f"/{encoded}/tags" if "/" in family else f"/library/{encoded}/tags"
        try:
            variants = parse_ollama_search_html(
                _fetch_catalog_html(tag_path, timeout_seconds), None,
            )
        except ModelCatalogSearchError:
            # The search page already established this family's existence.
            # A failed tag request must not erase every other search result.
            return [family], True
        return [family, *(model for model in variants if model.startswith(family + ":"))], False

    # Keep requests bounded and preserve catalog order regardless of completion order.
    incomplete = False
    with ThreadPoolExecutor(max_workers=4) as pool:
        for variants, failed in pool.map(family_variants, selected_families):
            incomplete = incomplete or failed
            expanded.extend(model for model in variants if model not in expanded)
    expanded.extend(
        model for model in models if model not in expanded
        and (not exact_family or model.startswith(exact_family + ":"))
    )
    if formats:
        expanded = [model for model in expanded if all(term in model.casefold() for term in formats)]
    return CatalogResults(expanded[:MAX_RESULTS], incomplete)
