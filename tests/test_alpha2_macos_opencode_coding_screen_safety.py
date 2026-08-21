import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "alpha2-macos-opencode-coding-screen.py"
SPEC = importlib.util.spec_from_file_location("opencode_screen", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CodingScreenSafetyTests(unittest.TestCase):
    def test_exact_shape_passes(self):
        self.assertTrue(MODULE.valid_add_function({"path": "app/main.py", "code": "def add(a: int, b: int) -> int:\n    return a + b\n"}))

    def test_generated_code_is_not_executed(self):
        self.assertFalse(MODULE.valid_add_function({"path": "app/main.py", "code": "raise RuntimeError('do not execute')\n"}))

    def test_extra_side_effect_fails(self):
        self.assertFalse(MODULE.valid_add_function({"path": "app/main.py", "code": "def add(a: int, b: int) -> int:\n    return a + b\nprint('side effect')\n"}))


if __name__ == "__main__":
    unittest.main()
