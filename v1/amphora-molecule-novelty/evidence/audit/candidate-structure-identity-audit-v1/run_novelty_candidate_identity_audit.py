#!/usr/bin/env python3
"""amphora-molecule-novelty AUDIT_ONLY attack: cross-module candidate-
structure IDENTITY audit of the signed Phase-0 Tanimoto-NN novelty finding
(KPI: 5/5 canonical DGEBA epoxy-amine hardeners classified NOVEL, Morgan
(r2,2048)/Tanimoto NN < 0.40 Bajusz-Racz-Heberger threshold, vs the
443-member SHA-locked OpenPoly reference corpus).

Every prior amphora-molecule-novelty audit (fingerprint-coefficient-
robustness, conformal-anomaly-detection, cross-family-concordance,
mondrian-conditional-coverage, corpus-duplicate-exchangeability, oligomer-
repeat-unit-capping-sensitivity) has treated the 5 candidate_smiles strings
in the signed KPI as ground truth and attacked only the REFERENCE CORPUS
side of the Tanimoto-NN computation. None has checked whether the 5
candidate structures are themselves correct representations of the named
industrial hardeners they claim to be.

This audit cross-checks each of the 5 signed candidate_smiles strings
against an INDEPENDENT, already-hash-lockable, already-cited ground-truth
source that exists elsewhere in this same repository: the
"known_answer_amines" definitional structure set in
amphora-molecule-generator/reference/mvp20/data/
hardener_stoichiometric_envelope.v1.json, which cites Lee & Neville 1967,
Handbook of Epoxy Resins, McGraw-Hill (LCCN 66-23992) and re-derives molar
mass via RDKit from IUPAC 2021 standard atomic weights. That file was
built independently, for a different purpose (AHEW/amine-value instrument
testing), by a different module, and is not a party to any prior
amphora-molecule-novelty receipt -- an authentic dual-source check, not a
circular re-use of the same asserted structure.

Falsifying observation sought: ANY of the 5 signed candidate_smiles fails
to canonicalize to the SAME molecule (same RDKit canonical SMILES / same
molecular formula) as the independently-cited known-answer structure for
the same named compound. If found, the signed KPI's claim to represent
"5 canonical DGEBA-based epoxy amine hardener candidates" is false for
that candidate: the Tanimoto-NN novelty score was computed against a
DIFFERENT, incorrectly-labeled molecule, not the real-world hardener the
receipt names.

Non-circular anchor: this script also re-derives the signed baseline
Tanimoto-NN values exactly (independent of the identity question) as an
internal consistency check that the featurization pipeline itself is not
buggy, using the SAME corpus / capping / fingerprint parameters as all
six prior amphora-molecule-novelty receipts.

Theory refs:
- Lee, H. & Neville, K. 1967, Handbook of Epoxy Resins, McGraw-Hill
  (LCCN 66-23992) -- cited by amphora-molecule-generator's known-answer
  amine set for isophoronediamine / DETA / TETA / MXDA / DDS structures.
- Rogers & Hahn 2010, J Chem Inf Model 50:742 (ECFP/Morgan).
- Bajusz, Racz, Heberger 2015, J Cheminform 7:20 (Tanimoto; 0.40 threshold).
- Ma, R. et al. 2023 (OpenPoly / OMG_PhysicalProperties dataset).
AUDIT_ONLY. Does not touch manifest, locked datasets, or any signed KPI.
"""
import csv, hashlib, json, sys
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem, rdMolDescriptors
RDLogger.DisableLog('rdApp.*')

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
CSV = f"{ROOT}/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
CSV_SHA_EXPECTED = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
GENMOD_ENVELOPE = f"{ROOT}/amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json"
NOVEL_T = 0.40  # Bajusz-Racz-Heberger 2015 novelty (dissimilarity) threshold

# Signed KPI candidate_smiles (evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json)
SIGNED_CANDS = {"IPDA": "CC1(CC(CC(C1)N)C)CN", "DDS": "NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
                "DETA": "NCCNCCN", "TETA": "NCCNCCNCCN", "m-XDA": "NCC1=CC=CC(=C1)CN"}
SIGNED_BASELINE_NN = {"IPDA": 0.16666666666666666, "DDS": 0.39285714285714285,
                       "DETA": 0.16666666666666666, "TETA": 0.15789473684210525,
                       "m-XDA": 0.23809523809523808}
# name mapping: signed KPI candidate name -> amphora-molecule-generator known_answer_amines name
NAME_MAP = {"IPDA": "isophoronediamine (IPDA)", "DDS": "4,4'-diaminodiphenylsulfone (DDS)",
            "DETA": "diethylenetriamine (DETA)", "TETA": "triethylenetetramine (TETA)",
            "m-XDA": "m-xylylenediamine (MXDA)"}

def sha(b): return hashlib.sha256(b).hexdigest()
def has(v): return v is not None and str(v).strip() != ""
def cap(s): return s.replace("*", "C")
def fp(mol): return AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
def tan(a, b): return DataStructs.TanimotoSimilarity(a, b)
def canon(smi):
    m = Chem.MolFromSmiles(smi)
    return Chem.MolToSmiles(m), rdMolDescriptors.CalcMolFormula(m), m

# ---- load independent ground-truth structure set (different module, different purpose) ----
genmod_raw = open(GENMOD_ENVELOPE, "rb").read()
genmod_sha = sha(genmod_raw)
genmod = json.loads(genmod_raw)
ka_entries = {e["name"]: e for e in genmod["known_answer_amines"]["entries"]}
ka_source_note = genmod["known_answer_amines"]["note"]

# ---- per-candidate identity check --------------------------------------------
identity = {}
for c, signed_smi in SIGNED_CANDS.items():
    genmod_name = NAME_MAP[c]
    entry = ka_entries.get(genmod_name)
    signed_canon, signed_formula, signed_mol = canon(signed_smi)
    row = {"signed_smiles": signed_smi, "signed_canonical": signed_canon,
           "signed_formula": signed_formula, "genmod_entry_found": entry is not None}
    if entry is not None:
        genmod_smi = entry["smiles"]
        genmod_canon, genmod_formula, genmod_mol = canon(genmod_smi)
        same_molecule = (signed_canon == genmod_canon)
        row.update({
            "genmod_name": genmod_name, "genmod_smiles": genmod_smi,
            "genmod_canonical": genmod_canon, "genmod_formula": genmod_formula,
            "genmod_expected_active_nh": entry.get("expected_active_nh"),
            "genmod_expected_basic_n": entry.get("expected_basic_n"),
            "same_molecule": same_molecule,
            "formula_match": signed_formula == genmod_formula,
        })
    identity[c] = row

mismatches = [c for c, r in identity.items() if r.get("genmod_entry_found") and not r["same_molecule"]]
any_identity_mismatch = len(mismatches) > 0

# ---- non-circular internal consistency: re-derive signed baseline NN exactly ----
raw = open(CSV, "rb").read()
csv_sha = sha(raw)
assert csv_sha == CSV_SHA_EXPECTED, f"CSV sha mismatch {csv_sha}"
rows = list(csv.DictReader(open(CSV)))
n_tg_rows = sum(1 for row in rows if has(row.get("Tg (K)")))
corpus = []
for row in rows:
    if not has(row.get("Tg (K)")):
        continue
    field = row.get("PSMILES")
    if not has(field):
        continue
    smi = cap(field)
    m = Chem.MolFromSmiles(smi)
    if m is None:
        continue
    corpus.append((row["Name"], smi, m))
corpus_fps = [fp(m) for _, _, m in corpus]
corpus_set_sha = sha("\n".join(sorted(Chem.MolToSmiles(m) for _, _, m in corpus)).encode())

ka_baseline = []
for c, smi in SIGNED_CANDS.items():
    cf = fp(Chem.MolFromSmiles(smi))
    nn = max(tan(cf, rf) for rf in corpus_fps)
    exp = SIGNED_BASELINE_NN[c]
    ka_baseline.append({"candidate": c, "nn_tanimoto": nn, "signed_receipt_nn": exp,
                         "abs_delta": abs(nn - exp), "exact": abs(nn - exp) < 1e-12})
ka_baseline_all_exact = all(x["exact"] for x in ka_baseline)

# ---- impact: recompute NN Tanimoto / novelty classification using the
# INDEPENDENTLY-CITED, structurally-CORRECT SMILES for every mismatching
# candidate, holding everything else (corpus, capping, fingerprint) fixed ----
impact = {}
for c in mismatches:
    genmod_smi = identity[c]["genmod_smiles"]
    cf = fp(Chem.MolFromSmiles(genmod_smi))
    sims = [(name, tan(cf, rf)) for (name, _, _), rf in zip(corpus, corpus_fps)]
    nn_name, nn = max(sims, key=lambda x: x[1])
    signed_nn = SIGNED_BASELINE_NN[c]
    impact[c] = {
        "corrected_smiles": genmod_smi,
        "corrected_nn_tanimoto": nn,
        "corrected_nn_reference_name": nn_name,
        "corrected_novel_below_0_40": nn < NOVEL_T,
        "signed_nn_tanimoto": signed_nn,
        "signed_novel_below_0_40": signed_nn < NOVEL_T,
        "classification_flips": (nn < NOVEL_T) != (signed_nn < NOVEL_T),
        "nn_delta": nn - signed_nn,
    }

classification_flips = any(v["classification_flips"] for v in impact.values())

# ---- hypothesis verdict -----------------------------------------------------
# H0: "Every signed candidate_smiles string in the Phase-0 Tanimoto-NN novelty
# KPI is a correct structural representation of the named industrial epoxy-
# amine hardener it claims to be, as cross-checked against an independent,
# already-hash-lockable ground-truth structure set (amphora-molecule-generator
# known_answer_amines, citing Lee & Neville 1967)."
h0_refuted = any_identity_mismatch
verdict = "H0_REFUTED_CANDIDATE_STRUCTURE_MISLABELED" if h0_refuted else "H0_SURVIVES_ALL_CANDIDATES_IDENTITY_VERIFIED"

diag = {
    "authority": "AUDIT_ONLY",
    "study_id": "amphora-molecule-novelty-candidate-structure-identity-audit-v1",
    "headline": (
        f"Cross-module candidate-structure identity check against the independent, "
        f"Lee & Neville 1967-cited known_answer_amines set in amphora-molecule-generator: "
        f"{verdict}. n_candidates_checked={len(identity)}, "
        f"n_genmod_matches_found={sum(1 for r in identity.values() if r['genmod_entry_found'])}, "
        f"n_identity_mismatches={len(mismatches)} ({mismatches}). "
        + (f"For IPDA the signed KPI's candidate_smiles ('{SIGNED_CANDS.get('IPDA')}') canonicalizes "
           f"to {identity.get('IPDA',{}).get('signed_formula')}, a DEMETHYLATED HOMOLOG missing one "
           f"ring methyl relative to real isophorone diamine (CAS 2855-13-2, "
           f"{identity.get('IPDA',{}).get('genmod_formula')}, per Lee & Neville 1967). "
           if "IPDA" in mismatches else "") +
        f"Baseline internal-consistency re-derivation of the signed monomer/methyl-capped "
        f"Morgan(r2,2048)/Tanimoto NN values is exact for all 5 candidates "
        f"(ka_baseline_all_exact={ka_baseline_all_exact}), isolating the defect to candidate "
        f"structure identity, not the featurization pipeline. "
        f"Recomputing NN Tanimoto with the STRUCTURALLY-CORRECT SMILES for each mismatching "
        f"candidate: classification_flips={classification_flips} "
        f"(impact={ {k: {'signed_nn': v['signed_nn_tanimoto'], 'corrected_nn': v['corrected_nn_tanimoto'], 'flips': v['classification_flips']} for k, v in impact.items()} })."
    ),
    "purpose": "Test whether the 5 signed candidate_smiles strings in the Phase-0 Tanimoto-NN "
               "novelty KPI actually represent the named industrial epoxy-amine hardeners they "
               "claim to be, using an independent, already-hash-lockable ground-truth structure "
               "set from a different module (amphora-molecule-generator), not the same asserted "
               "structures re-checked circularly.",
    "non_circularity": "Independent ground-truth source (amphora-molecule-generator "
                        "known_answer_amines, citing Lee & Neville 1967) was authored for a "
                        "different purpose (AHEW/amine-value instrument testing) by a different "
                        "audit lineage; not derived from or party to any amphora-molecule-novelty "
                        "receipt. Baseline Tanimoto-NN re-derivation independently confirms the "
                        "featurization pipeline itself reproduces the signed values exactly.",
    "theory_reference": [
        "Lee, H. & Neville, K. 1967, Handbook of Epoxy Resins, McGraw-Hill (LCCN 66-23992)",
        "Rogers & Hahn 2010 J Chem Inf Model 50:742 (ECFP/Morgan)",
        "Bajusz, Racz, Heberger 2015 J Cheminform 7:20 (Tanimoto; 0.40 threshold)",
        "Ma et al. 2023 OpenPoly / OMG_PhysicalProperties dataset",
    ],
    "rdkit_version": Chem.rdBase.rdkitVersion,
    "novelty_threshold": NOVEL_T,
    "independent_ground_truth_source": {
        "file": "amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json",
        "file_sha256": genmod_sha,
        "section": "known_answer_amines",
        "note": ka_source_note,
    },
    "corpus": {
        "csv_sha256": csv_sha, "n_rows_with_Tg": n_tg_rows, "n_corpus_members": len(corpus),
        "structure_set_sha256": corpus_set_sha,
        "wildcard_cap": "'*'->'C' (methyl end-cap; identical convention to all prior receipts)",
        "source": "OpenPoly final_polymer_properties_fromliterature.csv (Ma et al. 2023)",
        "rights_class": "DERIVATIVE_ALLOWED",
    },
    "identity_check": identity,
    "mismatches": mismatches,
    "any_identity_mismatch": any_identity_mismatch,
    "baseline_known_answer": {"all_exact": ka_baseline_all_exact, "lane": "morgan_r2_2048/tanimoto (PSMILES monomer)",
                               "per_candidate": ka_baseline},
    "impact_of_correction": impact,
    "classification_flips": classification_flips,
    "hypothesis_evaluation": {
        "h0": "Every signed candidate_smiles string in the Phase-0 Tanimoto-NN novelty KPI is a "
              "correct structural representation of the named hardener, per an independent "
              "hash-lockable ground-truth structure set.",
        "verdict": verdict,
        "h0_refuted": h0_refuted,
    },
    "closes": [
        "Tests whether the signed novelty KPI's candidate structures are correctly identified, "
        "using an independent ground-truth structure set from a different module lineage.",
    ],
    "does_not_close": [
        "USPTO/legal prior-art novelty.",
        "Comprehensive prior-art corpus (ChEMBL/PubChem/USPTO).",
        "Does not modify any prior signed receipt, the manifest, or the locked Phase-0 KPI.",
        "Does not establish whether the corrected structure remains NOVEL or NOT-NOVEL as a "
        "product-performance or FTO claim -- reports the recomputed reference-similarity number only.",
    ],
    "rights_posture": "OpenPoly Ma et al. 2023, CC/DERIVATIVE_ALLOWED, SHA-256-locked, read-only. "
                       "amphora-molecule-generator envelope file read-only, in-scope, no new external data.",
    "self_tests_all_pass": ka_baseline_all_exact and (len(corpus) == n_tg_rows),
}

out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/diagnostic.canonical.json"
with open(out_path, "w") as f:
    json.dump(diag, f, indent=2, sort_keys=True)
print("WROTE", out_path)
print("ka_baseline_all_exact", ka_baseline_all_exact)
print("verdict", verdict)
print("mismatches", mismatches)
print(json.dumps(identity, indent=2))
print("impact_of_correction", json.dumps(impact, indent=2))
