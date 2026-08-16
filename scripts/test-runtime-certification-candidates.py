#!/usr/bin/env python3
"""Offline hostile tests for on-demand runtime certification discovery."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "runtime_certification_candidates",
    ROOT / "scripts" / "discover-runtime-certification-candidates.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _asset(repository: str, tag: str, name: str, marker: str) -> dict:
    return {
        "name": name,
        "size": 1024 + len(name),
        "digest": f"sha256:{marker * 64}",
        "browser_download_url": (
            f"https://github.com/{repository}/releases/download/{tag}/{name}"
        ),
    }


def _release(repository: str, tag: str, names: list[str], marker: str) -> dict:
    return {
        "tag_name": tag,
        "draft": False,
        "prerelease": False,
        "html_url": f"https://github.com/{repository}/releases/tag/{tag}",
        "published_at": "2026-08-16T12:00:00Z",
        "assets": [_asset(repository, tag, name, marker) for name in names],
    }


def _refused(function, code: str) -> None:
    try:
        function()
    except MODULE.CertificationDiscoveryError as error:
        assert str(error) == code, (str(error), code)
    else:
        raise AssertionError(f"Expected refusal: {code}")


def main() -> int:
    checks = 0
    contract = json.loads(
        (ROOT / "config" / "runtime-certification-sources.json").read_text(
            encoding="utf-8"
        )
    )
    MODULE._validate_contract(contract)
    checks += 1

    ollama_names = [
        "ollama-windows-amd64.zip",
        "ollama-windows-amd64-rocm.zip",
        "ollama-linux-amd64.tar.zst",
        "ollama-linux-amd64-rocm.tar.zst",
    ]
    llama_names = [
        "llama-b10400-bin-win-cpu-x64.zip",
        "llama-b10400-bin-win-cuda-12.4-x64.zip",
        "llama-b10400-bin-win-rocm-7.14-x64.zip",
        "llama-b10400-bin-win-sycl-x64.zip",
        "llama-b10400-bin-win-vulkan-x64.zip",
        "llama-b10400-bin-ubuntu-x64.tar.gz",
        "llama-b10400-bin-ubuntu-rocm-7.14-x64.tar.gz",
        "llama-b10400-bin-ubuntu-sycl-fp16-x64.tar.gz",
        "llama-b10400-bin-ubuntu-vulkan-x64.tar.gz",
    ]
    with tempfile.TemporaryDirectory(prefix="haven42-runtime-cert-") as raw:
        work = Path(raw)
        ollama_path = work / "ollama.json"
        llama_path = work / "llama.json"
        registry_path = work / "registry.json"
        ollama = _release("ollama/ollama", "v0.32.13", ollama_names, "a")
        llama = _release("ggml-org/llama.cpp", "b10400", llama_names, "b")
        ollama_path.write_text(json.dumps(ollama), encoding="utf-8")
        llama_path.write_text(json.dumps(llama), encoding="utf-8")
        registry_path.write_text(
            json.dumps({
                "runtimes": [{"version": "0.32.13"}],
                "llamaCppRuntimes": [{"version": "b10375"}],
            }),
            encoding="utf-8",
        )
        report = MODULE.discover(
            ROOT / "config" / "runtime-certification-sources.json",
            registry_path,
            {"ollama": ollama_path, "llama-cpp": llama_path},
            set(),
            5,
        )
        by_id = {item["runtimeId"]: item for item in report["candidates"]}
        assert by_id["ollama"]["inventoryStatus"] == "already-tracked-exact-version"
        assert by_id["llama-cpp"]["inventoryStatus"] == "new-official-release-candidate"
        assert len(by_id["ollama"]["matchedArtifacts"]) == 4
        assert len(by_id["llama-cpp"]["matchedArtifacts"]) == 9
        assert not by_id["llama-cpp"]["missingArtifactProfiles"]
        assert all(item["status"] == "pending" for item in by_id["llama-cpp"]["certificationPlan"])
        assert report["summary"] == {
            "candidateCount": 2,
            "newReleaseCount": 1,
            "trackedLatestCount": 1,
            "missingProfileCount": 0,
        }
        assert report["effects"] == {
            "downloadsModelsOrRuntimes": False,
            "startsNativeTests": False,
            "writesCompatibilityRegistry": False,
            "changesManagedDefaults": False,
            "changesSupportLabels": False,
            "changesReleasePolicy": False,
        }
        checks += 10

        assert MODULE._tracked_versions(
            json.loads(registry_path.read_text(encoding="utf-8")),
            "llamaCppRuntimes",
            r"^b([1-9][0-9]*)$",
        ) == {"10375"}
        checks += 1

        ollama_source = next(
            source for source in contract["sources"] if source["id"] == "ollama"
        )
        tracked = {"0.32.13"}
        gates = contract["requiredCertificationGates"]

        hostile = copy.deepcopy(ollama)
        hostile["draft"] = True
        _refused(
            lambda: MODULE._release_record(ollama_source, hostile, tracked, gates),
            "invalid-official-release:ollama",
        )
        checks += 1

        hostile = copy.deepcopy(ollama)
        hostile["prerelease"] = True
        _refused(
            lambda: MODULE._release_record(ollama_source, hostile, tracked, gates),
            "invalid-official-release:ollama",
        )
        checks += 1

        hostile = copy.deepcopy(ollama)
        hostile["tag_name"] = "latest"
        hostile["html_url"] = "https://github.com/ollama/ollama/releases/tag/latest"
        _refused(
            lambda: MODULE._release_record(ollama_source, hostile, tracked, gates),
            "invalid-official-release:ollama",
        )
        checks += 1

        hostile = copy.deepcopy(ollama)
        hostile["assets"][0]["digest"] = None
        _refused(
            lambda: MODULE._release_record(ollama_source, hostile, tracked, gates),
            "invalid-official-release-asset:ollama",
        )
        checks += 1

        hostile = copy.deepcopy(ollama)
        hostile["assets"][0]["browser_download_url"] = "https://example.invalid/runtime.zip"
        _refused(
            lambda: MODULE._release_record(ollama_source, hostile, tracked, gates),
            "invalid-official-release-asset:ollama",
        )
        checks += 1

        hostile = copy.deepcopy(ollama)
        hostile["assets"].append(copy.deepcopy(hostile["assets"][0]))
        _refused(
            lambda: MODULE._release_record(ollama_source, hostile, tracked, gates),
            "invalid-official-release-asset:ollama",
        )
        checks += 1

        incomplete = copy.deepcopy(ollama)
        incomplete["assets"] = incomplete["assets"][:-1]
        candidate = MODULE._release_record(ollama_source, incomplete, tracked, gates)
        assert candidate["candidateStatus"] == "blocked-required-artifact-profiles-missing"
        assert candidate["missingArtifactProfiles"] == [{
            "platform": "linux-x64", "backend": "rocm", "role": "runtime-supplement"
        }]
        assert candidate["automaticPromotionAllowed"] is False
        checks += 3

        unsafe_contract = copy.deepcopy(contract)
        unsafe_contract["rules"]["startsNativeTests"] = True
        unsafe_path = work / "unsafe-contract.json"
        unsafe_path.write_text(json.dumps(unsafe_contract), encoding="utf-8")
        _refused(
            lambda: MODULE.discover(unsafe_path, registry_path, {}, set(), 5),
            "invalid-runtime-certification-rules",
        )
        checks += 1

        _refused(
            lambda: MODULE.discover(
                ROOT / "config" / "runtime-certification-sources.json",
                registry_path,
                {},
                {"unknown"},
                5,
            ),
            "unknown-runtime-source",
        )
        checks += 1

    print(f"Runtime certification discovery passed {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
