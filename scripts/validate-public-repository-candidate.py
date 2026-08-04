#!/usr/bin/env python3
"""Inspect an approved bare public repository without checkout or execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "config" / "public-repository-validation-candidates.json"
REVIEW_ROOT = (ROOT / "dist" / "local-review" / "public-repositories").resolve()
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PublicRepositoryError(ValueError):
    pass


def load_catalog(path: Path = CATALOG_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PublicRepositoryError("invalid-public-repository-catalog") from error
    if value.get("schemaVersion") != 1 or value.get("status") != "read-only-candidate-set-not-surface-promotion":
        raise PublicRepositoryError("invalid-public-repository-catalog")
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 3:
        raise PublicRepositoryError("invalid-public-repository-catalog")
    for item in candidates:
        if not SHA1.fullmatch(str(item.get("commit", ""))) or not SHA1.fullmatch(str(item.get("tagObject", ""))):
            raise PublicRepositoryError("invalid-public-repository-identity")
        if not str(item.get("repository", "")).startswith("https://github.com/"):
            raise PublicRepositoryError("invalid-public-repository-identity")
        licenses = item.get("licenseFiles")
        if not isinstance(licenses, dict) or not licenses or any(not SHA256.fullmatch(str(value)) for value in licenses.values()):
            raise PublicRepositoryError("invalid-public-repository-license")
    if any(flag is not False for flag in value.get("execution", {}).values()):
        raise PublicRepositoryError("unsafe-public-repository-catalog")
    if any(flag is not False for flag in value.get("authority", {}).values()):
        raise PublicRepositoryError("unsafe-public-repository-catalog")
    return value


def _git(repository: Path, *arguments: str) -> bytes:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_LFS_SKIP_SMUDGE": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "LC_ALL": "C",
    }
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", f"--git-dir={repository}", *arguments],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise PublicRepositoryError("bare-repository-read-failed") from error
    return result.stdout


def _validate_bare_control(repository: Path) -> None:
    entries = 0
    for directory, names, files in os.walk(repository, followlinks=False):
        for name in [*names, *files]:
            entries += 1
            if entries > 100_000:
                raise PublicRepositoryError("bare-repository-control-limit")
            path = Path(directory) / name
            info = path.lstat()
            attributes = getattr(info, "st_file_attributes", 0)
            reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            if path.is_symlink() or bool(attributes & reparse):
                raise PublicRepositoryError("bare-repository-link-rejected")
    for name in ("objects/info/alternates", "objects/info/http-alternates"):
        if (repository / name).exists():
            raise PublicRepositoryError("bare-repository-alternate-rejected")
    config_path = repository / "config"
    try:
        if config_path.stat().st_size > 65_536:
            raise PublicRepositoryError("bare-repository-config-limit")
        config = config_path.read_text(encoding="utf-8", errors="strict").casefold()
    except (OSError, UnicodeError) as error:
        raise PublicRepositoryError("bare-repository-config-rejected") from error
    forbidden = ("[include", "fsmonitor", "sshcommand", "credential", "[filter ", "uploadpack", "receivepack")
    if any(value in config for value in forbidden):
        raise PublicRepositoryError("bare-repository-config-rejected")


def _safe_repository(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(REVIEW_ROOT)
    except ValueError as error:
        raise PublicRepositoryError("repository-outside-review-root") from error
    if not resolved.is_dir() or resolved.suffix != ".git" or not (resolved / "HEAD").is_file():
        raise PublicRepositoryError("invalid-bare-repository")
    _validate_bare_control(resolved)
    return resolved


def _validate_identity(candidate: dict, repository: Path) -> str:
    try:
        origin = _git(repository, "config", "--get", "remote.origin.url").decode("utf-8", errors="strict").strip()
        tag_object = _git(repository, "rev-parse", candidate["tag"]).decode("ascii", errors="strict").strip()
        tag_type = _git(repository, "cat-file", "-t", tag_object).decode("ascii", errors="strict").strip()
        commit = _git(repository, "rev-parse", f"{candidate['tag']}^{{commit}}").decode("ascii", errors="strict").strip()
    except UnicodeError as error:
        raise PublicRepositoryError("public-repository-identity-mismatch") from error
    if (
        origin != candidate["repository"]
        or tag_object != candidate["tagObject"]
        or tag_type != "tag"
        or commit != candidate["commit"]
    ):
        raise PublicRepositoryError("public-repository-identity-mismatch")
    return commit


def inspect(candidate_id: str, repository: Path, catalog_path: Path = CATALOG_PATH) -> dict:
    catalog = load_catalog(catalog_path)
    matches = [item for item in catalog["candidates"] if item["id"] == candidate_id]
    if len(matches) != 1:
        raise PublicRepositoryError("unknown-public-repository-candidate")
    candidate = matches[0]
    bare = _safe_repository(repository)
    commit = _validate_identity(candidate, bare)
    raw_tree = _git(bare, "ls-tree", "-rz", "-l", commit)
    files = 0
    total = 0
    extensions: dict[str, int] = {}
    limits = catalog["limits"]
    for raw in raw_tree.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, encoded_path = raw.split(b"\t", 1)
            mode, object_type, _object_id, size = metadata.decode("ascii").split()
            path = encoded_path.decode("utf-8", errors="strict")
        except (ValueError, UnicodeError) as error:
            raise PublicRepositoryError("unsafe-tree-record") from error
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts or "" in pure.parts or len(path) > limits["maximumPathCharacters"]:
            raise PublicRepositoryError("unsafe-tree-path")
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise PublicRepositoryError("unsupported-tree-object")
        try:
            byte_count = int(size)
        except ValueError as error:
            raise PublicRepositoryError("unsafe-tree-size") from error
        if byte_count < 0:
            raise PublicRepositoryError("unsafe-tree-size")
        files += 1
        total += byte_count
        if files > limits["maximumFiles"] or total > limits["maximumRepositoryBytes"]:
            raise PublicRepositoryError("repository-resource-limit")
        suffix = pure.suffix.casefold() or "[none]"
        extensions[suffix] = extensions.get(suffix, 0) + 1
    verified = []
    for path, expected in candidate["licenseFiles"].items():
        content = _git(bare, "show", f"{commit}:{path}")
        if len(content) > limits["maximumLicenseBytes"] or hashlib.sha256(content).hexdigest() != expected:
            raise PublicRepositoryError("license-evidence-mismatch")
        verified.append({"path": path, "sha256": expected})
    return {
        "schemaVersion": 1,
        "status": "read-only-bare-repository-inspection-passed",
        "candidateId": candidate_id,
        "commit": commit,
        "licenseExpression": candidate["licenseExpression"],
        "licenseEvidence": verified,
        "scope": {"fileCount": files, "totalBlobBytes": total, "extensionCounts": dict(sorted(extensions.items()))},
        "execution": dict(catalog["execution"]),
        "authority": dict(catalog["authority"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        output.relative_to(REVIEW_ROOT)
    except ValueError as error:
        raise SystemExit("Output must stay under ignored public-repository review storage.") from error
    if output.exists() or output.is_symlink():
        raise SystemExit("Output already exists.")
    result = inspect(args.candidate, args.repository)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "candidateId": result["candidateId"], "scope": result["scope"]}, sort_keys=True))


if __name__ == "__main__":
    main()
