#!/usr/bin/env python3
"""Offline-only query/result/citation boundary with no transport authority."""

from __future__ import annotations

import hashlib
import ipaddress
import json
from datetime import datetime
from pathlib import Path
import re
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "config/web-research-adapter-foundation.json").read_text(encoding="utf-8")
)
LIMITS = CONTRACT["limits"]


class ResearchRejected(ValueError):
    pass


def bounded_text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ResearchRejected(f"{field}-type")
    normalized = " ".join(value.split())
    if not normalized:
        raise ResearchRejected(f"{field}-empty")
    if len(normalized) > maximum:
        raise ResearchRejected(f"{field}-budget")
    if any(ord(character) < 32 for character in value):
        raise ResearchRejected(f"{field}-control")
    if "<" in normalized or ">" in normalized:
        raise ResearchRejected(f"{field}-active-markup")
    return normalized


def validate_query(provider: object, query: object) -> dict[str, object]:
    providers = CONTRACT["providers"]
    if not isinstance(provider, str) or provider not in providers:
        raise ResearchRejected("provider-not-allowlisted")
    if providers[provider]["transport"] != "caller-supplied-fixture":
        raise ResearchRejected("provider-transport-not-offline")
    normalized = bounded_text(
        query, "query", LIMITS["maximumQueryCharacters"]
    )
    if re.search(
        r"(?i)\b(password|passwd|token|secret|api[-_ ]?key|authorization)\s*[:=]",
        normalized,
    ):
        raise ResearchRejected("query-credential-like")
    return {
        "schemaVersion": 1,
        "provider": provider,
        "query": normalized,
        "explicitUserActionRequired": True,
        "networkAuthorityGranted": False,
        "automaticFollowUpAllowed": False,
    }


def validate_url(raw: object) -> tuple[str, str]:
    value = bounded_text(raw, "url", LIMITS["maximumUrlCharacters"])
    parsed = urlsplit(value)
    if parsed.scheme != "https":
        raise ResearchRejected("url-https-required")
    if parsed.username is not None or parsed.password is not None:
        raise ResearchRejected("url-credentials")
    if not parsed.hostname:
        raise ResearchRejected("url-host")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ResearchRejected("url-port") from exc
    if port not in (None, 443):
        raise ResearchRejected("url-custom-port")
    if parsed.fragment:
        raise ResearchRejected("url-fragment")
    if parsed.query:
        raise ResearchRejected("url-query-unadmitted")
    host = parsed.hostname.casefold().rstrip(".")
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ResearchRejected("url-local-host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if not re.fullmatch(
            r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", host
        ):
            raise ResearchRejected("url-host-syntax")
    else:
        if not address.is_global:
            raise ResearchRejected("url-non-public-ip")
    canonical_host = f"[{host}]" if ":" in host else host
    canonical = parsed._replace(netloc=canonical_host, fragment="").geturl()
    return canonical, host


def validate_results(provider: object, query: object, results: object) -> dict[str, object]:
    request = validate_query(provider, query)
    if not isinstance(results, list):
        raise ResearchRejected("results-type")
    if not 1 <= len(results) <= LIMITS["maximumResults"]:
        raise ResearchRejected("results-count")
    output: list[dict[str, object]] = []
    response_characters = 0
    seen_urls: set[str] = set()
    for index, raw in enumerate(results, 1):
        if not isinstance(raw, dict):
            raise ResearchRejected("result-type")
        if set(raw) != {"title", "excerpt", "url", "retrievedAt"}:
            raise ResearchRejected("result-fields")
        title = bounded_text(raw["title"], "title", LIMITS["maximumTitleCharacters"])
        excerpt = bounded_text(
            raw["excerpt"], "excerpt", LIMITS["maximumExcerptCharacters"]
        )
        url, domain = validate_url(raw["url"])
        retrieved = bounded_text(raw["retrievedAt"], "retrievedAt", 32)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", retrieved):
            raise ResearchRejected("retrievedAt-format")
        try:
            datetime.strptime(retrieved, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise ResearchRejected("retrievedAt-format") from exc
        if url in seen_urls:
            raise ResearchRejected("result-duplicate-url")
        seen_urls.add(url)
        response_characters += len(title) + len(excerpt) + len(url)
        if response_characters > LIMITS["maximumResponseCharacters"]:
            raise ResearchRejected("response-budget")
        digest = hashlib.sha256(
            f"{request['provider']}\0{request['query']}\0{index}\0{url}".encode()
        ).hexdigest()[:20]
        output.append(
            {
                "citationId": f"source-{digest}",
                "title": title,
                "excerpt": excerpt,
                "url": url,
                "displayDomain": domain,
                "retrievedAt": retrieved,
                "contentTrust": "untrusted-inert-text",
                "activeNavigationAllowed": False,
            }
        )
    return {
        "schemaVersion": 1,
        "status": "offline-validated-caller-fixture",
        "request": request,
        "results": output,
        "sourceCount": len(output),
        "networkUsed": False,
        "dnsUsed": False,
        "filesWritten": False,
        "runtimeAdmissionGranted": False,
    }


def account_synthesis(bundle: dict[str, object], citations: object) -> dict[str, object]:
    if not isinstance(citations, list) or not citations:
        raise ResearchRejected("citation-accounting-empty")
    if len(citations) != len(set(citations)):
        raise ResearchRejected("citation-accounting-duplicate")
    allowed = {
        result["citationId"]: result for result in bundle.get("results", [])
    }
    if any(not isinstance(value, str) or value not in allowed for value in citations):
        raise ResearchRejected("citation-accounting-unknown")
    return {
        "schemaVersion": 1,
        "citations": [
            {
                "citationId": value,
                "title": allowed[value]["title"],
                "displayDomain": allowed[value]["displayDomain"],
                "destination": allowed[value]["url"],
                "destinationDisclosureRequired": True,
                "activeNavigationAllowed": False,
            }
            for value in citations
        ],
        "exactSourceAccounting": True,
        "modelSuppliedLinksAccepted": False,
        "runtimeAdmissionGranted": False,
    }


if __name__ == "__main__":
    print(json.dumps({"status": CONTRACT["status"], "networkAuthority": False}))
