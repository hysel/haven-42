#!/usr/bin/env python3
"""Fail closed on retrieval, research, and media expansion contracts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    value = json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))
    assert value["schemaVersion"] == 1
    return value


def main() -> None:
    retrieval = load("retrieval-expansion-evaluation.json")
    assert retrieval["status"] == "evaluation-contract-only"
    assert retrieval["semanticEmbeddings"]["candidateSelected"] is False
    assert retrieval["semanticEmbeddings"]["separateFromGenerationModelRequired"] is True
    assert retrieval["semanticEmbeddings"]["qualityComparisonAgainstLexicalRequired"] is True
    assert retrieval["persistentEncryptedLibrary"]["storageEngineSelected"] is False
    assert retrieval["persistentEncryptedLibrary"]["encryptionEngineSelected"] is False
    assert retrieval["persistentEncryptedLibrary"]["plaintextFallbackAllowed"] is False
    assert retrieval["persistentEncryptedLibrary"]["userScopedOsCredentialStoreRequired"] is True
    assert all(value is False for value in retrieval["authority"].values())

    research = load("web-research-expansion-evaluation.json")
    assert research["status"] == "evaluation-contract-only"
    assert research["selfHostedSearch"]["candidateSelected"] is False
    assert research["selfHostedSearch"]["credentialsAllowed"] is False
    assert research["selfHostedSearch"]["ssrfControlsMayBeWeakened"] is False
    assert research["boundedMultiQuery"]["maximumCandidateQueries"] == 4
    assert research["boundedMultiQuery"]["eachQueryRequiresVisibleApproval"] is True
    assert research["boundedMultiQuery"]["autonomousFollowUpAllowed"] is False
    assert research["boundedMultiQuery"]["queryContentFromUntrustedPageAllowed"] is False
    assert all(value is False for value in research["authority"].values())

    media = load("media-provider-admission-contract.json")
    assert media["status"] == "external-evidence-required-no-provider-admitted"
    assert set(media["artifactCandidates"]) == {"audio", "video"}
    assert media["artifactCandidates"]["audio"]["mediaTypes"] == ["audio/wav", "audio/flac"]
    assert media["artifactCandidates"]["video"]["mediaTypes"] == ["video/mp4", "video/webm"]
    assert all(item["activeContentAllowed"] is False for item in media["artifactCandidates"].values())
    assert len(media["promotionGates"]) == 12 and len(set(media["promotionGates"])) == 12
    assert all(value is False for value in media["authority"].values())
    print("Future expansion contracts passed 26 fail-closed checks.")


if __name__ == "__main__":
    main()
