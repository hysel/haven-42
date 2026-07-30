#!/usr/bin/env python3
"""Test the local source-attachment review fixture generator."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "create_source_attachment_review_fixtures",
    ROOT / "scripts" / "create-source-attachment-review-fixtures.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="haven42-source-review-") as temporary:
        output = Path(temporary) / "review"
        created = MODULE.create_fixtures(output)
        expected = set(MODULE.FILES)

        assert {path.name for path in created} == expected
        for path in created:
            assert path.is_file()
            content = path.read_text(encoding="utf-8")
            assert len(content.encode("utf-8")) <= 64 * 1024
            assert "\x00" not in content

        assert "<script>fixture text only; never execute</script>" in (
            output / "review-example.py"
        ).read_text(encoding="utf-8")
        assert "<img src=x onerror=" in (
            output / "review-example.tsx"
        ).read_text(encoding="utf-8")
        assert (output / "blocked-review.sh").read_text(encoding="utf-8").startswith(
            "# Intentionally blocked"
        )
        assert (output / "blocked-review.ps1").read_text(
            encoding="utf-8"
        ).startswith("# Intentionally blocked")
        assert (output / "renamed-powershell.txt").read_text(
            encoding="utf-8"
        ).startswith("Write-Host")
        review = (output / "REVIEW.md").read_text(encoding="utf-8")
        assert "must reject the entire" in review
        assert "contents" in review and "do not match its name" in review

        try:
            MODULE.create_fixtures(output)
        except FileExistsError:
            pass
        else:
            raise AssertionError("existing review fixtures were overwritten without --force")

        rewritten = MODULE.create_fixtures(output, force=True)
        assert {path.name for path in rewritten} == expected

    print("Source attachment review fixture test passed: 25 checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
