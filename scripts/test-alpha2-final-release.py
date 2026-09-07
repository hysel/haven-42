"""Positive and hostile tests for final publication evidence, using fake bytes."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from alpha2_final_release import CHECKS, NAMES, TRUST, evaluate_final


def main():
    repository = Path(__file__).resolve().parents[1]
    current = json.loads((repository / "config/alpha-2-final-release-evidence.json").read_text(encoding="utf-8"))
    current_report = evaluate_final(current, repository)
    assert current_report["PublicationAllowed"] is False  # no archive bytes supplied
    assert current_report["ManualAccessibility"] == "deferred-not-run"
    with tempfile.TemporaryDirectory(prefix="haven42-final-release-test-") as directory:
        root = Path(directory)
        proof = root / "proof.json"
        proof.write_text('{"testFixture":true}', encoding="utf-8")
        ref = {"path": proof.name, "sha256": hashlib.sha256(proof.read_bytes()).hexdigest()}
        source = "a" * 40
        artifacts = {}
        for platform, name in NAMES.items():
            blob = platform.encode()
            (root / name).write_bytes(blob)
            artifacts[platform] = dict(name=name, sha256=hashlib.sha256(blob).hexdigest(),
                                       sizeBytes=len(blob), sourceCommit=source,
                                       trust={k: True for k in TRUST[platform]}, evidence=ref.copy())
        hashes = {p: a["sha256"] for p, a in artifacts.items()}
        binding = dict(sourceCommit=source, artifactSha256=hashes)
        proof.write_text(json.dumps(binding, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        ref["sha256"] = hashlib.sha256(proof.read_bytes()).hexdigest()
        for item in artifacts.values():
            item["evidence"] = ref.copy()
        record = dict(schemaVersion=1, kind="haven42-alpha2-final-release-evidence",
                      version="0.4.0-alpha.2", sourceCommit=source, prerelease=True,
                      productionReady=False, artifacts=artifacts,
                      checks={k: dict(status="passed", evidence=ref.copy(), **binding) for k in CHECKS},
                      manualAccessibility=dict(status="deferred-not-run", ownerApprovedDeferral=True,
                                               evidence=ref.copy(), **binding),
                      ownerApproval=dict(approved=True, evidence=ref.copy(), **binding))
        assert evaluate_final(record, root, root)["PublicationAllowed"] is True
        assert evaluate_final(record, root)["PublicationAllowed"] is False
        cases = [
            lambda r: r.update(prerelease=False),
            lambda r: r.update(productionReady=True),
            lambda r: r.update(schemaVersion=True),
            lambda r: r["artifacts"].pop("linux-x64"),
            lambda r: r["artifacts"]["macos-arm64"]["trust"].update(notarization=False),
            lambda r: r["artifacts"]["windows-x64"]["trust"].pop("trusted-timestamp"),
            lambda r: r["artifacts"]["linux-x64"].update(sourceCommit="b" * 40),
            lambda r: r["artifacts"]["linux-x64"].update(name="../escape"),
            lambda r: r["artifacts"]["linux-x64"].update(sizeBytes=True),
            lambda r: r["artifacts"]["linux-x64"].update(sha256="0" * 64),
            lambda r: r["checks"].pop("ubuntu-26.04-x64-nvidia"),
            lambda r: r["checks"]["macos-arm64"].update(sourceCommit="b" * 40),
            lambda r: r["checks"]["macos-arm64"].update(artifactSha256={}),
            lambda r: r["checks"]["macos-arm64"]["evidence"].update(path="../proof.json"),
            lambda r: r["checks"]["macos-arm64"]["evidence"].update(sha256="0" * 64),
            lambda r: r["ownerApproval"].update(artifactSha256={}),
            lambda r: r["ownerApproval"].update(approved="true"),
            lambda r: r["manualAccessibility"].update(ownerApprovedDeferral=False),
            lambda r: r["manualAccessibility"].update(status="passed"),
            lambda r: r["manualAccessibility"].update(status="failed"),
        ]
        for mutate in cases:
            hostile = copy.deepcopy(record)
            mutate(hostile)
            try:
                evaluate_final(hostile, root, root)
            except (ValueError, OSError):
                pass
            else:
                raise AssertionError("unsafe final record accepted")
        for name in CHECKS:
            for status in ("not-run", "failed", "blocked"):
                pending = copy.deepcopy(record)
                pending["checks"][name].update(status=status, evidence=None)
                assert name in evaluate_final(pending, root, root)["RemainingGates"]
        pending = copy.deepcopy(record)
        pending["ownerApproval"].update(approved=False, evidence=None)
        assert not evaluate_final(pending, root, root)["PublicationAllowed"]
        # Deferral permits only unperformed manual assessment, not a regression.
        pending = copy.deepcopy(record)
        pending["manualAccessibility"].update(status="failed", ownerApprovedDeferral=False, evidence=None)
        assert not evaluate_final(pending, root, root)["PublicationAllowed"]
        proof.write_text("changed", encoding="utf-8")
        try:
            evaluate_final(record, root, root)
        except ValueError:
            pass
        else:
            raise AssertionError("modified evidence accepted")
    print("Final Alpha 2 evidence: positive, pending, hostile and byte-tamper checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
