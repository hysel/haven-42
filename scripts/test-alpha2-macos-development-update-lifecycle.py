#!/usr/bin/env python3
"""Tests for the physical macOS development update lifecycle runner."""

from __future__ import annotations

import hashlib
import importlib.util
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_update", ROOT / "scripts/alpha2-macos-development-update-lifecycle.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
PLAN_PATH = ROOT / "config/alpha-2-macos-development-update-lifecycle-plan.json"


def make_archive(path: Path, payload: bytes) -> str:
    with tarfile.open(path, "w:gz") as archive:
        for directory in ("Haven 42.app", "Haven 42.app/Contents", "Haven 42.app/Contents/MacOS"):
            info = tarfile.TarInfo(directory)
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            archive.addfile(info)
        info = tarfile.TarInfo("Haven 42.app/Contents/MacOS/haven42")
        info.size = len(payload)
        info.mode = 0o755
        archive.addfile(info, io.BytesIO(payload))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MacDevelopmentUpdateLifecycleTests(unittest.TestCase):
    def test_real_file_transition_and_cleanup(self) -> None:
        plan = MODULE.load_plan(PLAN_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.tar.gz"
            candidate = root / "candidate.tar.gz"
            baseline_sha = make_archive(baseline, b"baseline")
            candidate_sha = make_archive(candidate, b"candidate")
            workspace = root / "workspace"
            health_calls = []
            with patch.object(sys, "platform", "darwin"):
                result = MODULE.run_lifecycle(
                    plan,
                    baseline_archive=baseline,
                    baseline_sha256=baseline_sha,
                    baseline_commit="a" * 40,
                    candidate_archive=candidate,
                    candidate_sha256=candidate_sha,
                    candidate_commit="b" * 40,
                    workspace=workspace,
                    health_fn=lambda executable: health_calls.append(executable.read_bytes()),
                )
            self.assertEqual(health_calls, [b"baseline", b"candidate", b"baseline", b"candidate"])
            self.assertTrue(all(result["operations"].values()))
            self.assertFalse(workspace.exists())
            self.assertEqual(result["status"], "partial-pass")
            self.assertFalse(any(result["authority"].values()))

    def test_refuses_existing_workspace_and_digest_mismatch(self) -> None:
        plan = MODULE.load_plan(PLAN_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.tar.gz"
            candidate = root / "candidate.tar.gz"
            baseline_sha = make_archive(baseline, b"baseline")
            candidate_sha = make_archive(candidate, b"candidate")
            workspace = root / "workspace"
            workspace.mkdir()
            with patch.object(sys, "platform", "darwin"):
                with self.assertRaisesRegex(MODULE.LifecycleError, "artifact-digest-mismatch"):
                    MODULE.run_lifecycle(
                        plan,
                        baseline_archive=baseline,
                        baseline_sha256="c" * 64,
                        baseline_commit="a" * 40,
                        candidate_archive=candidate,
                        candidate_sha256=candidate_sha,
                        candidate_commit="b" * 40,
                        workspace=workspace,
                    )

    def test_plan_rejects_extra_authority(self) -> None:
        plan = MODULE.load_plan(PLAN_PATH)
        self.assertFalse(any(plan["authority"].values()))
        with tempfile.TemporaryDirectory() as directory:
            changed = dict(plan)
            changed["unexpected"] = True
            path = Path(directory) / "plan.json"
            path.write_text(__import__("json").dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.LifecycleError, "plan-invalid"):
                MODULE.load_plan(path)
            changed = dict(plan)
            changed["requiredOperations"] = plan["requiredOperations"][:-1]
            path.write_text(__import__("json").dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.LifecycleError, "plan-operations-invalid"):
                MODULE.load_plan(path)
                with self.assertRaisesRegex(MODULE.LifecycleError, "workspace-must-not-exist"):
                    MODULE.run_lifecycle(
                        plan,
                        baseline_archive=baseline,
                        baseline_sha256=baseline_sha,
                        baseline_commit="a" * 40,
                        candidate_archive=candidate,
                        candidate_sha256=candidate_sha,
                        candidate_commit="b" * 40,
                        workspace=workspace,
                    )

    def test_refuses_traversal_and_cleans_owned_failure(self) -> None:
        plan = MODULE.load_plan(PLAN_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hostile = root / "hostile.tar.gz"
            with tarfile.open(hostile, "w:gz") as archive:
                info = tarfile.TarInfo("../escape")
                info.size = 1
                archive.addfile(info, io.BytesIO(b"x"))
            with self.assertRaisesRegex(MODULE.LifecycleError, "unsafe-archive-member"):
                MODULE.extract_app(hostile, root / "extract", maximum_members=10, maximum_bytes=100)
            baseline = root / "baseline.tar.gz"
            candidate = root / "candidate.tar.gz"
            baseline_sha = make_archive(baseline, b"baseline")
            candidate_sha = make_archive(candidate, b"candidate")
            workspace = root / "workspace"
            with patch.object(sys, "platform", "darwin"):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    MODULE.run_lifecycle(
                        plan,
                        baseline_archive=baseline,
                        baseline_sha256=baseline_sha,
                        baseline_commit="a" * 40,
                        candidate_archive=candidate,
                        candidate_sha256=candidate_sha,
                        candidate_commit="b" * 40,
                        workspace=workspace,
                        health_fn=lambda _executable: (_ for _ in ()).throw(RuntimeError("injected")),
                    )
            self.assertFalse(workspace.exists())


if __name__ == "__main__":
    unittest.main()
