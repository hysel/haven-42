#!/usr/bin/env python3
"""Sign, notarize, staple, and verify one exact Haven 42 macOS app bundle."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable


CODESIGN = Path("/usr/bin/codesign")
DITTO = Path("/usr/bin/ditto")
FILE = Path("/usr/bin/file")
SECURITY = Path("/usr/bin/security")
SPCTL = Path("/usr/sbin/spctl")
XCRUN = Path("/usr/bin/xcrun")
APP_NAME = "Haven 42.app"
PACKAGE_ROOT_NAME = "Haven42"
DATA_DIRECTORY_NAME = "Haven42-Data"
LOG_DIRECTORY_NAME = "Haven42-Logs"
UNSIGNED_ARCHIVE_NAME = "haven42-darwin-arm64-unsigned-development-app.tar.gz"
UNSIGNED_EVIDENCE_NAME = "macos-app-build-result.json"
BUNDLE_ID = "org.haven42.desktop"
ALLOWED_VERSIONS = {"0.4.0-alpha.2"}
IDENTITY_SHA1 = re.compile(r"[0-9A-Fa-f]{40}")
PROFILE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
RESOURCE_RUNTIME_ENTRIES = {
    "base_library.zip", "config", "package", "scripts", "web",
}
SOURCE_APP_LINKS = {
    "Contents/Frameworks/Python": "Python.framework/Versions/3.14/Python",
    "Contents/Frameworks/Python.framework/Python": "Versions/Current/Python",
    "Contents/Frameworks/Python.framework/Resources": "Versions/Current/Resources",
    "Contents/Frameworks/Python.framework/Versions/Current": "3.14",
    **{
        f"Contents/Frameworks/{name}": f"../Resources/Runtime/{name}"
        for name in RESOURCE_RUNTIME_ENTRIES
    },
    "Contents/Frameworks/python3.14": "python3__dot__14",
    "Contents/Resources/python3.14": "../Frameworks/python3__dot__14",
}


class SigningError(RuntimeError):
    """Raised when a release-signing boundary cannot be proved."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def invoke(
    command: list[str],
    *,
    runner: Callable = subprocess.run,
    timeout: int = 900,
) -> subprocess.CompletedProcess:
    return runner(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        shell=False,
        close_fds=True,
        env={"PATH": "/usr/bin:/bin:/usr/sbin", "LANG": "C", "LC_ALL": "C"},
    )


def require_tool(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise SigningError(f"required-tool-unavailable:{path.name}")


def validate_identity(identity_sha1: str, *, runner: Callable) -> str:
    if IDENTITY_SHA1.fullmatch(identity_sha1) is None:
        raise SigningError("developer-id-sha1-invalid")
    result = invoke(
        [str(SECURITY), "find-identity", "-v", "-p", "codesigning"],
        runner=runner,
        timeout=30,
    )
    text = (result.stdout + result.stderr).decode("utf-8", "replace")
    if result.returncode != 0 or identity_sha1.upper() not in text.upper():
        raise SigningError("developer-id-identity-not-found")
    matching = [line for line in text.splitlines() if identity_sha1.upper() in line.upper()]
    if len(matching) != 1 or "Developer ID Application:" not in matching[0]:
        raise SigningError("developer-id-application-required")
    return identity_sha1.upper()


def validate_source_app(app: Path) -> str:
    if app.name != APP_NAME or not app.is_dir() or app.is_symlink():
        raise SigningError("source-app-invalid")
    plist_path = app / "Contents" / "Info.plist"
    executable = app / "Contents" / "MacOS" / "haven42"
    if not plist_path.is_file() or not executable.is_file():
        raise SigningError("source-app-incomplete")
    resolved_app = app.resolve()
    observed_links: dict[str, str] = {}
    for path in app.rglob("*"):
        if not path.is_symlink():
            continue
        relative = path.relative_to(app).as_posix()
        try:
            target = path.readlink().as_posix()
            path.resolve(strict=True).relative_to(resolved_app)
        except (OSError, ValueError) as error:
            raise SigningError("source-app-link-escaped-root") from error
        if SOURCE_APP_LINKS.get(relative) != target:
            raise SigningError("source-app-link-rejected")
        observed_links[relative] = target
    if observed_links != SOURCE_APP_LINKS:
        raise SigningError("source-app-link-set-incomplete")
    try:
        with plist_path.open("rb") as stream:
            plist = plistlib.load(stream)
    except (OSError, plistlib.InvalidFileException) as error:
        raise SigningError("source-app-plist-invalid") from error
    version = plist.get("Haven42ReleaseVersion")
    if (
        plist.get("CFBundleIdentifier") != BUNDLE_ID
        or plist.get("CFBundleExecutable") != "haven42"
        or version not in ALLOWED_VERSIONS
    ):
        raise SigningError("source-app-identity-mismatch")
    return str(version)


def validate_source_directory(directory: Path) -> tuple[Path, str, dict[str, str]]:
    validator_path = Path(__file__).with_name("validate-macos-development-app.py")
    if not validator_path.is_file() or validator_path.is_symlink():
        raise SigningError("unsigned-source-validator-unavailable")
    spec = importlib.util.spec_from_file_location("validate_macos_development_app_for_signing", validator_path)
    if spec is None or spec.loader is None:
        raise SigningError("unsigned-source-validator-unavailable")
    validator = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(validator)
        evidence = validator.validate(directory)
    except Exception as error:
        raise SigningError("unsigned-source-validation-failed") from error
    app = directory / APP_NAME
    version = validate_source_app(app)
    if evidence.get("application", {}).get("version") != version:
        raise SigningError("unsigned-source-version-mismatch")
    inventory_sha256 = evidence.get("inventory", {}).get("canonicalSha256")
    if not isinstance(inventory_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", inventory_sha256) is None:
        raise SigningError("unsigned-source-inventory-invalid")
    return app, version, {
        "unsignedArtifactSha256": sha256(directory / UNSIGNED_ARCHIVE_NAME),
        "buildEvidenceSha256": sha256(directory / UNSIGNED_EVIDENCE_NAME),
        "appInventoryCanonicalSha256": inventory_sha256,
    }


def is_macho(path: Path, *, runner: Callable) -> bool:
    result = invoke([str(FILE), "-b", str(path)], runner=runner, timeout=30)
    return result.returncode == 0 and b"Mach-O" in result.stdout


def code_targets(app: Path, *, runner: Callable) -> tuple[list[Path], list[Path]]:
    main_executable = app / "Contents" / "MacOS" / "haven42"
    files = [
        path for path in app.rglob("*")
        if (
            path.is_file()
            and not path.is_symlink()
            and path != main_executable
            and not any(parent.name.endswith(".framework") for parent in path.parents)
            and is_macho(path, runner=runner)
        )
    ]
    frameworks = [
        path for path in app.rglob("*.framework")
        if path.is_dir() and not path.is_symlink()
    ]
    return (
        sorted(files, key=lambda path: (len(path.parts), str(path)), reverse=True),
        sorted(frameworks, key=lambda path: (len(path.parts), str(path)), reverse=True),
    )


def sign_target(path: Path, identity: str, *, runner: Callable) -> None:
    result = invoke([
        str(CODESIGN), "--force", "--sign", identity, "--timestamp",
        "--options", "runtime", str(path),
    ], runner=runner)
    if result.returncode != 0:
        raise SigningError("codesign-target-failed")


def verify_signed_app(app: Path, *, runner: Callable) -> None:
    verify = invoke([
        str(CODESIGN), "--verify", "--deep", "--strict", "--verbose=4", str(app),
    ], runner=runner)
    if verify.returncode != 0:
        raise SigningError("codesign-verification-failed")
    details = invoke([str(CODESIGN), "-dv", "--verbose=4", str(app)], runner=runner)
    text = (details.stdout + details.stderr).decode("utf-8", "replace")
    if (
        details.returncode != 0
        or "Authority=Developer ID Application:" not in text
        or "TeamIdentifier=" not in text
        or "runtime" not in text.lower()
    ):
        raise SigningError("developer-id-runtime-proof-missing")


def notarize(
    app: Path,
    archive: Path,
    profile: str,
    *,
    runner: Callable,
) -> None:
    packed = invoke([
        str(DITTO), "-c", "-k", "--keepParent", "--sequesterRsrc",
        str(app), str(archive),
    ], runner=runner)
    if packed.returncode != 0 or not archive.is_file():
        raise SigningError("notarization-archive-failed")
    submitted = invoke([
        str(XCRUN), "notarytool", "submit", str(archive),
        "--keychain-profile", profile, "--wait", "--output-format", "json",
    ], runner=runner, timeout=3600)
    try:
        response = json.loads(submitted.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        if submitted.returncode != 0:
            raise SigningError("notarization-submit-failed") from error
        raise SigningError("notarization-response-invalid") from error
    if submitted.returncode != 0 or response.get("status") != "Accepted":
        raise SigningError("notarization-not-accepted")
    stapled = invoke([str(XCRUN), "stapler", "staple", str(app)], runner=runner)
    validated = invoke([str(XCRUN), "stapler", "validate", str(app)], runner=runner)
    assessed = invoke([str(SPCTL), "--assess", "--type", "execute", "--verbose=4", str(app)], runner=runner)
    if any(item.returncode != 0 for item in (stapled, validated, assessed)):
        raise SigningError("staple-or-gatekeeper-verification-failed")
    archive.unlink()
    repacked = invoke([
        str(DITTO), "-c", "-k", "--keepParent", "--sequesterRsrc",
        str(app), str(archive),
    ], runner=runner)
    if repacked.returncode != 0 or not archive.is_file():
        raise SigningError("stapled-archive-repack-failed")


def package_visible_distribution(app: Path, archive: Path, *, runner: Callable) -> Path:
    """Wrap the notarized app and its user-visible state directories in one folder."""
    archive.unlink(missing_ok=True)
    package_root = app.parent / PACKAGE_ROOT_NAME
    if package_root.exists() or package_root.is_symlink():
        raise SigningError("distribution-root-already-exists")
    package_root.mkdir(mode=0o755)
    packaged_app = package_root / APP_NAME
    app.rename(packaged_app)
    for directory_name in (DATA_DIRECTORY_NAME, LOG_DIRECTORY_NAME):
        directory = package_root / directory_name
        directory.mkdir(mode=0o700)
        (directory / "README.txt").write_text(
            "Haven 42 keeps its own files in this visible folder.\n",
            encoding="utf-8",
        )
    packed = invoke([
        str(DITTO), "-c", "-k", "--keepParent", "--sequesterRsrc",
        str(package_root), str(archive),
    ], runner=runner)
    if packed.returncode != 0 or not archive.is_file():
        raise SigningError("visible-distribution-archive-failed")
    return packaged_app


def write_result(
    output: Path,
    version: str,
    archive: Path,
    source: dict[str, str],
) -> dict[str, object]:
    result: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-macos-developer-id-notarization-result",
        "release": version,
        "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "passed",
        "source": source,
        "artifact": {
            "name": archive.name,
            "sha256": sha256(archive),
            "sizeBytes": archive.stat().st_size,
        },
        "platformTrust": {
            "developerIdSigned": True,
            "hardenedRuntime": True,
            "notarized": True,
            "ticketStapled": True,
            "gatekeeperAdmittedOnTestHost": True,
        },
        "privacy": {
            "certificateIdentityRetained": False,
            "teamIdentifierRetained": False,
            "notaryProfileRetained": False,
            "notaryCredentialRetained": False,
            "rawToolOutputRetained": False,
        },
        "authority": {
            "automaticUpdateActivationGranted": False,
            "releasePublicationGranted": False,
        },
    }
    evidence = output / "macos-signing-notarization-result.json"
    evidence.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "SHA256SUMS").write_text(
        f"{sha256(archive)}  {archive.name}\n{sha256(evidence)}  {evidence.name}\n",
        encoding="utf-8",
    )
    return result


def execute(
    source_directory: Path,
    output: Path,
    identity_sha1: str,
    notary_profile: str,
    *,
    runner: Callable = subprocess.run,
    platform_name: str = sys.platform,
) -> dict[str, object]:
    if platform_name != "darwin":
        raise SigningError("physical-macos-required")
    if PROFILE_NAME.fullmatch(notary_profile) is None:
        raise SigningError("notary-profile-name-invalid")
    for tool in (CODESIGN, DITTO, FILE, SECURITY, SPCTL, XCRUN):
        require_tool(tool)
    source_app, version, source = validate_source_directory(source_directory)
    identity = validate_identity(identity_sha1, runner=runner)
    if output.exists() or output.is_symlink():
        raise SigningError("output-must-not-exist")
    output_parent = output.parent.resolve()
    output_parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = Path(tempfile.mkdtemp(
        prefix="haven42-macos-signing-", dir=output_parent,
    ))
    try:
        app = temporary / APP_NAME
        shutil.copytree(source_app, app, symlinks=True)
        files, frameworks = code_targets(app, runner=runner)
        for target in files:
            sign_target(target, identity, runner=runner)
        for target in frameworks:
            sign_target(target, identity, runner=runner)
        sign_target(app, identity, runner=runner)
        verify_signed_app(app, runner=runner)
        archive = temporary / "haven42-darwin-arm64-developer-id-notarized.zip"
        notarize(app, archive, notary_profile, runner=runner)
        verify_signed_app(app, runner=runner)
        app = package_visible_distribution(app, archive, runner=runner)
        verify_signed_app(app, runner=runner)
        write_result(temporary, version, archive, source)
        shutil.rmtree(app.parent)
        os.replace(temporary, output)
        temporary = None
        return json.loads((output / "macos-signing-notarization-result.json").read_text(encoding="utf-8"))
    finally:
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-directory", type=Path, required=True,
        help="Unsigned macOS development-app output verified by validate-macos-development-app.py",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--identity-sha1", required=True)
    parser.add_argument("--notary-profile", required=True)
    args = parser.parse_args()
    try:
        result = execute(
            args.source_directory.expanduser().resolve(),
            args.output.expanduser().resolve(),
            args.identity_sha1,
            args.notary_profile,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError, SigningError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
