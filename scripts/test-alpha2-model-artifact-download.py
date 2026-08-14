#!/usr/bin/env python3
"""Offline hostile checks for exact model artifact preparation."""

from __future__ import annotations

from io import BytesIO
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alpha2_model_artifact_download",
    ROOT / "scripts/alpha2-model-artifact-download.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def refused(function, code: str) -> None:
    try:
        function()
    except MODULE.DownloadError as error:
        assert str(error) == code, str(error)
    else:
        raise AssertionError(f"Expected {code}")


def main() -> None:
    completed, total = MODULE._consume_pull_stream(
        BytesIO(
            b'{"status":"pulling","completed":5,"total":10}\n'
            b'{"status":"success"}\n'
        )
    )
    assert (completed, total) == (5, 10)
    refused(
        lambda: MODULE._consume_pull_stream(BytesIO(b'{"status":"pulling"}\n')),
        "provider-download-incomplete",
    )
    refused(
        lambda: MODULE._consume_pull_stream(BytesIO(b'{"error":"bad"}\n')),
        "provider-download-failed",
    )

    runner = MODULE.RUNNER
    originals = {
        "_json_request": runner._json_request,
        "reviewed_qualification_model": runner.reviewed_qualification_model,
    }
    model = {
        "id": "granite41-3b-q4",
        "name": "granite4.1:3b-q4_K_M",
        "manifestDigest": "a" * 64,
        "modelBytes": 100,
        "downloadBytes": 120,
        "automaticEvidenceCandidate": False,
        "qualificationOnly": True,
    }
    try:
        runner.reviewed_qualification_model = lambda _model_id: (
            model, "b" * 64, "0.32.5"
        )
        runner._json_request = lambda _origin, route, **_kwargs: (
            {"version": "0.32.5"} if route == "/api/version" else {"models": []}
        )
        planned = MODULE.prepare_artifact(
            origin="http://127.0.0.1:11434",
            model_id="granite41-3b-q4",
        )
        assert planned["action"] == "planned"
        assert planned["expectedDownloadBytes"] == 120
        assert planned["automaticPromotionAllowed"] is False
        runner._json_request = lambda _origin, route, **_kwargs: (
            {"version": "0.32.5"}
            if route == "/api/version"
            else {"models": [{"name": model["name"], "digest": "sha256:" + "a" * 64}]}
        )
        reused = MODULE.prepare_artifact(
            origin="http://127.0.0.1:11434",
            model_id="granite41-3b-q4",
            apply_download=True,
        )
        assert reused["action"] == "reused"
        MODULE._require_ready_candidate("qwen36-27b-q4")
        refused(
            lambda: MODULE._require_ready_candidate("qwen36-35b-a3b-q4"),
            "candidate-not-ready-for-qualification",
        )
        for deferred_model in (
            "muse-glimmer-30b-q4",
            "muse-glimmer-30b-mlx-nvfp4",
        ):
            refused(
                lambda model_id=deferred_model: MODULE._require_ready_candidate(
                    model_id
                ),
                "candidate-not-ready-for-qualification",
            )
    finally:
        for name, value in originals.items():
            setattr(runner, name, value)
    source = (ROOT / "scripts/alpha2-model-artifact-download.py").read_text(
        encoding="utf-8"
    )
    assert "subprocess" not in source and "shell=True" not in source
    assert "os.remove" not in source and "unlink(" not in source
    documentation = (
        ROOT / "docs/alpha-2-linux-long-term-validation.md"
    ).read_text(encoding="utf-8")
    assert "batch capacity gate" in documentation
    assert "adds at least 8 GiB of working reserve" in documentation
    assert "evidence is already complete and verified" in documentation
    print("Alpha 2 exact model artifact preparation passed hostile offline checks.")


if __name__ == "__main__":
    main()
