#!/usr/bin/env python3
"""
Convert data/*.json into a single JSONL file for publishing the corpus as a
Hugging Face Dataset (one row per document, nested units/ecus/relations kept
as-is so no annotation detail is lost).

Usage:
    python scripts/convert_to_hf.py [--out hf/rhetconnect_corpus.jsonl]

Then, to publish:
    huggingface-cli login
    huggingface-cli upload <your-org>/rhetconnect-corpus hf/ --repo-type dataset

This keeps GitHub as the source of truth (data/*.json, validated by CI) and
the JSONL as a derived, republishable artifact -- regenerate it any time the
underlying documents change, same as docs/manifest.json.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_FILES = {"_TEMPLATE.json", "corpus_results_final.json"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(ROOT / "data"))
    ap.add_argument("--out", default=str(ROOT / "hf" / "rhetconnect_corpus.jsonl"))
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for path in sorted(data_dir.glob("*.json")):
            if path.name in SKIP_FILES:
                continue
            doc = json.loads(path.read_text(encoding="utf-8"))
            fh.write(json.dumps(doc, ensure_ascii=False) + "\n")
            n += 1

    print(f"Wrote {n} documents to {out_path}")

    readme = out_path.parent / "README.md"
    readme.write_text(
        "---\n"
        "license: cc-by-4.0\n"
        "language:\n"
        "  - en\n"
        "tags:\n"
        "  - rhetorical-structure-theory\n"
        "  - multimedia\n"
        "  - education\n"
        "pretty_name: RhetConnect Corpus v1.0\n"
        "---\n\n"
        "# RhetConnect Corpus v1.0\n\n"
        "40 multimedia educational documents annotated with cross-media rhetorical "
        "structure (Extended Rhetorical Graph formalism). One JSON object per line "
        "in `rhetconnect_corpus.jsonl`; each row is a full document with its `units`, "
        "`ecus`, and `relations`.\n\n"
        "This is a mirror of the canonical, CI-validated source at "
        "[GitHub repo URL] (`data/*.json`). See that repository's `docs/DATA_DICTIONARY.md` "
        "for the full field reference, and `LICENSES/` for licensing "
        "(annotations: CC BY 4.0; 38/40 documents reference CK-12 Foundation CC BY-NC 4.0 "
        "source content, see `LICENSES/CK12-ATTRIBUTION.md`).\n",
        encoding="utf-8",
    )
    print(f"Wrote {readme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
