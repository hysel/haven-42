#!/usr/bin/env python3
"""Hostile tests for the disabled fixed-provider query adapter."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-web-research-query-adapter.py"
SPEC = importlib.util.spec_from_file_location("query_adapter", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONTRACT = ROOT / "config" / "web-research-query-adapter.json"


def response(**changes) -> bytes:
    item = {
        "ns": 0,
        "pageid": 42,
        "timestamp": "2026-01-01T00:00:00Z",
        "title": "Safe result",
    }
    item.update(changes)
    return json.dumps({"batchcomplete": True, "query": {"searchinfo": {"totalhits": 1}, "search": [item]}}).encode()


class QueryAdapterTests(unittest.TestCase):
    def test_fixed_request_and_engine_derived_destination(self):
        captured = []
        result = MODULE.exercise_fixture_transport("local AI privacy", 3, lambda request: captured.append(request) or response())
        self.assertEqual(captured[0]["host"], "en.wikipedia.org")
        self.assertEqual(captured[0]["path"], "/w/api.php")
        self.assertEqual(captured[0]["credentials"], None)
        self.assertEqual(result["results"][0]["destination"], "https://en.wikipedia.org/?curid=42")
        self.assertFalse(result["results"][0]["activeNavigationAllowed"])
        self.assertFalse(result["networkAuthorityGranted"])

    def test_credential_like_query_is_rejected(self):
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "query-credential-like"):
            MODULE.build_request("token=private", 3)

    def test_active_query_content_is_rejected(self):
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "query-active-content"):
            MODULE.build_request("<script>", 3)

    def test_result_limit_is_bounded(self):
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "result-limit"):
            MODULE.build_request("safe", 11)

    def test_model_style_result_url_is_rejected(self):
        hostile = json.loads(response())
        hostile["query"]["search"][0]["url"] = "https://attacker.example/"
        request = MODULE.build_request("safe", 1)
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "response-result-fields"):
            MODULE.validate_response(request, json.dumps(hostile).encode())

    def test_active_result_title_is_rejected(self):
        request = MODULE.build_request("safe", 1)
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "response-title-active-content"):
            MODULE.validate_response(request, response(title="<img>"))

    def test_oversized_response_is_rejected_before_parse(self):
        request = MODULE.build_request("safe", 1)
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "response-size"):
            MODULE.validate_response(request, b"x" * 65537)

    def test_duplicate_page_ids_are_rejected(self):
        item = json.loads(response())["query"]["search"][0]
        payload = {"batchcomplete": True, "query": {"searchinfo": {"totalhits": 2}, "search": [item, item]}}
        request = MODULE.build_request("safe", 2)
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "response-page-id"):
            MODULE.validate_response(request, json.dumps(payload).encode())

    def test_citation_identity_survives_provider_ranking_changes(self):
        first = json.loads(response())
        second_item = dict(first["query"]["search"][0])
        second_item.update({"pageid": 43, "title": "Another safe result"})
        first["query"]["searchinfo"]["totalhits"] = 2
        first["query"]["search"] = [first["query"]["search"][0], second_item]
        request = MODULE.build_request("safe", 2)
        first_result = MODULE.validate_response(request, json.dumps(first).encode())
        first["query"]["search"].reverse()
        second_result = MODULE.validate_response(request, json.dumps(first).encode())
        first_ids = {
            item["destination"]: item["citationId"] for item in first_result["results"]
        }
        second_ids = {
            item["destination"]: item["citationId"] for item in second_result["results"]
        }
        self.assertEqual(first_ids, second_ids)

    def test_transport_must_be_explicitly_injected(self):
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "fixture-transport-required"):
            MODULE.exercise_fixture_transport("safe", 1, None)

    def test_contract_cannot_enable_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["authority"]["networkActivationAllowed"] = True
            path = Path(temporary) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.QueryAdapterError, "unsafe-query-adapter-contract"):
                MODULE.load_contract(path)

    def test_tampered_request_is_rejected(self):
        request = MODULE.build_request("safe", 1)
        request["host"] = "attacker.example"
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "request-shape"):
            MODULE.validate_response(request, response())

    def test_non_finite_json_number_is_rejected(self):
        request = MODULE.build_request("safe", 1)
        hostile = response().replace(b'"pageid": 42', b'"pageid": NaN')
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "response-json"):
            MODULE.validate_response(request, hostile)

    def test_duplicate_json_keys_are_rejected(self):
        request = MODULE.build_request("safe", 1)
        hostile = response().replace(b'"pageid": 42', b'"pageid": 42, "pageid": 43')
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "response-json"):
            MODULE.validate_response(request, hostile)

    def test_opaque_search_metadata_is_rejected(self):
        request = MODULE.build_request("safe", 1)
        hostile = json.loads(response())
        hostile["query"]["searchinfo"]["suggestion"] = "<active>"
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "response-search-info"):
            MODULE.validate_response(request, json.dumps(hostile).encode())

    def test_unicode_control_characters_are_rejected(self):
        with self.assertRaisesRegex(MODULE.QueryAdapterError, "query-active-content"):
            MODULE.build_request("safe\u202equery", 1)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(QueryAdapterTests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"Web research query adapter passed {result.testsRun} security checks.")
