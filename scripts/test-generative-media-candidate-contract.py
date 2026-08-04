#!/usr/bin/env python3
"""Validate inactive audio/video candidate and consent boundaries."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
HEX40 = re.compile(r"[0-9a-f]{40}")


def match_route(pattern: str, request: str) -> bool:
    if pattern.endswith("/{provider:path}"):
        return request.startswith(pattern.removesuffix("{provider:path}"))
    return pattern == request


def main() -> None:
    contract = json.loads((ROOT / "config/generative-media-candidate-contract.json").read_text(encoding="utf-8"))
    assert contract["status"] == "documentation-and-test-contract-only"
    assert contract["runtimeAdmitted"] is False
    assert contract["activeRegistryEntriesAllowed"] is False
    assert contract["downloadsAllowed"] is False
    assert set(contract["audio"]["formats"]) == {"wav", "flac"}
    assert set(contract["video"]["formats"]) == {"mp4", "webm"}
    assert len(contract["audio"]["requiredGates"]) == 9
    assert len(contract["video"]["requiredGates"]) == 9
    assert all(value is True for key, value in contract["consent"].items() if key != "pathsAndIdentityInputsMayEnterEvidence")
    assert contract["consent"]["pathsAndIdentityInputsMayEnterEvidence"] is False
    candidates = contract["candidates"]
    assert len(candidates) == 6
    assert all(item["promotionBlocked"] is True for item in candidates)
    assert all(HEX40.fullmatch(item["modelRevision"]) for item in candidates)
    assert all(HEX40.fullmatch(item["sourceRevision"]) for item in candidates if "sourceRevision" in item)
    assert all("candidate" in item["status"] or "partial-pass" in item["status"] for item in candidates)
    assert all(contract["audio"]["retention"].values())
    assert all(contract["video"]["retention"].values())
    assert all(contract["lifecycle"].values())

    fixtures = json.loads((ROOT / "examples/fixtures/ace-step-route-collision-cases.json").read_text(encoding="utf-8"))
    for case in fixtures["cases"]:
        first = next(route for route in case["routes"] if match_route(route, case["request"]))
        result = "exact" if first == case["request"] else "collision"
        assert result == case["expected"], case["id"]

    manifests = json.loads((ROOT / "examples/fixtures/generative-media-native-validation-manifests.json").read_text(encoding="utf-8"))
    assert len(manifests["manifests"]) == 4
    assert not any(manifests["authority"].values())
    capability_text = (ROOT / "config/capabilities.json").read_text(encoding="utf-8")
    workflow_text = (ROOT / "config/workflows.json").read_text(encoding="utf-8")
    spec = (ROOT / "package/haven42.spec").read_text(encoding="utf-8").casefold()
    for marker in ("audio.music.create", "media.video.create"):
        assert marker not in capability_text and marker not in workflow_text
    for marker in ("ace-step", "hunyuan", "wan2.2", "ltx-2", "stable-audio"):
        assert marker not in spec
    print("Generative media candidates passed 6 records, 3 route cases, and inactive-registry/package checks.")


if __name__ == "__main__":
    main()
