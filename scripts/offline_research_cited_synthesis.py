#!/usr/bin/env python3
"""Offline cited-synthesis boundary with no model or network authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "config/web-research-synthesis-foundation.json").read_text(
        encoding="utf-8"
    )
)
LIMITS = CONTRACT["limits"]
CITATION_ID = re.compile(r"^source-[0-9a-f]{20}$")
ACTIVE_LINK = re.compile(r"(?i)(?:https?://|www\.|\[[^\]]+\]\([^\)]+\))")


class SynthesisRejected(ValueError):
    pass


def bounded_text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise SynthesisRejected(f"{field}-type")
    normalized = " ".join(value.split())
    if not normalized:
        raise SynthesisRejected(f"{field}-empty")
    if len(normalized) > maximum:
        raise SynthesisRejected(f"{field}-budget")
    if any(ord(character) < 32 for character in value):
        raise SynthesisRejected(f"{field}-control")
    if "<" in normalized or ">" in normalized or ACTIVE_LINK.search(normalized):
        raise SynthesisRejected(f"{field}-active-link")
    return normalized


def validated_result(result: object) -> dict[str, str]:
    fields = {
        "citationId", "title", "excerpt", "url", "displayDomain",
        "retrievedAt", "contentTrust", "activeNavigationAllowed",
    }
    if not isinstance(result, dict) or set(result) != fields:
        raise SynthesisRejected("source-shape")
    citation_id = result["citationId"]
    if not isinstance(citation_id, str) or CITATION_ID.fullmatch(citation_id) is None:
        raise SynthesisRejected("source-citation-id")
    if result["contentTrust"] != "untrusted-inert-text":
        raise SynthesisRejected("source-trust")
    if result["activeNavigationAllowed"] is not False:
        raise SynthesisRejected("source-navigation")
    return {
        "citationId": citation_id,
        "title": bounded_text(result["title"], "source-title", 200),
        "excerpt": bounded_text(result["excerpt"], "source-excerpt", 500),
        "retrievedAt": bounded_text(result["retrievedAt"], "source-time", 32),
    }


def validated_page(page: object) -> list[str]:
    fields = {
        "schemaVersion", "status", "contentType", "segments",
        "contentCharacters", "networkUsed", "remoteReferencesRetained",
        "filesWritten", "runtimeAdmissionGranted",
    }
    if not isinstance(page, dict) or set(page) != fields:
        raise SynthesisRejected("page-shape")
    if (
        page["schemaVersion"] != 1
        or page["status"] != "offline-inert-caller-bytes"
        or page["contentType"] not in {"text/plain", "text/html"}
        or page["networkUsed"] is not False
        or page["remoteReferencesRetained"] is not False
        or page["filesWritten"] is not False
        or page["runtimeAdmissionGranted"] is not False
    ):
        raise SynthesisRejected("page-authority")
    segments = page["segments"]
    if not isinstance(segments, list) or not 1 <= len(segments) <= LIMITS["maximumPageSegmentsPerSource"]:
        raise SynthesisRejected("page-segments")
    output: list[str] = []
    for expected_index, segment in enumerate(segments, 1):
        if not isinstance(segment, dict) or set(segment) != {"index", "text", "trust"}:
            raise SynthesisRejected("page-segment-shape")
        if segment["index"] != expected_index or segment["trust"] != "untrusted-inert-text":
            raise SynthesisRejected("page-segment-trust")
        output.append(
            bounded_text(
                segment["text"], "page-segment", LIMITS["maximumSegmentCharacters"]
            )
        )
    if page["contentCharacters"] != sum(len(value) for value in output):
        raise SynthesisRejected("page-character-accounting")
    return output


def prepare(bundle: object, pages: object) -> dict[str, object]:
    bundle_fields = {
        "schemaVersion", "status", "request", "results", "sourceCount",
        "networkUsed", "dnsUsed", "filesWritten", "runtimeAdmissionGranted",
    }
    if not isinstance(bundle, dict) or set(bundle) != bundle_fields:
        raise SynthesisRejected("bundle-shape")
    if (
        bundle["schemaVersion"] != 1
        or bundle["status"] != "offline-validated-caller-fixture"
        or bundle["networkUsed"] is not False
        or bundle["dnsUsed"] is not False
        or bundle["filesWritten"] is not False
        or bundle["runtimeAdmissionGranted"] is not False
    ):
        raise SynthesisRejected("bundle-authority")
    results = bundle["results"]
    if not isinstance(results, list) or not 1 <= len(results) <= LIMITS["maximumSources"]:
        raise SynthesisRejected("source-count")
    if bundle["sourceCount"] != len(results):
        raise SynthesisRejected("source-count-accounting")
    if not isinstance(pages, dict):
        raise SynthesisRejected("pages-shape")

    sources: list[dict[str, object]] = []
    allowed: set[str] = set()
    context_characters = 0
    for raw in results:
        source = validated_result(raw)
        citation_id = source["citationId"]
        if citation_id in allowed:
            raise SynthesisRejected("source-duplicate")
        allowed.add(citation_id)
        page_segments = validated_page(pages[citation_id]) if citation_id in pages else []
        context_characters += len(source["title"]) + len(source["excerpt"])
        context_characters += sum(len(value) for value in page_segments)
        if context_characters > LIMITS["maximumContextCharacters"]:
            raise SynthesisRejected("context-budget")
        digest_input = json.dumps(
            {**source, "pageSegments": page_segments},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        sources.append(
            {
                **source,
                "pageSegments": page_segments,
                "sourceDigest": hashlib.sha256(digest_input).hexdigest(),
                "trust": "untrusted-research-context",
            }
        )
    if any(not isinstance(key, str) or key not in allowed for key in pages):
        raise SynthesisRejected("page-source-unknown")
    return {
        "schemaVersion": 1,
        "status": "offline-cited-synthesis-input",
        "instruction": "Use only the supplied sources. Return bounded claims with approved citation IDs. Do not request another search, page, tool, or action.",
        "sources": sources,
        "sourceCount": len(sources),
        "sourceUrlsIncluded": False,
        "modelInvocationAllowed": False,
        "automaticFollowUpAllowed": False,
        "runtimeAdmissionGranted": False,
    }


def validate_candidate(request: object, candidate: object) -> dict[str, object]:
    if not isinstance(request, dict) or request.get("status") != "offline-cited-synthesis-input":
        raise SynthesisRejected("request-shape")
    if (
        request.get("modelInvocationAllowed") is not False
        or request.get("automaticFollowUpAllowed") is not False
        or request.get("runtimeAdmissionGranted") is not False
        or request.get("sourceUrlsIncluded") is not False
    ):
        raise SynthesisRejected("request-authority")
    sources = request.get("sources")
    if not isinstance(sources, list) or request.get("sourceCount") != len(sources):
        raise SynthesisRejected("request-source-count")
    allowed = {source.get("citationId") for source in sources if isinstance(source, dict)}
    if len(allowed) != len(sources) or any(
        not isinstance(value, str) or CITATION_ID.fullmatch(value) is None for value in allowed
    ):
        raise SynthesisRejected("request-sources")
    if not isinstance(candidate, dict) or set(candidate) != {"claims"}:
        raise SynthesisRejected("candidate-shape")
    claims = candidate["claims"]
    if not isinstance(claims, list) or not 1 <= len(claims) <= LIMITS["maximumClaims"]:
        raise SynthesisRejected("claim-count")
    output: list[dict[str, object]] = []
    used: set[str] = set()
    answer_characters = 0
    for index, raw in enumerate(claims, 1):
        if not isinstance(raw, dict) or set(raw) != {"text", "citationIds"}:
            raise SynthesisRejected("claim-shape")
        text = bounded_text(raw["text"], "claim", LIMITS["maximumClaimCharacters"])
        citations = raw["citationIds"]
        if not isinstance(citations, list) or not 1 <= len(citations) <= LIMITS["maximumCitationsPerClaim"]:
            raise SynthesisRejected("claim-citation-count")
        if len(citations) != len(set(citations)):
            raise SynthesisRejected("claim-citation-duplicate")
        if any(not isinstance(value, str) or value not in allowed for value in citations):
            raise SynthesisRejected("claim-citation-unknown")
        answer_characters += len(text)
        if answer_characters > LIMITS["maximumAnswerCharacters"]:
            raise SynthesisRejected("answer-budget")
        used.update(citations)
        output.append({"claimIndex": index, "text": text, "citationIds": citations})
    return {
        "schemaVersion": 1,
        "status": "offline-cited-synthesis-validated",
        "claims": output,
        "usedCitationIds": sorted(used),
        "unusedCitationIds": sorted(allowed - used),
        "exactSourceAccounting": True,
        "modelSuppliedLinksAccepted": False,
        "automaticFollowUpAllowed": False,
        "toolExecutionAllowed": False,
        "networkUsed": False,
        "filesWritten": False,
        "runtimeAdmissionGranted": False,
    }


if __name__ == "__main__":
    print(json.dumps({"status": CONTRACT["status"], "modelAuthority": False}))
