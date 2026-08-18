# RhetConnect Corpus v1.0

**A corpus of 40 annotated multimedia educational documents with cross-media rhetorical structure, for the empirical validation of coherence-preserving multimedia adaptation algorithms.**

[![License: CC BY 4.0 (annotations)](https://img.shields.io/badge/Annotations-CC--BY--4.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Code: MIT](https://img.shields.io/badge/Code-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Validate corpus](https://github.com/smadjid/RhetConnect/actions/workflows/validate.yml/badge.svg)](https://github.com/smadjid/RhetConnect/actions/workflows/validate.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

**[Browse the corpus interactively &rarr;](https://<org>.github.io/<repo>/)**

---

## What is this?

This repository accompanies the paper:

> Sadallah, M., Maredj, A.-E. (2026). _Coherence-Preserving Adaptation and
> Summarization of Multimedia Documents: A Rhetorical Connectivity-Constrained
> Subgraph Selection Approach._ [Journal name, under review].

It provides the first publicly available corpus of multimedia educational
documents annotated with **cross-media rhetorical structure** — i.e.,
rhetorical relations (Elaboration, Evidence, Demonstration, etc.) that
explicitly connect units of _different_ media types (text, image, video,
audio), following the Extended Rhetorical Graph (ERG) formalism of
[Maredj et al. (2024)](https://doi.org/10.1007/s10115-023-01984-6).

No such corpus previously existed: RST corpora (RST-DT, GUM) are purely
textual, and multimedia summarization datasets (video saliency, segment
selection) do not annotate inter-media rhetorical dependency.

## What's in the corpus?

| Property                          | Value                                                                                          |
| --------------------------------- | ---------------------------------------------------------------------------------------------- |
| Documents                         | 40                                                                                             |
| Elementary Simple Units (ESUs)    | 559                                                                                            |
| Elementary Composite Units (ECUs) | 114                                                                                            |
| Rhetorical relations annotated    | 396                                                                                            |
| Academic domains                  | 10 (math, physics, biology, chemistry, CS, history, geography, language arts, economics, arts) |
| Structural complexity classes     | Class A: 8 · Class B: 16 · Class C: 16                                                         |
| Media types                       | text (69.6%), image (25.0%), video (4.8%), audio (0.5%)                                        |
| Inter-annotator agreement         | Cohen's κ = 0.82 (almost perfect)                                                              |
| Sources                           | 38 documents from CK-12 Foundation OER (CC-BY-NC); 2 constructed documents                     |

See `docs/CORPUS_DESCRIPTION.md` for full per-document statistics and
`docs/DATA_DICTIONARY.md` for the complete JSON schema.

## Repository structure

```
RhetConnect-Corpus-v1.0/
├── README.md                      <- you are here
├── CITATION.cff                   <- machine-readable citation metadata
├── LICENSES/
│   ├── LICENSE-DATA.txt           <- CC BY 4.0 (annotations)
│   ├── LICENSE-CODE.txt           <- MIT (validator/tools)
│   └── CK12-ATTRIBUTION.md        <- CC BY-NC 4.0 notice for source content
├── data/
│   ├── CK12-MATH-001.json         <- 40 annotated documents (ERG format)
│   ├── ...
│   ├── _TEMPLATE.json             <- blank annotation template
│   └── corpus_results_final.json  <- RhetConnect vs. naive baseline results
├── docs/
│   ├── index.html                 <- interactive corpus browser + ERG graph
│   │                                  viewer, served via GitHub Pages
│   ├── manifest.json              <- generated index consumed by index.html
│   ├── ANNOTATION_GUIDE.md        <- full annotation protocol (14 pages)
│   ├── CORPUS_DESCRIPTION.md      <- per-document statistics, domain breakdown
│   └── DATA_DICTIONARY.md         <- JSON schema reference
├── code/
│   └── erg_validator.py           <- structural validator + weight calculator
│                                      + Cohen's κ inter-annotator agreement tool
├── scripts/
│   ├── build_manifest.py          <- (re)generates docs/manifest.json
│   └── convert_to_hf.py           <- exports data/*.json to a Hugging Face
│                                      Datasets-ready JSONL (see below)
└── .github/workflows/validate.yml <- CI: validates every document on push
```

## Explore the corpus without cloning

Open **[the live browser](https://<org>.github.io/<repo>/)** (GitHub Pages,
served from `docs/`) to filter the 40 documents by domain or complexity class
and inspect any document's rhetorical graph — nucleus/satellite relations,
ECU groupings, and media types — without downloading anything. It reads
`data/*.json` directly, so it's always in sync with the raw corpus.

To regenerate the browser's index after editing `data/`:

```bash
python scripts/build_manifest.py
```

CI re-runs this and fails the build if `docs/manifest.json` drifts from the
data files (see `.github/workflows/validate.yml`), alongside full structural
validation of all 40 documents.

## Also available on Hugging Face

For users who'd rather load the corpus with `datasets` than parse individual
JSON files:

```bash
python scripts/convert_to_hf.py   # writes hf/rhetconnect_corpus.jsonl
huggingface-cli upload <org>/rhetconnect-corpus hf/ --repo-type dataset
```

```python
from datasets import load_dataset
ds = load_dataset("<org>/rhetconnect-corpus")
```

GitHub remains the source of truth and the only place changes are made;
the Hugging Face copy is a regenerated mirror.

## Quick start

```bash
# Validate a single document and compute its ERG weights
python code/erg_validator.py data/CK12-MATH-001.json

# Validate the entire corpus
python code/erg_validator.py --all data/

# Corpus-wide statistics (domains, media types, relation frequencies)
python code/erg_validator.py --stats data/

# Compute inter-annotator agreement (Cohen's κ) between two annotation sets
python code/erg_validator.py --kappa data/CK12-MATH-001.json other_annotator/CK12-MATH-001.json
```

Requires Python ≥ 3.8, no external dependencies beyond the standard library.

## Licensing — please read before reuse

This repository combines content under **three different licenses**:

1. **Annotations (rhetorical structure, relation labels, ERG metadata)** —
   original intellectual contribution of the authors — released under
   **CC BY 4.0**. See `LICENSES/LICENSE-DATA.txt`.
2. **Code (`erg_validator.py`, template)** — released under **MIT**.
   See `LICENSES/LICENSE-CODE.txt`.
3. **Source lesson content referenced by 38/40 documents** — text/image/video
   _content summaries_ (not verbatim reproductions) derived from
   **CK-12 Foundation FlexBooks**, licensed CC BY-NC 4.0 by CK-12. Our
   annotations describe and reference this content but do not reproduce it
   verbatim; see `LICENSES/CK12-ATTRIBUTION.md` for the precise scope and
   attribution requirements. **The 2 `BUILT-*` documents are original
   content by the authors and are not subject to this restriction.**

## Citing this corpus

If you use this corpus, please cite both the corpus and the paper that
introduces it (see `CITATION.cff` for machine-readable metadata, and
`docs/CORPUS_DESCRIPTION.md` for the full reference list including
[Maredj et al. 2024], the ERG formalism this corpus instantiates).

## Contact

Madjid Sadallah
madjid.sadallah@univ-lyon1.fr

## Version history

- **v1.0** (2026-07) — 40 documents, 10 domains, all three structural
  complexity classes (A/B/C) represented. Single annotator with
  independent review (κ = 0.82 on the original 20-document subset,
  same protocol applied throughout). Companion to the journal submission.
  Supersedes an initial 20-document release (2026-06) that lacked Class A
  (5–8 unit) documents and covered only 8 domains.
