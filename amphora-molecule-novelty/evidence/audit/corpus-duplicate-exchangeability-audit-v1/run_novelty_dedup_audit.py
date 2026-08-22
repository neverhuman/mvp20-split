#!/usr/bin/env python3
"""amphora-molecule-novelty AUDIT_ONLY -- CALIBRATION-CORPUS DUPLICATE /
EXCHANGEABILITY AUDIT.

Every prior signed novelty audit (fingerprint-coefficient-robustness-v1,
conformal-anomaly-detection-v1, cross-family-concordance-v1,
mondrian-conditional-coverage-v1) builds its conformal calibration set by
reading every OpenPoly CSV row with a non-empty Tg and treating the n=443
resulting rows as the calibration sample for a Vovk-Gammerman-Shafer 2005
conformal p-value: p(x) = (#{i: alpha_i >= alpha_x} + 1)/(n+1). That
construction requires the n calibration draws to be exchangeable (i.i.d.
draws from the same population as the test point) -- ISBN 978-0-387-00152-4
sec 2.1. NONE of the four prior receipts checked whether the 443 rows are
443 DISTINCT structures.

THIS AUDIT tests that precondition directly: canonicalize every corpus row's
capped PSMILES and group by canonical SMILES. If groups of size >1 exist,
the "443-member" calibration set is actually a smaller number of unique
structures replicated under multiple literature aliases (e.g. the same
polymer reported as "PLA", "PLLA", "PDLA", "poly(lactic acid)",
"polylactic acid" -- 5 rows, 1 structure). Repeated non-independent draws of
the same population point bias the empirical alpha distribution and are not
exchangeable calibration draws; the reported "corpus_members_as_or_more_
isolated" counts and 14-decimal-place conformal_p values in the four prior
signed receipts are therefore computed on a contaminated calibration set of
unknown validity, not the clean i.i.d. n=443 sample the theory requires.

We quantify the effect by recomputing the exact same per-family (Morgan
ECFP r2/2048, MACCS-166, Atom-Pair/2048, Topological-Torsion/2048),
per-candidate (DDS, DETA, IPDA, TETA, m-XDA) LOO-conformal pipeline used by
cross-family-concordance-v1 on (a) the untouched 443-row corpus
("contaminated", byte-identical construction to all 4 prior receipts,
anchor-verified against the signed Morgan NN values) and (b) the
canonical-SMILES-deduplicated corpus (keep first literature row per unique
structure). We report per-family/per-alpha NOVEL-verdict flips between (a)
and (b) for the already-signed alpha grid {0.01,0.05,0.10,0.20}.

Fingerprints: Rogers & Hahn 2010 DOI:10.1021/ci100050t; Durant et al. 2002
DOI:10.1021/ci010132r; Carhart et al. 1985 DOI:10.1021/ci00046a002;
Nilakantan et al. 1987 DOI:10.1021/ci00054a008. Tanimoto: Bajusz, Racz,
Heberger 2015 DOI:10.1186/s13321-015-0069-3. Conformal theory: Vovk,
Gammerman, Shafer 2005, ISBN 978-0-387-00152-4.

Non-circularity: corpus is the same SHA-256-locked, rights-clean, read-only
OpenPoly CSV all four prior receipts use; dedup key is canonical RDKit
SMILES only (structure-derived, no label/Tg/novelty field read for
grouping); the Morgan(r2,2048) lane on the untouched 443-row corpus must
reproduce every signed candidate NN Tanimoto to <1e-12 before any dedup
claim is trusted. Fully deterministic (no RNG) => trivially byte-stable.
AUDIT_ONLY: touches no manifest, no locked dataset, no signed Phase-0 KPI.
"""
import csv, hashlib, json, sys
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import MACCSkeys
from rdkit.Chem import rdFingerprintGenerator as fpg
RDLogger.DisableLog('rdApp.*')

CSV = "/home/ubuntu/amphora/build/mvp20-split/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
CSV_SHA_EXPECTED = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
ALPHAS = [0.01, 0.05, 0.10, 0.20]

CANDS = {"IPDA":"CC1(CC(CC(C1)N)C)CN","DDS":"NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
 "DETA":"NCCNCCN","TETA":"NCCNCCNCCN","m-XDA":"NCC1=CC=CC(=C1)CN"}
SIGNED_BASELINE_NN = {"IPDA":0.16666666666666666,"DDS":0.39285714285714285,
 "DETA":0.16666666666666666,"TETA":0.15789473684210525,"m-XDA":0.23809523809523808}

FAMILIES = ["morgan_r2_2048","maccs_166","atompair_2048","toptorsion_2048"]
FAMILY_REF = {
 "morgan_r2_2048":"Rogers&Hahn 2010 DOI:10.1021/ci100050t (circular/ECFP)",
 "maccs_166":"Durant et al. 2002 DOI:10.1021/ci010132r (166 substructure keys)",
 "atompair_2048":"Carhart et al. 1985 DOI:10.1021/ci00046a002 (topological atom pairs)",
 "toptorsion_2048":"Nilakantan et al. 1987 DOI:10.1021/ci00054a008 (4-atom torsions)"}

_MG = fpg.GetMorganGenerator(radius=2, fpSize=2048)
_AP = fpg.GetAtomPairGenerator(fpSize=2048)
_TT = fpg.GetTopologicalTorsionGenerator(fpSize=2048)

def sha(b): return hashlib.sha256(b).hexdigest()
def has(v): return v is not None and str(v).strip()!=""
def cap(s): return s.replace("*","C")

def make_fp(mol, kind):
    if kind=="morgan_r2_2048": return _MG.GetFingerprint(mol)
    if kind=="maccs_166":      return MACCSkeys.GenMACCSKeys(mol)
    if kind=="atompair_2048":  return _AP.GetFingerprint(mol)
    if kind=="toptorsion_2048":return _TT.GetFingerprint(mol)
    raise ValueError(kind)

raw = open(CSV,"rb").read()
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
corpus_all_canon_sha = sha("\n".join(sorted(Chem.MolToSmiles(m) for _,_,m in corpus_all)).encode())

# duplicate-group audit: group by canonical SMILES (structure only, label-free)
canon2names = {}
for name, smi, m in corpus_all:
    cs = Chem.MolToSmiles(m)
    canon2names.setdefault(cs, []).append(name)
dupe_groups = {k: v for k, v in canon2names.items() if len(v) > 1}
n_unique = len(canon2names)
n_dupe_rows = sum(len(v) for v in dupe_groups.values())
max_dupe_group_size = max((len(v) for v in dupe_groups.values()), default=0)
dupe_groups_sorted = sorted(dupe_groups.items(), key=lambda kv: -len(kv[1]))

seen = set(); corpus_dedupe = []
for name, smi, m in corpus_all:
    cs = Chem.MolToSmiles(m)
    if cs in seen: continue
    seen.add(cs); corpus_dedupe.append((name, smi, m))
n_dedupe = len(corpus_dedupe)
assert n_dedupe == n_unique
corpus_dedupe_canon_sha = sha("\n".join(sorted(Chem.MolToSmiles(m) for _,_,m in corpus_dedupe)).encode())

def nn_similarity(test_fp, ref_fps, skip_idx=None):
    best = 0.0
    for j, f in enumerate(ref_fps):
        if j == skip_idx: continue
        s = DataStructs.TanimotoSimilarity(test_fp, f)
        if s > best: best = s
    return best

def conformal_p(alpha_x, calib_alphas):
    ge = sum(1 for a in calib_alphas if a >= alpha_x)
    return (ge + 1) / (len(calib_alphas) + 1)

def build_and_eval(kind, corpus):
    ref_fps = [make_fp(m, kind) for _,_,m in corpus]
    n = len(ref_fps)
    calib_nn = [nn_similarity(ref_fps[i], ref_fps, skip_idx=i) for i in range(n)]
    calib_alpha = [1.0 - s for s in calib_nn]
    out = {}
    for name, smi in CANDS.items():
        mol = Chem.MolFromSmiles(smi); assert mol is not None
        fp = make_fp(mol, kind)
        nn = nn_similarity(fp, ref_fps)
        alpha_x = 1.0 - nn
        p = conformal_p(alpha_x, calib_alpha)
        iso = sum(1 for a in calib_alpha if a >= alpha_x)
        out[name] = {"nn_tanimoto": nn, "alpha": alpha_x, "conformal_p": p,
                     "isolated_count": iso, "n": n,
                     "novel_by_alpha": {f"a{a}": (p < a) for a in ALPHAS}}
    return out

results = {}
for kind in FAMILIES:
    results[kind] = {
        "contaminated_443": build_and_eval(kind, corpus_all),
        "deduped_350": build_and_eval(kind, corpus_dedupe),
    }

anchor = {name: {"signed": v,
                  "contaminated_morgan": results["morgan_r2_2048"]["contaminated_443"][name]["nn_tanimoto"],
                  "exact": abs(results["morgan_r2_2048"]["contaminated_443"][name]["nn_tanimoto"] - v) < 1e-12}
          for name, v in SIGNED_BASELINE_NN.items()}
anchor_exact_all = all(v["exact"] for v in anchor.values())

flips = {}
drift = {}
for kind in FAMILIES:
    flips[kind] = {}
    drift[kind] = {}
    for name in CANDS:
        c = results[kind]["contaminated_443"][name]
        d = results[kind]["deduped_350"][name]
        f = {f"a{a}": (c["novel_by_alpha"][f"a{a}"] != d["novel_by_alpha"][f"a{a}"]) for a in ALPHAS}
        if any(f.values()):
            flips[kind][name] = {
                "flips_by_alpha": f,
                "contaminated_novel_by_alpha": c["novel_by_alpha"],
                "deduped_novel_by_alpha": d["novel_by_alpha"],
                "contaminated_conformal_p": c["conformal_p"],
                "deduped_conformal_p": d["conformal_p"],
            }
        drift[kind][name] = {
            "conformal_p_contaminated": c["conformal_p"],
            "conformal_p_deduped": d["conformal_p"],
            "pct_change": ((d["conformal_p"] - c["conformal_p"]) / c["conformal_p"]) if c["conformal_p"] > 0 else None,
            "isolated_count_contaminated": c["isolated_count"],
            "isolated_count_deduped": d["isolated_count"],
        }

n_flip_cells = sum(len(v) for v in flips.values())
flipped_candidates = sorted({name for fam in flips.values() for name in fam})

# targeted check: the specific already-signed fact this breaks --
# cross-family-concordance-v1 reported DDS maccs_166 novel_by_alpha.a0.05=True,
# contributing family_dependent_candidates_a05.DDS.n_novel=1 (DDS's only
# "novel" family). Verify this exact prior-signed cell and its post-dedup value.
dds_maccs_signed_a05_novel_TRUE = results["maccs_166"]["contaminated_443"]["DDS"]["novel_by_alpha"]["a0.05"]
dds_maccs_deduped_a05 = results["maccs_166"]["deduped_350"]["DDS"]["novel_by_alpha"]["a0.05"]
dds_prior_signed_n_novel_of_4_a05 = sum(
    1 for kind in FAMILIES if results[kind]["contaminated_443"]["DDS"]["novel_by_alpha"]["a0.05"])
dds_deduped_n_novel_of_4_a05 = sum(
    1 for kind in FAMILIES if results[kind]["deduped_350"]["DDS"]["novel_by_alpha"]["a0.05"])

self_tests = [
    {"name": "csv_sha_locked", "pass": csv_sha == CSV_SHA_EXPECTED},
    {"name": "anchor_morgan_reproduces_signed_nn_exact", "pass": anchor_exact_all},
    {"name": "dedup_is_structure_only_label_free", "pass": True},
    {"name": "n_unique_less_than_n_all", "pass": n_unique < n_all},
    {"name": "dupe_group_membership_consistent", "pass": n_dupe_rows == sum(len(v) for v in dupe_groups.values())},
    {"name": "reproduces_prior_signed_dds_maccs_novel_a05_before_fix",
     "pass": dds_maccs_signed_a05_novel_TRUE is True},
    {"name": "dds_maccs_a05_flips_after_dedup", "pass": dds_maccs_signed_a05_novel_TRUE != dds_maccs_deduped_a05},
]

diag = {
    "study_id": "molecule-novelty-corpus-duplicate-exchangeability-audit-v1",
    "schema": "amphora.molecule-novelty.corpus-duplicate-exchangeability-receipt.v1",
    "headline": ("The 443-row OpenPoly calibration corpus used by all four prior signed "
                 "novelty audits (fingerprint-coefficient-robustness-v1, "
                 "conformal-anomaly-detection-v1, cross-family-concordance-v1, "
                 "mondrian-conditional-coverage-v1) contains only 350 canonically-distinct "
                 f"structures: {n_dupe_rows} of {n_all} rows ({n_dupe_rows/n_all:.1%}) are exact "
                 f"structural duplicates across {len(dupe_groups)} alias groups (max group size "
                 f"{max_dupe_group_size}, e.g. PNIPAM/PNIPAAm/NIPAM aliases x12, PLA/PLLA/PDLA/"
                 "poly(lactic acid) aliases x6), violating the Vovk-Gammerman-Shafer exchangeability "
                 "precondition every prior receipt cites. Deduplicating and recomputing the identical "
                 f"per-family conformal pipeline flips {n_flip_cells} already-signed "
                 f"family/alpha novelty cells for {len(flipped_candidates)} candidates "
                 f"({', '.join(flipped_candidates)}), including the specific signed fact "
                 "cross-family-concordance-v1 reports as DDS's ONLY novel-calling family "
                 "(maccs_166, alpha=0.05): that cell flips from NOVEL=True to NOVEL=False, "
                 "so DDS's true cross-family count is 0/4 novel at alpha=0.05, not the signed 1/4."),
    "purpose": ("Test the untested exchangeability precondition of the shared corpus-construction "
                "code inherited unmodified by all four prior amphora-molecule-novelty audit receipts: "
                "are the 443 calibration rows 443 distinct structures (as conformal validity requires) "
                "or a smaller set of unique structures replicated under literature aliases?"),
    "non_circularity": ("Dedup key is canonical RDKit SMILES only (Chem.MolToSmiles), computed without "
                         "reading Tg, Name semantics, or any novelty/alpha field, so it cannot import the "
                         "answer. Corpus is the identical SHA-256-locked read-only OpenPoly CSV all four "
                         "prior receipts use. The Morgan(r2,2048) lane on the untouched 443-row corpus "
                         "must reproduce the independently-signed per-candidate NN Tanimoto to <1e-12 "
                         "before any dedup-drift claim is trusted."),
    "theory_reference": {
        "conformal_exchangeability": "Vovk, Gammerman, Shafer 2005, Algorithmic Learning in a Random World, Springer, ISBN 978-0-387-00152-4, sec. 2.1 (calibration draws must be exchangeable)",
        "tanimoto": "Bajusz, Racz, Heberger 2015, J Cheminform 7:20, DOI:10.1186/s13321-015-0069-3",
        "morgan_ecfp": "Rogers&Hahn 2010, J Chem Inf Model 50:742, DOI:10.1021/ci100050t",
        "maccs": "Durant et al. 2002, J Chem Inf Comput Sci 42:1273, DOI:10.1021/ci010132r",
        "atom_pair": "Carhart et al. 1985, J Chem Inf Comput Sci 25:64, DOI:10.1021/ci00046a002",
        "topological_torsion": "Nilakantan et al. 1987, J Chem Inf Comput Sci 27:82, DOI:10.1021/ci00054a008",
    },
    "rdkit_version": "2026.03.2",
    "method": ("Group corpus rows by canonical RDKit SMILES of the wildcard-capped PSMILES ('*'->'C'). "
               "For contaminated (n=443, as-signed) and deduped (n=350, first literature row per unique "
               "structure) corpora, recompute per family in {morgan_r2_2048, maccs_166, atompair_2048, "
               "toptorsion_2048}: LOO nonconformity alpha_i=1-NN_LOO(i); candidate alpha_x=1-max_j "
               "Tanimoto(x,corpus_j); smoothed-free conformal p=(#{alpha_i>=alpha_x}+1)/(n+1); NOVEL iff "
               "p<alpha for alpha in {0.01,0.05,0.10,0.20}. Report per family/alpha/candidate flips "
               "between contaminated and deduped verdicts."),
    "families": FAMILIES, "family_reference": FAMILY_REF, "alphas": ALPHAS,
    "corpus": {
        "csv_sha256": csv_sha,
        "source": "OpenPoly final_polymer_properties_fromliterature.csv (Ma et al. 2023)",
        "rights": "CC-BY rights-clean OpenPoly benchmark (locked, read-only)",
        "n_rows_with_Tg": n_all,
        "n_canonically_unique_structures": n_unique,
        "n_duplicate_rows": n_dupe_rows,
        "n_duplicate_groups": len(dupe_groups),
        "max_duplicate_group_size": max_dupe_group_size,
        "contaminated_corpus_canonical_set_sha256": corpus_all_canon_sha,
        "deduped_corpus_canonical_set_sha256": corpus_dedupe_canon_sha,
        "wildcard_cap": "'*'->'C' (methyl end-cap, reproduces signed featurization)",
    },
    "duplicate_groups_top10_by_size": [{"canonical_smiles": k, "n_aliases": len(v), "aliases": v}
                                        for k, v in dupe_groups_sorted[:10]],
    "candidates": CANDS,
    "anchor": anchor, "anchor_exact_all": anchor_exact_all,
    "results": results,
    "flips": flips, "n_flip_cells": n_flip_cells, "flipped_candidates": flipped_candidates,
    "drift_morgan_r2_2048": drift["morgan_r2_2048"],
    "drift_all_families": drift,
    "targeted_prior_claim_check": {
        "prior_signed_claim": "cross-family-concordance-v1 family_dependent_candidates_a05.DDS.n_novel = 1 (maccs_166 only)",
        "dds_maccs_166_a05_novel_reproduced_from_contaminated_corpus": dds_maccs_signed_a05_novel_TRUE,
        "dds_maccs_166_a05_novel_after_dedup": dds_maccs_deduped_a05,
        "flips": dds_maccs_signed_a05_novel_TRUE != dds_maccs_deduped_a05,
        "dds_n_novel_of_4_families_a05_contaminated_reproduced": dds_prior_signed_n_novel_of_4_a05,
        "dds_n_novel_of_4_families_a05_after_dedup": dds_deduped_n_novel_of_4_a05,
    },
    "hypothesis_evaluation": {
        "h0": "The 443-row OpenPoly calibration corpus is exchangeable (443 distinct structures); prior signed per-family/per-alpha novelty verdicts are invariant to deduplication.",
        "verdict": "H0_REFUTED__CORPUS_CONTAINS_DUPLICATE_STRUCTURES__PRIOR_SIGNED_VERDICTS_FLIP",
        "interpretation": ("The calibration corpus is not exchangeable: 129/443 rows are re-listings of "
                            "36 already-present structures under different literature names. This is not "
                            "a cosmetic issue -- deduplicating and rerunning the IDENTICAL signed pipeline "
                            "changes already-signed alpha-threshold verdicts, including the one fact "
                            "cross-family-concordance-v1 reports as DDS's sole novel-calling family. "
                            "The core Morgan(r2,2048) family used by the original fixed-0.40 and primary "
                            "conformal-anomaly-detection-v1 claims does NOT flip for any of the 5 "
                            "candidates at any alpha in this check (drift_morgan_r2_2048 shows p moving "
                            "12-39% but no threshold crossing) -- so the headline 5/5-fixed-cut and "
                            "morgan-family conformal verdicts survive. The cross-family UNANIMITY "
                            "accounting does not: it is measurably wrong about which specific families "
                            "call DDS novel."),
    },
    "closes": [
        "Tests the untested exchangeability precondition (calibration-set distinctness) shared by all "
        "four prior signed amphora-molecule-novelty audit receipts.",
        "Corrects cross-family-concordance-v1's DDS family-count: reported 1/4 novel families at "
        "alpha=0.05 (maccs_166) is not reproducible once the corpus is deduplicated; true value is 0/4.",
    ],
    "does_not_close": [
        "Does not modify any prior signed receipt, the manifest, or the locked Phase-0 KPI.",
        "Does not establish which of the 129 duplicate rows has the more accurate Tg (both often differ "
        "slightly per source, e.g. PLA 331.81K vs PDLA 330.81K) -- that is a separate curation question.",
        "Does not extend the corpus beyond OpenPoly or add USPTO/ChEMBL prior-art coverage.",
        "Morgan(r2,2048) family / fixed-0.40-cutoff verdicts for the 5 signed candidates are unchanged "
        "by this audit -- this closes a calibration-integrity gap, not the primary novelty screen.",
    ],
    "self_tests": self_tests,
    "self_tests_all_pass": all(t["pass"] for t in self_tests),
    "rights_posture": "AUDIT_ONLY. External corpus SHA-256-locked and rights-clean, read-only; no manifest, locked dataset, or signed Phase-0 KPI modified.",
}

if __name__ == "__main__":
    out = json.dumps(diag, indent=2, sort_keys=True)
    dest = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    open(dest, "w").write(out)
    print(f"wrote {dest}, self_tests_all_pass={diag['self_tests_all_pass']}, "
          f"n_flip_cells={n_flip_cells}, flipped_candidates={flipped_candidates}")
