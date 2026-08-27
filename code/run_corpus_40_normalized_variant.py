"""
RhetConnect vs A_naive -- RANK-normalization variant (Limitation L3 check)

This is NOT the script that produces the paper's Tables 8-10. It is a
deliberate variant of run_corpus_40.py that normalizes the composite RANK
score (see validation notes) to check whether the un-normalized version
used in the main pipeline biases results. It is kept for transparency and
reproducibility of that specific check, not as an alternative "real"
result.

OUTPUT SAFETY: this writes to data/corpus_results_normalized_variant.json,
deliberately NOT data/corpus_results_final.json -- the latter is the
canonical file backing the paper's published tables and must never be
overwritten by this script. If you're refactoring paths, keep these two
outputs on different filenames; a shared path here previously caused this
script to silently corrupt the canonical results when run after
run_corpus_40.py (same directory, same default path logic).

REPRODUCIBILITY NOTE: reruns may show +/-0.001-0.004 drift in the CS/CSR
columns (3rd decimal only; RCR/OUC columns are exact) versus any
previously-saved run of this variant. This comes from Python's string-hash
randomization affecting the iteration order of the V_safe/closure sets
inside rhet_connect(), which changes the order of floating-point
summation (non-associative) when durations are accumulated. Not a bug.

KNOWN LIMITATION (see AUDIT_NOTES.md, applies to both this script and
run_corpus_40.py): the PRUNE step in rhet_connect() below enforces
Conditions C1 (satellite->nucleus) and C2 (ECU membership) but does NOT
enforce Condition C3 (semantic multinuclear group atomicity) as a hard
removal pass -- it only attempts group closure opportunistically during
SELECT (closure() pulls in co-nuclei, but budget can still cut a group in
half). As a result, checking RhetConnect's own corpus outputs against
strict RC (C1-C3) shows C3 violations in 67 of 120 pairs under the
un-normalized scoring; this variant exists to check whether normalizing
RANK changes that picture (see validation notes for the conclusion).
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent / "data"

def get_type(doc, uid):
    for u in doc.get('units', []):
        if u['id'] == uid: return u['type']
    return None

def ecu_esus_set(doc, ecu_id, _cache={}):
    key = (id(doc), ecu_id)
    if key not in _cache:
        s = set()
        for e in doc.get('ecus', []):
            if e['id'] == ecu_id:
                for m in e['members']:
                    if get_type(doc, m) is not None: s.add(m)
                    else: s |= ecu_esus_set(doc, m, _cache)
                break
        _cache[key] = s
    return _cache[key]

def build_indices(doc):
    sat_to_nuc = {}
    multi_grps = defaultdict(list)
    for r in doc.get('relations', []):
        if r['type'] == 'mononuclear':
            sat_to_nuc[r['satellite_id']] = r['nucleus_id']
        else:
            co = r['co_nuclei_ids']
            for c in co: multi_grps[c] = [x for x in co if x != c]
    return sat_to_nuc, multi_grps

def is_rc_weak(selected, doc):
    """RC check: Conditions 1 and 2 only (satellite -> nucleus chain)."""
    sel = set(selected)
    sat_to_nuc, _ = build_indices(doc)
    orphans = 0
    for uid in sel:
        if uid not in sat_to_nuc: continue
        nuc = sat_to_nuc[uid]
        if get_type(doc, nuc) is not None:
            if nuc not in sel: orphans += 1
        else:
            if not (ecu_esus_set(doc, nuc) & sel): orphans += 1
    return orphans == 0, orphans

def coverage(selected, doc):
    # Coverage = fraction of POSITIVE importance captured. A unit whose
    # computed weight is negative (edge case of the [Maredj et al. 2024]
    # formula for deeply-nested, high-orbit satellites with a low-weight
    # predecessor) contributes 0, not a negative amount, to numerator and
    # denominator alike.
    weights = doc.get('computed', {}).get('weights', {})
    tot = sum(max(w, 0.0) for w in weights.values())
    sel = sum(max(weights.get(u, 0.0), 0.0) for u in selected)
    return sel/tot if tot > 0 else 0.0

def a_naive(doc, M, budget):
    weights = doc.get('computed', {}).get('weights', {})
    cands = [(u['id'], weights.get(u['id'], 0.0), u['duration'])
             for u in doc.get('units', []) if u['type'] in M]
    cands.sort(key=lambda x: -x[1])
    sel = []; used = 0.0
    for uid, w, dur in cands:
        if used + dur <= budget + 1e-9:
            sel.append(uid); used += dur
    return sel, used

def rhet_connect(doc, M, budget, lam=None, alpha=0.7):
    if lam is None: lam = {t: 0.25 for t in ['text', 'image', 'video', 'audio']}
    weights = doc.get('computed', {}).get('weights', {})
    sat_to_nuc, multi_grps = build_indices(doc)
    V_M = {u['id'] for u in doc.get('units', []) if u['type'] in M}
    V_safe = set(V_M); changed = True
    while changed:
        changed = False; V_prev = set(V_safe)
        for uid in V_prev:
            if uid not in sat_to_nuc: continue
            nuc = sat_to_nuc[uid]
            if get_type(doc, nuc) is not None:
                if nuc not in V_prev: V_safe.discard(uid); changed = True
            else:
                if not (ecu_esus_set(doc, nuc) & V_prev): V_safe.discard(uid); changed = True
    def score(uid):
        t = get_type(doc, uid) or 'text'
        w_max = max((weights.get(u, 0.0) for u in V_safe), default=1.0)
        if w_max <= 0: w_max = 1.0
        return alpha * (weights.get(uid, 0) / w_max) + (1 - alpha) * lam.get(t, 0)
    V_ranked = sorted(V_safe, key=score, reverse=True)
    def closure(uid):
        cl = {uid}; wl = {uid}
        while wl:
            u = wl.pop()
            if u in sat_to_nuc:
                nuc = sat_to_nuc[u]
                if get_type(doc, nuc) is not None:
                    if nuc in V_safe and nuc not in cl: cl.add(nuc); wl.add(nuc)
                else:
                    for e in ecu_esus_set(doc, nuc):
                        if e in V_safe and e not in cl: cl.add(e); wl.add(e)
            for p in multi_grps.get(u, []):
                if p in V_safe and p not in cl: cl.add(p); wl.add(p)
        return cl
    sel = set(); used = 0.0
    for uid in V_ranked:
        must = closure(uid)
        delta = sum(next((u['duration'] for u in doc.get('units', []) if u['id'] == v), 0.0)
                    for v in must - sel)
        if used + delta <= budget + 1e-9: sel |= must; used += delta
    return list(sel), used

PROFILES = {
    'P1': {'M': {'image', 'video'}, 'frac': 0.50, 'lam': {'text':0.0,'image':0.5,'video':0.5,'audio':0.0}},
    'P2': {'M': {'text', 'image'},  'frac': 0.70, 'lam': {'text':0.6,'image':0.4,'video':0.0,'audio':0.0}},
    'P3': {'M': {'text','image','video','audio'}, 'frac': 0.80, 'lam': {'text':0.3,'image':0.3,'video':0.2,'audio':0.2}},
}

def main():
    docs = [json.load(open(f)) for f in sorted(BASE.glob("*.json"))
            if not f.name.startswith('_') and 'results' not in f.name]
    print(f"Loaded {len(docs)} documents")

    results = []
    for doc in docs:
        did = doc['doc_id']; total = doc['computed']['total_duration']
        for pname, profile in PROFILES.items():
            budget = total * profile['frac']; M, lam = profile['M'], profile['lam']
            sel_n, _ = a_naive(doc, M, budget)
            rc_n, ouc_n = is_rc_weak(sel_n, doc)
            cs_n = coverage(sel_n, doc)
            sel_r, _ = rhet_connect(doc, M, budget, lam)
            rc_r, ouc_r = is_rc_weak(sel_r, doc)
            cs_r = coverage(sel_r, doc)
            results.append({'doc': did, 'profile': pname,
                            'naive_rc': rc_n, 'naive_ouc': ouc_n, 'naive_cs': cs_n,
                            'rc_rc': rc_r, 'rc_ouc': ouc_r, 'rc_cs': cs_r})

    out = {'summary': {}, 'per_doc': results, 'n_docs': len(docs)}
    for p in ['P1', 'P2', 'P3']:
        rows = [r for r in results if r['profile'] == p]; n = len(rows)
        cs_n = sum(r['naive_cs'] for r in rows) / n
        cs_r = sum(r['rc_cs'] for r in rows) / n
        out['summary'][p] = {
            'naive_rcr': round(100 * sum(1 for r in rows if r['naive_rc']) / n, 1),
            'rc_rcr': round(100 * sum(1 for r in rows if r['rc_rc']) / n, 1),
            'naive_ouc': round(sum(r['naive_ouc'] for r in rows) / n, 2),
            'rc_ouc': round(sum(r['rc_ouc'] for r in rows) / n, 2),
            'naive_cs': round(cs_n, 3), 'rc_cs': round(cs_r, 3),
            'csr': round(cs_r / cs_n if cs_n > 0 else 1.0, 3)
        }
    with open(Path(__file__).resolve().parent.parent / 'data' / 'corpus_results_normalized_variant.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out['summary'], indent=2))
    print("Saved -> persistent storage")

if __name__ == '__main__':
    main()
