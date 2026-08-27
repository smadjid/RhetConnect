# ERG Annotation Guide — Multimedia Educational Documents
## Version 1.0 — For the RhetConnect Journal Corpus

**Authors:** Sadallah M., Maredj A.-E.  
**Based on:** Maredj et al. [2024], Mann & Thompson [1988]

---

## 1. Purpose and Scope

This guide defines the annotation protocol for building the **RhetConnect Corpus** — a set of 20 annotated multimedia educational documents used to validate the RhetConnect algorithm empirically.

Each document is annotated with:
1. Its **units** (ESU and ECU)
2. The **rhetorical relations** between units
3. Automatically computed **weights** and **levels** (by the validator tool)

---

## 2. Unit Types

### 2.1 Elementary Simple Unit (ESU)

An ESU is the smallest indivisible media element in the document. It carries a single idea expressed through a single medium.

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique ID, format: `DOC_ID-U001`, `DOC_ID-U002`, etc. |
| `label` | string | Short descriptive name (e.g., "Pythagorean Theorem statement") |
| `type` | enum | `text` \| `image` \| `video` \| `audio` |
| `duration` | float | Seconds. For text: word_count / 200 × 60. For image: 15s. For video: actual duration. For audio: actual duration. |
| `content_summary` | string | 1–2 sentence description of what the unit contains |
| `source_url` | string | URL or reference to the original OER source |

**Segmentation rules for text:**
- One ESU = one coherent thought (definition, theorem statement, explanation paragraph, example, exercise, solution)
- Do NOT split a single paragraph if it develops one idea
- DO split if a paragraph introduces a definition AND then gives an example (two ideas = two ESUs)
- A title is always its own ESU (type = text)

**Segmentation rules for images:**
- One ESU = one image or diagram
- A figure with multiple panels = multiple ESUs if each panel is independently meaningful

**Segmentation rules for video:**
- One ESU = one video clip or embedded video segment
- If a video has clearly distinct segments (intro / demonstration / summary), treat as separate ESUs

### 2.2 Elementary Composite Unit (ECU)

An ECU groups multiple units (ESU or ECU) that together convey a coherent, self-contained pedagogical block.

| Field | Type | Description |
|---|---|---|
| `id` | string | Format: `DOC_ID-ECU01`, etc. |
| `label` | string | Short name (e.g., "Exercise 1 Block", "Introduction Section") |
| `members` | list[id] | IDs of constituent units (ESU or ECU) |
| `main_unit_id` | string | ID of the nucleus of the highest-level internal relation |

**When to create an ECU:**
- A set of units that always travels together and forms a self-contained module
- Example: an exercise image + its solution image + a hints text → ECU "Exercise 1"
- Example: a theorem statement + its proof text → ECU "Theorem Block"

**When NOT to create an ECU:**
- Do not wrap every pair of units in an ECU. Only create ECUs when the grouping is pedagogically meaningful and would be extracted as a whole.
- A document introduction with 3 paragraphs does NOT necessarily form an ECU unless the 3 paragraphs are truly inseparable.

---

## 3. Rhetorical Relations

### 3.1 Mononuclear Relations

In a mononuclear relation, one unit is the **Nucleus (N)** and the other is the **Satellite (S)**.
- The nucleus carries the essential information
- The satellite provides support, context, or elaboration
- Removing the nucleus causes more coherence loss than removing the satellite

| Relation | Nucleus | Satellite | Typical multimedia case |
|---|---|---|---|
| **Elaboration** | Concept or claim | Further detail or expansion | Text definition (N) + explanatory image (S) |
| **Evidence** | Claim | Supporting data or proof | Statement (N) + demonstration video (S) |
| **Background** | Main content | Prerequisite context | Theorem (N) + historical context (S) |
| **Motivation** | Action or procedure | Reason why | Exercise set (N) + "why this matters" text (S) |
| **Cause** | Effect | Cause | Result image (N) + causal explanation (S) |
| **Contrast** | Main option | Alternative | Primary method (N) + alternative approach (S) |
| **Demonstration** | Procedure | Worked example | Method text (N) + step-by-step video (S) |
| **Annotation** | Main unit | Supplementary note | Diagram (N) + annotation text (S) |
| **Clarification** | Concept | Disambiguation | Theorem (N) + geometric interpretation (S) |
| **Identification** | Document/section | Title or label | Course (N) + title text (S) |
| **Preparation** | Main content | Introductory context | Lesson (N) + "who was Pythagoras" (S) |
| **Reinforcement** | Core concept | Practice material | Theorem (N) + exercise set (S) |

### 3.2 Multinuclear Relations

All connected units have **equal status** (all are co-nuclei). Use when no unit is more important than the others.

| Relation | Description | Typical case |
|---|---|---|
| **List** | Unordered set of equal items | A set of properties, all equally important |
| **Sequence** | Ordered set (order matters) | Step 1 → Step 2 → Step 3 |
| **Joint** | Loosely connected equal units | Two examples of the same concept |
| **Enumeration** | Numbered list of equal items | Numbered exercises in a problem set |

**Decision rule:** If you can remove any one unit without disrupting understanding of the others → multinuclear. If removing one makes the other incomprehensible → mononuclear (one is satellite of the other).

---

## 4. Orbit Numbers

Orbit numbers apply only to **satellites** and indicate proximity to their nucleus.
- Orbit 0 = directly attached satellite (closest to nucleus)
- Orbit 1 = satellite of a satellite
- Orbit 2 = satellite of a satellite of a satellite

**Rule:** In practice, for most educational documents, orbits 0 and 1 are sufficient. Only assign orbit > 1 if there is genuine three-level nesting.

---

## 5. Graph-Level Rules

The graph level of each unit is computed automatically by the validator. For reference:
- The root unit (main nucleus of the whole document) gets the highest level value N
- Levels decrease as you go down toward leaves (satellites of satellites)
- Two nuclei in a multinuclear relation share the same level
- A satellite is at level (nucleus_level - 1)

---

## 6. Annotation Decision Tree

When facing a pair of units, ask:

```
1. Are both units essential to understand each other?
   YES → Multinuclear (List, Sequence, Joint, or Enumeration)
   NO  → Go to 2

2. Which one can be removed with less coherence damage?
   The removable one = Satellite
   The essential one = Nucleus
   → Choose the mononuclear relation from §3.1 that best describes 
     how the Satellite supports the Nucleus

3. Does the Satellite directly support the Nucleus (orbit 0)?
   Or does it support another Satellite (orbit 1+)?
   → Assign orbit accordingly

4. Should these units be grouped into an ECU?
   Only if they form a self-contained pedagogical module
   that would be selected or rejected as a whole.
```

---

## 7. Annotation Format (JSON)

Each annotated document is stored as a JSON file with the following structure:

```json
{
  "doc_id": "CK12-MATH-001",
  "doc_title": "The Pythagorean Theorem",
  "source": "CK-12 Foundation, CC-BY-NC",
  "source_url": "https://www.ck12.org/...",
  "domain": "mathematics",
  "annotator": "Sadallah M.",
  "annotation_date": "2026-07-01",
  "units": [
    {
      "id": "CK12-MATH-001-U001",
      "label": "Title: The Pythagorean Theorem",
      "type": "text",
      "duration": 3.0,
      "content_summary": "Title of the lesson",
      "role": "S",
      "orbit": 0
    },
    {
      "id": "CK12-MATH-001-U002",
      "label": "Learning Objectives",
      "type": "text",
      "duration": 18.0,
      "content_summary": "List of 3 learning objectives for the lesson",
      "role": "S",
      "orbit": 0
    }
  ],
  "ecus": [
    {
      "id": "CK12-MATH-001-ECU01",
      "label": "Exercise 1 Block",
      "members": ["CK12-MATH-001-U009", "CK12-MATH-001-U010"],
      "main_unit_id": "CK12-MATH-001-U009"
    }
  ],
  "relations": [
    {
      "id": "R001",
      "type": "mononuclear",
      "relation_name": "Identification",
      "nucleus_id": "CK12-MATH-001-U003",
      "satellite_id": "CK12-MATH-001-U001",
      "nucleus_role": "N",
      "satellite_orbit": 0
    },
    {
      "id": "R002",
      "type": "multinuclear",
      "relation_name": "List",
      "co_nuclei_ids": ["CK12-MATH-001-U005", "CK12-MATH-001-U006", "CK12-MATH-001-U007"]
    }
  ],
  "root_unit_id": "CK12-MATH-001-U003",
  "computed": {
    "weights": {},
    "levels": {},
    "max_orbit": null,
    "total_duration": null
  }
}
```

The `computed` section is filled automatically by the validator. Do not fill it manually.

---

## 8. Difficult Cases and Conventions

**Case 1 — A video that explains a text concept**
→ The text is the Nucleus (Elaboration), the video is the Satellite.
Rationale: the text carries the essential propositional content; the video provides a dynamic illustration.

**Case 2 — An exercise and its solution**
→ The exercise image/text is the Nucleus, the solution is the Satellite (Annotation or Demonstration).
Rationale: the exercise is the pedagogically essential content; the solution is support.

**Case 3 — Multiple worked examples of the same concept**
→ Multinuclear (Joint or List) if the examples are interchangeable.
→ Mononuclear (Reinforcement) if one is the "main" example and others are supplementary.

**Case 4 — A "Did You Know?" sidebar**
→ Satellite of the nearest conceptual nucleus, relation = Background or Annotation.

**Case 5 — A summary at the end of a section**
→ Satellite of the section nucleus, relation = Elaboration (summarization is a form of elaboration pointing backward).

**Case 6 — Prerequisites section ("Before reading this, you should know...")**
→ Satellite of the main lesson nucleus, relation = Background. Orbit 0.

**Case 7 — Learning objectives at the start**
→ Satellite of the main lesson nucleus, relation = Preparation. Orbit 0.

---

## 9. Quality Checklist (before submitting an annotation)

- [ ] Every unit has a unique id, a type, a duration > 0, and a content_summary
- [ ] Every unit appears in exactly one relation (as nucleus or satellite or co-nucleus)
- [ ] No unit is both nucleus and satellite in the same relation
- [ ] Every satellite has a valid nucleus_id that exists in the document
- [ ] Every ECU's main_unit_id is a member of that ECU
- [ ] Orbit numbers are consistent (satellite of satellite = orbit 1, not orbit 0)
- [ ] The root_unit_id is the nucleus that anchors the entire document
- [ ] Run the validator tool before submitting — zero errors required

---

## 10. Inter-Annotator Agreement Protocol

For each document annotated by two annotators independently:

1. Both annotators annotate the same document without consulting each other
2. The validator computes pairwise agreement on:
   - Unit segmentation (F1 on unit boundaries)
   - Relation assignment (κ on relation labels for shared unit pairs)
   - Nucleus/satellite assignment (κ on N/S role for shared mononuclear relations)
3. Disagreements are discussed and resolved by consensus
4. If consensus cannot be reached, the document is flagged and excluded or adjudicated by a third annotator

**Target κ:** ≥ 0.70 on relation labels (acceptable for RST annotation, consistent with the literature)

---

*End of annotation guide*
