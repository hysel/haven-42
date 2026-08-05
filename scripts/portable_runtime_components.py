#!/usr/bin/env python3
"""Deterministically classify portable package files for license evidence."""

from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath
import re
from typing import Any


PROJECT_FILES = {
    "DEVELOPMENT-BUILD.txt",
    "_internal/package/resource-integrity.json",
    "_internal/web/static/index.html",
    "_internal/web/static/app.js",
    "_internal/web/static/styles.css",
    "_internal/config/text-capability-model-recommendations.json",
    "_internal/config/evidence-catalog.tsv",
    "_internal/config/agent-surface-capabilities.json",
    "_internal/config/agent-surface-solutions.json",
    "_internal/config/install-component-registry.json",
    "_internal/config/workflows.json",
    "_internal/config/windows-alpha-contract.json",
    "_internal/config/windows-alpha-model-catalog.json",
    "_internal/config/windows-alpha-component-registry.json",
    "_internal/config/windows-alpha-resource-monitor-contract.json",
    "_internal/config/windows-alpha-quantization-contract.json",
}
NATIVE_SUFFIX = re.compile(r"(?i)(?:\.dll|\.pyd|\.dylib|\.so(?:\.\d+)*)$")
PYTHON_LIBRARY = re.compile(
    r"(?i)(?:^|/)(?:python\d+(?:t)?\.dll|libpython\d+(?:\.\d+)*(?:t)?\.so(?:\.\d+)*"
    r"|libpython\d+(?:\.\d+)*(?:t)?\.dylib|Python)$"
)
CPYTHON_EXTENSION = re.compile(
    r"(?i)(?:\.pyd|(?:cpython|lib-dynload|^_internal/(?:_|select|unicodedata))"
    r".*\.so(?:\.\d+)*)$"
)

COMPONENTS = {
    "cpython": {
        "name": "CPython embedded runtime",
        "license": "PSF-2.0",
        "reviewStatus": "license-text-included-source-provenance-required",
    },
    "openssl": {
        "name": "OpenSSL runtime",
        "license": "Apache-2.0",
        "reviewStatus": "license-text-included-source-provenance-required",
    },
    "libffi": {
        "name": "libffi runtime",
        "license": "MIT",
        "reviewStatus": "source-version-and-license-text-required",
    },
    "microsoft-runtime": {
        "name": "Microsoft application-local runtime",
        "license": "LicenseRef-Microsoft-Redistributable-Review",
        "reviewStatus": "licensed-source-and-redistribution-review-required",
    },
    "platform-runtime": {
        "name": "Other platform-native runtime",
        "license": "NOASSERTION",
        "reviewStatus": "source-version-and-license-review-required",
    },
}
WINDOWS_PYTHON_DISTRIBUTION = {
    "url": "https://www.python.org/ftp/python/3.14.6/python-3.14.6-amd64.exe",
    "sha256": "14b3e9a710a3fcf0bd9b55ab6b60412bd91227563f813fc49040cabc0209e0bd",
    "sbom": (
        "https://www.python.org/ftp/python/3.14.6/"
        "python-3.14.6-amd64.exe.spdx.json"
    ),
    "sigstore": (
        "https://www.python.org/ftp/python/3.14.6/"
        "python-3.14.6-amd64.exe.sigstore"
    ),
}
WINDOWS_SOURCE_PROVENANCE = {
    "cpython": {
        "status": "recorded",
        "distribution": WINDOWS_PYTHON_DISTRIBUTION,
        "sourceRepository": "https://github.com/python/cpython",
        "sourceTag": "v3.14.6",
        "sourceCommit": "c63aec69bd59c55314c06c23f4c22c03de76fe45",
    },
    "openssl": {
        "status": "recorded",
        "parentDistribution": WINDOWS_PYTHON_DISTRIBUTION,
        "sourceArchive": (
            "https://github.com/python/cpython-source-deps/archive/"
            "refs/tags/openssl-3.5.7.tar.gz"
        ),
        "sourceArchiveSha256": (
            "ca94e7c6c223d9caf77bb51aac5949186379608ea2a0cad3aa8bdf31856912e9"
        ),
        "sourceTagCommit": "6a6901fa60c604816acb50b4e167791e5339c8f8",
        "binaryTagCommit": "3217be5a2a7e20dbc5f5b5160ef21a9c84de7138",
        "licenseEvidence": "APACHE-2.0.txt",
    },
    "libffi": {
        "status": "recorded",
        "parentDistribution": WINDOWS_PYTHON_DISTRIBUTION,
        "sourceArchive": (
            "https://github.com/python/cpython-source-deps/archive/"
            "refs/tags/libffi-3.4.4.tar.gz"
        ),
        "sourceArchiveSha256": (
            "9d802681adfea27d84cae0487a785fb9caa925bdad44c401b364c59ab2b8edda"
        ),
        "sourceTagCommit": "73b247f34ef3ae1859b8c2c34d321d34ebc5db15",
        "binaryTagCommit": "94cb9a1c7feb608adf2b9f8fe2dbd6925ffbf90d",
        "licenseEvidence": "LIBFFI-3.4.4-LICENSE.txt",
    },
    "microsoft-runtime": {
        "status": "recorded-review-required",
        "distribution": {
            "url": (
                "https://www.python.org/ftp/python/3.14.6/"
                "python-3.14.6-embed-amd64.zip"
            ),
            "sha256": (
                "df901e84a896ff1ee720ad03377e0c8d"
                "8c2244fda79808aeeaff6316df1cb75c"
            ),
        },
        "individualFileOriginVerified": True,
        "authenticode": {
            "auditStatus": "valid",
            "signerSubject": (
                "CN=Microsoft Windows Software Compatibility Publisher, "
                "O=Microsoft Corporation, L=Redmond, S=Washington, C=US"
            ),
        },
        "redistributionCleared": False,
    },
}
WINDOWS_RUNTIME_HASHES = {
    "vcruntime140.dll": (
        "052ad6a20d375957e82aa6a3c441ea548d89be0981516ca7eb306e063d5027f4"
    ),
    "vcruntime140_1.dll": (
        "6a99bc0128e0c7d6cbbf615fcc26909565e17d4ca3451b97f8987f9c6acbc6c8"
    ),
}


class ComponentClassificationError(ValueError):
    """Raised when a packaged file cannot be classified safely."""


def _classify(path: str) -> str:
    name = PurePosixPath(path).name
    folded = name.casefold()
    if PYTHON_LIBRARY.search(path) or "python.framework/" in path.casefold():
        return "cpython"
    if CPYTHON_EXTENSION.search(path):
        return "cpython"
    if folded in {"base_library.zip", "python3.zip"}:
        return "cpython"
    if re.fullmatch(
        r"lib(?:ssl|crypto)(?:-[0-9]+)?(?:\.\d+)*\.(?:dll|dylib)",
        folded,
    ):
        return "openssl"
    if re.fullmatch(r"lib(?:ssl|crypto)\.so(?:\.\d+)*", folded):
        return "openssl"
    if folded.startswith("libffi") and NATIVE_SUFFIX.search(folded):
        return "libffi"
    if (
        re.fullmatch(r"api-ms-win-.*\.dll", folded)
        or folded in {"ucrtbase.dll", "vcruntime140.dll", "vcruntime140_1.dll"}
    ):
        return "microsoft-runtime"
    if NATIVE_SUFFIX.search(folded):
        return "platform-runtime"
    raise ComponentClassificationError(f"unclassified-package-file:{path}")


def classify(
    package_files: list[dict[str, Any]],
    target: str,
    python_version: str,
    openssl_version: str,
) -> dict[str, Any]:
    if not re.fullmatch(r"(?:windows|linux|darwin)-[a-z0-9_]+", target):
        raise ComponentClassificationError("invalid-component-target")
    project_files: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[str] = set()
    for record in package_files:
        path_value = record.get("path") if isinstance(record, dict) else None
        if (
            not isinstance(record, dict)
            or set(record) != {"path", "sha256", "sizeBytes"}
            or not isinstance(path_value, str)
            or not path_value
            or "\\" in path_value
            or PurePosixPath(path_value).is_absolute()
            or any(part in {"", ".", ".."} for part in PurePosixPath(path_value).parts)
            or not re.fullmatch(r"[0-9a-f]{64}", str(record["sha256"]))
            or isinstance(record["sizeBytes"], bool)
            or not isinstance(record["sizeBytes"], int)
            or record["sizeBytes"] < 0
            or path_value in seen
        ):
            raise ComponentClassificationError("invalid-component-file-record")
        path = path_value
        seen.add(path)
        if path in {"haven42", "haven42.exe"} or path in PROJECT_FILES:
            project_files.append(record)
            continue
        component_id = _classify(path)
        folded_name = PurePosixPath(path).name.casefold()
        if target == "windows-amd64" and component_id == "microsoft-runtime":
            expected_hash = WINDOWS_RUNTIME_HASHES.get(folded_name)
            if expected_hash is None:
                raise ComponentClassificationError(
                    f"host-derived-windows-runtime-file:{path}"
                )
            if record["sha256"] != expected_hash:
                raise ComponentClassificationError(
                    f"windows-runtime-hash-mismatch:{path}"
                )
        grouped[component_id].append(record)
    if not project_files or not grouped.get("cpython"):
        raise ComponentClassificationError("required-component-files-missing")

    windows_target = target == "windows-amd64"
    versions = {
        "cpython": python_version,
        "openssl": openssl_version,
        "libffi": "3.4.4" if windows_target else "unresolved",
        "microsoft-runtime": "14.42.34438.0" if windows_target else "unresolved",
        "platform-runtime": "unresolved",
    }
    runtime_components = []
    for component_id in sorted(grouped):
        definition = COMPONENTS[component_id]
        files = sorted(grouped[component_id], key=lambda item: item["path"])
        runtime_components.append({
            "id": component_id,
            "name": definition["name"],
            "version": versions[component_id],
            "license": definition["license"],
            "reviewStatus": (
                "license-text-and-source-provenance-recorded-review-required"
                if windows_target and component_id in {
                    "cpython", "libffi", "openssl"
                }
                else "file-origin-recorded-redistribution-review-required"
                if windows_target and component_id == "microsoft-runtime"
                else definition["reviewStatus"]
            ),
            "sourceProvenance": WINDOWS_SOURCE_PROVENANCE.get(
                component_id,
                {"status": "target-native-verification-required"},
            ) if windows_target else {
                "status": "target-native-verification-required",
            },
            "signingEligible": False,
            "fileCount": len(files),
            "files": files,
        })
    project_files.sort(key=lambda item: item["path"])
    if len(project_files) + sum(item["fileCount"] for item in runtime_components) != len(package_files):
        raise ComponentClassificationError("component-file-coverage-mismatch")
    return {
        "schemaVersion": 1,
        "target": target,
        "projectOwned": {
            "name": "Haven 42",
            "version": "0.4.0-alpha.1",
            "license": "MIT",
            "signingEligibleFiles": [
                path for path in ("haven42", "haven42.exe") if path in seen
            ],
            "fileCount": len(project_files),
            "files": project_files,
        },
        "runtimeComponents": runtime_components,
        "unclassifiedFiles": [],
        "review": {
            "completeFileCoverage": True,
            "runtimeRedistributionCleared": False,
            "productionPromotionAllowed": False,
        },
    }
