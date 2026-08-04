#!/usr/bin/env python3
"""Hostile tests for the effect-free research transport guard."""

from __future__ import annotations

import ast
import importlib.util
import ipaddress
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "scripts/offline_research_transport_guard.py"
SPEC = importlib.util.spec_from_file_location("research_transport_guard", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
HOST = "en.wikipedia.org"


def rejected(action, reason: str) -> None:
    try:
        action()
    except MODULE.TransportRejected as error:
        assert str(error) == reason, (str(error), reason)
        return
    raise AssertionError(f"unexpected transport admission: {reason}")


def receipt(**changes):
    value = {
        "status": 200,
        "contentType": "application/json",
        "contentEncoding": "identity",
        "elapsedMilliseconds": 25,
        "redirects": [],
        "body": b"{}",
    }
    value.update(changes)
    return value


def main() -> int:
    checks = 0
    assert MODULE.validate_destination("https://en.wikipedia.org/w/api.php", HOST)
    for value in (
        "http://en.wikipedia.org/", "https://user@en.wikipedia.org/",
        "https://en.wikipedia.org:8443/", "https://en.wikipedia.org/#x",
        "https://127.0.0.1/", "https://attacker.example/",
    ):
        rejected(lambda value=value: MODULE.validate_destination(value, HOST), "destination-not-allowlisted" if "127.0.0.1" not in value else "destination-not-allowlisted")
        checks += 1
    rejected(lambda: MODULE.validate_destination("https://en.wikipedia.org:bad/", HOST), "destination-shape")
    checks += 1
    assert MODULE.validate_resolution(HOST, HOST, ["208.80.154.224"], ["208.80.154.224"])
    rejected(lambda: MODULE.validate_resolution("attacker.example", HOST, ["8.8.8.8"], ["8.8.8.8"]), "dns-host-not-allowlisted")
    non_public = (
        [str(ipaddress.ip_address(0x7F000001))],
        [str(ipaddress.ip_address(0x0A000001))],
        [str(ipaddress.ip_address(0xA9FE0101))],
        [str(ipaddress.ip_address(1))],
    )
    for value in non_public:
        rejected(lambda value=value: MODULE.validate_resolution(HOST, HOST, value, value), "dns-answer-not-public")
        checks += 1
    rejected(lambda: MODULE.validate_resolution(HOST, HOST, ["8.8.8.8"], ["1.1.1.1"]), "dns-rebinding-detected")
    rejected(lambda: MODULE.validate_resolution(HOST, HOST, ["8.8.8.8", "8.8.8.8"], ["8.8.8.8"]), "dns-answer-duplicate")
    assert MODULE.validate_receipt(receipt(), 65536, 10) == b"{}"
    cases = (
        ({"status": 302}, "http-status"),
        ({"contentType": "text/html"}, "content-type"),
        ({"contentEncoding": "gzip"}, "content-encoding"),
        ({"elapsedMilliseconds": 10001}, "response-time"),
        ({"redirects": ["https://en.wikipedia.org/next"]}, "redirect-not-allowed"),
        ({"body": b"x" * 65537}, "response-size"),
    )
    for change, reason in cases:
        rejected(lambda change=change: MODULE.validate_receipt(receipt(**change), 65536, 10), reason)
        checks += 1
    imports = set()
    for node in ast.walk(ast.parse(PATH.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    assert imports <= {"__future__", "ipaddress", "urllib"}
    runtime = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "web").rglob("*") if path.is_file() and path.suffix in {".py", ".js", ".html", ".css"})
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert "offline_research_transport_guard" not in runtime + package
    for contract_name in (
        "config/web-research-provider-candidates.json",
        "config/web-research-approval-lifecycle.json",
    ):
        contract = json.loads((ROOT / contract_name).read_text(encoding="utf-8"))
        assert not any(contract["authority"].values())
    checks += 8
    print(f"Offline research transport guard passed {checks} hostile and exclusion checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
