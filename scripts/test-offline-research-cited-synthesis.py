#!/usr/bin/env python3
"""Hostile tests for the offline cited-synthesis boundary."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_PATH = ROOT / "scripts/offline_web_research_boundary.py"
PAGE_PATH = ROOT / "scripts/offline_research_page_text.py"
SYNTHESIS_PATH = ROOT / "scripts/offline_research_cited_synthesis.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BOUNDARY = load("offline_research_boundary_for_synthesis", BOUNDARY_PATH)
PAGE = load("offline_research_page_for_synthesis", PAGE_PATH)
SYNTHESIS = load("offline_research_synthesis", SYNTHESIS_PATH)
FIXTURES = json.loads(
    (ROOT / "examples/fixtures/web-research-adapter-cases.json").read_text(encoding="utf-8")
)
CASES = json.loads(
    (ROOT / "examples/fixtures/web-research-synthesis-cases.json").read_text(encoding="utf-8")
)


def rejected(callable_value, expected: str) -> None:
    try:
        callable_value()
    except SYNTHESIS.SynthesisRejected as exc:
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
    bundle = BOUNDARY.validate_results(FIXTURES["provider"], safe["query"], safe["results"])
    citation_id = bundle["results"][0]["citationId"]
    page = PAGE.extract("text/html", b"<article><p>Bounded page fact.</p></article>")
    request = SYNTHESIS.prepare(bundle, {citation_id: page})
    assert request["sourceCount"] == 1 and request["sourceUrlsIncluded"] is False
    assert request["modelInvocationAllowed"] is False
    assert request["sources"][0]["sourceDigest"]
    candidate = copy.deepcopy(CASES["safeCandidate"])
    candidate["claims"][0]["citationIds"] = [citation_id]
    result = SYNTHESIS.validate_candidate(request, candidate)
    assert result["exactSourceAccounting"] is True
    assert result["usedCitationIds"] == [citation_id] and result["unusedCitationIds"] == []
    assert result["toolExecutionAllowed"] is False and result["networkUsed"] is False
    assert result["runtimeAdmissionGranted"] is False
    checks += 9

    for case in CASES["hostileCandidates"]:
        value = json.loads(json.dumps(case["value"]).replace("SOURCE_ID", citation_id))
        rejected(lambda value=value: SYNTHESIS.validate_candidate(request, value), case["reason"])
        checks += 1

    unknown_pages = {"source-00000000000000000000": page}
    rejected(lambda: SYNTHESIS.prepare(bundle, unknown_pages), "page-source-unknown")
    bad_page = copy.deepcopy(page)
    bad_page["networkUsed"] = True
    rejected(lambda: SYNTHESIS.prepare(bundle, {citation_id: bad_page}), "page-authority")
    bad_count = copy.deepcopy(bundle)
    bad_count["sourceCount"] = 2
    rejected(lambda: SYNTHESIS.prepare(bad_count, {}), "source-count-accounting")
    duplicate = copy.deepcopy(bundle)
    duplicate["results"].append(copy.deepcopy(duplicate["results"][0]))
    duplicate["sourceCount"] = 2
    rejected(lambda: SYNTHESIS.prepare(duplicate, {}), "source-duplicate")
    checks += 4

    contract = json.loads(
        (ROOT / "config/web-research-synthesis-foundation.json").read_text(encoding="utf-8")
    )
    assert not any(contract["authority"].values())
    assert contract["policy"]["sourceUrlsIncludedInModelContext"] is False
    assert imports(SYNTHESIS_PATH).isdisjoint(
        {"socket", "urllib", "requests", "http", "subprocess", "webbrowser", "sqlite3"}
    )
    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".py", ".js", ".html", ".css", ".json"}
    )
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert "offline_research_cited_synthesis" not in runtime + package
    checks += 4
    print(f"Offline cited-synthesis boundary passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
