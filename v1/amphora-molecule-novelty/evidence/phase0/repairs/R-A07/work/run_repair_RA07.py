#!/usr/bin/env python3
"""R-A07 REPAIR compute -- amphora-molecule-novelty.

Builds the corrected diagnostic that supersedes (without modifying):
  (1) evidence/audit/cross-family-concordance-v1/cross-family-concordance-receipt.v1.dsse.json
  (2) evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json

Corrections carried:
  (a) corpus-duplicate-exchangeability-audit-v1 (2026-08-02): the 443-row OpenPoly
      calibration corpus has only 350 canonically-unique structures; the corrected
      family/alpha conformal table is computed on the DEDUPED (n=350) corpus, the 5
      signed cell flips are embedded, and DDS's cross-family count at alpha=0.05 is
      corrected from 1/4 to 0/4.
  (b) candidate-structure-identity-audit-v1 (2026-08-03): the signed IPDA
      candidate_smiles CC1(CC(CC(C1)N)C)CN canonicalizes to C9H20N2 (demethylated
      non-molecule). Corrected structure: real isophorone diamine
      3-(aminomethyl)-3,5,5-trimethylcyclohexan-1-amine (CAS 2855-13-2), derived
      independently here as NC1CC(C)(C)CC(C)(CN)C1, RDKit-verified C10H22N2, with
      Tanimoto-NN recomputed against the deduped corpus.

RE-ATTACK: re-runs both refuting checks against the corrected values and embeds the
observed results. Deterministic (no RNG); two-replay byte-stability enforced by the
signer. AUDIT pipeline is byte-identical to run_novelty_dedup_audit.py /
run_novelty_candidate_identity_audit.py conventions ('*'->'C' cap, Morgan r2/2048,
MACCS-166, AtomPair/2048, TopTorsion/2048, LOO conformal p=(#{a_i>=a_x}+1)/(n+1)).
"""
import csv, hashlib, json, sys
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import MACCSkeys, rdMolDescriptors
from rdkit.Chem import rdFingerprintGenerator as fpg
RDLogger.DisableLog('rdApp.*')

CSV = "/home/ubuntu/amphora/build/mvp20-split/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
CSV_SHA_EXPECTED = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
DEDUP_SET_SHA_EXPECTED = "74513e30071335d097ee83315f5b21249da86ea6a5d61e98a27d07b631593dce"
ALPHAS = [0.01, 0.05, 0.10, 0.20]

# Signed (superseded) candidate structures -- IPDA entry is the refuted one.
SIGNED_CANDS = {"IPDA": "CC1(CC(CC(C1)N)C)CN",
                "DDS": "NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
                "DETA": "NCCNCCN", "TETA": "NCCNCCNCCN",
                "m-XDA": "NCC1=CC=CC(=C1)CN"}

# Independent derivation of real isophorone diamine:
# 3-(aminomethyl)-3,5,5-trimethylcyclohexan-1-amine (CAS 2855-13-2):
# cyclohexane ring; C1 primary amine; C3 quaternary bearing aminomethyl + methyl;
# C5 gem-dimethyl.
IPDA_CORRECTED_INPUT = "NC1CC(C)(C)CC(C)(CN)C1"
IPDA_EXPECTED_FORMULA = "C10H22N2"
# Ground-truth canonical from amphora-molecule-generator known_answer_amines
# (Lee & Neville 1967), used by the refuting identity audit:
GENMOD_IPDA_CANONICAL = "CC1(C)CC(N)CC(C)(CN)C1"

CORRECTED_CANDS = dict(SIGNED_CANDS)
CORRECTED_CANDS["IPDA"] = IPDA_CORRECTED_INPUT

# Values signed in the superseded KPI (Morgan r2/2048 monomer lane):
SIGNED_BASELINE_NN = {"IPDA": 0.16666666666666666, "DDS": 0.39285714285714285,
                      "DETA": 0.16666666666666666, "TETA": 0.15789473684210525,
                      "m-XDA": 0.23809523809523808}
# Corrected-IPDA NN reported by the refuting identity audit (vs 443 corpus):
REFUTING_RECEIPT_IPDA_CORRECTED_NN = 0.16666666666666666
# The 5 flip cells reported by the refuting dedup audit (family, candidate, alpha):
REFUTING_RECEIPT_FLIP_CELLS = [
    ["atompair_2048", "DDS", "a0.2"], ["atompair_2048", "IPDA", "a0.01"],
    ["atompair_2048", "m-XDA", "a0.01"], ["maccs_166", "DDS", "a0.05"],
    ["maccs_166", "IPDA", "a0.01"]]

FAMILIES = ["morgan_r2_2048", "maccs_166", "atompair_2048", "toptorsion_2048"]
_MG = fpg.GetMorganGenerator(radius=2, fpSize=2048)
_AP = fpg.GetAtomPairGenerator(fpSize=2048)
_TT = fpg.GetTopologicalTorsionGenerator(fpSize=2048)

def sha(b): return hashlib.sha256(b).hexdigest()
def has(v): return v is not None and str(v).strip() != ""
def cap(s): return s.replace("*", "C")

def make_fp(mol, kind):
    if kind == "morgan_r2_2048": return _MG.GetFingerprint(mol)
    if kind == "maccs_166":      return MACCSkeys.GenMACCSKeys(mol)
    if kind == "atompair_2048":  return _AP.GetFingerprint(mol)
    if kind == "toptorsion_2048": return _TT.GetFingerprint(mol)
    raise ValueError(kind)

raw = open(CSV, "rb").read()
csv_sha = sha(raw)
assert csv_sha == CSV_SHA_EXPECTED, f"CSV sha mismatch {csv_sha}"
rows = list(csv.DictReader(open(CSV)))

corpus_all = []
for r in rows:
    if not has(r.get("Tg (K)")): continue
    smi = cap(r["PSMILES"]); m = Chem.MolFromSmiles(smi)
    if m is None: continue
    corpus_all.append((r["Name"], smi, m))
n_all = len(corpus_all)

canon2names = {}
for name, smi, m in corpus_all:
    canon2names.setdefault(Chem.MolToSmiles(m), []).append(name)
dupe_groups = {k: v for k, v in canon2names.items() if len(v) > 1}
n_unique = len(canon2names)
n_dupe_rows = sum(len(v) for v in dupe_groups.values())

seen = set(); corpus_dedupe = []
for name, smi, m in corpus_all:
    cs = Chem.MolToSmiles(m)
    if cs in seen: continue
    seen.add(cs); corpus_dedupe.append((name, smi, m))
n_dedupe = len(corpus_dedupe)
dedup_set_sha = sha("\n".join(sorted(Chem.MolToSmiles(m) for _, _, m in corpus_dedupe)).encode())
assert dedup_set_sha == DEDUP_SET_SHA_EXPECTED, f"dedup set sha mismatch {dedup_set_sha}"
assert n_all == 443 and n_unique == 350 and n_dupe_rows == 129 and len(dupe_groups) == 36

def nn_info(test_fp, ref, skip_idx=None):
    best, best_name = 0.0, None
    for j, (nm, f) in enumerate(ref):
        if j == skip_idx: continue
        s = DataStructs.TanimotoSimilarity(test_fp, f)
        if s > best: best, best_name = s, nm
    return best, best_name

def conformal_p(alpha_x, calib):
    return (sum(1 for a in calib if a >= alpha_x) + 1) / (len(calib) + 1)

def build_and_eval(kind, corpus, cands):
    ref = [(nm, make_fp(m, kind)) for nm, _, m in corpus]
    n = len(ref)
    calib_nn = [nn_info(ref[i][1], ref, skip_idx=i)[0] for i in range(n)]
    calib_alpha = [1.0 - s for s in calib_nn]
    out = {}
    for name, smi in cands.items():
        mol = Chem.MolFromSmiles(smi); assert mol is not None
        fp = make_fp(mol, kind)
        nn, nn_name = nn_info(fp, ref)
        alpha_x = 1.0 - nn
        p = conformal_p(alpha_x, calib_alpha)
        out[name] = {"nn_tanimoto": nn, "nn_reference_name": nn_name, "alpha": alpha_x,
                     "conformal_p": p,
                     "isolated_count": sum(1 for a in calib_alpha if a >= alpha_x),
                     "n": n, "novel_by_alpha": {f"a{a}": (p < a) for a in ALPHAS}}
    return out, calib_nn

# ---- (1) corrected family/alpha table on DEDUPED corpus (signed candidate set,
#      to reproduce and correct the superseded cross-family accounting) ----
contaminated, deduped = {}, {}
morgan_loo_dedup = None
for kind in FAMILIES:
    contaminated[kind], _ = build_and_eval(kind, corpus_all, SIGNED_CANDS)
    deduped[kind], loo_nn = build_and_eval(kind, corpus_dedupe, SIGNED_CANDS)
    if kind == "morgan_r2_2048":
        morgan_loo_dedup = loo_nn

# anchor: contaminated morgan lane must reproduce the signed NN exactly
anchor_exact_all = all(
    abs(contaminated["morgan_r2_2048"][k]["nn_tanimoto"] - v) < 1e-12
    for k, v in SIGNED_BASELINE_NN.items())
assert anchor_exact_all, "anchor reproduction failed"

# embedded old->new cell flips
flip_cells = []
for kind in FAMILIES:
    for name in SIGNED_CANDS:
        c, d = contaminated[kind][name], deduped[kind][name]
        for a in ALPHAS:
            key = f"a{a}"
            if c["novel_by_alpha"][key] != d["novel_by_alpha"][key]:
                flip_cells.append({
                    "family": kind, "candidate": name, "alpha": key,
                    "old_signed_verdict_contaminated_443": c["novel_by_alpha"][key],
                    "new_corrected_verdict_deduped_350": d["novel_by_alpha"][key],
                    "old_conformal_p": c["conformal_p"], "new_conformal_p": d["conformal_p"]})
flip_cells.sort(key=lambda x: (x["family"], x["candidate"], x["alpha"]))
observed_flip_triples = sorted([f["family"], f["candidate"], f["alpha"]] for f in flip_cells)
flips_match_refuting_receipt = observed_flip_triples == sorted(REFUTING_RECEIPT_FLIP_CELLS)

dds_n_novel_a05_old = sum(1 for k in FAMILIES if contaminated[k]["DDS"]["novel_by_alpha"]["a0.05"])
dds_n_novel_a05_new = sum(1 for k in FAMILIES if deduped[k]["DDS"]["novel_by_alpha"]["a0.05"])
assert dds_n_novel_a05_old == 1 and dds_n_novel_a05_new == 0

# ---- (2) corrected IPDA structure ----
old_mol = Chem.MolFromSmiles(SIGNED_CANDS["IPDA"])
old_canonical = Chem.MolToSmiles(old_mol)
old_formula = rdMolDescriptors.CalcMolFormula(old_mol)
new_mol = Chem.MolFromSmiles(IPDA_CORRECTED_INPUT)
assert new_mol is not None
new_canonical = Chem.MolToSmiles(new_mol)
new_formula = rdMolDescriptors.CalcMolFormula(new_mol)
formula_check_pass = (new_formula == IPDA_EXPECTED_FORMULA)
assert formula_check_pass, f"formula {new_formula} != {IPDA_EXPECTED_FORMULA}"
matches_genmod_ground_truth = (
    new_canonical == Chem.MolToSmiles(Chem.MolFromSmiles(GENMOD_IPDA_CANONICAL)))
assert matches_genmod_ground_truth
old_formula_refutation_reproduced = (old_formula == "C9H20N2")

# corrected-IPDA Morgan NN vs DEDUPED corpus (the repair lane) + vs 443 for x-check
morgan_ref_dedup = [(nm, _MG.GetFingerprint(m)) for nm, _, m in corpus_dedupe]
morgan_ref_all = [(nm, _MG.GetFingerprint(m)) for nm, _, m in corpus_all]
ipda_fp = _MG.GetFingerprint(new_mol)
ipda_nn_dedup, ipda_nn_dedup_name = nn_info(ipda_fp, morgan_ref_dedup)
ipda_nn_443, _ = nn_info(ipda_fp, morgan_ref_all)
ipda_nn_below_cutoff = ipda_nn_dedup < 0.40
ipda_nn_consistent_with_refuting_receipt = (
    abs(ipda_nn_dedup - REFUTING_RECEIPT_IPDA_CORRECTED_NN) < 1e-12
    and abs(ipda_nn_443 - REFUTING_RECEIPT_IPDA_CORRECTED_NN) < 1e-12)

# ---- (3) top-level 5/5 table: corrected candidate set vs deduped corpus ----
corrected_top, _ = build_and_eval("morgan_r2_2048", corpus_dedupe, CORRECTED_CANDS)
five_over_five = {}
for name in sorted(CORRECTED_CANDS):
    e = corrected_top[name]
    five_over_five[name] = {
        "candidate_smiles_canonical": Chem.MolToSmiles(Chem.MolFromSmiles(CORRECTED_CANDS[name])),
        "nn_tanimoto_vs_deduped_350": e["nn_tanimoto"],
        "nn_reference_name": e["nn_reference_name"],
        "novel_below_0_40": e["nn_tanimoto"] < 0.40}
n_novel = sum(1 for v in five_over_five.values() if v["novel_below_0_40"])
assert n_novel == 5

loo = sorted(morgan_loo_dedup)
def pct(q):
    i = (len(loo) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(loo) - 1)
    return loo[lo] + (loo[hi] - loo[lo]) * (i - lo)
loo_stats = {"n": len(loo), "min": loo[0], "max": loo[-1],
             "mean": sum(loo) / len(loo), "median": pct(0.5), "p5": pct(0.05),
             "p25": pct(0.25), "p75": pct(0.75), "p95": pct(0.95)}

self_tests = [
    {"name": "csv_sha_locked", "pass": csv_sha == CSV_SHA_EXPECTED},
    {"name": "dedup_counts_443_350_129_36", "pass": n_all == 443 and n_unique == 350
        and n_dupe_rows == 129 and len(dupe_groups) == 36},
    {"name": "dedup_canonical_set_sha_matches_refuting_receipt",
     "pass": dedup_set_sha == DEDUP_SET_SHA_EXPECTED},
    {"name": "anchor_morgan_contaminated_reproduces_signed_nn_exact", "pass": anchor_exact_all},
    {"name": "five_flip_cells_match_refuting_receipt",
     "pass": len(flip_cells) == 5 and flips_match_refuting_receipt},
    {"name": "dds_cross_family_a05_corrected_1_of_4_to_0_of_4",
     "pass": dds_n_novel_a05_old == 1 and dds_n_novel_a05_new == 0},
    {"name": "old_ipda_smiles_refutation_reproduced_C9H20N2",
     "pass": old_formula_refutation_reproduced},
    {"name": "corrected_ipda_rdkit_formula_C10H22N2", "pass": formula_check_pass},
    {"name": "corrected_ipda_matches_independent_genmod_ground_truth",
     "pass": matches_genmod_ground_truth},
    {"name": "corrected_ipda_nn_below_0_40_cutoff", "pass": ipda_nn_below_cutoff},
    {"name": "corrected_ipda_nn_consistent_with_refuting_receipt_1e-12",
     "pass": ipda_nn_consistent_with_refuting_receipt},
    {"name": "five_of_five_novel_under_both_corrections", "pass": n_novel == 5},
]
assert all(t["pass"] for t in self_tests)

diag = {
    "study_id": "r-a07-novelty-dedup-and-ipda-identity-repair-v1",
    "schema": "amphora.molecule-novelty.r-a07-superseding-repair-receipt.v1",
    "repair_item": "R-A07", "repair_mode": "interactive-2026-08-03",
    "date": "2026-08-03", "rdkit_version": "2026.03.2",
    "statement": (
        "5/5 NOVEL stands under both corrections, and the exchangeability precondition is "
        "now satisfied: (1) the conformal family/alpha table is recomputed on the "
        "canonically-deduplicated 350-structure OpenPoly calibration corpus (dedup set "
        "sha256 " + dedup_set_sha + "), flipping 5 previously-signed family/alpha cells "
        "(DDS, IPDA, m-XDA) and correcting DDS's cross-family count at alpha=0.05 from "
        "1/4 to 0/4; (2) the IPDA candidate structure is corrected from the demethylated "
        "C9H20N2 string to real isophorone diamine (CAS 2855-13-2, C10H22N2, canonical "
        + new_canonical + "), whose recomputed Morgan(r2,2048) Tanimoto-NN vs the deduped "
        "corpus is " + repr(ipda_nn_dedup) + " -- unchanged from the signed value and below "
        "the 0.40 Bajusz-Racz-Heberger novelty cutoff. All 5 candidates remain NOVEL "
        "(NN 0.1579-0.3929) on the deduped corpus with the corrected IPDA structure."),
    "method": (
        "Identical pipeline to the refuting audits: '*'->'C' methyl cap; canonical RDKit "
        "SMILES dedup (structure-only, label-free); families morgan_r2_2048/maccs_166/"
        "atompair_2048/toptorsion_2048; LOO nonconformity alpha_i=1-NN_LOO(i); candidate "
        "alpha_x=1-max_j Tanimoto; conformal p=(#{alpha_i>=alpha_x}+1)/(n+1); NOVEL iff "
        "p<alpha, alpha in {0.01,0.05,0.10,0.20}; fixed-cutoff lane: NOVEL iff Morgan NN "
        "Tanimoto < 0.40."),
    "corpus": {
        "csv_sha256": csv_sha,
        "source": "OpenPoly final_polymer_properties_fromliterature.csv (Ma et al. 2023)",
        "rights": "CC-BY rights-clean OpenPoly benchmark (locked, read-only)",
        "n_rows_with_Tg": n_all, "n_canonically_unique_structures": n_unique,
        "n_duplicate_rows": n_dupe_rows, "n_duplicate_groups": len(dupe_groups),
        "deduped_corpus_canonical_set_sha256": dedup_set_sha,
        "wildcard_cap": "'*'->'C' (methyl end-cap, reproduces signed featurization)"},
    "corrected_family_alpha_table_deduped_350": deduped,
    "embedded_cell_flips_old_to_new": flip_cells,
    "n_flip_cells": len(flip_cells),
    "dds_cross_family_count_a05": {
        "superseded_signed_value": "1/4 (maccs_166 only)",
        "corrected_value": "0/4",
        "old_n_novel_of_4": dds_n_novel_a05_old, "new_n_novel_of_4": dds_n_novel_a05_new},
    "corrected_ipda": {
        "superseded_smiles": SIGNED_CANDS["IPDA"],
        "superseded_canonical": old_canonical, "superseded_formula": old_formula,
        "corrected_input_smiles": IPDA_CORRECTED_INPUT,
        "corrected_canonical": new_canonical, "corrected_formula": new_formula,
        "iupac_name": "3-(aminomethyl)-3,5,5-trimethylcyclohexan-1-amine",
        "cas": "2855-13-2",
        "derivation": ("Independently derived from the Lee & Neville 1967 isophorone "
                       "diamine constitution: cyclohexane ring, C1 primary amine, C3 "
                       "quaternary carbon bearing aminomethyl and methyl, C5 gem-dimethyl "
                       "-> NC1CC(C)(C)CC(C)(CN)C1; RDKit canonical form equals the "
                       "amphora-molecule-generator known_answer_amines ground truth."),
        "matches_genmod_ground_truth_canonical": matches_genmod_ground_truth,
        "rdkit_formula_check_pass": formula_check_pass,
        "recomputed_nn_tanimoto_vs_deduped_350": ipda_nn_dedup,
        "recomputed_nn_tanimoto_vs_contaminated_443": ipda_nn_443,
        "nn_reference_name": ipda_nn_dedup_name,
        "below_0_40_cutoff": ipda_nn_below_cutoff,
        "consistent_with_refuting_receipt_corrected_nn":
            ipda_nn_consistent_with_refuting_receipt},
    "top_level_five_over_five_corrected": {
        "lane": "morgan_r2_2048 Tanimoto fixed 0.40 cutoff, deduped 350-structure corpus, corrected IPDA structure",
        "per_candidate": five_over_five, "n_candidates": 5, "n_novel": n_novel,
        "verdict": "5/5 NOVEL stands under both corrections"},
    "reference_LOO_NN_distribution_deduped_morgan": loo_stats,
    "reattack": {
        "note": ("Re-ran the checks from both refuting receipts against this repair's "
                 "corrected values; all reproduce and the corrections hold."),
        "dedup_audit_reattack": {
            "dedup_counts_reproduced_443_350_129_36": True,
            "dedup_set_sha256_matches": dedup_set_sha == DEDUP_SET_SHA_EXPECTED,
            "anchor_morgan_reproduces_signed_nn_exact": anchor_exact_all,
            "observed_flip_cells": observed_flip_triples,
            "flip_cells_match_refuting_receipt": flips_match_refuting_receipt,
            "dds_maccs_a05_contaminated_true_deduped_false":
                contaminated["maccs_166"]["DDS"]["novel_by_alpha"]["a0.05"] is True
                and deduped["maccs_166"]["DDS"]["novel_by_alpha"]["a0.05"] is False,
            "dds_n_novel_of_4_a05_old_1_new_0":
                dds_n_novel_a05_old == 1 and dds_n_novel_a05_new == 0,
            "morgan_family_no_flips_at_any_alpha": all(
                contaminated["morgan_r2_2048"][n]["novel_by_alpha"] ==
                deduped["morgan_r2_2048"][n]["novel_by_alpha"] for n in SIGNED_CANDS)},
        "identity_audit_reattack": {
            "old_ipda_canonicalizes_to_C9H20N2": old_formula_refutation_reproduced,
            "corrected_ipda_canonicalizes_to_C10H22N2": formula_check_pass,
            "corrected_ipda_equals_independent_ground_truth": matches_genmod_ground_truth,
            "recomputed_nn_equals_refuting_receipt_corrected_nn_1e-12":
                ipda_nn_consistent_with_refuting_receipt,
            "recomputed_nn_value": ipda_nn_dedup,
            "stays_below_0_40": ipda_nn_below_cutoff,
            "classification_flip": False}},
    "self_tests": self_tests,
    "self_tests_all_pass": all(t["pass"] for t in self_tests),
    "theory_reference": [
        "Vovk, Gammerman, Shafer 2005, Algorithmic Learning in a Random World, ISBN 978-0-387-00152-4, sec 2.1 (exchangeability)",
        "Rogers & Hahn 2010, J Chem Inf Model 50:742, DOI:10.1021/ci100050t (Morgan/ECFP)",
        "Bajusz, Racz, Heberger 2015, J Cheminform 7:20, DOI:10.1186/s13321-015-0069-3 (Tanimoto; 0.40 cutoff)",
        "Durant et al. 2002 DOI:10.1021/ci010132r; Carhart et al. 1985 DOI:10.1021/ci00046a002; Nilakantan et al. 1987 DOI:10.1021/ci00054a008",
        "Lee, H. & Neville, K. 1967, Handbook of Epoxy Resins, McGraw-Hill (isophorone diamine constitution)",
        "Ma et al. 2023 OpenPoly / OMG_PhysicalProperties dataset"],
    "rights_posture": ("AUDIT/REPAIR artifact. External corpus SHA-256-locked, "
                       "rights-clean, read-only. No manifest, ledger, locked dataset, or "
                       "existing signed receipt modified; supersession by NEW receipt only."),
}

if __name__ == "__main__":
    out = json.dumps(diag, indent=2, sort_keys=True)
    dest = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    open(dest, "w").write(out)
    print(f"wrote {dest} self_tests_all_pass={diag['self_tests_all_pass']} "
          f"n_flip_cells={len(flip_cells)} ipda_nn={ipda_nn_dedup} n_novel={n_novel}")
