#!/usr/bin/env python3
"""amphora-molecule-novelty AUDIT_ONLY -- SECOND-CORPUS NOVELTY ATTACK (W-D-NOV).

Every signed novelty verdict for the 5 canonical DGEBA-based epoxy amine
hardener candidates (IPDA, DDS, DETA, TETA, m-XDA) is measured against a
SINGLE reference corpus: the OpenPoly literature dataset (Ma et al. 2023),
443 rows / 350 canonically-distinct structures after R-A07's dedup repair.
A novelty score against one corpus is a statement about that corpus, not
about novelty in general -- this is the exact claim the W-D-NOV campaign
item targets.

THIS ATTACK acquires a second, independent, rights-clean structure corpus
-- PolyInfo_p.csv from the PolyUniverse dataset (Yue, T. 2024, Zenodo
10.5281/zenodo.12585902, CC-BY-4.0, license id "cc-by-4.0" per the Zenodo
REST API) -- and re-runs the identical Morgan(r2,2048) Tanimoto-NN novelty
pipeline used by the signed KPI
(tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json)
against it. PolyInfo_p.csv (12,400 PSMILES rows) is the real, literature-
sourced NIMS PolyInfo polymer set PolyUniverse used as one of its two
"real" reference libraries (as opposed to its GDB-13/17 and PubChem
*virtual* generated-candidate files, which are excluded from this analysis
because they are not independent reference structures -- they are
combinatorially enumerated from fragment rules and would not constitute an
independent corpus).

FALSIFICATION LOGIC: if any of the 5 candidates classified NOVEL
(NN Tanimoto < 0.40, Bajusz-Racz-Heberger 2015) against the OpenPoly-350
corpus has NN Tanimoto >= 0.40 against PolyInfo, the "5/5 NOVEL" claim does
NOT generalize beyond the single OpenPoly corpus and is REFUTED as a
general novelty statement (though it may still hold vs OpenPoly alone).
If all 5 remain below 0.40 against the independent corpus too, the novelty
claim survives a genuinely capable second-corpus attack.

We also report the corpus-level Tanimoto NN overlap between OpenPoly-350
and PolyInfo-dedup, i.e. how much the two corpora structurally overlap
(near-duplicate rate at T>=0.95), which the campaign item explicitly asks
for as a measure of corpus independence.

Non-circularity: OpenPoly corpus is the same SHA-256-locked, rights-clean,
read-only CSV used by all prior novelty receipts; dedup key is canonical
RDKit SMILES only. PolyInfo corpus is downloaded fresh, SHA-256-locked in
this receipt, canonicalized the same way. Featurization is byte-identical
to the signed KPI (Morgan r2/2048, RDKit rdFingerprintGenerator). Fully
deterministic (no RNG) => trivially byte-stable across replays.
AUDIT_ONLY: touches no manifest, no locked dataset, no signed Phase-0 KPI.
"""
import csv, hashlib, json, sys
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator as fpg
RDLogger.DisableLog('rdApp.*')

OPENPOLY_CSV = "/home/ubuntu/amphora/build/mvp20-split/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
OPENPOLY_CSV_SHA_EXPECTED = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
OPENPOLY_DEDUP_SHA_EXPECTED = "74513e30071335d097ee83315f5b21249da86ea6a5d61e98a27d07b631593dce"

POLYINFO_CSV = sys.argv[1] if len(sys.argv) > 1 else "/tmp/w-d-nov-fire2/PolyInfo_p.csv"
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else "/tmp/w-d-nov-fire2/diagnostic.canonical.json"

CANDS = {"IPDA":"CC1(CC(CC(C1)N)C)CN","DDS":"NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
 "DETA":"NCCNCCN","TETA":"NCCNCCNCCN","m-XDA":"NCC1=CC=CC(=C1)CN"}
SIGNED_BASELINE_NN = {"IPDA":0.16666666666666666,"DDS":0.39285714285714285,
 "DETA":0.16666666666666666,"TETA":0.15789473684210525,"m-XDA":0.23809523809523808}
NOVELTY_THRESHOLD = 0.40

_MG = fpg.GetMorganGenerator(radius=2, fpSize=2048)

def sha(b): return hashlib.sha256(b).hexdigest()
def has(v): return v is not None and str(v).strip()!=""
def cap(s): return s.replace("*","C")
def fp(mol): return _MG.GetFingerprint(mol)

def load_openpoly():
    raw = open(OPENPOLY_CSV,"rb").read()
    csv_sha = sha(raw)
    assert csv_sha == OPENPOLY_CSV_SHA_EXPECTED, f"OpenPoly CSV sha mismatch {csv_sha}"
    rows = list(csv.DictReader(open(OPENPOLY_CSV)))
    corpus_all = []
    for r in rows:
        if not has(r.get("Tg (K)")): continue
        smi = cap(r["PSMILES"]); m = Chem.MolFromSmiles(smi)
        if m is None: continue
        corpus_all.append((r["Name"], smi, m))
    seen = set(); dedupe = []
    for name, smi, m in corpus_all:
        cs = Chem.MolToSmiles(m)
        if cs in seen: continue
        seen.add(cs); dedupe.append((name, smi, m))
    dedupe_sha = sha("\n".join(sorted(Chem.MolToSmiles(m) for _,_,m in dedupe)).encode())
    assert dedupe_sha == OPENPOLY_DEDUP_SHA_EXPECTED, f"OpenPoly dedup sha mismatch {dedupe_sha} != {OPENPOLY_DEDUP_SHA_EXPECTED}"
    return len(rows), len(corpus_all), dedupe, csv_sha, dedupe_sha

def load_polyinfo():
    raw = open(POLYINFO_CSV,"rb").read()
    csv_sha = sha(raw)
    rows = list(csv.DictReader(open(POLYINFO_CSV)))
    n_rows = len(rows)
    corpus_all = []
    n_parse_fail = 0
    for i, r in enumerate(rows):
        smi_raw = r.get("Smiles")
        if not has(smi_raw): continue
        smi = cap(smi_raw)
        m = Chem.MolFromSmiles(smi)
        if m is None:
            n_parse_fail += 1
            continue
        corpus_all.append((f"PolyInfo_{i}", smi, m))
    n_parsed = len(corpus_all)
    seen = set(); dedupe = []
    for name, smi, m in corpus_all:
        cs = Chem.MolToSmiles(m)
        if cs in seen: continue
        seen.add(cs); dedupe.append((name, smi, m))
    dedupe_sha = sha("\n".join(sorted(Chem.MolToSmiles(m) for _,_,m in dedupe)).encode())
    return n_rows, n_parsed, n_parse_fail, dedupe, csv_sha, dedupe_sha

def nn_similarity(test_fp, ref_fps, skip_idx=None):
    best = 0.0; best_j = -1
    for j, f in enumerate(ref_fps):
        if j == skip_idx: continue
        s = DataStructs.TanimotoSimilarity(test_fp, f)
        if s > best: best = s; best_j = j
    return best, best_j

def main():
    n_openpoly_raw, n_openpoly_labeled, openpoly_dedupe, openpoly_csv_sha, openpoly_dedupe_sha = load_openpoly()
    n_polyinfo_rows, n_polyinfo_parsed, n_polyinfo_parsefail, polyinfo_dedupe, polyinfo_csv_sha, polyinfo_dedupe_sha = load_polyinfo()

    openpoly_fps = [fp(m) for _,_,m in openpoly_dedupe]
    polyinfo_fps = [fp(m) for _,_,m in polyinfo_dedupe]

    # 1) corpus-level overlap: for each OpenPoly-350 structure, NN in PolyInfo-dedup
    overlap = []
    for idx, (name, smi, m) in enumerate(openpoly_dedupe):
        best, bj = nn_similarity(openpoly_fps[idx], polyinfo_fps)
        overlap.append({"openpoly_name": name, "openpoly_smiles": smi,
                         "nn_tanimoto_vs_polyinfo": best,
                         "polyinfo_nn_name": polyinfo_dedupe[bj][0] if bj>=0 else None,
                         "polyinfo_nn_smiles": polyinfo_dedupe[bj][1] if bj>=0 else None})
    overlap_vals = sorted(o["nn_tanimoto_vs_polyinfo"] for o in overlap)
    n = len(overlap_vals)
    def pct(p):
        if n==0: return None
        k = min(n-1, int(p*n))
        return overlap_vals[k]
    n_near_dup_ge_95 = sum(1 for v in overlap_vals if v >= 0.95)
    n_exact_1_0 = sum(1 for v in overlap_vals if v >= 1.0 - 1e-12)
    overlap_summary = {
        "n_openpoly_structures": n,
        "n_polyinfo_reference": len(polyinfo_dedupe),
        "mean": sum(overlap_vals)/n if n else None,
        "median": pct(0.5), "p5": pct(0.05), "p25": pct(0.25), "p75": pct(0.75), "p95": pct(0.95),
        "min": overlap_vals[0] if n else None, "max": overlap_vals[-1] if n else None,
        "n_near_duplicate_T_ge_0_95": n_near_dup_ge_95,
        "n_exact_structural_match_T_eq_1_0": n_exact_1_0,
        "frac_near_duplicate": n_near_dup_ge_95 / n if n else None,
    }

    # 2) candidate re-test: NN Tanimoto vs PolyInfo-dedup alone, and vs UNION(OpenPoly-350, PolyInfo-dedup)
    union_fps = openpoly_fps + polyinfo_fps
    union_names = [nm for nm,_,_ in openpoly_dedupe] + [nm for nm,_,_ in polyinfo_dedupe]
    cand_results = {}
    flips = {}
    for name, smi in CANDS.items():
        mol = Chem.MolFromSmiles(smi); assert mol is not None
        f = fp(mol)
        nn_openpoly, j_op = nn_similarity(f, openpoly_fps)
        nn_polyinfo, j_pi = nn_similarity(f, polyinfo_fps)
        nn_union, j_un = nn_similarity(f, union_fps)
        signed_nn = SIGNED_BASELINE_NN[name]
        anchor_exact = abs(nn_openpoly - signed_nn) < 1e-12
        novel_openpoly = nn_openpoly < NOVELTY_THRESHOLD
        novel_polyinfo = nn_polyinfo < NOVELTY_THRESHOLD
        novel_union = nn_union < NOVELTY_THRESHOLD
        cand_results[name] = {
            "candidate_smiles": smi,
            "nn_tanimoto_vs_openpoly_350": nn_openpoly,
            "openpoly_nn_match": openpoly_dedupe[j_op][0] if j_op>=0 else None,
            "anchor_exact_match_to_signed_kpi": anchor_exact,
            "nn_tanimoto_vs_polyinfo_dedup": nn_polyinfo,
            "polyinfo_nn_match": polyinfo_dedupe[j_pi][0] if j_pi>=0 else None,
            "polyinfo_nn_match_smiles": polyinfo_dedupe[j_pi][1] if j_pi>=0 else None,
            "nn_tanimoto_vs_union_corpus": nn_union,
            "union_nn_match": union_names[j_un] if j_un>=0 else None,
            "novel_vs_openpoly_350": novel_openpoly,
            "novel_vs_polyinfo_dedup": novel_polyinfo,
            "novel_vs_union_corpus": novel_union,
        }
        flip = (novel_openpoly != novel_union)
        flips[name] = flip

    n_flips = sum(1 for v in flips.values() if v)
    all_survive_union = all(cand_results[n]["novel_vs_union_corpus"] for n in CANDS)
    anchor_ok = all(cand_results[n]["anchor_exact_match_to_signed_kpi"] for n in CANDS)

    out = {
        "attack_id": "amphora-molecule-novelty-w-d-nov-second-corpus-novelty-attack-v1",
        "claim_under_attack": "amphora-molecule-novelty/evidence/ :: Novelty claims rest on more than one reference corpus (signed KPI: 5/5 canonical epoxy-amine candidates NOVEL, NN Tanimoto < 0.40, vs OpenPoly-only corpus)",
        "refutation_criterion": "Any of the 5 canonical candidates (IPDA, DDS, DETA, TETA, m-XDA), classified NOVEL (NN Tanimoto < 0.40) against the OpenPoly-350 corpus alone, flips to NOT-NOVEL (NN Tanimoto >= 0.40) when the reference corpus is the union of OpenPoly-350 and the independent PolyInfo-dedup corpus.",
        "second_corpus": {
            "source": "PolyUniverse: Generation Results (Yue, T. et al. 2024) -- file PolyInfo_p.csv",
            "url": "https://zenodo.org/records/12585902",
            "doi": "10.5281/zenodo.12585902",
            "license_verbatim": "{'id': 'cc-by-4.0'}",
            "license_source": "https://zenodo.org/api/records/12585902 (metadata.license field, fetched live this fire)",
            "file_sha256": polyinfo_csv_sha,
            "file_md5_dryad_or_zenodo_reported": "n/a (Zenodo record; no md5 field returned by API for this file)",
            "underlying_real_source_note": "PolyInfo_p.csv is PolyUniverse's export of real, literature-sourced NIMS PolyInfo polymer structures (PSMILES) used as their reference/seed library -- NOT one of PolyUniverse's GDB-13/17 or PubChem *virtual* combinatorially-generated candidate files, which were excluded from this analysis as not independent reference structures.",
            "n_rows_raw": n_polyinfo_rows,
            "n_rows_smiles_parsed": n_polyinfo_parsed,
            "n_parse_failures": n_polyinfo_parsefail,
            "n_canonically_unique_structures_after_dedup": len(polyinfo_dedupe),
            "n_duplicate_rows_removed_by_dedup": n_polyinfo_parsed - len(polyinfo_dedupe),
        },
        "openpoly_corpus_recap": {
            "csv_sha256": openpoly_csv_sha,
            "n_rows_raw": n_openpoly_raw,
            "n_rows_with_Tg": n_openpoly_labeled,
            "n_canonically_unique_structures_after_dedup": len(openpoly_dedupe),
            "dedup_canonical_set_sha256": openpoly_dedupe_sha,
            "dedup_sha256_matches_r_a07_signed_value": openpoly_dedupe_sha == OPENPOLY_DEDUP_SHA_EXPECTED,
        },
        "corpus_cross_overlap": overlap_summary,
        "candidate_second_corpus_retest": cand_results,
        "anchor_check_openpoly_nn_matches_signed_kpi_exactly": anchor_ok,
        "n_candidates_flipped_novel_to_not_novel_under_union_corpus": n_flips,
        "all_5_survive_union_corpus_novelty_below_0_40": all_survive_union,
        "novelty_threshold_source": "Bajusz-Rácz-Héberger 2015 J. Cheminform. DOI:10.1186/s13321-015-0069-3",
        "featurization": {"fingerprint_method": "Morgan/ECFP", "morgan_bits": 2048, "morgan_radius": 2,
                           "similarity_method": "Tanimoto (Jaccard on bit sets)",
                           "generator": "rdkit.Chem.rdFingerprintGenerator.GetMorganGenerator", "rdkit_version": __import__("rdkit").__version__},
    }
    json.dump(out, open(OUT_PATH,"w"), indent=None, sort_keys=True)
    print(json.dumps({"status":"ok",
                       "n_flips": n_flips,
                       "all_5_survive": all_survive_union,
                       "anchor_ok": anchor_ok,
                       "overlap_median": overlap_summary["median"],
                       "overlap_frac_near_dup": overlap_summary["frac_near_duplicate"]}, indent=2))

if __name__ == "__main__":
    main()
