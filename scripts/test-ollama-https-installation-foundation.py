#!/usr/bin/env python3
"""Fail-closed checks for the inactive Ollama HTTPS installation contract."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "ollama-https-installation-contract.json"


class ContractError(ValueError):
    pass


def validate(value: object) -> None:
    required = {
        "schemaVersion", "contractId", "implementationStatus", "runtimeAdmitted",
        "externalSoftwareBundled", "officialCapabilityBasis", "profiles",
        "tlsGatewayPolicy", "certificatePolicy", "clientTrustPolicy",
        "requiredLifecycleEvidence", "currentMachineEffects", "promotionRequires",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ContractError("invalid-contract-shape")
    if (
        value["schemaVersion"] != 1
        or value["contractId"] != "haven42.ollama-https-installation"
        or value["implementationStatus"] != "simulation-only-not-runtime-admitted"
        or value["runtimeAdmitted"] is not False
        or value["externalSoftwareBundled"] is not False
    ):
        raise ContractError("installation-authority-broadened")

    basis = value["officialCapabilityBasis"]
    if basis != {
        "ollamaListenerTransport": "http",
        "documentedNetworkExposurePattern": "reverse-proxy",
        "ollamaMustRemainLoopbackBound": True,
        "sources": [
            "https://docs.ollama.com/faq",
            "https://github.com/ollama/ollama/blob/main/docs/faq.mdx",
        ],
    }:
        raise ContractError("invalid-official-capability-basis")

    profiles = value["profiles"]
    if set(profiles) != {"same-device", "private-network"}:
        raise ContractError("invalid-transport-profiles")
    if profiles["same-device"] != {
        "ollamaBind": "127.0.0.1",
        "havenTransport": "http-loopback",
        "tlsGatewayRequired": False,
        "certificateRequired": False,
    }:
        raise ContractError("unsafe-same-device-profile")
    private = profiles["private-network"]
    if private != {
        "ollamaBind": "127.0.0.1",
        "havenTransport": "https",
        "tlsGatewayRequired": True,
        "certificateRequired": True,
        "authenticationRequired": True,
        "publicExposureAllowed": False,
    }:
        raise ContractError("unsafe-private-network-profile")

    gateway = value["tlsGatewayPolicy"]
    if (
        set(gateway) != {
            "separatelyAcquiredComponentRequired", "immutableVersionRequired",
            "licenseReviewRequired", "publisherSignatureOrAttestationRequired",
            "checksumRequired", "defaultListenScope", "upstream",
            "arbitraryUpstreamAllowed", "allowedRoutes", "unlistedRoutesDefault",
            "managementRoutesExposed", "minimumTlsVersion", "tls13Preferred",
            "clientAuthenticationModes", "minimumGeneratedCredentialEntropyBits",
            "constantTimeCredentialComparisonRequired",
            "credentialHeaderStrippedBeforeUpstream",
            "authenticationFailureRateLimitRequired", "requestBodyLoggingAllowed",
            "authorizationHeaderLoggingAllowed",
        }
        or gateway.get("separatelyAcquiredComponentRequired") is not True
        or gateway.get("immutableVersionRequired") is not True
        or gateway.get("licenseReviewRequired") is not True
        or gateway.get("publisherSignatureOrAttestationRequired") is not True
        or gateway.get("checksumRequired") is not True
        or gateway.get("defaultListenScope") != "selected-private-interface-only"
        or gateway.get("upstream") != "http://127.0.0.1:11434"
        or gateway.get("arbitraryUpstreamAllowed") is not False
        or gateway.get("allowedRoutes") != {
            "GET": ["/api/version", "/api/tags", "/api/ps"],
            "POST": ["/api/chat", "/api/generate"],
        }
        or gateway.get("unlistedRoutesDefault") != "deny"
        or gateway.get("managementRoutesExposed") is not False
        or gateway.get("minimumTlsVersion") != "1.2"
        or gateway.get("tls13Preferred") is not True
        or gateway.get("clientAuthenticationModes") != ["bearer", "x-api-key"]
        or gateway.get("minimumGeneratedCredentialEntropyBits", 0) < 256
        or gateway.get("constantTimeCredentialComparisonRequired") is not True
        or gateway.get("credentialHeaderStrippedBeforeUpstream") is not True
        or gateway.get("authenticationFailureRateLimitRequired") is not True
        or gateway.get("requestBodyLoggingAllowed") is not False
        or gateway.get("authorizationHeaderLoggingAllowed") is not False
    ):
        raise ContractError("unsafe-tls-gateway-policy")

    certificate = value["certificatePolicy"]
    if (
        certificate.get("locallyGeneratedAllowed") is not True
        or certificate.get("endpointIpSanRequired") is not True
        or certificate.get("commonNameOnlyAllowed") is not False
        or certificate.get("minimumRsaBits", 0) < 3072
        or certificate.get("allowedEcdsaCurves") != ["P-256", "P-384"]
        or certificate.get("allowedSignatureHashes") != ["SHA-256", "SHA-384"]
        or not 1 <= certificate.get("maximumValidityDays", 0) <= 397
        or certificate.get("privateKeyExportAllowed") is not False
        or certificate.get("privateKeyRepositoryStorageAllowed") is not False
        or certificate.get("privateKeyLoggingAllowed") is not False
        or certificate.get("privateKeyNetworkTransferAllowed") is not False
        or certificate.get("certificateFingerprintMustBeDisplayed") is not True
    ):
        raise ContractError("unsafe-certificate-policy")

    trust = value["clientTrustPolicy"]
    if (
        trust.get("certificateVerificationRequired") is not True
        or trust.get("hostnameOrIpVerificationRequired") is not True
        or trust.get("trustOnFirstUseAllowed") is not False
        or trust.get("globalVerificationDisableAllowed") is not False
        or trust.get("explicitUserApprovalRequired") is not True
        or trust.get("perUserTrustPreferred") is not True
        or trust.get("systemTrustRequiresSeparateElevationApproval") is not True
        or trust.get("removeOnlyTransactionOwnedTrustEntries") is not True
    ):
        raise ContractError("unsafe-client-trust-policy")

    required_evidence = {
        "clean-install", "existing-ollama-preservation", "certificate-generation",
        "exact-ip-san-verification", "trusted-client-handshake",
        "untrusted-certificate-rejection", "wrong-ip-rejection",
        "unlisted-route-rejection", "authentication-rate-limit",
        "credential-header-upstream-stripping",
        "expired-certificate-rejection", "authenticated-inference",
        "gateway-restart", "certificate-rotation", "upgrade-rollback",
        "exact-uninstall", "trust-entry-removal", "private-key-cleanup",
    }
    if set(value["requiredLifecycleEvidence"]) != required_evidence:
        raise ContractError("incomplete-lifecycle-evidence")
    effects = value["currentMachineEffects"]
    if not effects or any(effect is not False for effect in effects.values()):
        raise ContractError("machine-effect-enabled")
    if len(value["promotionRequires"]) != 8:
        raise ContractError("incomplete-promotion-gates")


def main() -> int:
    baseline = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    validate(baseline)
    checks = 1
    mutations = (
        lambda value: value.update(runtimeAdmitted=True),
        lambda value: value.update(externalSoftwareBundled=True),
        lambda value: value["officialCapabilityBasis"].update(ollamaListenerTransport="https"),
        lambda value: value["profiles"]["private-network"].update(havenTransport="http"),
        lambda value: value["profiles"]["private-network"].update(authenticationRequired=False),
        lambda value: value["profiles"]["private-network"].update(publicExposureAllowed=True),
        lambda value: value["tlsGatewayPolicy"].update(upstream="http://0.0.0.0:11434"),
        lambda value: value["tlsGatewayPolicy"].update(arbitraryUpstreamAllowed=True),
        lambda value: value["tlsGatewayPolicy"].update(unlistedRoutesDefault="allow"),
        lambda value: value["tlsGatewayPolicy"].update(managementRoutesExposed=True),
        lambda value: value["tlsGatewayPolicy"].update(minimumTlsVersion="1.0"),
        lambda value: value["tlsGatewayPolicy"].update(clientAuthenticationModes=[]),
        lambda value: value["tlsGatewayPolicy"].update(minimumGeneratedCredentialEntropyBits=64),
        lambda value: value["tlsGatewayPolicy"].update(credentialHeaderStrippedBeforeUpstream=False),
        lambda value: value["tlsGatewayPolicy"].update(authenticationFailureRateLimitRequired=False),
        lambda value: value["tlsGatewayPolicy"].update(authorizationHeaderLoggingAllowed=True),
        lambda value: value["certificatePolicy"].update(endpointIpSanRequired=False),
        lambda value: value["certificatePolicy"].update(commonNameOnlyAllowed=True),
        lambda value: value["certificatePolicy"].update(minimumRsaBits=2048),
        lambda value: value["certificatePolicy"].update(maximumValidityDays=398),
        lambda value: value["certificatePolicy"].update(privateKeyExportAllowed=True),
        lambda value: value["clientTrustPolicy"].update(certificateVerificationRequired=False),
        lambda value: value["clientTrustPolicy"].update(trustOnFirstUseAllowed=True),
        lambda value: value["clientTrustPolicy"].update(globalVerificationDisableAllowed=True),
        lambda value: value["requiredLifecycleEvidence"].remove("wrong-ip-rejection"),
        lambda value: value["currentMachineEffects"].update(certificateGenerated=True),
    )
    for mutate in mutations:
        hostile = copy.deepcopy(baseline)
        mutate(hostile)
        try:
            validate(hostile)
        except ContractError:
            checks += 1
        else:
            raise AssertionError("unsafe HTTPS installation contract was accepted")
    print(f"Ollama HTTPS installation foundation passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
