#!/usr/bin/env python3
"""Deterministic, bounded, memory-only lexical retrieval.

This module has no runtime route and performs no file, network, provider, or
process operation. Callers may pass only text already validated in memory.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
from typing import Iterable


TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)


class RetrievalError(ValueError):
    """A stable rejection at the lexical-retrieval trust boundary."""


@dataclass(frozen=True)
class _Chunk:
    source_name: str
    source_order: int
    offset: int
    text: str
    terms: Counter[str]


def _terms(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(value.casefold())


def _validate_source_name(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 255:
        raise RetrievalError("invalid-source-name")
    if value in {".", ".."} or "/" in value or "\\" in value or "\x00" in value:
        raise RetrievalError("path-bearing-source")
    if not value.casefold().endswith((".txt", ".md", ".csv", ".json")):
        raise RetrievalError("unsupported-source-type")
    return value


class MemoryLexicalRetrieval:
    """A bounded index whose only retained state is caller-supplied memory."""

    def __init__(self, contract: dict):
        self._contract = contract
        self._chunks: list[_Chunk] = []
        self._source_names: list[str] = []

    @property
    def source_count(self) -> int:
        return len(self._source_names)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def clear(self) -> None:
        self._chunks.clear()
        self._source_names.clear()

    def load(self, attachments: Iterable[dict]) -> None:
        self.clear()
        try:
            values = list(attachments)
            budgets = self._contract["budgets"]
            if not values or len(values) > budgets["maximumAttachments"]:
                raise RetrievalError("invalid-source-count")

            seen: set[str] = set()
            total_bytes = 0
            chunks: list[_Chunk] = []
            names: list[str] = []
            for source_order, attachment in enumerate(values):
                if not isinstance(attachment, dict) or set(attachment) != {
                    "name", "text", "sizeBytes"
                }:
                    raise RetrievalError("invalid-source-fields")
                name = _validate_source_name(attachment["name"])
                folded_name = name.casefold()
                if folded_name in seen:
                    raise RetrievalError("duplicate-source-name")
                seen.add(folded_name)

                text = attachment["text"]
                size_bytes = attachment["sizeBytes"]
                if not isinstance(text, str) or not text or "\x00" in text:
                    raise RetrievalError("invalid-source-text")
                actual_bytes = len(text.encode("utf-8"))
                if (
                    isinstance(size_bytes, bool)
                    or not isinstance(size_bytes, int)
                    or size_bytes != actual_bytes
                ):
                    raise RetrievalError("source-size-mismatch")
                total_bytes += actual_bytes
                if total_bytes > budgets["maximumSourceBytes"]:
                    raise RetrievalError("source-budget-exceeded")

                chunk_size = budgets["maximumChunkCharacters"]
                source_chunks = [
                    _Chunk(
                        source_name=name,
                        source_order=source_order,
                        offset=offset,
                        text=text[offset:offset + chunk_size],
                        terms=Counter(_terms(text[offset:offset + chunk_size])),
                    )
                    for offset in range(0, len(text), chunk_size)
                ]
                if len(source_chunks) > budgets["maximumChunksPerAttachment"]:
                    raise RetrievalError("chunk-budget-exceeded")
                chunks.extend(source_chunks)
                names.append(name)

            self._chunks = chunks
            self._source_names = names
        except Exception:
            self.clear()
            raise

    def remove(self, source_name: str) -> None:
        try:
            folded_name = _validate_source_name(source_name).casefold()
            if folded_name not in {name.casefold() for name in self._source_names}:
                raise RetrievalError("unknown-source")
            self._chunks = [
                chunk for chunk in self._chunks
                if chunk.source_name.casefold() != folded_name
            ]
            self._source_names = [
                name for name in self._source_names
                if name.casefold() != folded_name
            ]
        except Exception:
            self.clear()
            raise

    def search(self, query: object) -> dict:
        try:
            budgets = self._contract["budgets"]
            if not isinstance(query, str) or not query.strip():
                raise RetrievalError("invalid-query")
            if len(query) > budgets["maximumQueryCharacters"]:
                raise RetrievalError("query-budget-exceeded")
            query_terms = _terms(query)
            if not query_terms:
                raise RetrievalError("invalid-query")

            scored = []
            for chunk in self._chunks:
                score = sum(chunk.terms[term] for term in query_terms)
                if score:
                    scored.append((score, chunk))
            scored.sort(
                key=lambda item: (
                    -item[0],
                    item[1].source_order,
                    item[1].offset,
                )
            )

            selected = []
            selected_characters = 0
            character_budget_omissions = 0
            chunk_budget_reached = False
            for score, chunk in scored:
                if len(selected) >= budgets["maximumSelectedChunks"]:
                    chunk_budget_reached = True
                    break
                if (
                    selected_characters + len(chunk.text)
                    > budgets["maximumSelectedCharacters"]
                ):
                    character_budget_omissions += 1
                    continue
                selected.append({
                    "sourceName": chunk.source_name,
                    "sourceOffset": chunk.offset,
                    "sourceEndOffset": chunk.offset + len(chunk.text),
                    "score": score,
                    "characters": len(chunk.text),
                    "tokenEstimate": (len(chunk.text) + 3) // 4,
                    "content": chunk.text,
                    "contentAuthority": False,
                    "disclosure": "Selected from untrusted in-memory attachment text.",
                })
                selected_characters += len(chunk.text)

            omitted_matching_chunks = len(scored) - len(selected)
            truncation_reasons = []
            if chunk_budget_reached:
                truncation_reasons.append("selected-chunk-limit")
            if character_budget_omissions:
                truncation_reasons.append("selected-character-limit")

            return {
                "kind": "memory-lexical-retrieval-result",
                "runtimeAdmitted": False,
                "providerPayloadAllowed": False,
                "algorithm": self._contract["determinism"]["algorithm"],
                "queryTermCount": len(query_terms),
                "matchingChunkCount": len(scored),
                "selectedChunkCount": len(selected),
                "omittedMatchingChunkCount": omitted_matching_chunks,
                "selectionTruncated": omitted_matching_chunks > 0,
                "truncationReasons": truncation_reasons,
                "selectedCharacters": selected_characters,
                "tokenEstimate": sum(item["tokenEstimate"] for item in selected),
                "chunks": selected,
                "effects": {
                    "filesystemRead": False,
                    "filesystemWrite": False,
                    "networkAccess": False,
                    "providerInvocation": False,
                    "processCreation": False,
                },
            }
        except Exception:
            self.clear()
            raise
