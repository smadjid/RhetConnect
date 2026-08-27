# Data Dictionary — RhetConnect Corpus v1.0

This document describes every field in the JSON annotation files found in
`data/CK12-*.json` and `data/BUILT-*.json`.

---

## Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `doc_id` | string | ✓ | Unique document identifier. Format: `SOURCE-DOMAIN-NNN` where SOURCE ∈ {CK12, BUILT}, DOMAIN ∈ {MATH, SCI, CS, HIST, LANG, GEO}, NNN = zero-padded sequence number. |
| `doc_title` | string | ✓ | Human-readable lesson title. |
| `source` | string | ✓ | Attribution string for the source material. |
| `source_url` | string | ✓ | URL of the original CK-12 lesson at annotation time. `N/A` for BUILT documents. |
| `domain` | string | ✓ | Academic domain. One of: `mathematics`, `physics`, `biology`, `chemistry`, `computer_science`, `history`, `geography`, `language_arts`. |
| `annotator` | string | ✓ | Name(s) of annotator(s). |
| `annotation_date` | string | ✓ | ISO 8601 date of annotation (YYYY-MM-DD). |
| `notes` | string | — | Free-text annotation notes, difficulties encountered, and structural observations. |
| `units` | array | ✓ | List of Elementary Simple Units (ESUs). See **Unit schema** below. |
| `ecus` | array | ✓ | List of Elementary Composite Units (ECUs). Empty array `[]` if none. See **ECU schema** below. |
| `relations` | array | ✓ | List of rhetorical relations. See **Relation schema** below. |
| `root_unit_id` | string | ✓ | ID of the top-level nucleus of the entire document. |
| `computed` | object | ✓ | Automatically filled by `code/erg_validator.py`. Contains weights, levels, and corpus statistics. See **Computed schema** below. |

---

## Unit schema (`units[]`)

Each object in `units` represents one **Elementary Simple Unit (ESU)** —
an atomic media element from the source document.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✓ | Unique unit ID. Format: `DOC_ID-UNNN` (e.g. `CK12-MATH-001-U003`). |
| `label` | string | ✓ | Short descriptive name (max ~60 chars). Human-readable identifier used in analysis. |
| `type` | string | ✓ | Media type. One of: `text`, `image`, `video`, `audio`. |
| `duration` | float | ✓ | Estimated reading/viewing time in seconds. **Convention:** text = word_count / 200 × 60; image = 15s; video = actual duration in seconds; audio = actual duration in seconds. Must be > 0. |
| `content_summary` | string | ✓ | One-to-two-sentence paraphrase of the unit's content. Original authorial description — not a verbatim reproduction of source material. |

**Notes:**
- Audio units (`type = "audio"`) do not appear in v1.0 (0 audio units in corpus), but are supported by the schema and validator.
- `duration` values for text units are computed as: floor(estimated_word_count / 200 × 60), rounded to nearest second. The 200 wpm figure follows standard adult reading-speed estimates for educational text.

---

## ECU schema (`ecus[]`)

Each object in `ecus` represents one **Elementary Composite Unit (ECU)** —
a named grouping of units that form a self-contained pedagogical module.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✓ | Unique ECU ID. Format: `DOC_ID-ECUNN` (e.g. `CK12-MATH-001-ECU03`). |
| `label` | string | ✓ | Short descriptive name (e.g. "Exercise 1 Block", "Theorem Content Block"). |
| `members` | array[string] | ✓ | Ordered list of unit IDs (ESU or ECU) that constitute this ECU. Must contain ≥ 2 members. |
| `main_unit_id` | string | ✓ | ID of the main unit (nucleus) of this ECU. Must be one of the `members`. Represents the ECU in its external rhetorical relations. |

**ECU formation criteria** (from `docs/ANNOTATION_GUIDE.md`, §2.2):
- An ECU is created when a set of units forms a self-contained pedagogical module that would always be selected or rejected as a whole.
- Typical ECUs: exercise + solution block; theorem statement + proof + diagram; all steps of a worked example.
- Do NOT create ECUs for loosely-connected pairs of units that could be independently meaningful.

---

## Relation schema (`relations[]`)

Each object in `relations` represents one rhetorical relation between units
or ECUs. Two types are supported:

### Mononuclear relation

```json
{
  "id": "R001",
  "type": "mononuclear",
  "relation_name": "Elaboration",
  "nucleus_id": "CK12-MATH-001-U003",
  "satellite_id": "CK12-MATH-001-U004",
  "satellite_orbit": 0
}
```

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique relation ID within document. Format: `RNNN`. |
| `type` | string | Always `"mononuclear"` for this type. |
| `relation_name` | string | One of the 12 mononuclear relations (see table below). |
| `nucleus_id` | string | ID of the nucleus unit (ESU or ECU). The rhetorically essential element. |
| `satellite_id` | string | ID of the satellite unit (ESU or ECU). The supporting element. |
| `satellite_orbit` | integer | Orbit number (≥ 0). 0 = directly attached to nucleus; 1 = satellite of a satellite; etc. Used in weight formula. |

**Mononuclear relations used in v1.0:**

| Relation | Nucleus | Satellite | Frequency (v1.0, 40 docs) |
|---|---|---|---|
| Preparation | Main content | Introductory context | 63 |
| Elaboration | Concept/claim | Further detail | 62 |
| Clarification | Concept | Alternate representation | 61 |
| Identification | Document/section | Title or label | 41 |
| Demonstration | Procedure | Worked example | 27 |
| Evidence | Claim | Supporting data | 20 |
| Reinforcement | Core concept | Practice material | 19 |
| Annotation | Main unit | Supplementary note | 15 |
| Motivation | Action | Reason why | 11 |
| Background | Main content | Prerequisite context | 8 |
| Cause | Effect | Cause | 2 |
| Contrast | Main option | Alternative | 1 |

### Multinuclear relation

```json
{
  "id": "R004",
  "type": "multinuclear",
  "relation_name": "Joint",
  "co_nuclei_ids": ["CK12-MATH-001-U013", "CK12-MATH-001-ECU03", "CK12-MATH-001-ECU04"]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique relation ID within document. Format: `RNNN`. |
| `type` | string | Always `"multinuclear"` for this type. |
| `relation_name` | string | One of: `"Joint"`, `"List"`, `"Sequence"`, `"Enumeration"`. |
| `co_nuclei_ids` | array[string] | IDs of all co-nuclei (≥ 2). All have equal rhetorical status. |

**Multinuclear relations and their semantics:**

| Relation | Semantics | Condition C3 (RC) | Frequency (v1.0, 40 docs) |
|---|---|---|---|
| Joint | Structural assembly of document sections; no explicit interpretive dependency (Mann & Thompson 1988: "relation of last resort") | NOT applied — sections independently selectable | 27 |
| List | Unordered set of equal-status items | Applied — partial list is incoherent | 18 |
| Sequence | Ordered succession of equal-status steps | Applied — partial sequence loses ordering meaning | 10 |
| Enumeration | Numbered set of equal-status items | Applied — partial enumeration is incomplete | 11 |

**Important:** The distinction between Joint (structural) and List/Sequence/Enumeration (semantic) is theoretically grounded in RST literature and affects the rhetorical connectivity (RC) definition used in the companion paper. See §3.2 Remark 1 of the paper for the formal justification.

---

## Computed schema (`computed`)

This object is populated automatically by `code/erg_validator.py`. Do not
fill it manually — run the validator to compute it.

| Field | Type | Description |
|---|---|---|
| `weights` | object | Map from unit/ECU id → float. Importance weight computed by Algorithm 1 of [Maredj et al. 2024]. Root node starts at P_start = 3.0. MaxOrbit = max_satellite_orbit + 1. |
| `levels` | object | Map from unit/ECU id → integer. BFS depth from root (root = level 1, direct satellites = level 2, etc.). |
| `max_orbit` | integer | Global maximum orbit value across all mononuclear relations in the document. |
| `total_duration` | float | Sum of all ESU durations in seconds. |
| `n_units` | integer | Number of ESUs in the document. |
| `n_ecus` | integer | Number of ECUs in the document. |
| `n_relations` | integer | Number of relations (mononuclear + multinuclear) in the document. |

### Weight formula (from [Maredj et al. 2024], Eq. 1)

For a **satellite** at orbit `Num`, graph level `Level`, with predecessor weight `Pp`:

```
w(v) = Pp - 1 - Num / (MaxOrbit × 10^(Level-1))
```

For a **nucleus**: `w(v) = Pp + 1`  
For an **ECU**: `w(U) = w(main_unit(U))`  
Root unit: `w = P_start = 3.0`

**Note:** `MaxOrbit = max_satellite_orbit_value + 1 ≥ 1` always, so the denominator is never zero, including for flat documents where all satellites have orbit 0.

---

## Validation rules enforced by `erg_validator.py`

The validator checks:
1. All required top-level fields are present.
2. Every unit has a valid `type` and `duration > 0`.
3. Every ECU's `main_unit_id` is listed in its `members`.
4. Every ECU `member` ID exists in the document's unit or ECU list.
5. Every mononuclear relation uses a known `relation_name` from the set above.
6. Every multinuclear relation uses a known `relation_name` and has ≥ 2 co-nuclei.
7. All referenced IDs exist.
8. The rhetorical graph (mononuclear edges only) is a DAG (no cycles).
9. `root_unit_id` exists in the document.

Warnings (non-blocking) are issued for:
- Units that appear in no relation (may indicate annotation incompleteness).

---

*Data Dictionary v1.0 — Sadallah & Maredj, 2026*
