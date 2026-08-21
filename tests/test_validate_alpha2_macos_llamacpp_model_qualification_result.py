import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "validate-alpha2-macos-llamacpp-model-qualification-result.py"
SPEC = importlib.util.spec_from_file_location("validator", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def fixture():
    plan = json.loads((ROOT / "config" / "alpha-2-apple-silicon-16gib-lfm25-addendum-plan.json").read_text())
    checks = {}
    metrics = {}
    for name in set(plan["testContract"]) - {"version"}:
        checks[name] = {"status": "passed", "responseRetained": False}
        metrics[name] = {"metalDetected": True, "allLayersOffloaded": True, "authenticationRequired": True, "unloadPassed": True}
    checks["structuredCode"] = {"status": "failed", "errorCode": "planned-execution-not-performed-safety-boundary", "responseRetained": False}
    metrics["structuredCode"] |= {"validationMethod": "ast-only", "modelGeneratedCodeExecuted": False}
    results = []
    for candidate in plan["candidates"]:
        results.append({"modelId": candidate["modelId"], "modelSha256": candidate["modelSha256"], "repositoryRevision": candidate["repositoryRevision"], "status": "failed", "corePassed": False, "checks": checks, "metrics": metrics, "codingSurfaceStatus": "not-run", "codingRecommendationEligible": False})
    result = {"schemaVersion": 1, "kind": "haven42-apple-silicon-llamacpp-model-qualification-result", "planCanonicalSha256": MODULE.canonical_sha256(plan), "runtime": plan["runtime"], "results": results, "rawPromptsOrResponsesRetained": False, "privateIdentityRetained": False, "automaticDefaultChangeAllowed": False, "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False}
    return plan, result


class ValidatorTests(unittest.TestCase):
    def test_valid_result_passes(self):
        plan, result = fixture()
        MODULE.validate(result, plan)

    def test_overclaim_fails(self):
        plan, result = fixture()
        result["results"][0]["codingRecommendationEligible"] = True
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate(result, plan)

    def test_missing_runtime_proof_fails(self):
        plan, result = fixture()
        result["results"][0]["metrics"]["generalChat"]["metalDetected"] = False
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate(result, plan)

    def test_model_code_execution_overclaim_fails(self):
        plan, result = fixture()
        result["results"][0]["checks"]["structuredCode"] = {"status": "passed", "responseRetained": False}
        result["results"][0]["metrics"]["structuredCode"]["modelGeneratedCodeExecuted"] = True
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate(result, plan)


if __name__ == "__main__":
    unittest.main()
