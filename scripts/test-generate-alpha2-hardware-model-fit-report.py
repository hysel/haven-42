#!/usr/bin/env python3
"""Offline hostile checks for hardware-fit comparison and proposals."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/generate-alpha2-hardware-model-fit-report.py"


def load_module():
    spec = importlib.util.spec_from_file_location("hardware_fit_report", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def result(model_id: str, model: str, *, rate: float, peak: int, full: bool = True) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "haven42-amd-common-baseline-soak",
        "outcome": "passed",
        "modelId": model_id,
        "model": model,
        "manifestDigest": ("a" if model_id == "model-a" else "b") * 64,
        "residency": {"backend": "fixture", "fullGpuOffload": full},
        "capabilityCounts": {"general.chat": 5, "content.write": 5, "content.summarize": 5},
        "metrics": {"averageTokensPerSecond": rate, "peakGpuResidentBytes": peak},
        "powerEvidence": {"collected": False, "reason": "fixture"},
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "automaticPromotionAllowed": False,
    }


def request(reviews: list[dict]) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-hardware-model-comparison-request",
        "hardwareProfiles": [
            {
                "id": "gpu-a", "label": "Fixture GPU A", "vendor": "Fixture",
                "operatingSystem": "Fixture OS", "runtime": "Fixture runtime",
                "usableAcceleratorMemoryBytes": 16 * 1024**3,
                "campaignScope": "shared-baseline", "evidenceDirectories": ["gpu-a"],
            },
            {
                "id": "gpu-b", "label": "Fixture GPU B", "vendor": "Fixture",
                "operatingSystem": "Fixture OS", "runtime": "Fixture runtime",
                "usableAcceleratorMemoryBytes": 12 * 1024**3,
                "campaignScope": "hardware-fit-expansion", "evidenceDirectories": ["gpu-b"],
            },
        ],
        "qualityReviews": reviews,
    }


def refused(module, callback, code: str) -> None:
    try:
        callback()
    except module.ComparisonError as error:
        assert str(error) == code, (str(error), code)
    else:
        raise AssertionError(f"expected refusal: {code}")


def main() -> int:
    module = load_module()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(root / "gpu-a/model-a.json", result("model-a", "Model A", rate=100, peak=2 * 1024**3))
        write(root / "gpu-a/model-b.json", result("model-b", "Model B", rate=200, peak=5 * 1024**3))
        write(root / "gpu-b/model-a.json", result("model-a", "Model A", rate=80, peak=2 * 1024**3))
        write(root / "reviews/a.json", {"sanitized": True})
        write(root / "reviews/b.json", {"sanitized": True})
        request_path = root / "request.json"
        write(request_path, request([]))

        report = module.build_report(request_path, root)
        assert report["disclosures"]["automaticSelectionChanged"] is False
        assert report["disclosures"]["modelCountUsedAsQualityScore"] is False
        gpu_a = next(item for item in report["hardware"] if item["id"] == "gpu-a")
        assert gpu_a["fallbackCandidate"]["modelId"] == "model-a"
        assert gpu_a["taskRecommendationProposals"]["general.chat"]["proposedModelId"] is None
        assert report["crossHardwareModels"][0]["modelId"] == "model-a"

        reviews = []
        for model_id, score, reference in (("model-a", 95, "reviews/a.json"), ("model-b", 80, "reviews/b.json")):
            reviews.append({
                "hardwareId": "gpu-a", "modelId": model_id,
                "scores": {task: score for task in module.TASKS},
                "evidenceReference": reference,
            })
        write(request_path, request(reviews))
        reviewed = module.build_report(request_path, root)
        gpu_a = next(item for item in reviewed["hardware"] if item["id"] == "gpu-a")
        proposal = gpu_a["taskRecommendationProposals"]["general.chat"]
        assert proposal["status"] == "owner-review-required"
        assert proposal["proposedModelId"] == "model-a"  # quality outranks raw speed
        rendered = module.markdown(reviewed)
        assert "Counts show coverage, not quality" in rendered
        assert "No automatic model selection" in rendered

        hostile = result("model-a", "Model A", rate=100, peak=2 * 1024**3)
        hostile["containsRawPromptsOrResponses"] = True
        write(root / "gpu-a/model-a.json", hostile)
        refused(module, lambda: module.build_report(request_path, root), "unsafe-comparison-evidence")

        write(root / "gpu-a/model-a.json", result("model-a", "Model A", rate=100, peak=2 * 1024**3, full=False))
        partial = module.build_report(request_path, root)
        gpu_a = next(item for item in partial["hardware"] if item["id"] == "gpu-a")
        model_a = next(item for item in gpu_a["results"] if item["modelId"] == "model-a")
        assert "partial-offload-observed" in model_a["eligibilityBlockers"]

        unsafe_request = request([])
        unsafe_request["hardwareProfiles"][0]["evidenceDirectories"] = ["../private"]
        write(request_path, unsafe_request)
        refused(module, lambda: module.build_report(request_path, root), "unsafe-comparison-path")

    source = SCRIPT.read_text(encoding="utf-8")
    assert "subprocess" not in source and "urllib" not in source
    assert '.get("response")' not in source and '["response"]' not in source
    print("Alpha 2 hardware model-fit report passed hostile offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
