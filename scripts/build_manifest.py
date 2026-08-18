#!/usr/bin/env python3
"""
Build docs/manifest.json from data/*.json.

The manifest is a lightweight index (metadata only, no unit/relation bodies)
consumed by the GitHub Pages viewer (docs/index.html) so the browser doesn't
need to fetch and parse all 40 documents just to render the corpus overview
table. Individual documents are still fetched lazily, in full, when a user
opens the graph viewer for one of them.

Usage:
    python scripts/build_manifest.py

Run this any time a file under data/*.json changes. CI checks that the
committed manifest matches a fresh build (see .github/workflows/validate.yml).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_PATH = ROOT / "docs" / "manifest.json"

SKIP_FILES = {"_TEMPLATE.json", "corpus_results_final.json"}


def complexity_class(n_esu: int) -> str:
    if n_esu <= 8:
        return "A"
    if n_esu <= 15:
        return "B"
    return "C"


def main() -> int:
    docs = []
    media_counter = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name in SKIP_FILES:
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        units = d.get("units", [])
        ecus = d.get("ecus", [])
        relations = d.get("relations", [])
        n_esu = len(units)
        duration = sum(u.get("duration", 0) or 0 for u in units)
        orbits = [
            r.get("satellite_orbit", 0)
            for r in relations
            if r.get("type") == "mononuclear"
        ]
        for u in units:
            media_counter[u.get("type", "unknown")] = (
                media_counter.get(u.get("type", "unknown"), 0) + 1
            )
        docs.append(
            {
                "doc_id": d.get("doc_id"),
                "title": d.get("doc_title"),
                "domain": d.get("domain"),
                "n_esu": n_esu,
                "n_ecu": len(ecus),
                "n_relations": len(relations),
                "duration_s": round(duration, 1),
                "max_orbit": max(orbits) if orbits else 0,
                "complexity_class": complexity_class(n_esu),
                "file": f"../data/{path.name}",
            }
        )

    manifest = {
        "corpus": "RhetConnect Corpus v1.0",
        "n_documents": len(docs),
        "n_esu_total": sum(x["n_esu"] for x in docs),
        "n_ecu_total": sum(x["n_ecu"] for x in docs),
        "n_relations_total": sum(x["n_relations"] for x in docs),
        "media_distribution": media_counter,
        "documents": docs,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(docs)} documents)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
