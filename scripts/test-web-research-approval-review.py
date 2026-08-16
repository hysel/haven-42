#!/usr/bin/env python3
"""Static hostile checks for the dormant explicit research-review UI."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "web-research-approval-review-foundation.json"
APP_PATH = ROOT / "web" / "static" / "app.js"
HTML_PATH = ROOT / "web" / "static" / "index.html"
STYLE_PATH = ROOT / "web" / "static" / "styles.css"


class ReviewParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.layer: dict[str, str | None] = {}
        self.dialog: dict[str, str | None] = {}
        self.elements: dict[str, tuple[str, dict[str, str | None]]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        identifier = values.get("id")
        if identifier:
            self.elements[str(identifier)] = (tag, values)
        if identifier == "research-review-layer":
            self.layer = values
        elif identifier == "research-review-dialog":
            self.dialog = values


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
    require(contract["status"] == "dormant-effect-free-explicit-review-ui", "status")
    checks += 1
    require(contract["provider"] == {
        "id": "wikipedia",
        "displayName": "Wikipedia",
        "fixedDisplayDomain": "en.wikipedia.org",
    }, "fixed provider")
    checks += 1
    require(contract["input"]["reviewKinds"] == ["query", "page"], "review kinds")
    checks += 1
    require(contract["input"]["maximumQueryCharacters"] == 256, "query limit")
    checks += 1
    require(contract["input"]["pageReviewRequiresTrustedCitation"] is True, "trusted page citation")
    checks += 1
    require(contract["input"]["queryReviewRequiresNullCitation"] is True, "query citation denied")
    checks += 1
    require(contract["input"]["modelSuppliedApprovalAccepted"] is False, "model approval denied")
    checks += 1
    for field in (
        "explicitTrustedUserActionRequired", "cancelAndCloseAlwaysAvailable",
        "escapeCancels", "focusMovesIntoDialog", "focusIsTrapped",
        "focusReturnsAfterClose", "backgroundIsInert", "singleUseDecision",
    ):
        require(contract["interaction"][field] is True, f"interaction: {field}")
        checks += 1
    require(contract["interaction"]["decisionStartsNetwork"] is False, "decision has no network effect")
    checks += 1
    require(contract["accessibility"]["role"] == "dialog", "dialog role contract")
    checks += 1
    require(contract["accessibility"]["ariaModal"] is True, "modal contract")
    checks += 1
    require(contract["accessibility"]["minimumTargetPixels"] == 44, "target size")
    checks += 1
    require(contract["accessibility"]["forcedColorsSupported"] is True, "forced colors")
    checks += 1
    require(contract["accessibility"]["reducedMotionSupported"] is True, "reduced motion")
    checks += 1
    require(contract["lifecycle"] == {
        "memoryOnly": True,
        "clearOnNewTask": True,
        "clearOnInvalidInput": True,
        "persistenceAllowed": False,
        "telemetryAllowed": False,
    }, "lifecycle")
    checks += 1
    require(all(value is False for value in contract["authority"].values()), "authority denied")
    checks += 1

    parser = ReviewParser()
    parser.feed(page)
    require("hidden" in str(parser.layer.get("class", "")).split(), "dormant layer")
    checks += 1
    require(parser.layer.get("aria-hidden") == "true", "hidden accessibility state")
    checks += 1
    require(parser.dialog.get("role") == "dialog", "dialog role")
    checks += 1
    require(parser.dialog.get("aria-modal") == "true", "aria modal")
    checks += 1
    require(parser.dialog.get("aria-labelledby") == "research-review-title", "accessible name")
    checks += 1
    require(parser.dialog.get("aria-describedby") == "research-review-description research-review-privacy", "accessible description")
    checks += 1
    require(parser.dialog.get("tabindex") == "-1", "focus target")
    checks += 1
    required_ids = {
        "research-review-close", "research-review-title", "research-review-description",
        "research-review-kind", "research-review-query", "research-review-source",
        "research-review-destination", "research-review-privacy",
        "research-review-status", "research-review-cancel", "research-review-approve",
    }
    require(required_ids <= set(parser.elements), "required elements")
    checks += 1
    require(parser.elements["research-review-close"][1].get("aria-label") == "Cancel this web research request", "close label")
    checks += 1
    require(parser.elements["research-review-status"][1].get("role") == "status", "status role")
    checks += 1
    require(parser.elements["research-review-status"][1].get("aria-live") == "polite", "status live")
    checks += 1
    require("Nothing is sent yet." in page and "Approve once" in page, "plain disclosure")
    checks += 1
    require("<a" not in page[page.index('id="research-review-layer"'):page.index('id="section-tour-layer"')], "no active link")
    checks += 1

    start = app.index("const RESEARCH_REVIEW_FIELDS")
    end = app.index("function updatePromptHistoryStatus")
    implementation = app[start:end]
    for token in (
        "validateResearchReviewBundle", "openResearchApprovalReview",
        "consumeResearchApprovalDecision", "clearResearchApprovalReview",
        "event.isTrusted", "element.inert = true", 'event.key === "Escape"',
        'event.key !== "Tab"', "focus({ preventScroll: true })",
        "singleUse: true", "networkStarted: false",
        "const wasOpen = review !== null", "if (!wasOpen)",
        '[first, byId("research-review-dialog")].includes(document.activeElement)',
        "citation: bundle.citation === null ? null : Object.freeze",
        "window.Haven42ResearchApprovalReview = Object.freeze",
    ):
        require(token in implementation, f"implementation token: {token}")
        checks += 1
    require("fetch(" not in implementation, "no network call")
    checks += 1
    require("localStorage" not in implementation and "sessionStorage" not in implementation, "no persistence")
    checks += 1
    require("innerHTML" not in implementation, "no HTML injection")
    checks += 1
    require(app.count("openResearchApprovalReview(") == 1, "no product invocation")
    checks += 1
    require("clearTrustedCitations();\n  clearResearchApprovalReview();" in app, "new task cleanup")
    checks += 1

    require(".research-review-layer" in styles and ".research-review-dialog" in styles, "dialog styles")
    checks += 1
    require("min-height: 44px" in styles[styles.index(".research-review-actions"):], "button target size")
    checks += 1
    require("overflow-wrap: anywhere" in styles[styles.index(".research-review-details"):], "zoom wrapping")
    checks += 1
    require("@media (prefers-reduced-motion: reduce)" in styles and ".research-review-layer" in styles[styles.index("@media (prefers-reduced-motion: reduce)"):], "reduced motion styles")
    checks += 1
    forced = styles.index(
        "@media (forced-colors: active)", styles.index(".research-review-layer")
    )
    require(".research-review-dialog" in styles[forced:forced + 500], "forced colors styles")
    checks += 1

    print(f"Research approval review foundation passed: {checks} checks.")


if __name__ == "__main__":
    main()
