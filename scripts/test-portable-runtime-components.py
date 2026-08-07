#!/usr/bin/env python3
"""Hostile tests for exact portable runtime component classification."""

from __future__ import annotations

import copy
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from portable_runtime_components import (  # noqa: E402
    ComponentClassificationError,
    classify,
)


def record(path: str, byte: str = "a") -> dict:
    return {"path": path, "sha256": byte * 64, "sizeBytes": 1}


def hashed_record(path: str, digest: str) -> dict:
    return {"path": path, "sha256": digest, "sizeBytes": 1}


def distribution_records() -> list[dict]:
    return [
        hashed_record(
            "LICENSE.txt",
            "da343e362fb1cc2b46c07e179936040dcfe8e92de4aa6d61f2bd4a43486f3ccc",
        ),
        hashed_record(
            "licenses/APACHE-2.0.txt",
            "69849221bfb90053de2134ef5e6d540287b4b98062326492f1f96f5da685524b",
        ),
        hashed_record(
            "licenses/CPYTHON-3.14.6-LICENSE.txt",
            "214919267ac05a769eed6c9e442432ab7cacf108774e4597b2d676c5dd12d020",
        ),
        hashed_record(
            "licenses/LIBFFI-3.4.4-LICENSE.txt",
            "2c9c2acb9743e6b007b91350475308aee44691d96aa20eacef8e199988c8c388",
        ),
        record("THIRD-PARTY-NOTICES.txt"),
    ]


def rejected(files: list[dict], code: str, target: str = "windows-amd64") -> None:
    try:
        classify(files, target, "3.14.6", "3.5.7")
    except ComponentClassificationError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"component classifier unexpectedly accepted: {code}")


def main() -> int:
    fixture = distribution_records() + [
        record("haven42.exe"),
        record("DEVELOPMENT-BUILD.txt"),
        record("_internal/package/resource-integrity.json"),
        record("_internal/python314.dll"),
        record("_internal/_ssl.pyd"),
        record("_internal/base_library.zip"),
        record("_internal/libcrypto-3.dll"),
        record("_internal/libssl-3.dll"),
        record("_internal/libffi-8.dll"),
        hashed_record(
            "_internal/VCRUNTIME140.dll",
            "052ad6a20d375957e82aa6a3c441ea548d89be0981516ca7eb306e063d5027f4",
        ),
        hashed_record(
            "_internal/VCRUNTIME140_1.dll",
            "6a99bc0128e0c7d6cbbf615fcc26909565e17d4ca3451b97f8987f9c6acbc6c8",
        ),
    ]
    result = classify(copy.deepcopy(fixture), "windows-amd64", "3.14.6", "3.5.7")
    assert result["review"] == {
        "completeFileCoverage": True,
        "runtimeRedistributionCleared": False,
        "productionPromotionAllowed": False,
    }
    assert result["projectOwned"]["signingEligibleFiles"] == ["haven42.exe"]
    assert result["distributionEvidence"]["fileCount"] == 5
    assert result["distributionEvidence"]["signingEligible"] is False
    assert result["unclassifiedFiles"] == []
    groups = {item["id"]: item for item in result["runtimeComponents"]}
    assert set(groups) == {"cpython", "libffi", "microsoft-runtime", "openssl"}
    assert groups["cpython"]["fileCount"] == 3
    assert groups["openssl"]["version"] == "3.5.7"
    assert groups["libffi"]["version"] == "3.4.4"
    assert groups["microsoft-runtime"]["version"] == "14.42.34438.0"
    assert groups["cpython"]["reviewStatus"] == (
        "license-text-and-source-provenance-recorded-review-required"
    )
    assert groups["openssl"]["reviewStatus"] == (
        "license-text-and-source-provenance-recorded-review-required"
    )
    assert groups["libffi"]["reviewStatus"] == (
        "license-text-and-source-provenance-recorded-review-required"
    )
    assert groups["cpython"]["sourceProvenance"]["distribution"]["sha256"] == (
        "14b3e9a710a3fcf0bd9b55ab6b60412bd91227563f813fc49040cabc0209e0bd"
    )
    assert groups["libffi"]["sourceProvenance"]["sourceTagCommit"] == (
        "73b247f34ef3ae1859b8c2c34d321d34ebc5db15"
    )
    assert (
        groups["microsoft-runtime"]["sourceProvenance"]["redistributionCleared"]
        is False
    )
    assert all(not item["signingEligible"] for item in groups.values())
    passed = 1

    hostile = [
        (
            fixture + [record("_internal/unknown.dat")],
            "unclassified-package-file:_internal/unknown.dat",
            "windows-amd64",
        ),
        (
            [
                record("LICENSE.txt") if item["path"] == "LICENSE.txt" else item
                for item in fixture
            ],
            "distribution-evidence-hash-mismatch:LICENSE.txt",
            "windows-amd64",
        ),
        (
            fixture + [record("_internal/script.py")],
            "unclassified-package-file:_internal/script.py",
            "windows-amd64",
        ),
        (
            fixture + [copy.deepcopy(fixture[0])],
            "invalid-component-file-record",
            "windows-amd64",
        ),
        (
            fixture + [record("../escape.dll")],
            "invalid-component-file-record",
            "windows-amd64",
        ),
        (
            fixture + [{"path": "_internal/new.dll", "sha256": "bad", "sizeBytes": 1}],
            "invalid-component-file-record",
            "windows-amd64",
        ),
        (
            fixture + [record("_internal/api-ms-win-core-file-l1-1-0.dll")],
            "host-derived-windows-runtime-file:"
            "_internal/api-ms-win-core-file-l1-1-0.dll",
            "windows-amd64",
        ),
        (
            [
                record("_internal/VCRUNTIME140.dll")
                if item["path"] == "_internal/VCRUNTIME140.dll"
                else item
                for item in fixture
            ],
            "windows-runtime-hash-mismatch:_internal/VCRUNTIME140.dll",
            "windows-amd64",
        ),
        (
            [item for item in fixture if item["path"] != "_internal/python314.dll"
             and item["path"] != "_internal/_ssl.pyd"
             and item["path"] != "_internal/base_library.zip"],
            "required-component-files-missing",
            "windows-amd64",
        ),
        (fixture, "invalid-component-target", "../windows"),
    ]
    for files, code, target in hostile:
        rejected(files, code, target)
        passed += 1

    linux = distribution_records() + [
        record("haven42"),
        record("DEVELOPMENT-BUILD.txt"),
        record("_internal/package/resource-integrity.json"),
        record("_internal/libpython3.14.so.1.0"),
        record("_internal/lib-dynload/_ssl.cpython-314-x86_64-linux-gnu.so"),
        record("_internal/libssl.so.3"),
        record("_internal/libcrypto.so.3"),
        record("_internal/libffi.so.8"),
        record("_internal/libz.so.1"),
    ]
    linux_result = classify(linux, "linux-x86_64", "3.14.6", "3.5.7")
    assert {item["id"] for item in linux_result["runtimeComponents"]} == {
        "cpython", "libffi", "openssl", "platform-runtime",
    }
    assert all(
        item["sourceProvenance"] == {
            "status": "target-native-verification-required",
        }
        for item in linux_result["runtimeComponents"]
    )
    passed += 1

    macos = distribution_records() + [
        record("haven42"),
        record("DEVELOPMENT-BUILD.txt"),
        record("_internal/package/resource-integrity.json"),
        record("_internal/Python.framework/Versions/3.14/Python"),
        record("_internal/_ssl.cpython-314-darwin.so"),
        record("_internal/libssl.3.dylib"),
    ]
    macos_result = classify(macos, "darwin-arm64", "3.14.6", "3.5.7")
    assert {item["id"] for item in macos_result["runtimeComponents"]} == {
        "cpython", "openssl",
    }
    passed += 1

    print(f"Portable runtime component self-test passed: {passed} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
