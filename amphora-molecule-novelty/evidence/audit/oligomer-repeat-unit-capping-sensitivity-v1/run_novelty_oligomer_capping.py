#!/usr/bin/env python3
"""amphora-molecule-novelty AUDIT_ONLY attack: oligomer-repeat-unit
representation-convention sensitivity of the signed Phase-0 Tanimoto-NN
novelty finding (KPI: 5/5 canonical DGEBA epoxy-amine hardeners classified
NOVEL, Morgan(r2,2048)/Tanimoto NN < 0.40 Bajusz-Racz-Heberger threshold,
vs the 443-member SHA-locked OpenPoly reference corpus).

Question: the signed KPI and all four prior audit receipts (fingerprint-
coefficient-robustness-v1, conformal-anomaly-detection-v1, cross-family-
concordance-v1, mondrian-conditional-coverage-v1, corpus-duplicate-
exchangeability-audit-v1) represent EVERY reference polymer using its
single-repeat-unit PSMILES with the polymer attachment wildcard '*'
capped to a methyl group ('*'->'C'). That is one arbitrary truncation
choice among several defensible ones. Crucially, the OpenPoly source CSV
itself (Ma et al. 2023, the exact SHA-256-locked file every receipt
cites) ALSO ships PSMILES_2 (2x repeat / dimer) and PSMILES_4 (4x repeat
/ tetramer) explicit oligomer-expansion columns for every one of the 443
Tg rows -- a strictly more chemically realistic local environment around
the former wildcard position for a RADIUS-2 Morgan fingerprint than a
single monomer capped with a foreign methyl substituent. This audit asks:
does the signed 5/5-NOVEL verdict at the declared Morgan(r2,2048)/Tanimoto
family survive when the SAME declared featurization is applied to the
SAME SHA-locked CSV's own dimer/tetramer columns instead of the monomer
column? If any candidate's NN Tanimoto crosses 0.40 under a representation
the source data itself provides, the signed finding is not robust to an
arbitrary, undisclosed monomer-vs-oligomer representation choice.

Non-circular anchor: the baseline (monomer, methyl-capped) Morgan(r2,2048)/
Tanimoto lane must reproduce EVERY signed-receipt candidate NN EXACTLY
before the dimer/tetramer extension is trusted.

Corpus: rights-clean OpenPoly literature polymers (Ma et al. 2023),
CC/DERIVATIVE_ALLOWED, SHA-256-locked CSV (same file, same hash, as all
five prior amphora-molecule-novelty audits).

Theory refs:
- Rogers & Hahn 2010, J Chem Inf Model 50:742 (ECFP/Morgan).
- Bajusz, Racz, Heberger 2015, J Cheminform 7:20 (Tanimoto; 0.40 threshold).
- Ma, R. et al. 2023 (OpenPoly / OMG_PhysicalProperties dataset), the
  source of the PSMILES / PSMILES_2 / PSMILES_4 oligomer-expansion columns.
AUDIT_ONLY. Does not touch manifest, locked datasets, or any signed KPI.
"""
import csv, hashlib, json, sys
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
RDLogger.DisableLog('rdApp.*')

CSV = "/home/ubuntu/amphora/build/mvp20-split/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
CSV_SHA_EXPECTED = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
NOVEL_T = 0.40  # Bajusz-Racz-Heberger 2015 novelty (dissimilarity) threshold

CANDS = {"IPDA": "CC1(CC(CC(C1)N)C)CN", "DDS": "NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
         "DETA": "NCCNCCN", "TETA": "NCCNCCNCCN", "m-XDA": "NCC1=CC=CC(=C1)CN"}
SIGNED_BASELINE_NN = {"IPDA": 0.16666666666666666, "DDS": 0.39285714285714285,
                       "DETA": 0.16666666666666666, "TETA": 0.15789473684210525,
                       "m-XDA": 0.23809523809523808}
# fail-closed positive controls from fingerprint-coefficient-robustness-v1
POS_CONTROLS = {"polyethersulfone_exact": "COC1=CC=C(S(=O)(C2=CC=C(OC)C=C2)=O)C=C1"}

def sha(b): return hashlib.sha256(b).hexdigest()
def has(v): return v is not None and str(v).strip() != ""
def cap(s): return s.replace("*", "C")

def fp(mol): return AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
def tan(a, b): return DataStructs.TanimotoSimilarity(a, b)

raw = open(CSV, "rb").read()
csv_sha = sha(raw)
assert csv_sha == CSV_SHA_EXPECTED, f"CSV sha mismatch {csv_sha}"
rows = list(csv.DictReader(open(CSV)))

REPS = ["PSMILES", "PSMILES_2", "PSMILES_4"]
REP_LABEL = {"PSMILES": "monomer_1x", "PSMILES_2": "dimer_2x", "PSMILES_4": "tetramer_4x"}

corpus = {r: [] for r in REPS}
parse_fail = {r: 0 for r in REPS}
for row in rows:
    if not has(row.get("Tg (K)")):
        continue
    for rep in REPS:
        field = row.get(rep)
        if not has(field):
            parse_fail[rep] += 1
            continue
        smi = cap(field)
        m = Chem.MolFromSmiles(smi)
        if m is None:
            parse_fail[rep] += 1
            continue
        corpus[rep].append((row["Name"], smi, m))

n_tg_rows = sum(1 for row in rows if has(row.get("Tg (K)")))

corpus_fps = {rep: [fp(m) for _, _, m in corpus[rep]] for rep in REPS}
corpus_set_sha = {rep: sha("\n".join(sorted(Chem.MolToSmiles(m) for _, _, m in corpus[rep])).encode())
                   for rep in REPS}

# ---- baseline KA (monomer lane): reproduce signed per-candidate NN exactly
ka = []
for c, smi in CANDS.items():
    cf = fp(Chem.MolFromSmiles(smi))
    nn = max(tan(cf, rf) for rf in corpus_fps["PSMILES"])
    exp = SIGNED_BASELINE_NN[c]
    ka.append({"candidate": c, "nn_tanimoto": nn, "signed_receipt_nn": exp,
               "abs_delta": abs(nn - exp), "exact": abs(nn - exp) < 1e-12})
ka_all_exact = all(x["exact"] for x in ka)

# ---- main grid: per candidate x per representation --------------------------
grid = {}
for c, smi in CANDS.items():
    cf = fp(Chem.MolFromSmiles(smi))
    grid[c] = {}
    for rep in REPS:
        sims = [(name, tan(cf, rf)) for (name, _, _), rf in zip(corpus[rep], corpus_fps[rep])]
        nn_name, nn = max(sims, key=lambda x: x[1])
        grid[c][rep] = {"nn_tanimoto": nn, "nn_reference_name": nn_name,
                         "novel_below_0_40": nn < NOVEL_T}

flips = []
for c in CANDS:
    mono = grid[c]["PSMILES"]["novel_below_0_40"]
    for rep in ("PSMILES_2", "PSMILES_4"):
        other = grid[c][rep]["novel_below_0_40"]
        if mono != other:
            flips.append({"candidate": c, "representation": REP_LABEL[rep],
                           "monomer_novel": mono, "other_novel": other,
                           "monomer_nn": grid[c]["PSMILES"]["nn_tanimoto"],
                           "other_nn": grid[c][rep]["nn_tanimoto"]})

any_candidate_flips = len(flips) > 0
all_5_novel_monomer = all(grid[c]["PSMILES"]["novel_below_0_40"] for c in CANDS)
all_5_novel_dimer = all(grid[c]["PSMILES_2"]["novel_below_0_40"] for c in CANDS)
all_5_novel_tetramer = all(grid[c]["PSMILES_4"]["novel_below_0_40"] for c in CANDS)

# ---- fail-closed positive control: exact reference-corpus duplicate must
# classify NON_NOVEL (NN==1.0) in every representation it's parseable in
fail_closed = {}
for name, smi in POS_CONTROLS.items():
    m = Chem.MolFromSmiles(smi)
    cf = fp(m)
    per_rep = {}
    for rep in REPS:
        if not corpus_fps[rep]:
            continue
        nn = max(tan(cf, rf) for rf in corpus_fps[rep])
        per_rep[REP_LABEL[rep]] = {"nn_tanimoto": nn, "classified_non_novel": nn >= NOVEL_T}
    fail_closed[name] = per_rep
fail_closed_all_hold = all(v["classified_non_novel"] for per_rep in fail_closed.values() for v in per_rep.values())

# ---- hypothesis verdict -----------------------------------------------------
# H0: "the signed 5/5-NOVEL Morgan(r2,2048)/Tanimoto verdict is invariant to
# whether the reference corpus is represented via monomer, dimer, or tetramer
# PSMILES -- all three columns being present in, and drawn directly from, the
# same SHA-locked source CSV every prior receipt cites."
h0_refuted = any_candidate_flips
verdict = "H0_REFUTED_REPRESENTATION_DEPENDENT" if h0_refuted else "H0_SURVIVES_REPRESENTATION_INVARIANT"

diag = {
    "authority": "AUDIT_ONLY",
    "study_id": "amphora-molecule-novelty-oligomer-repeat-unit-capping-sensitivity-v1",
    "headline": (
        f"Baseline monomer/methyl-capped Morgan(r2,2048)/Tanimoto lane reproduces every "
        f"signed candidate NN EXACTLY (all_exact={ka_all_exact}). Re-featurizing the SAME "
        f"SHA-locked OpenPoly CSV's own PSMILES_2 (dimer) and PSMILES_4 (tetramer) oligomer-"
        f"expansion columns -- present for all {n_tg_rows} Tg rows, never used by any of the "
        f"five prior signed/audit receipts -- under the IDENTICAL declared Morgan(r2,2048)/"
        f"Tanimoto/0.40 family: {verdict}. "
        f"any_candidate_flips={any_candidate_flips}, n_flips={len(flips)}, "
        f"all_5_novel(monomer)={all_5_novel_monomer}, all_5_novel(dimer)={all_5_novel_dimer}, "
        f"all_5_novel(tetramer)={all_5_novel_tetramer}."
    ),
    "purpose": "Test whether the signed 5/5-NOVEL finding depends on an undisclosed, "
               "arbitrary monomer-vs-oligomer PSMILES representation choice, using ONLY "
               "representations the source CSV itself ships.",
    "non_circularity": "Baseline monomer/methyl-cap Morgan(r2,2048)/Tanimoto lane must "
                        "reproduce every signed-receipt candidate NN exactly before the "
                        "dimer/tetramer extension is trusted.",
    "theory_reference": ["Rogers & Hahn 2010 J Chem Inf Model 50:742 (ECFP/Morgan)",
                          "Bajusz, Racz, Heberger 2015 J Cheminform 7:20 (Tanimoto; 0.40 threshold)",
                          "Ma et al. 2023 OpenPoly / OMG_PhysicalProperties dataset "
                          "(source of PSMILES / PSMILES_2 / PSMILES_4 columns)"],
    "rdkit_version": Chem.rdBase.rdkitVersion,
    "novelty_threshold": NOVEL_T,
    "corpus": {
        "csv_sha256": csv_sha,
        "n_rows_with_Tg": n_tg_rows,
        "representations": {REP_LABEL[r]: {"field": r, "n_members": len(corpus[r]),
                                            "n_parse_fail": parse_fail[r],
                                            "structure_set_sha256": corpus_set_sha[r]}
                             for r in REPS},
        "wildcard_cap": "'*'->'C' (methyl end-cap; identical convention to all prior receipts)",
        "source": "OpenPoly final_polymer_properties_fromliterature.csv (Ma et al. 2023)",
        "rights_class": "DERIVATIVE_ALLOWED",
    },
    "baseline_known_answer": {"all_exact": ka_all_exact, "lane": "morgan_r2_2048/tanimoto (PSMILES monomer)",
                               "per_candidate": ka},
    "candidate_grid": {c: {REP_LABEL[r]: grid[c][r] for r in REPS} for c in CANDS},
    "flips": flips,
    "summary": {
        "any_candidate_flips": any_candidate_flips,
        "n_flips": len(flips),
        "all_5_novel_monomer_baseline": all_5_novel_monomer,
        "all_5_novel_dimer": all_5_novel_dimer,
        "all_5_novel_tetramer": all_5_novel_tetramer,
    },
    "fail_closed": {"positive_controls": fail_closed, "all_controls_non_novel": fail_closed_all_hold},
    "hypothesis_evaluation": {
        "h0": "Signed 5/5-NOVEL Morgan(r2,2048)/Tanimoto verdict is invariant to monomer vs "
              "dimer vs tetramer PSMILES representation of the SAME SHA-locked reference rows.",
        "verdict": verdict,
        "h0_refuted": h0_refuted,
    },
    "closes": [
        "Tests whether the signed novelty verdict depends on an undisclosed monomer-vs-oligomer "
        "PSMILES representation choice, using representations shipped in the same locked source CSV.",
    ],
    "does_not_close": [
        "USPTO/legal prior-art novelty.",
        "Comprehensive prior-art corpus (ChEMBL/PubChem/USPTO).",
        "Does not modify any prior signed receipt, the manifest, or the locked Phase-0 KPI.",
        "Does not establish which representation (monomer/dimer/tetramer) is the 'correct' one for "
        "novelty scoring -- documents that the choice is under-specified and outcome-relevant.",
    ],
    "rights_posture": "OpenPoly Ma et al. 2023, CC/DERIVATIVE_ALLOWED, SHA-256-locked, read-only.",
    "self_tests_all_pass": ka_all_exact and (len(corpus["PSMILES"]) == n_tg_rows),
}

out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/diagnostic.canonical.json"
with open(out_path, "w") as f:
    json.dump(diag, f, indent=2, sort_keys=True)
print("WROTE", out_path)
print("ka_all_exact", ka_all_exact)
print("verdict", verdict)
print("n_flips", len(flips))
print(json.dumps(flips, indent=2))
print("fail_closed_all_hold", fail_closed_all_hold)
