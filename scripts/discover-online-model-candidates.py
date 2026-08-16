#!/usr/bin/env python3
"""Provider-neutral, candidate-only public model discovery."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


def csv_values(values):
    result = []
    for value in values or []:
        for item in value.split(","):
            item = item.strip()
            if item and item not in result:
                result.append(item)
    return result


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def inventory_index(path):
    if not path:
        return {"models": set(), "repositories": set(), "families": set()}
    inventory = load_json(path)
    models, repositories = set(), set()
    for family in inventory.get("families") or []:
        for version in family.get("versions") or []:
            for candidate in version.get("candidates") or []:
                model = str(candidate.get("model") or "").strip().lower()
                if model:
                    models.add(model)
                    repositories.add(model.split(":", 1)[0])
    return {
        "models": models,
        "repositories": repositories,
        "families": {
            str(item.get("family") or "").strip().lower()
            for item in inventory.get("families") or []
            if str(item.get("family") or "").strip()
        },
    }


def previous_candidate_keys(path):
    if not path:
        return set()
    previous = load_json(path)
    records = previous.get("Candidates") or previous.get("NewTestCandidates") or []
    return {
        (str(item.get("SourceId") or ""), str(item.get("ArtifactId") or ""), str(item.get("Revision") or ""))
        for item in records
        if isinstance(item, dict)
    }


def classify_inventory_candidates(candidates, inventory, previous_keys):
    untracked = []
    new_since_previous = []
    for candidate in candidates:
        model = str(candidate.get("Model") or "").lower()
        repository = model.split(":", 1)[0]
        key = (
            str(candidate.get("SourceId") or ""),
            str(candidate.get("ArtifactId") or ""),
            str(candidate.get("Revision") or ""),
        )
        if model in inventory["models"]:
            inventory_status = "already-tracked-exact-artifact"
            queue_status = "no-action-already-tracked"
        elif candidate.get("SourceId") == "ollama" and repository in inventory["repositories"]:
            inventory_status = "new-artifact-in-tracked-model-repository"
            queue_status = "review-for-test-queue"
        else:
            inventory_status = "new-upstream-model-candidate"
            queue_status = "review-official-publisher-license-and-local-artifacts"
        if re.search(r"(?i)(^|:)latest$", model):
            queue_status = "blocked-mutable-tag-requires-version-pinned-artifact"
        if candidate.get("SourceType") == "huggingface-publisher-feed" and not candidate.get("Revision"):
            queue_status = "blocked-missing-immutable-revision"
        elif candidate.get("SourceType") == "huggingface-publisher-feed" and not candidate.get("License"):
            queue_status = "blocked-license-review-required"
        candidate["InventoryStatus"] = inventory_status
        candidate["TestQueueStatus"] = queue_status
        candidate["SeenInPreviousReport"] = key in previous_keys
        if inventory_status != "already-tracked-exact-artifact":
            untracked.append(candidate)
            if key not in previous_keys:
                new_since_previous.append(candidate)
    return untracked, new_since_previous


def markdown_report(report):
    summary = report["UpdateSummary"]
    lines = [
        "# New Model Candidate Check",
        "",
        f"_Checked: {report['GeneratedAtUtc']}_",
        "",
        "This is a review queue, not an installation or certification result. No model was downloaded, no test was started, and Haven 42's automatic model choices were not changed.",
        "",
        "## Summary",
        "",
        f"- {summary['DiscoveredCount']} public candidate records were examined.",
        f"- {summary['UntrackedCandidateCount']} are not represented by an exact tracked artifact.",
        f"- {summary['NewSincePreviousReportCount']} were not present in the supplied previous report.",
        f"- {summary['AlreadyTrackedExactCount']} already match an exact inventory entry.",
        f"- {summary['SourceErrorCount']} source queries failed.",
        "",
        "## Candidates requiring review",
        "",
        "| Candidate | Source | Inventory comparison | Next action |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["NewTestCandidates"]:
        lines.append(
            f"| `{item['Model']}` | {item['SourceId']} | {item['InventoryStatus'].replace('-', ' ')} | {item['TestQueueStatus'].replace('-', ' ')} |"
        )
    if not report["NewTestCandidates"]:
        lines.append("| None | — | No untracked candidates were found | — |")
    lines.extend([
        "",
        "Before testing, confirm the official publisher, license, immutable revision or manifest digest, local runtime artifact, quantization, size, and hardware fit. Preparing that test still does not authorize a download or soak run.",
        "",
    ])
    return "\n".join(lines)


def platform_name(value=None):
    value = str(value or sys.platform)
    if re.search(r"(?i)mac|darwin", value):
        return "macOS"
    if re.search(r"(?i)win", value):
        return "Windows"
    if re.search(r"(?i)linux", value):
        return "Linux"
    return platform.system() or "Unknown"


def load_profile(path, selection_mode, explicit_vram):
    host = platform_name()
    available = float(explicit_vram or 0)
    source = "explicit" if available > 0 else None
    if not path:
        return host, available, source
    profile = load_json(path)
    host = platform_name(profile.get("Platform"))
    if available <= 0:
        values = []
        for gpu in profile.get("Gpus") or []:
            memory_type = str(gpu.get("MemoryType") or "")
            if memory_type and not re.search(r"(?i)dedicated|unknown", memory_type):
                continue
            try:
                value = float(gpu.get("VramGb"))
            except (TypeError, ValueError):
                continue
            if value > 0:
                values.append(value)
        if values:
            available = max(values) if selection_mode == "MaxDedicated" else sum(values)
            source = f"model-profile:{selection_mode}"
    return host, round(available, 2), source


def size_billion(text, tags=None):
    values = [text, *(tags or [])]
    for value in values:
        match = re.search(r"(?i)(\d+(?:\.\d+)?)\s*b(?:\b|[-_])", str(value))
        if match:
            return float(match.group(1))
    return 0


def recommended_vram(size):
    if size <= 0:
        return 0
    for limit, vram in ((1, 4), (2, 6), (4, 8), (9, 12), (14, 20), (27, 36), (35, 48), (80, 80), (122, 128)):
        if size <= limit:
            return vram
    return 512


def vram_record(size, available, source):
    required = recommended_vram(size)
    return {
        "AvailableVramGb": available if available > 0 else None,
        "AvailableVramSource": source,
        "RecommendedMinVramGb": required or None,
        "FitsAvailableVram": not (available > 0 and required > 0 and required > available),
        "Confidence": "low-name-and-tag-heuristic" if required else "unknown",
    }


def get_text(url, timeout):
    request = urllib.request.Request(url, headers={"User-Agent": "Haven-42-model-discovery/2"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def ollama_tags(content, query):
    escaped = re.escape(query)
    patterns = [
        rf"(?i)\b{escaped}:[a-z0-9][a-z0-9._-]*\b",
        rf"(?i)/library/({escaped}:[a-z0-9][a-z0-9._-]*)",
        rf"(?i)\b([a-z0-9][a-z0-9._/-]*{escaped}[a-z0-9._/-]*:[a-z0-9][a-z0-9._-]*)\b",
    ]
    values = []
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            value = (match.group(1) if match.groups() else match.group(0)).strip().strip('"\'<>.,;()')
            value = re.sub(r"^/?library/", "", value)
            if re.match(r"^[A-Za-z0-9][A-Za-z0-9._/-]*:[A-Za-z0-9][A-Za-z0-9._-]*$", value) and value not in values:
                values.append(value)
    return values


def ollama_families(content):
    """Return model families from the registry's newest-first library index."""
    values = []
    for match in re.finditer(r'''(?i)href=["']/library/([a-z0-9][a-z0-9._-]*)''', content):
        value = match.group(1).lower()
        if value not in values:
            values.append(value)
    return values


def common_candidate(model, artifact, source_id, source_type, query, publisher, revision, license_name, gated,
                     pipeline_tag, formats, runtimes, quantizations, tags, size, available, vram_source):
    vram = vram_record(size, available, vram_source)
    status = "online candidate" if vram["FitsAvailableVram"] else "online candidate above vram estimate"
    provenance = "immutable-revision-recorded" if revision else "publisher-identity-unverified"
    return {
        "Model": model,
        "ArtifactId": artifact,
        "Family": query,
        "Query": query,
        "Source": source_type,
        "SourceId": source_id,
        "SourceType": source_type,
        "Publisher": publisher,
        "Revision": revision,
        "License": license_name,
        "Gated": gated,
        "PipelineTag": pipeline_tag,
        "Formats": sorted(set(formats)),
        "RuntimeCandidates": sorted(set(runtimes)),
        "QuantizationSignals": sorted(set(quantizations)),
        "Tags": sorted(set(tags)),
        "ParameterCountBillion": size or None,
        "ProvenanceStatus": provenance,
        "ValidationStatus": "candidate-only",
        "Status": status,
        "Reason": "Public metadata candidate; source claims, format tags, and popularity do not prove local quality or tool safety.",
        "NextStep": "Review provenance and license, resolve an immutable artifact, then run hardware and operation-specific local validation.",
        "VramRecommendation": vram,
    }


def discover_ollama(source, queries, args, host, available, vram_source):
    results, skipped, errors = [], [], []
    fixture = Path(args.ollama_html_fixture) if args.ollama_html_fixture else None
    for query in queries:
        try:
            content = fixture.read_text(encoding="utf-8") if fixture else get_text(
                f"{source['baseUrl'].rstrip('/')}/{urllib.parse.quote(query, safe='-._~')}", args.timeout_seconds
            )
            for model in ollama_tags(content, query):
                if "cloud" in model.lower() or ("-mlx" in model.lower() and host != "macOS"):
                    skipped.append({
                        "Model": model, "ArtifactId": model, "Family": query, "Query": query,
                        "Source": "ollama-library-page", "SourceId": "ollama", "SourceType": "ollama-library",
                        "Status": "online candidate skipped for platform", "ValidationStatus": "candidate-only",
                        "Reason": "Cloud tags are not local pulls, and MLX artifacts require an Apple Silicon host.",
                        "NextStep": "Select a compatible local artifact or model host.", "FailureSignal": "MODEL_SKIPPED_FOR_PLATFORM",
                        "ModelHostPlatform": host,
                    })
                    continue
                size = size_billion(model)
                quant = [token.upper() for token in re.findall(r"(?i)(q\d(?:_[a-z0-9]+)*|fp\d+|bf16)", model)]
                results.append(common_candidate(
                    model, model, "ollama", "ollama-library", query, None, None, None, False,
                    "text-generation", ["ollama-manifest"], ["ollama"], quant, [], size, available, vram_source
                ))
        except Exception as exc:
            errors.append({"SourceId": "ollama", "Query": query, "Error": str(exc)})
    return results, skipped, errors


def discover_ollama_newest(source, args, host, available, vram_source):
    """Discover registry families without requiring a pre-existing seed name."""
    try:
        content = (
            Path(args.ollama_newest_html_fixture).read_text(encoding="utf-8")
            if args.ollama_newest_html_fixture
            else get_text(source["baseUrl"], args.timeout_seconds)
        )
        families = ollama_families(content)[:args.max_results_per_query]
        detail_args = argparse.Namespace(**vars(args))
        detail_args.ollama_html_fixture = args.ollama_newest_html_fixture
        detail_source = {**source, "baseUrl": source["detailBaseUrl"]}
        found, skipped, errors = discover_ollama(
            detail_source, families, detail_args, host, available, vram_source
        )
        represented = {item["Family"] for item in [*found, *skipped]}
        for family in families:
            if family not in represented:
                skipped.append({
                    "Model": family,
                    "ArtifactId": family,
                    "Family": family,
                    "Query": family,
                    "Source": "ollama-newest-index",
                    "SourceId": "ollama-newest",
                    "SourceType": "ollama-newest-index",
                    "Status": "registry family found but exact local tag unresolved",
                    "ValidationStatus": "candidate-only",
                    "Reason": "The newest-first registry index exposed the family, but no versioned local tag was parsed from its detail page.",
                    "NextStep": "Review the registry detail page and resolve a full immutable local manifest before planning execution.",
                    "FailureSignal": "MODEL_TAG_UNRESOLVED",
                })
        for item in found:
            item["SourceId"] = "ollama-newest"
            item["SourceType"] = "ollama-newest-index"
            item["Source"] = "ollama-newest-index"
            item["DiscoveredWithoutSeedQuery"] = True
        return found, skipped, errors, families
    except Exception as exc:
        return [], [], [{"SourceId": "ollama-newest", "Error": str(exc)}], []


def hf_formats(item):
    tags = [str(tag).lower() for tag in item.get("tags") or []]
    files = [str(value.get("rfilename") or "").lower() for value in item.get("siblings") or []]
    formats, quant, runtimes = [], [], ["transformers"]
    combined = tags + files
    if any(".gguf" in value or value == "gguf" for value in combined):
        formats.append("gguf"); runtimes.extend(["llama.cpp", "ollama-import"])
    if any("safetensors" in value for value in combined): formats.append("safetensors")
    if any("mlx" in value for value in combined): formats.append("mlx"); runtimes.append("mlx")
    for name in ("awq", "gptq", "fp8", "int4", "q4_k_m", "q8_0", "bf16"):
        if any(name in value for value in combined): quant.append(name.upper())
    for runtime in ("vllm", "sglang", "ollama"):
        if runtime in tags: runtimes.append(runtime if runtime != "ollama" else "ollama-import")
    return formats, quant, runtimes


def discover_huggingface(source, queries, args, host, available, vram_source):
    results, errors = [], []
    fixture_items = load_json(args.huggingface_json_fixture) if args.huggingface_json_fixture else None
    for query in queries:
        try:
            if fixture_items is not None:
                items = fixture_items
            else:
                params = urllib.parse.urlencode({
                    "search": query, "pipeline_tag": "text-generation", "sort": "trendingScore",
                    "direction": -1, "limit": args.max_results_per_query, "full": "true", "config": "true",
                })
                items = json.loads(get_text(f"{source['baseUrl'].rstrip('/')}/api/models?{params}", args.timeout_seconds))
            for item in items[:args.max_results_per_query]:
                model = str(item.get("id") or item.get("modelId") or "").strip()
                if not model:
                    continue
                tags = [str(tag) for tag in item.get("tags") or []]
                license_name = next((tag.split(":", 1)[1] for tag in tags if tag.lower().startswith("license:")), None)
                formats, quant, runtimes = hf_formats(item)
                candidate = common_candidate(
                    model, model, "huggingface", "huggingface-hub", query, item.get("author") or model.split("/", 1)[0],
                    item.get("sha"), license_name, item.get("gated", False), item.get("pipeline_tag"), formats,
                    runtimes, quant, tags, size_billion(model, tags), available, vram_source
                )
                candidate.update({
                    "Downloads": item.get("downloads"), "Likes": item.get("likes"),
                    "LastModified": item.get("lastModified"), "LibraryName": item.get("library_name"),
                    "DirectOllamaPull": False,
                })
                if not license_name:
                    candidate["Status"] = "online candidate license review required"
                    candidate["FailureSignal"] = "MODEL_LICENSE_MISSING"
                results.append(candidate)
        except Exception as exc:
            errors.append({"SourceId": "huggingface", "Query": query, "Error": str(exc)})
    return results, errors


def parse_utc(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise ValueError("invalid publisher-feed timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError("publisher-feed timestamp must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def discover_publisher_feed(source, args, host, available, vram_source):
    """Poll configured publisher namespaces directly instead of relying on search rank."""
    results, skipped, errors = [], [], []
    publishers = source.get("publisherNamespaces") or []
    eligible_pipelines = set(source.get("eligiblePipelineTags") or [])
    discovery_now = (
        parse_utc(args.discovery_now_utc)
        if args.discovery_now_utc
        else datetime.now(timezone.utc)
    )
    rolling_since = discovery_now - timedelta(days=int(source.get("lookbackDays") or 45))
    # A manual timestamp may widen an investigation, but it must never narrow
    # the configured rolling window.  Publisher metadata dates can precede a
    # public announcement, so narrowing the window can silently hide a new
    # family even when its official namespace is polled directly.
    since = min(parse_utc(args.publisher_since_utc), rolling_since) if args.publisher_since_utc else rolling_since
    fixture_items = load_json(args.publisher_feed_json_fixture) if args.publisher_feed_json_fixture else None
    for publisher in publishers:
        try:
            if fixture_items is not None:
                items = [
                    item for item in fixture_items
                    if str(item.get("id") or item.get("modelId") or "").split("/", 1)[0].lower()
                    == str(publisher).lower()
                ]
            else:
                params = urllib.parse.urlencode({
                    "author": publisher,
                    "sort": "lastModified",
                    "direction": -1,
                    "limit": args.max_results_per_publisher,
                    "full": "true",
                    "config": "true",
                })
                items = json.loads(get_text(
                    f"{source['baseUrl'].rstrip('/')}/api/models?{params}", args.timeout_seconds
                ))
            for item in items:
                modified = item.get("lastModified")
                if not modified or parse_utc(modified) < since:
                    continue
                model = str(item.get("id") or item.get("modelId") or "").strip()
                if not model:
                    continue
                pipeline = item.get("pipeline_tag")
                if pipeline not in eligible_pipelines:
                    skipped.append({
                        "Model": model,
                        "ArtifactId": model,
                        "Publisher": publisher,
                        "SourceId": "official-publishers",
                        "SourceType": "huggingface-publisher-feed",
                        "Status": "publisher release outside current Haven capability lanes",
                        "ValidationStatus": "candidate-only",
                        "LastModified": modified,
                        "Reason": "The official namespace changed, but its declared pipeline is outside the configured local assistant capability lanes.",
                        "NextStep": "Reconsider only if the Haven capability roadmap expands to this pipeline.",
                    })
                    continue
                tags = [str(tag) for tag in item.get("tags") or []]
                license_name = next(
                    (tag.split(":", 1)[1] for tag in tags if tag.lower().startswith("license:")),
                    None,
                )
                formats, quant, runtimes = hf_formats(item)
                revision = item.get("sha")
                candidate = common_candidate(
                    model,
                    model,
                    "official-publishers",
                    "huggingface-publisher-feed",
                    model.split("/", 1)[-1],
                    publisher,
                    revision,
                    license_name,
                    item.get("gated", False),
                    pipeline,
                    formats,
                    runtimes,
                    quant,
                    tags,
                    size_billion(model, tags),
                    available,
                    vram_source,
                )
                candidate.update({
                    "Downloads": item.get("downloads"),
                    "Likes": item.get("likes"),
                    "LastModified": modified,
                    "LibraryName": item.get("library_name"),
                    "DirectOllamaPull": False,
                    "OfficialPublisherFeed": True,
                    "PublisherIdentityStatus": "configured-publisher-namespace",
                })
                if not revision:
                    candidate["Status"] = "publisher candidate missing immutable revision"
                    candidate["FailureSignal"] = "MODEL_REVISION_MISSING"
                elif not license_name:
                    candidate["Status"] = "publisher candidate license review required"
                    candidate["FailureSignal"] = "MODEL_LICENSE_MISSING"
                results.append(candidate)
        except Exception as exc:
            errors.append({
                "SourceId": "official-publishers",
                "Publisher": publisher,
                "Error": str(exc),
            })
    return results, skipped, errors, since.isoformat().replace("+00:00", "Z")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-config", required=True)
    parser.add_argument("--contract-path", required=True)
    parser.add_argument("--sources", action="append", default=[])
    parser.add_argument("--queries", action="append", default=[])
    parser.add_argument("--families", "--family", action="append", default=[])
    parser.add_argument("--ollama-base-url", "--source-base-url")
    parser.add_argument("--hugging-face-base-url")
    parser.add_argument("--ollama-html-fixture", "--source-html-path")
    parser.add_argument("--ollama-newest-html-fixture")
    parser.add_argument("--huggingface-json-fixture", "--hugging-face-json-path")
    parser.add_argument("--publisher-feed-json-fixture")
    parser.add_argument("--publisher-since-utc")
    parser.add_argument("--discovery-now-utc")
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--markdown-output-path")
    parser.add_argument("--inventory-path")
    parser.add_argument("--previous-report-path")
    parser.add_argument("--model-profile-path")
    parser.add_argument("--vram-selection-mode", choices=("TotalDedicated", "MaxDedicated"), default="TotalDedicated")
    parser.add_argument("--available-vram-gb", type=float, default=0)
    parser.add_argument("--include-oversized-models", action="store_true")
    parser.add_argument("--max-results-per-query", type=int, default=10)
    parser.add_argument("--max-results-per-publisher", type=int, default=60)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    config, contract = load_json(args.source_config), load_json(args.contract_path)
    selected = csv_values(args.sources)
    if not selected and (
        args.ollama_html_fixture or args.ollama_newest_html_fixture or args.huggingface_json_fixture or args.publisher_feed_json_fixture
    ):
        selected = []
        if args.ollama_html_fixture: selected.append("ollama")
        if args.ollama_newest_html_fixture: selected.append("ollama-newest")
        if args.huggingface_json_fixture: selected.append("huggingface")
        if args.publisher_feed_json_fixture: selected.append("official-publishers")
    selected = selected or config["defaultSources"]
    global_queries = csv_values(args.queries) or csv_values(args.families)
    host, available, vram_source = load_profile(args.model_profile_path, args.vram_selection_mode, args.available_vram_gb)
    candidates, skipped, errors, query_record, publisher_feed_since = [], [], [], {}, None
    for source in config["sources"]:
        if source["id"] not in selected:
            continue
        if source["id"] == "ollama" and args.ollama_base_url: source = {**source, "baseUrl": args.ollama_base_url}
        if source["id"] == "huggingface" and args.hugging_face_base_url: source = {**source, "baseUrl": args.hugging_face_base_url}
        queries = global_queries or source.get("defaultQueries") or []
        query_record[source["id"]] = queries
        if source["id"] == "ollama":
            found, source_skipped, source_errors = discover_ollama(source, queries, args, host, available, vram_source)
            candidates.extend(found); skipped.extend(source_skipped); errors.extend(source_errors)
        elif source["id"] == "ollama-newest":
            found, source_skipped, source_errors, newest_families = discover_ollama_newest(
                source, args, host, available, vram_source
            )
            query_record[source["id"]] = newest_families
            candidates.extend(found); skipped.extend(source_skipped); errors.extend(source_errors)
        elif source["id"] == "huggingface":
            found, source_errors = discover_huggingface(source, queries, args, host, available, vram_source)
            candidates.extend(found); errors.extend(source_errors)
        elif source["id"] == "official-publishers":
            found, source_skipped, source_errors, publisher_feed_since = discover_publisher_feed(
                source, args, host, available, vram_source
            )
            candidates.extend(found); skipped.extend(source_skipped); errors.extend(source_errors)

    unique = {}
    for candidate in candidates:
        key = (candidate["SourceId"], candidate["ArtifactId"], candidate.get("Revision"))
        unique[key] = candidate
    candidates = sorted(unique.values(), key=lambda item: (item["SourceId"], item["Model"]))
    if not args.include_oversized_models:
        pass  # Oversized candidates remain visible but are explicitly labeled and never pulled.
    inventory = inventory_index(args.inventory_path)
    previous_keys = previous_candidate_keys(args.previous_report_path)
    untracked, new_since_previous = classify_inventory_candidates(candidates, inventory, previous_keys)
    report = {
        "SchemaVersion": contract["schemaVersion"],
        "GeneratedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "GeneratedAtUtc": datetime.now(timezone.utc).isoformat(),
        "DiscoveryMode": "local-fixture" if args.ollama_html_fixture or args.ollama_newest_html_fixture or args.huggingface_json_fixture or args.publisher_feed_json_fixture else "online",
        "DiscoveryContract": "config/model-discovery-contract.json", "Sources": selected, "QueriesBySource": query_record,
        "RepositoryContentSent": False, "HardwareProfileSent": False,
        "CertificationInventoryReadLocally": bool(args.inventory_path),
        "CertificationInventorySent": False,
        "ModelProfilePath": "redacted" if args.model_profile_path else None,
        "VramSelectionMode": args.vram_selection_mode, "AvailableVramGb": available or None,
        "AvailableVramSource": vram_source, "ModelHostPlatform": host,
        "PublisherFeedSinceUtc": publisher_feed_since,
        "IncludeOversizedModels": args.include_oversized_models, "PullsModels": False,
        "RewritesContinueConfig": False, "WritesCertificationInventory": False,
        "StartsTests": False, "ChangesAutomaticModelSelection": False,
        "Candidates": candidates, "NewTestCandidates": untracked,
        "NewSincePreviousReport": new_since_previous,
        "UpdateSummary": {
            "DiscoveredCount": len(candidates),
            "UntrackedCandidateCount": len(untracked),
            "NewSincePreviousReportCount": len(new_since_previous),
            "AlreadyTrackedExactCount": sum(
                item["InventoryStatus"] == "already-tracked-exact-artifact"
                for item in candidates
            ),
            "SkippedCount": len(skipped),
            "SourceErrorCount": len(errors),
        },
        "SkippedCandidates": skipped, "Errors": errors,
        "Note": "Discovery records public metadata candidates only; it never proves provenance, license suitability, runtime compatibility, quality, tool use, or approved-write readiness."
    }
    output = Path(args.output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output_path:
        markdown_output = Path(args.markdown_output_path)
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(markdown_report(report), encoding="utf-8")
    print(f"Discovery summary: {len(candidates)} candidate(s), {len(skipped)} skipped candidate(s), {len(errors)} source error(s).")
    print(f"Update summary: {len(untracked)} untracked candidate(s), {len(new_since_previous)} new since the previous report.")
    print(f"Sources: {', '.join(selected)}")
    print(f"Candidate report written to {output}")
    if args.markdown_output_path:
        print(f"Human-readable review written to {args.markdown_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
