"""
ERG Annotation Validator and Weight Calculator
RhetConnect Corpus — Sadallah & Maredj 2026

Usage:
    python erg_validator.py <annotation_file.json>
    python erg_validator.py --all <corpus_dir>
    python erg_validator.py --stats <corpus_dir>
    python erg_validator.py --kappa <file1.json> <file2.json>
"""

import json
import sys
import os
import math
from pathlib import Path
from collections import defaultdict, deque


# ═══════════════════════════════════════════════════════════════════════════════
# LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_doc(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_doc(doc, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURAL VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate(doc):
    errors = []
    warnings = []

    unit_ids  = {u['id'] for u in doc.get('units', [])}
    ecu_ids   = {e['id'] for e in doc.get('ecus', [])}
    all_ids   = unit_ids | ecu_ids
    relations = doc.get('relations', [])

    # ── 1. Required top-level fields ──────────────────────────────────────────
    for field in ['doc_id', 'doc_title', 'source', 'domain', 'annotator',
                  'units', 'relations', 'root_unit_id']:
        if field not in doc:
            errors.append(f"Missing required field: '{field}'")

    # ── 2. Unit field completeness ────────────────────────────────────────────
    valid_types = {'text', 'image', 'video', 'audio'}
    valid_roles = {'N', 'S', None}
    for u in doc.get('units', []):
        uid = u.get('id', '?')
        if not u.get('label'):
            errors.append(f"Unit {uid}: missing 'label'")
        if u.get('type') not in valid_types:
            errors.append(f"Unit {uid}: invalid type '{u.get('type')}' "
                          f"(must be text|image|video|audio)")
        if not isinstance(u.get('duration', 0), (int, float)) or u.get('duration', 0) <= 0:
            errors.append(f"Unit {uid}: duration must be a positive number "
                          f"(got {u.get('duration')})")
        if not u.get('content_summary'):
            warnings.append(f"Unit {uid}: missing 'content_summary' (recommended)")

    # ── 3. ECU field completeness ─────────────────────────────────────────────
    for e in doc.get('ecus', []):
        eid = e.get('id', '?')
        members = e.get('members', [])
        if not members:
            errors.append(f"ECU {eid}: 'members' list is empty")
        for m in members:
            if m not in all_ids:
                errors.append(f"ECU {eid}: member '{m}' not found in units or ECUs")
        main = e.get('main_unit_id')
        if not main:
            errors.append(f"ECU {eid}: missing 'main_unit_id'")
        elif main not in members:
            errors.append(f"ECU {eid}: main_unit_id '{main}' is not a member of the ECU")

    # ── 4. Relation validity ──────────────────────────────────────────────────
    MONO_RELATIONS = {
        'Elaboration', 'Evidence', 'Background', 'Motivation', 'Cause',
        'Contrast', 'Demonstration', 'Annotation', 'Clarification',
        'Identification', 'Preparation', 'Reinforcement'
    }
    MULTI_RELATIONS = {'List', 'Sequence', 'Joint', 'Enumeration'}

    rel_ids = set()
    for r in relations:
        rid = r.get('id', '?')
        if rid in rel_ids:
            errors.append(f"Relation {rid}: duplicate relation id")
        rel_ids.add(rid)

        rtype = r.get('type')
        rname = r.get('relation_name')

        if rtype == 'mononuclear':
            if rname not in MONO_RELATIONS:
                errors.append(f"Relation {rid}: unknown mononuclear relation '{rname}'")
            nid = r.get('nucleus_id')
            sid = r.get('satellite_id')
            if not nid:
                errors.append(f"Relation {rid}: missing 'nucleus_id'")
            elif nid not in all_ids:
                errors.append(f"Relation {rid}: nucleus_id '{nid}' not found")
            if not sid:
                errors.append(f"Relation {rid}: missing 'satellite_id'")
            elif sid not in all_ids:
                errors.append(f"Relation {rid}: satellite_id '{sid}' not found")
            if nid and sid and nid == sid:
                errors.append(f"Relation {rid}: nucleus and satellite are the same unit")
            orbit = r.get('satellite_orbit')
            if orbit is None:
                errors.append(f"Relation {rid}: missing 'satellite_orbit'")
            elif not isinstance(orbit, int) or orbit < 0:
                errors.append(f"Relation {rid}: satellite_orbit must be a non-negative integer")

        elif rtype == 'multinuclear':
            if rname not in MULTI_RELATIONS:
                errors.append(f"Relation {rid}: unknown multinuclear relation '{rname}'")
            co = r.get('co_nuclei_ids', [])
            if len(co) < 2:
                errors.append(f"Relation {rid}: multinuclear relation needs ≥ 2 co_nuclei_ids")
            for cid in co:
                if cid not in all_ids:
                    errors.append(f"Relation {rid}: co_nucleus '{cid}' not found")
        else:
            errors.append(f"Relation {rid}: 'type' must be 'mononuclear' or 'multinuclear'")

    # ── 5. Every unit appears in at least one relation ────────────────────────
    units_in_relations = set()
    for r in relations:
        if r.get('type') == 'mononuclear':
            units_in_relations.add(r.get('nucleus_id'))
            units_in_relations.add(r.get('satellite_id'))
        elif r.get('type') == 'multinuclear':
            units_in_relations.update(r.get('co_nuclei_ids', []))

    for uid in all_ids:
        if uid not in units_in_relations:
            warnings.append(f"Unit/ECU '{uid}' does not appear in any relation")

    # ── 6. Root unit exists ───────────────────────────────────────────────────
    root = doc.get('root_unit_id')
    if root and root not in all_ids:
        errors.append(f"root_unit_id '{root}' not found in units or ECUs")

    # ── 7. Cycle detection in the rhetorical graph ────────────────────────────
    graph = defaultdict(set)
    for r in relations:
        if r.get('type') == 'mononuclear':
            n, s = r.get('nucleus_id'), r.get('satellite_id')
            if n and s:
                graph[n].add(s)

    def has_cycle(graph, nodes):
        visited, rec_stack = set(), set()
        def dfs(v):
            visited.add(v); rec_stack.add(v)
            for nb in graph.get(v, []):
                if nb not in visited:
                    if dfs(nb): return True
                elif nb in rec_stack:
                    return True
            rec_stack.discard(v)
            return False
        return any(dfs(n) for n in nodes if n not in visited)

    if has_cycle(graph, all_ids):
        errors.append("CYCLE DETECTED in the rhetorical graph — the ERG must be a DAG")

    return errors, warnings


# ═══════════════════════════════════════════════════════════════════════════════
# WEIGHT AND LEVEL COMPUTATION  (Algorithm 1 & 2 from Maredj et al. 2024)
# ═══════════════════════════════════════════════════════════════════════════════


def _build_index(doc):
    """Internal helper — build adjacency structures."""
    ecu_main     = {e['id']: e['main_unit_id'] for e in doc.get('ecus', [])}
    nuc_to_sats  = defaultdict(list)
    multi_groups = defaultdict(list)
    for r in doc.get('relations', []):
        if r['type'] == 'mononuclear':
            nuc_to_sats[r['nucleus_id']].append(
                (r['satellite_id'], r.get('satellite_orbit', 0)))
        else:
            co = r['co_nuclei_ids']
            for c in co:
                multi_groups[c] = [x for x in co if x != c]
    return ecu_main, nuc_to_sats, multi_groups


def compute_weights(doc, P_start=3.0):
    """
    Compute ERG unit weights and levels following Algorithm 1 & 2
    of Maredj et al. [2024], with correct ECU expansion and MaxOrbit
    interpretation (MaxOrbit = max_satellite_orbit_value + 1).

    Returns: (weights dict, levels dict, max_orbit int)
    """
    root_id = doc.get('root_unit_id')
    if not root_id:
        return {}, {}, 0

    ecu_main, nuc_to_sats, multi_groups = _build_index(doc)

    # MaxOrbit = number of orbit levels = max orbit value + 1
    max_sat_orbit = max(
        (r.get('satellite_orbit', 0) for r in doc.get('relations', [])
         if r['type'] == 'mononuclear'),
        default=0)
    max_orbit = max_sat_orbit + 1

    # ── Level assignment (BFS from root) ────────────────────────────────────
    levels = {root_id: 1}
    q = deque([root_id]); seen = {root_id}

    def enqueue(uid, lev):
        if uid not in seen:
            levels[uid] = lev; seen.add(uid); q.append(uid)

    while q:
        uid = q.popleft(); lev = levels[uid]
        for (sid, _) in nuc_to_sats.get(uid, []):
            enqueue(sid, lev + 1)
            if sid in ecu_main:
                enqueue(ecu_main[sid], lev + 1)
        if uid in ecu_main:
            enqueue(ecu_main[uid], lev)
        for co in multi_groups.get(uid, []):
            enqueue(co, lev)

    # ── Weight assignment (DFS from root) ───────────────────────────────────
    weights = {}; visited = set()

    def visit(uid, w):
        if uid in visited:
            return
        visited.add(uid)
        weights[uid] = w
        lev = levels.get(uid, 1)

        # ECU → delegate to its main_unit (same weight), then process own relations
        if uid in ecu_main:
            m = ecu_main[uid]
            if m not in visited:
                visit(m, w)
            weights[uid] = weights.get(m, w)
            # Fall through: also process ECU's own outgoing relations below

        # Mononuclear satellites
        for (sid, orb) in nuc_to_sats.get(uid, []):
            if sid not in visited:
                denom = max_orbit * (10 ** max(lev - 1, 0))
                visit(sid, round(w - 1.0 - orb / denom, 4))

        # Multinuclear co-nuclei (same weight)
        for co in multi_groups.get(uid, []):
            if co not in visited:
                visit(co, w)

    visit(root_id, P_start)

    # Any unreachable unit gets weight 0
    all_ids = ({u['id'] for u in doc.get('units', [])} |
               {e['id'] for e in doc.get('ecus',  [])})
    for uid in all_ids:
        if uid not in weights:
            weights[uid] = 0.0

    return weights, levels, max_orbit

def compute_total_duration(doc):
    return round(sum(u['duration'] for u in doc.get('units', [])), 2)


def enrich_doc(doc):
    """Fill in the 'computed' section of the document."""
    weights, levels, max_orbit = compute_weights(doc, P_start=3.0)
    total_dur = compute_total_duration(doc)
    doc['computed'] = {
        'weights':        weights,
        'levels':         levels,
        'max_orbit':      max_orbit,
        'total_duration': total_dur,
        'n_units':        len(doc.get('units', [])),
        'n_ecus':         len(doc.get('ecus', [])),
        'n_relations':    len(doc.get('relations', [])),
    }
    return doc


# ═══════════════════════════════════════════════════════════════════════════════
# CORPUS STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

def corpus_stats(corpus_dir):
    files = [f for f in Path(corpus_dir).glob('**/*.json')
             if not f.name.startswith('_') and 'results' not in f.name]
    if not files:
        print(f"No JSON files found in {corpus_dir}")
        return

    total_units = total_ecus = total_rels = total_dur = 0
    domains = defaultdict(int)
    type_counts = defaultdict(int)
    rel_counts  = defaultdict(int)
    n_docs = 0

    for f in files:
        try:
            doc = load_doc(f)
            if 'doc_id' not in doc:
                continue
            n_docs += 1
            c = doc.get('computed', {})
            total_units += c.get('n_units', 0)
            total_ecus  += c.get('n_ecus', 0)
            total_rels  += c.get('n_relations', 0)
            total_dur   += c.get('total_duration', 0)
            domains[doc.get('domain', 'unknown')] += 1
            for u in doc.get('units', []):
                type_counts[u.get('type', '?')] += 1
            for r in doc.get('relations', []):
                rel_counts[r.get('relation_name', '?')] += 1
        except Exception as e:
            print(f"  [!] Error reading {f.name}: {e}")

    print(f"\n{'='*50}")
    print(f"CORPUS STATISTICS — {n_docs} documents")
    print(f"{'='*50}")
    print(f"  Total ESUs         : {total_units}")
    print(f"  Total ECUs         : {total_ecus}")
    print(f"  Total relations    : {total_rels}")
    print(f"  Total duration     : {total_dur:.1f}s ({total_dur/60:.1f} min)")
    print(f"  Avg units/doc      : {total_units/max(n_docs,1):.1f}")
    print(f"  Avg relations/doc  : {total_rels/max(n_docs,1):.1f}")
    print(f"\n  Domains:")
    for d, cnt in sorted(domains.items(), key=lambda x: -x[1]):
        print(f"    {d:<20}: {cnt} docs")
    print(f"\n  Media type distribution:")
    for t, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
        pct = 100*cnt/max(sum(type_counts.values()),1)
        print(f"    {t:<10}: {cnt:>4} ({pct:.1f}%)")
    print(f"\n  Rhetorical relation distribution:")
    for r, cnt in sorted(rel_counts.items(), key=lambda x: -x[1]):
        pct = 100*cnt/max(sum(rel_counts.values()),1)
        print(f"    {r:<20}: {cnt:>4} ({pct:.1f}%)")


# ═══════════════════════════════════════════════════════════════════════════════
# INTER-ANNOTATOR AGREEMENT (Cohen's κ)
# ═══════════════════════════════════════════════════════════════════════════════

def cohen_kappa(doc1, doc2):
    """
    Compute Cohen's κ on relation labels for pairs of units
    that appear in both annotations.
    We align on (nucleus_id, satellite_id) pairs for mononuclear relations.
    """
    def get_mono_dict(doc):
        d = {}
        for r in doc.get('relations', []):
            if r['type'] == 'mononuclear':
                key = tuple(sorted([r['nucleus_id'], r['satellite_id']]))
                d[key] = r['relation_name']
        return d

    d1 = get_mono_dict(doc1)
    d2 = get_mono_dict(doc2)
    shared_pairs = set(d1.keys()) & set(d2.keys())

    if not shared_pairs:
        print("No shared (nucleus, satellite) pairs found between the two annotations.")
        return None

    labels1 = [d1[k] for k in shared_pairs]
    labels2 = [d2[k] for k in shared_pairs]

    all_labels = sorted(set(labels1) | set(labels2))
    label_to_idx = {l: i for i, l in enumerate(all_labels)}
    n = len(all_labels)

    # Confusion matrix
    conf = [[0]*n for _ in range(n)]
    for l1, l2 in zip(labels1, labels2):
        conf[label_to_idx[l1]][label_to_idx[l2]] += 1

    total = len(labels1)
    # Observed agreement P_o
    P_o = sum(conf[i][i] for i in range(n)) / total

    # Expected agreement P_e
    row_sums = [sum(conf[i]) for i in range(n)]
    col_sums = [sum(conf[i][j] for i in range(n)) for j in range(n)]
    P_e = sum(row_sums[i] * col_sums[i] for i in range(n)) / (total ** 2)

    kappa = (P_o - P_e) / (1 - P_e) if (1 - P_e) > 0 else 1.0

    print(f"\nInter-Annotator Agreement")
    print(f"  Shared pairs     : {len(shared_pairs)}")
    print(f"  Only in annot. 1 : {len(d1) - len(shared_pairs)}")
    print(f"  Only in annot. 2 : {len(d2) - len(shared_pairs)}")
    print(f"  P_observed       : {P_o:.3f}")
    print(f"  P_expected       : {P_e:.3f}")
    print(f"  Cohen's κ        : {kappa:.3f}  ", end='')
    if   kappa >= 0.80: print("(Almost perfect ✓)")
    elif kappa >= 0.70: print("(Substantial — acceptable for RST ✓)")
    elif kappa >= 0.60: print("(Moderate — borderline, discuss disagreements)")
    else:               print("(Fair/Poor — revision needed ✗)")

    # Disagreement analysis
    disagreements = [(k, d1[k], d2[k]) for k in shared_pairs if d1[k] != d2[k]]
    if disagreements:
        print(f"\n  Disagreements ({len(disagreements)}):")
        for pair, l1, l2 in disagreements[:10]:
            print(f"    {pair} → A1: {l1}, A2: {l2}")
        if len(disagreements) > 10:
            print(f"    ... and {len(disagreements)-10} more")

    return kappa


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def process_file(path, save=True):
    print(f"\n{'─'*60}")
    print(f"Validating: {path}")
    doc = load_doc(path)

    errors, warnings = validate(doc)

    if errors:
        print(f"\n  ✗ {len(errors)} ERROR(S):")
        for e in errors:
            print(f"    • {e}")
    else:
        print(f"  ✓ No structural errors")

    if warnings:
        print(f"\n  ⚠  {len(warnings)} WARNING(S):")
        for w in warnings:
            print(f"    • {w}")

    if not errors:
        doc = enrich_doc(doc)
        c = doc['computed']
        print(f"\n  Computed:")
        print(f"    Units: {c['n_units']}  ECUs: {c['n_ecus']}  Relations: {c['n_relations']}")
        print(f"    Total duration: {c['total_duration']}s")
        print(f"    Max orbit: {c['max_orbit']}")
        print(f"    Weight range: [{min(c['weights'].values()):.2f}, {max(c['weights'].values()):.2f}]")

        # Show weight table
        print(f"\n  Unit weights (sorted by importance):")
        all_u = {u['id']: u for u in doc.get('units', [])}
        all_u.update({e['id']: e for e in doc.get('ecus', [])})
        sorted_units = sorted(c['weights'].items(), key=lambda x: -x[1])
        for uid, w in sorted_units:
            u = all_u.get(uid, {})
            label = u.get('label', uid)[:45]
            utype = u.get('type', 'ECU' if 'ECU' in uid else '?')
            print(f"    {w:6.3f}  [{utype:<5}]  {label}")

        if save:
            save_doc(doc, path)
            print(f"\n  Saved (with computed fields): {path}")

    return len(errors) == 0


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    if args[0] == '--all' and len(args) >= 2:
        files = [f for f in Path(args[1]).glob('**/*.json')
                 if not f.name.startswith('_') and 'results' not in f.name]
        ok = sum(process_file(str(f)) for f in files)
        print(f"\n{'='*60}")
        print(f"Result: {ok}/{len(files)} documents valid")

    elif args[0] == '--stats' and len(args) >= 2:
        corpus_stats(args[1])

    elif args[0] == '--kappa' and len(args) >= 3:
        doc1 = load_doc(args[1])
        doc2 = load_doc(args[2])
        cohen_kappa(doc1, doc2)

    else:
        process_file(args[0])


if __name__ == '__main__':
    main()
