#!/usr/bin/env python3
"""Validate the fixed-Wikipedia path through an exact portable executable."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.parse
import urllib.request


def launch(executable: Path) -> tuple[subprocess.Popen[str], str]:
    process = subprocess.Popen(
        [str(executable), "--port", "0", "--no-open"],
        cwd=executable.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        line = process.stdout.readline() if process.stdout else ""
        match = re.search(r"http://127\.0\.0\.1:\d+", line)
        if match:
            return process, match.group(0)
        if process.poll() is not None:
            raise RuntimeError("packaged-runtime-exited-before-ready")
    process.kill()
    raise RuntimeError("packaged-runtime-startup-timeout")


def request(origin: str, path: str, method: str = "GET", token: str = "", value=None):
    parsed = urllib.parse.urlsplit(origin)
    data = None if value is None else json.dumps(value, separators=(",", ":")).encode()
    headers = {"Host": parsed.netloc}
    if method == "POST":
        headers.update({
            "Origin": origin,
            "Sec-Fetch-Site": "same-origin",
            "Content-Type": "application/json",
            "X-Haven-Token": token,
        })
    with urllib.request.urlopen(
        urllib.request.Request(origin + path, method=method, data=data, headers=headers),
        timeout=30,
    ) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--query", default="local artificial intelligence")
    parser.add_argument("--result-limit", type=int, default=3)
    arguments = parser.parse_args()
    executable = arguments.executable.resolve()
    if not executable.is_file():
        parser.error("--executable must be an existing file")

    process, origin = launch(executable)
    token = ""
    try:
        bootstrap = request(origin, "/api/bootstrap")
        token = bootstrap["sessionToken"]
        prepared = request(
            origin, "/api/research/query/prepare", "POST", token,
            {"query": arguments.query, "resultLimit": arguments.result_limit},
        )
        query_result = request(
            origin, "/api/research/query/execute", "POST", token,
            {"approvalToken": prepared["approvalToken"], "confirmed": True},
        )
        citations = query_result["citations"]["citations"]
        if not citations:
            raise RuntimeError("live-query-returned-no-citations")
        selected = citations[0]
        page_prepared = request(
            origin, "/api/research/page/prepare", "POST", token,
            {"resultId": query_result["resultId"], "citationId": selected["citationId"]},
        )
        page_result = request(
            origin, "/api/research/page/execute", "POST", token,
            {"approvalToken": page_prepared["approvalToken"], "confirmed": True},
        )
        if page_result["source"] != selected or page_result["contentCharacters"] <= 0:
            raise RuntimeError("packaged-selected-source-binding-failed")
        receipt = {
            "schemaVersion": 1,
            "kind": "haven42-sanitized-packaged-live-wikipedia-validation",
            "appVersion": bootstrap["version"],
            "packageIntegrityVerified": bootstrap["package"]["verified"],
            "provider": "fixed-English-Wikipedia",
            "queryDigest": hashlib.sha256(
                query_result["normalizedQuery"].encode("utf-8")
            ).hexdigest(),
            "resultCount": len(citations),
            "selectedDisplayDomain": selected["displayDomain"],
            "contentDigest": hashlib.sha256(
                "\n".join(item["text"] for item in page_result["segments"]).encode("utf-8")
            ).hexdigest(),
            "contentCharacters": page_result["contentCharacters"],
            "queryApprovalSingleUse": prepared["singleUse"],
            "pageApprovalSingleUse": page_prepared["singleUse"],
            "activeNavigationAllowed": page_result["activeNavigationAllowed"],
            "pageExecutionAllowed": page_result["pageExecutionAllowed"],
            "automaticFollowUpAllowed": page_result["automaticFollowUpAllowed"],
            "contentPersisted": page_result["contentPersisted"],
            "modelToolAllowed": page_result["modelToolAllowed"],
        }
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        request(origin, "/api/research/clear", "POST", token, {})
    finally:
        if token and process.poll() is None:
            try:
                request(origin, "/api/shutdown", "POST", token, {})
            except Exception:
                pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
