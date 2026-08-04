#!/usr/bin/env python3
"""Memory-only approval state for offline controlled-research validation."""

from __future__ import annotations


class ApprovalRejected(ValueError):
    pass


class OfflineApprovalState:
    def __init__(self, maximum_queries: int = 4):
        if not 1 <= maximum_queries <= 4:
            raise ApprovalRejected("query-budget")
        self.maximum_queries = maximum_queries
        self.clear()

    def clear(self) -> None:
        self._approved_queries: list[str] = []
        self._destinations: dict[str, str] = {}
        self._approved_pages: set[str] = set()

    def approve_query(self, normalized_query: object) -> None:
        if not isinstance(normalized_query, str) or not normalized_query or normalized_query != " ".join(normalized_query.split()):
            self.clear()
            raise ApprovalRejected("query-not-normalized")
        if normalized_query in self._approved_queries:
            self.clear()
            raise ApprovalRejected("query-duplicate")
        if len(self._approved_queries) >= self.maximum_queries:
            self.clear()
            raise ApprovalRejected("query-budget")
        self._approved_queries.append(normalized_query)

    def consume_query(self, normalized_query: object) -> None:
        if normalized_query not in self._approved_queries:
            self.clear()
            raise ApprovalRejected("query-not-approved")
        self._approved_queries.remove(normalized_query)

    def register_results(self, results: object) -> None:
        if not isinstance(results, list):
            self.clear()
            raise ApprovalRejected("result-shape")
        destinations: dict[str, str] = {}
        for result in results:
            if not isinstance(result, dict) or set(result) != {"citationId", "destination"}:
                self.clear()
                raise ApprovalRejected("result-shape")
            citation_id = result["citationId"]
            destination = result["destination"]
            if not isinstance(citation_id, str) or not citation_id.startswith("source-") or not isinstance(destination, str) or not destination.startswith("https://"):
                self.clear()
                raise ApprovalRejected("result-shape")
            if citation_id in destinations:
                self.clear()
                raise ApprovalRejected("result-duplicate")
            destinations[citation_id] = destination
        self._destinations = destinations
        self._approved_pages.clear()

    def approve_page(self, citation_id: object, exact_destination: object) -> None:
        if not isinstance(citation_id, str) or not isinstance(exact_destination, str):
            self.clear()
            raise ApprovalRejected("page-not-trusted")
        if self._destinations.get(citation_id) != exact_destination:
            self.clear()
            raise ApprovalRejected("page-not-trusted")
        self._approved_pages.add(citation_id)

    def consume_page(self, citation_id: object, exact_destination: object) -> None:
        if not isinstance(citation_id, str) or not isinstance(exact_destination, str):
            self.clear()
            raise ApprovalRejected("page-not-approved")
        if citation_id not in self._approved_pages or self._destinations.get(citation_id) != exact_destination:
            self.clear()
            raise ApprovalRejected("page-not-approved")
        self._approved_pages.remove(citation_id)

    cancel = clear
    fail = clear
    provider_changed = clear
    shutdown = clear


if __name__ == "__main__":
    print("offline approval state only; no route, UI, or network authority")
