#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate-evidence-wiki-pages.py"
COLUMNS = [
    "schema_version", "area", "subject", "surface", "surface_version",
    "provider", "os", "model", "operation", "validation_mode", "status",
    "evidence", "notes",
]


class EvidenceWikiPageTests(unittest.TestCase):
    def test_generates_stable_pages_registry_and_wiki_map(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "config").mkdir()
            (root / "docs").mkdir()
            rows = [
                ["2", "model-runtime", "Small model chat", "Haven 42", "alpha2", "Ollama", "Windows", "example:1b", "chat", "local-endpoint", "partial-pass", "examples/example.md", "Chat passed; broader use remains untested."],
                ["2", "model-runtime", "Small model summary", "Haven 42", "alpha2", "Ollama", "Linux", "example:1b", "summarize", "local-endpoint", "validated-by-tests", "scripts/example.py", "The exact summary control passed."],
            ]
            catalog = root / "config" / "evidence-catalog.tsv"
            with catalog.open("w", encoding="utf-8", newline="") as target:
                writer = csv.writer(target, delimiter="\t", lineterminator="\n")
                writer.writerow(COLUMNS)
                writer.writerows(rows)
            (root / "config" / "capability-evidence-contract.json").write_text(json.dumps({"columns": COLUMNS}), encoding="utf-8")
            (root / "config" / "wiki-sync.tsv").write_text("source\tpage\ttitle\ndocs/wiki-home.md\tHome.md\tHome\n", encoding="utf-8")
            command = [
                sys.executable, str(GENERATOR), "--root", str(root),
                "--catalog", str(catalog),
                "--contract", str(root / "config" / "capability-evidence-contract.json"),
                "--registry", str(root / "config" / "evidence-page-registry.json"),
                "--pages", str(root / "docs" / "evidence-records"),
                "--index", str(root / "docs" / "wiki-evidence-record-index.md"),
                "--wiki-map", str(root / "config" / "wiki-sync.tsv"),
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            first = (root / "config" / "evidence-page-registry.json").read_bytes()
            subprocess.run(command, check=True, capture_output=True, text=True)
            subprocess.run([*command, "--check"], check=True, capture_output=True, text=True)
            self.assertEqual(first, (root / "config" / "evidence-page-registry.json").read_bytes())
            registry = json.loads(first)
            self.assertEqual(2, registry["recordCount"])
            self.assertFalse(registry["futureAutomaticUpdateUse"]["automaticUpdateActivationAuthorized"])
            self.assertTrue(registry["futureAutomaticUpdateUse"]["requiresSignedUpdateMetadata"])
            pages = list((root / "docs" / "evidence-records").glob("*.md"))
            self.assertEqual(2, len(pages))
            page = pages[0].read_text(encoding="utf-8")
            self.assertIn("Boundary of this result", page)
            self.assertIn("Future update use", page)
            wiki_map = (root / "config" / "wiki-sync.tsv").read_text(encoding="utf-8")
            self.assertEqual(2, wiki_map.count("docs/evidence-records/"))
            self.assertIn("docs/wiki-evidence-record-index.md", wiki_map)

    def test_repository_generated_evidence_pages_are_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
