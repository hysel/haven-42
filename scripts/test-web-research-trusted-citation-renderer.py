#!/usr/bin/env python3
"""Static fail-closed checks for the dormant trusted citation renderer."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "web-research-citation-renderer-foundation.json"
APP_PATH = ROOT / "web" / "static" / "app.js"
HTML_PATH = ROOT / "web" / "static" / "index.html"
STYLE_PATH = ROOT / "web" / "static" / "styles.css"


class SourceRegionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.region_attributes: dict[str, str | None] = {}
        self.tags: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if self.depth == 0 and values.get("id") == "research-sources":
            self.depth = 1
            self.region_attributes = values
        elif self.depth:
            self.depth += 1
        if self.depth:
            self.tags.append(tag)
            if values.get("id"):
                self.ids.add(str(values["id"]))

    def handle_endtag(self, _tag: str) -> None:
        if self.depth:
            self.depth -= 1


def require(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def main() -> None:
    checks = 0
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    app = APP_PATH.read_text(encoding="utf-8")
    page = HTML_PATH.read_text(encoding="utf-8")
    styles = STYLE_PATH.read_text(encoding="utf-8")

    require(contract["schemaVersion"] == 1, "schema")
    checks += 1
    require(contract["status"] == "dormant-fixed-provider-renderer-no-navigation-authority", "status")
    checks += 1
    require(contract["input"]["maximumCitations"] == 10, "citation limit")
    checks += 1
    require(contract["input"]["fixedDisplayDomain"] == "en.wikipedia.org", "fixed domain")
    checks += 1
    require(contract["input"]["duplicateCitationIdsAllowed"] is False, "duplicate ids")
    checks += 1
    require(contract["input"]["duplicateDestinationsAllowed"] is False, "duplicate destinations")
    checks += 1
    require(contract["rendering"]["textContentOnly"] is True, "text only")
    checks += 1
    for field in (
        "modelMarkdownAllowed", "activeLinksAllowed", "remoteMediaAllowed",
        "remoteStylesAllowed", "remoteScriptsAllowed", "framesAllowed",
        "downloadsAllowed", "trackingAllowed",
    ):
        require(contract["rendering"][field] is False, f"rendering deny: {field}")
        checks += 1
    require(contract["rendering"]["fullDestinationDisclosureRequired"] is True, "destination disclosure")
    checks += 1
    require(contract["rendering"]["screenReaderStatusRequired"] is True, "screen reader status")
    checks += 1
    require(contract["rendering"]["forcedColorsSupported"] is True, "forced colors")
    checks += 1
    require(contract["rendering"]["packageIncludedAsDormantComponent"] is True, "dormant package component")
    checks += 1
    require(contract["lifecycle"] == {
        "memoryOnly": True,
        "clearOnNewTask": True,
        "persistenceAllowed": False,
        "telemetryAllowed": False,
    }, "lifecycle")
    checks += 1
    require(all(value is False for value in contract["authority"].values()), "authority denied")
    checks += 1

    parser = SourceRegionParser()
    parser.feed(page)
    require(parser.region_attributes.get("role") == "region", "region role")
    checks += 1
    require("hidden" in str(parser.region_attributes.get("class", "")).split(), "dormant hidden region")
    checks += 1
    require(parser.region_attributes.get("aria-labelledby") == "research-sources-title", "accessible label")
    checks += 1
    require(parser.region_attributes.get("aria-describedby") == "research-sources-disclosure", "accessible description")
    checks += 1
    require({"research-sources-title", "research-sources-disclosure", "research-source-list", "research-sources-status"} <= parser.ids, "region ids")
    checks += 1
    require(not ({"a", "img", "script", "style", "iframe", "object", "embed"} & set(parser.tags)), "no active region elements")
    checks += 1

    for token in (
        "validateTrustedCitationBundle", "renderTrustedCitations", "clearTrustedCitations",
        "window.Haven42TrustedCitationRenderer", ".textContent = citation.title",
        ".textContent = `Destination: ${citation.destination}`", "clearTrustedCitations();",
    ):
        require(token in app, f"missing renderer token: {token}")
        checks += 1
    require("document.createElement(\"a\")" not in app[app.index("function renderTrustedCitations"):app.index("function updatePromptHistoryStatus")], "no active link construction")
    checks += 1
    require("innerHTML" not in app[app.index("function renderTrustedCitations"):app.index("function updatePromptHistoryStatus")], "no HTML injection")
    checks += 1
    require("fetch(" not in app[app.index("function renderTrustedCitations"):app.index("function updatePromptHistoryStatus")], "no renderer network")
    checks += 1
    require("@media (forced-colors: active)" in styles and ".trusted-citations" in styles, "forced-colors styling")
    checks += 1
    require("overflow-wrap: anywhere" in styles, "zoom-safe destination wrapping")
    checks += 1

    print(f"Trusted citation renderer foundation passed: {checks} checks.")


if __name__ == "__main__":
    main()
