#!/usr/bin/env python3
"""Hostile tests for the offline-only research adapter/citation boundary."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/offline_web_research_boundary.py"
SPEC = importlib.util.spec_from_file_location("offline_research", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
FIXTURES = json.loads(
    (ROOT / "examples/fixtures/web-research-adapter-cases.json").read_text(
        encoding="utf-8"
    )
)


def rejected(callable_value, expected: str) -> None:
    try:
        callable_value()
    except MODULE.ResearchRejected as exc:
        assert str(exc) == expected, (str(exc), expected)
    else:
        raise AssertionError(f"expected rejection: {expected}")


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".", 1)[0])
    return result


def main() -> int:
    checks = 0
    safe = FIXTURES["safe"]
    bundle = MODULE.validate_results(
        FIXTURES["provider"], safe["query"], safe["results"]
    )
    assert bundle["sourceCount"] == 1
    assert bundle["networkUsed"] is False and bundle["dnsUsed"] is False
    assert bundle["runtimeAdmissionGranted"] is False
    citation_id = bundle["results"][0]["citationId"]
    accounting = MODULE.account_synthesis(bundle, [citation_id])
    assert accounting["exactSourceAccounting"] is True
    assert accounting["citations"][0]["activeNavigationAllowed"] is False
    checks += 6

    reasons = {
        "unknown-provider": "provider-not-allowlisted",
        "query-control": "query-control",
        "query-credentials": "query-credential-like",
        "http-url": "url-https-required",
        "credential-url": "url-credentials",
        "loopback-url": "url-non-public-ip",
        "private-url": "url-non-public-ip",
        "link-local-url": "url-non-public-ip",
        "ipv6-loopback": "url-non-public-ip",
        "custom-port": "url-custom-port",
        "fragment": "url-fragment",
        "active-title": "title-active-markup",
        "invalid-retrieval-time": "retrievedAt-format",
        "forged-citation": "result-fields",
        "oversized-results": "results-count",
    }
    for case in FIXTURES["hostile"]:
        provider = FIXTURES["provider"]
        query = safe["query"]
        results = copy.deepcopy(safe["results"])
        field = case["field"]
        if field == "provider":
            provider = case["value"]
        elif field == "query":
            query = case["value"]
        elif field == "resultCount":
            results = results * case["value"]
        else:
            results[0][field] = case["value"]
        rejected(
            lambda p=provider, q=query, r=results: MODULE.validate_results(p, q, r),
            reasons[case["id"]],
        )
        checks += 1

    duplicate = copy.deepcopy(safe["results"]) * 2
    rejected(
        lambda: MODULE.validate_results(FIXTURES["provider"], safe["query"], duplicate),
        "result-duplicate-url",
    )
    rejected(lambda: MODULE.account_synthesis(bundle, ["model-link"]), "citation-accounting-unknown")
    rejected(lambda: MODULE.account_synthesis(bundle, [citation_id, citation_id]), "citation-accounting-duplicate")
    checks += 3

    contract = json.loads(
        (ROOT / "config/web-research-adapter-foundation.json").read_text(
            encoding="utf-8"
        )
    )
    assert not any(contract["authority"].values())
    assert contract["providers"]["fixture-search"]["networkAuthority"] is False
    assert imports(PATH).isdisjoint(
        {"socket", "requests", "http", "subprocess", "webbrowser", "selenium"}
    )
    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".py", ".js", ".html", ".css", ".json"}
    )
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert "offline_web_research_boundary" not in runtime + package
    checks += 4
    print(f"Offline web-research boundary passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
