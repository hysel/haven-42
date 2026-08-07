#!/usr/bin/env python3
"""Hostile checks for the unsigned Windows Alpha packet contract."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("alpha_candidate", ROOT / "scripts/build-windows-alpha-candidate.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "portable" / "artifacts"
        source.mkdir(parents=True)
        (source / "haven42-windows-amd64-unsigned-development.zip").write_bytes(b"candidate")
        for name in MODULE.REQUIRED_EVIDENCE:
            (source / name).write_text("evidence\n", encoding="utf-8")
        (source / "build-provenance.json").write_text(json.dumps({
            "application": {"name": "Haven 42", "version": MODULE.VERSION},
            "source": {"commit": "a" * 40, "commitIsExactSource": False, "treeState": "modified-uncommitted"},
            "security": {"signed": False, "releasePublished": False},
        }), encoding="utf-8")
        output = root / "candidate"
        with patch.object(MODULE.platform, "system", return_value="Windows"), patch.object(MODULE.platform, "machine", return_value="AMD64"):
            built = MODULE.build(root / "portable", output)
        assert built["distributionAuthorized"] is False and built["signed"] is False
        assert MODULE.verify(output)["archive"]["name"] == MODULE.ARCHIVE_NAME
        checks += 2
        manifest_path = output / "candidate-manifest.json"
        baseline = json.loads(manifest_path.read_text(encoding="utf-8"))
        for field in ("signed", "publicReleaseAllowed", "distributionAuthorized", "productionReady"):
            hostile = dict(baseline, **{field: True})
            manifest_path.write_text(json.dumps(hostile), encoding="utf-8")
            try:
                MODULE.verify(output)
            except ValueError as error:
                assert str(error) == "candidate-authority-broadened"
            else:
                raise AssertionError(f"candidate authority broadened: {field}")
            checks += 1
        manifest_path.write_text(json.dumps(baseline), encoding="utf-8")
        (output / MODULE.ARCHIVE_NAME).write_bytes(b"tampered")
        try:
            MODULE.verify(output)
        except ValueError as error:
            assert str(error) == "candidate-archive-integrity-failed"
        else:
            raise AssertionError("tampered candidate accepted")
        checks += 1

        clean_source = root / "clean-portable" / "artifacts"
        clean_source.mkdir(parents=True)
        for item in source.iterdir():
            if item.name == "build-provenance.json":
                continue
            (clean_source / item.name).write_bytes(item.read_bytes())
        (clean_source / "build-provenance.json").write_text(json.dumps({
            "application": {"name": "Haven 42", "version": MODULE.VERSION},
            "source": {"commit": "b" * 40, "commitIsExactSource": True, "treeState": "clean"},
            "security": {"signed": False, "releasePublished": False},
        }), encoding="utf-8")
        issue_output = root / "issue-verification"
        with patch.object(MODULE.platform, "system", return_value="Windows"), patch.object(MODULE.platform, "machine", return_value="AMD64"):
            issue = MODULE.build_issue_verification(
                root / "clean-portable", issue_output, 71, 1,
            )
        assert issue["archive"]["name"] == (
            f"haven42-{MODULE.VERSION}-issue71-test1-windows-x64-unsigned.zip"
        )
        assert issue["publicReleaseAllowed"] is True
        assert issue["distributionAuthorized"] is True
        assert issue["productionReady"] is False and issue["signed"] is False
        assert MODULE.verify(issue_output) == issue
        checks += 5

        issue_manifest = issue_output / "candidate-manifest.json"
        issue_baseline = json.loads(issue_manifest.read_text(encoding="utf-8"))
        for mutation in (
            {"exactSourceCommit": False},
            {"treeState": "modified-uncommitted"},
            {"productionReady": True},
            {"issueNumber": 72},
        ):
            issue_manifest.write_text(
                json.dumps({**issue_baseline, **mutation}), encoding="utf-8",
            )
            try:
                MODULE.verify(issue_output)
            except ValueError as error:
                assert str(error) == "issue-verification-authority-invalid"
            else:
                raise AssertionError(f"unsafe issue verification accepted: {mutation}")
            checks += 1
        issue_manifest.write_text(json.dumps(issue_baseline), encoding="utf-8")

        dirty_issue_output = root / "dirty-issue"
        with patch.object(MODULE.platform, "system", return_value="Windows"), patch.object(MODULE.platform, "machine", return_value="AMD64"):
            try:
                MODULE.build_issue_verification(root / "portable", dirty_issue_output, 71, 1)
            except ValueError as error:
                assert str(error) == "issue-verification-requires-clean-exact-source"
            else:
                raise AssertionError("dirty issue-verification package accepted")
        checks += 1
    print(f"Windows alpha candidate tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
