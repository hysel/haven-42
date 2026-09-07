#!/usr/bin/env python3
"""Print bundled size metadata from official Ollama tag pages; never download weights."""
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from model_catalog_search import search_ollama_catalog

ROOT = Path(__file__).resolve().parent.parent


def listed_models():
    names = set()
    for filename in ("hardware-qualified-chat-models.json", "tested-model-library.json"):
        data = json.loads((ROOT / "config" / filename).read_text(encoding="utf-8"))
        for profile in data["profiles"]:
            names.update(profile["models"])
    data = json.loads((ROOT / "config/text-capability-model-recommendations.json").read_text(encoding="utf-8"))
    for entries in data["capabilities"].values():
        names.update(item["model"] for item in entries)
    for filename in ("alpha-2-model-catalog.json", "windows-alpha-model-catalog.json"):
        data = json.loads((ROOT / "config" / filename).read_text(encoding="utf-8"))
        names.update(item["name"] for item in data["models"])
    return sorted(names)


def main():
    names = listed_models()
    families = sorted({name.rsplit(":", 1)[0] for name in names})
    def fetch(family):
        try:
            return search_ollama_catalog(family).sizes
        except ValueError:
            return {}
    sizes = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(fetch, families):
            sizes.update(result)
    print(json.dumps({"schemaVersion": 1, "source": "https://ollama.com",
                      "checkedAt": datetime.now(timezone.utc).isoformat(),
                      "sizes": {name: sizes[name] for name in names if name in sizes},
                      "unavailable": [name for name in names if name not in sizes]}, indent=2))


if __name__ == "__main__":
    main()
