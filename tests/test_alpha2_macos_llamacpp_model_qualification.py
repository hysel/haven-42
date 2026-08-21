import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "alpha2-macos-llamacpp-model-qualification.py"
SPEC = importlib.util.spec_from_file_location("llamacpp_qualification", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class LlamaCppQualificationTests(unittest.TestCase):
    def test_exact_safe_code_shape_passes(self):
        value = {"path": "app/main.py", "code": "def add(a: int, b: int) -> int:\n    return a + b\n"}
        self.assertTrue(MODULE.valid_code_json(json.dumps(value)))

    def test_model_code_is_never_executed(self):
        value = {"path": "app/main.py", "code": "raise RuntimeError('must not execute')\n"}
        self.assertFalse(MODULE.valid_code_json(json.dumps(value)))

    def test_extra_statement_fails(self):
        value = {"path": "app/main.py", "code": "def add(a: int, b: int) -> int:\n    return a + b\nprint('side effect')\n"}
        self.assertFalse(MODULE.valid_code_json(json.dumps(value)))

    def test_wrong_path_fails(self):
        value = {"path": "../app/main.py", "code": "def add(a: int, b: int) -> int:\n    return a + b\n"}
        self.assertFalse(MODULE.valid_code_json(json.dumps(value)))

    def test_tool_contract_accepts_only_one_exact_call(self):
        passing = {"choices": [{"message": {"tool_calls": [{"function": {"name": "read_file", "arguments": '{"filepath":"README.md"}'}}]}}]}
        self.assertTrue(MODULE.valid_tool(passing))
        passing["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = '{"filepath":"secrets.txt"}'
        self.assertFalse(MODULE.valid_tool(passing))

    def test_offload_requires_all_layers(self):
        self.assertTrue(MODULE.full_offload_observed("offloaded 28/28 layers to GPU"))
        self.assertTrue(MODULE.full_offload_observed("offloaded all layers"))
        self.assertFalse(MODULE.full_offload_observed("offloaded 27/28 layers to GPU"))


if __name__ == "__main__":
    unittest.main()
