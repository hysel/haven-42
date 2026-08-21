import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "validate-alpha2-macos-llamacpp-opencode-coding-result.py"
SPEC = importlib.util.spec_from_file_location("coding_validator", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def load(name):
    return json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))


def fixture():
    return (
        load("alpha-2-apple-m4-lfm25-opencode-coding-result.json"),
        load("alpha-2-apple-silicon-16gib-lfm25-addendum-plan.json"),
        load("alpha-2-apple-m4-lfm25-llamacpp-qualification-result.json"),
        load("model-coding-agent-qualification-policy.json"),
    )


class CodingValidatorTests(unittest.TestCase):
    def test_recorded_failure_result_passes(self):
        MODULE.validate(*fixture())

    def test_recommendation_overclaim_fails(self):
        result, plan, qualification, policy = fixture()
        hostile = copy.deepcopy(result)
        hostile["results"][0]["codingRecommendationEligible"] = True
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate(hostile, plan, qualification, policy)

    def test_missing_gate_fails(self):
        result, plan, qualification, policy = fixture()
        hostile = copy.deepcopy(result)
        hostile["results"][0]["gates"].pop("tool-contract")
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate(hostile, plan, qualification, policy)

    def test_failed_check_cannot_be_reported_as_passed(self):
        result, plan, qualification, policy = fixture()
        hostile = copy.deepcopy(result)
        hostile["results"][0]["gates"]["repository-read-plan-review"]["status"] = "passed"
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate(hostile, plan, qualification, policy)


if __name__ == "__main__":
    unittest.main()
