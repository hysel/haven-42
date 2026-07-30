#!/usr/bin/env python3
"""Bounded inert text extraction from caller-supplied bytes only."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "config/web-research-page-foundation.json").read_text(encoding="utf-8")
)
LIMITS = CONTRACT["limits"]
ALLOWED = set(CONTRACT["html"]["allowedTags"])


class PageRejected(ValueError):
    pass


class InertHtmlText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.values: list[str] = []

    def handle_decl(self, decl: str) -> None:
        raise PageRejected("html-doctype")

    def handle_starttag(self, tag: str, attrs) -> None:
        value = tag.casefold()
        if value not in ALLOWED:
            raise PageRejected("html-tag-not-allowlisted")
        if value == "br":
            self.values.append("\n")
            return
        self.stack.append(value)
        if len(self.stack) > LIMITS["maximumNestingDepth"]:
            raise PageRejected("html-depth-budget")

    def handle_startendtag(self, tag: str, attrs) -> None:
        value = tag.casefold()
        if value != "br":
            raise PageRejected("html-structure")
        self.handle_starttag(value, attrs)

    def handle_endtag(self, tag: str) -> None:
        value = tag.casefold()
        if value == "br" or value not in ALLOWED:
            raise PageRejected("html-structure")
        if not self.stack or self.stack[-1] != value:
            raise PageRejected("html-structure")
        self.stack.pop()
        if value in {
            "p", "li", "blockquote", "pre", "div", "section", "article",
            "h1", "h2", "h3", "h4", "h5", "h6",
        }:
            self.values.append("\n")

    def handle_data(self, data: str) -> None:
        self.values.append(data)

    def handle_entityref(self, name: str) -> None:
        raise PageRejected("html-entity-unexpected")

    def handle_charref(self, name: str) -> None:
        raise PageRejected("html-entity-unexpected")

    def handle_pi(self, data: str) -> None:
        raise PageRejected("html-processing-instruction")

    def unknown_decl(self, data: str) -> None:
        raise PageRejected("html-declaration")


def decode(data: object) -> str:
    if not isinstance(data, bytes):
        raise PageRejected("page-bytes-type")
    if not data or len(data) > LIMITS["maximumInputBytes"]:
        raise PageRejected("page-byte-budget")
    if b"\x00" in data:
        raise PageRejected("page-nul")
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise PageRejected("page-utf8") from exc


def normalize_segments(values: list[str]) -> list[str]:
    result: list[str] = []
    total = 0
    for raw in "".join(values).splitlines():
        value = " ".join(raw.split())
        if not value:
            continue
        total += len(value)
        if total > LIMITS["maximumOutputCharacters"]:
            raise PageRejected("page-output-budget")
        result.append(value)
        if len(result) > LIMITS["maximumSegments"]:
            raise PageRejected("page-segment-budget")
    return result


def extract(content_type: object, data: object) -> dict[str, object]:
    if not isinstance(content_type, str):
        raise PageRejected("content-type")
    media_type = content_type.split(";", 1)[0].strip().casefold()
    if media_type not in CONTRACT["contentTypes"]:
        raise PageRejected("content-type-not-allowlisted")
    text = decode(data)
    if media_type == "text/plain":
        values = [text]
    else:
        parser = InertHtmlText()
        try:
            parser.feed(text)
            parser.close()
        except PageRejected:
            raise
        except Exception as exc:
            raise PageRejected("html-malformed") from exc
        if parser.stack:
            raise PageRejected("html-structure")
        values = parser.values
    segments = normalize_segments(values)
    if not segments:
        raise PageRejected("page-empty")
    return {
        "schemaVersion": 1,
        "status": "offline-inert-caller-bytes",
        "contentType": media_type,
        "segments": [
            {"index": index, "text": value, "trust": "untrusted-inert-text"}
            for index, value in enumerate(segments, 1)
        ],
        "contentCharacters": sum(len(value) for value in segments),
        "networkUsed": False,
        "remoteReferencesRetained": False,
        "filesWritten": False,
        "runtimeAdmissionGranted": False,
    }


if __name__ == "__main__":
    print(json.dumps({"status": CONTRACT["status"], "urlFetchAllowed": False}))
