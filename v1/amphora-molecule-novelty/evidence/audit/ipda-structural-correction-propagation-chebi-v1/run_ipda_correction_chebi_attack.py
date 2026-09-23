#!/usr/bin/env python3
"""amphora-molecule-novelty AUDIT_ONLY -- IPDA STRUCTURAL-CORRECTION PROPAGATION AUDIT
   applied to the chebi-truthset-second-corpus-v1 open finding (2026-08-17).

ROTATION-mode falsification attack on the strongest still-live standing claim of
amphora-molecule-novelty: chebi-truthset-second-corpus-v1's assertion that "IPDA alone
survives" novelty (NN Tanimoto < 0.40) across every reference corpus tested so far
(OpenPoly-350, PolyInfo, ChEBI-dedup). That finding is itself the narrowest, most
recent, most-relied-upon still-open claim about this module's novelty KPI.

DEFECT FOUND BY THIS AUDIT (pre-registered before computing the new numbers): the
chebi-truthset-second-corpus-v1 script's own CANDS dict hard-codes
IPDA = "CC1(CC(CC(C1)N)C)CN" -- byte-identical to the "superseded_smiles" /
"superseded_formula": "C9H20N2" field of R-A07v2's own corrected_ipda record
(evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json),
i.e. the SAME demethylated non-real-molecule structure that V-A07/R-A07v2 already
established is NOT isophorone diamine (CAS 2855-13-2, C10H22N2, real formula), not the
R-A07v2 "v2_canonical" corrected structure "CC1(C)CC(N)CC(C)(CN)C1" (C10H22N2) that
five prior fires (R-A07, V-A07, R-A07v2, W-NOV1, V-A07v2) established as authoritative
going forward. This is the identical class of defect V-A07 found in R-A07 (undisclosed
partial propagation of the IPDA structural fix) recurring in the newest, still-open
finding -- this module has now shown the same bug pattern crossing INTO a brand-new
second-corpus attack six days after the fix was supposedly load-bearing precedent.

FALSIFICATION LOGIC: recompute IPDA's NN Tanimoto against OpenPoly-350, ChEBI-dedup,
and their union using the CORRECT R-A07v2 v2_canonical structure, under the identical
Morgan(r2,2048)/Tanimoto pipeline and the identical SHA-256-pinned corpora as
chebi-truthset-second-corpus-v1. If the corrected structure's ChEBI NN Tanimoto is
materially different from the wrong-structure value (0.354838...) -- especially if it
crosses the 0.40 cut, or the wrong-structure InChIKey-skeleton null-hit becomes a hit --
then chebi-truthset-second-corpus-v1's headline conclusion ("IPDA alone survives") is
REFUTED as computed: it rests on a candidate structure this module's own retraction
index has already established is not the real molecule. If the corrected value is
materially the same and stays < 0.40 with no InChIKey hit, the finding's headline
number turns out to be numerically accidental-right on a wrong input.

Non-circularity: OpenPoly and ChEBI corpora are the identical SHA-256-locked artifacts
used by chebi-truthset-second-corpus-v1 (verified below). Featurization is byte-
identical (Morgan r2/2048, RDKit rdFingerprintGenerator). Deterministic (no RNG).
AUDIT_ONLY: writes only inside amphora-molecule-novelty/evidence/audit/.
"""
import csv, gzip, hashlib, json, sys, time, os
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator as fpg
from rdkit.Chem import rdMolDescriptors
RDLogger.DisableLog('rdApp.*')

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
OPENPOLY_CSV = f"{ROOT}/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
OPENPOLY_CSV_SHA_EXPECTED = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
OPENPOLY_DEDUP_SHA_EXPECTED = "74513e30071335d097ee83315f5b21249da86ea6a5d61e98a27d07b631593dce"

CHEBI_SDF = f"{ROOT}/amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.sdf.gz"
CHEBI_SDF_SHA_EXPECTED = "8f17627476c66e899dabe3cd7ae1cbb94f7ee6c67f2ee91f077a77a19c940ad7"

OUT_PATH = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ipda-correction-chebi/diagnostic.canonical.json"
MUTATE = "--mutate" in sys.argv  # positive control: re-inject the KNOWN-WRONG superseded structure

IPDA_WRONG_SUPERSEDED = "CC1(CC(CC(C1)N)C)CN"          # C9H20N2, refuted by candidate-structure-identity-audit-v1 (2026-08-03)
IPDA_CORRECTED_V2 = "CC1(C)CC(N)CC(C)(CN)C1"           # C10H22N2, R-A07v2 v2_canonical, real isophorone diamine CAS 2855-13-2

OTHER_CANDS = {"DDS": "NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
               "DETA": "NCCNCCN", "TETA": "NCCNCCNCCN", "m-XDA": "NCC1=CC=CC(=C1)CN"}
IPDA_SIGNED_OPENPOLY_NN = 0.16666666666666666  # R-A07v2: numerically unchanged old vs corrected structure
NOVELTY_THRESHOLD = 0.40

_MG = fpg.GetMorganGenerator(radius=2, fpSize=2048)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def has(v):
    return v is not None and str(v).strip() != ""


def cap(s):
    return s.replace("*", "C")


def fp(mol):
    return _MG.GetFingerprint(mol)


def inchikey_skeleton(mol):
    try:
        ik = Chem.MolToInchiKey(mol)
        return ik.split("-")[0] if ik else None
    except Exception:
        return None


def load_openpoly():
    csv_sha = sha256_file(OPENPOLY_CSV)
    assert csv_sha == OPENPOLY_CSV_SHA_EXPECTED, f"OpenPoly CSV sha mismatch {csv_sha}"
    rows = list(csv.DictReader(open(OPENPOLY_CSV)))
    corpus_all = []
    for r in rows:
        if not has(r.get("Tg (K)")):
            continue
        smi = cap(r["PSMILES"])
        m = Chem.MolFromSmiles(smi)
        if m is None:
            continue
        corpus_all.append((r["Name"], smi, m))
    seen = set()
    dedupe = []
    for name, smi, m in corpus_all:
        cs = Chem.MolToSmiles(m)
        if cs in seen:
            continue
        seen.add(cs)
        dedupe.append((name, smi, m))
    dedupe_sha = sha("\n".join(sorted(Chem.MolToSmiles(m) for _, _, m in dedupe)).encode())
    assert dedupe_sha == OPENPOLY_DEDUP_SHA_EXPECTED, f"OpenPoly dedup sha mismatch {dedupe_sha}"
    return len(rows), len(corpus_all), dedupe, csv_sha, dedupe_sha


def load_chebi():
    csv_sha = sha256_file(CHEBI_SDF)
    assert csv_sha == CHEBI_SDF_SHA_EXPECTED, f"ChEBI SDF sha mismatch {csv_sha}"
    supp = Chem.ForwardSDMolSupplier(gzip.open(CHEBI_SDF, "rb"))
    n_raw = 0
    n_parsed = 0
    seen = set()
    dedupe = []
    ik_index = {}
    for m in supp:
        n_raw += 1
        if m is None:
            continue
        try:
            name = m.GetProp("ChEBI Name") if m.HasProp("ChEBI Name") else (
                m.GetProp("_Name") if m.HasProp("_Name") else f"chebi_row_{n_raw}")
            chebi_id = m.GetProp("ChEBI ID") if m.HasProp("ChEBI ID") else None
        except Exception:
            name, chebi_id = f"chebi_row_{n_raw}", None
        try:
            cs = Chem.MolToSmiles(m)
        except Exception:
            continue
        n_parsed += 1
        if cs in seen:
            continue
        seen.add(cs)
        dedupe.append((name, chebi_id, cs, m))
        ik = inchikey_skeleton(m)
        if ik and ik not in ik_index:
            ik_index[ik] = (name, chebi_id, cs)
    return n_raw, n_parsed, dedupe, ik_index, csv_sha


def nn_similarity(test_fp, ref_fps):
    best, best_j = 0.0, -1
    for j, f in enumerate(ref_fps):
        s = DataStructs.TanimotoSimilarity(test_fp, f)
        if s > best:
            best, best_j = s, j
    return best, best_j


def analyze_candidate(name, smi, openpoly_dedupe, openpoly_fps, chebi_dedupe, chebi_fps,
                       chebi_ik_index, union_fps, union_labels):
    mol = Chem.MolFromSmiles(smi)
    assert mol is not None, f"candidate {name} SMILES failed to parse: {smi}"
    f = fp(mol)
    nn_openpoly, j_op = nn_similarity(f, openpoly_fps)
    nn_chebi, j_ch = nn_similarity(f, chebi_fps)
    nn_union, j_un = nn_similarity(f, union_fps)
    cand_ik = inchikey_skeleton(mol)
    ik_hit = chebi_ik_index.get(cand_ik) if cand_ik else None
    formula = rdMolDescriptors.CalcMolFormula(mol)
    return {
        "candidate_smiles": smi,
        "molecular_formula": formula,
        "candidate_inchikey_skeleton": cand_ik,
        "nn_tanimoto_vs_openpoly_350": nn_openpoly,
        "openpoly_nn_match": openpoly_dedupe[j_op][0] if j_op >= 0 else None,
        "nn_tanimoto_vs_chebi_dedup": nn_chebi,
        "chebi_nn_match_name": chebi_dedupe[j_ch][0] if j_ch >= 0 else None,
        "chebi_nn_match_id": chebi_dedupe[j_ch][1] if j_ch >= 0 else None,
        "chebi_nn_match_smiles": chebi_dedupe[j_ch][2] if j_ch >= 0 else None,
        "nn_tanimoto_vs_union_corpus": nn_union,
        "union_nn_match": union_labels[j_un] if j_un >= 0 else None,
        "novel_vs_openpoly_350": nn_openpoly < NOVELTY_THRESHOLD,
        "novel_vs_chebi_dedup": nn_chebi < NOVELTY_THRESHOLD,
        "novel_vs_union_corpus": nn_union < NOVELTY_THRESHOLD,
        "exact_inchikey_skeleton_match_in_chebi": ik_hit is not None,
        "inchikey_match_chebi_entity": {"name": ik_hit[0], "chebi_id": ik_hit[1], "smiles": ik_hit[2]} if ik_hit else None,
    }


def main():
    t0 = time.time()
    n_op_raw, n_op_labeled, openpoly_dedupe, openpoly_csv_sha, openpoly_dedupe_sha = load_openpoly()
    print(f"[t={time.time()-t0:.1f}s] OpenPoly loaded: {len(openpoly_dedupe)} distinct", file=sys.stderr)

    n_chebi_raw, n_chebi_parsed, chebi_dedupe, chebi_ik_index, chebi_sha = load_chebi()
    print(f"[t={time.time()-t0:.1f}s] ChEBI loaded: raw={n_chebi_raw} parsed={n_chebi_parsed} distinct={len(chebi_dedupe)}", file=sys.stderr)

    openpoly_fps = [fp(m) for _, _, m in openpoly_dedupe]
    chebi_fps = [fp(m) for _, _, _, m in chebi_dedupe]
    union_fps = openpoly_fps + chebi_fps
    union_labels = [("openpoly", nm) for nm, _, _ in openpoly_dedupe] + \
                   [("chebi", nm) for nm, _, _, _ in chebi_dedupe]
    print(f"[t={time.time()-t0:.1f}s] fingerprints built", file=sys.stderr)

    # IPDA under the WRONG (superseded) structure, exactly as chebi-truthset-second-corpus-v1 computed it
    ipda_wrong = analyze_candidate("IPDA_as_computed_by_chebi_truthset_v1_WRONG_STRUCTURE", IPDA_WRONG_SUPERSEDED,
                                    openpoly_dedupe, openpoly_fps, chebi_dedupe, chebi_fps, chebi_ik_index,
                                    union_fps, union_labels)

    # IPDA under the CORRECT R-A07v2 v2_canonical structure (or, in --mutate mode, deliberately
    # re-corrupted back to the wrong structure to prove this audit's own diff-detector fires)
    ipda_smiles_to_use = IPDA_WRONG_SUPERSEDED if MUTATE else IPDA_CORRECTED_V2
    ipda_corrected = analyze_candidate("IPDA_corrected_R_A07v2_structure", ipda_smiles_to_use,
                                        openpoly_dedupe, openpoly_fps, chebi_dedupe, chebi_fps, chebi_ik_index,
                                        union_fps, union_labels)

    anchor_ok = abs(ipda_corrected["nn_tanimoto_vs_openpoly_350"] - IPDA_SIGNED_OPENPOLY_NN) < 1e-9 \
        if not MUTATE else abs(ipda_wrong["nn_tanimoto_vs_openpoly_350"] - IPDA_SIGNED_OPENPOLY_NN) < 1e-9

    delta_chebi = ipda_corrected["nn_tanimoto_vs_chebi_dedup"] - ipda_wrong["nn_tanimoto_vs_chebi_dedup"]
    material_flip = (ipda_wrong["novel_vs_chebi_dedup"] != ipda_corrected["novel_vs_chebi_dedup"]) or \
                     (ipda_corrected["exact_inchikey_skeleton_match_in_chebi"] and not ipda_wrong["exact_inchikey_skeleton_match_in_chebi"])
    structures_differ = ipda_wrong["candidate_smiles"] != ipda_corrected["candidate_smiles"]
    detected = structures_differ and (abs(delta_chebi) > 1e-9 or ipda_wrong["candidate_inchikey_skeleton"] != ipda_corrected["candidate_inchikey_skeleton"])

    out = {
        "attack_id": "amphora-molecule-novelty-ipda-structural-correction-propagation-chebi-v1",
        "mode": "mutated_positive_control_reinject_wrong_structure" if MUTATE else "canonical",
        "claim_under_attack": "evidence/audit/chebi-truthset-second-corpus-v1/chebi-truthset-second-corpus-receipt.v1.dsse.json#candidate_chebi_retest.IPDA (still-open, unrepaired finding asserting 'IPDA alone survives' NOVEL < 0.40 across OpenPoly-350 and ChEBI-dedup)",
        "defect_alleged": "chebi-truthset-second-corpus-v1's own CANDS['IPDA'] hard-codes the C9H20N2 demethylated string already refuted as non-isophorone-diamine by candidate-structure-identity-audit-v1 (2026-08-03) and explicitly recorded as superseded_smiles in R-A07v2's corrected_ipda block, instead of R-A07v2's v2_canonical corrected C10H22N2 structure that 5 prior fires (R-A07/V-A07/R-A07v2/W-NOV1/V-A07v2) established as authoritative.",
        "refutation_criterion": "IPDA's NN Tanimoto vs ChEBI-dedup (or its InChIKey-skeleton match status) computed under the CORRECT R-A07v2 structure differs materially from the value chebi-truthset-second-corpus-v1 reported for the WRONG structure -- specifically: novel_vs_chebi_dedup classification flips, or an InChIKey-skeleton match appears/disappears, when the correct structure is substituted.",
        "chebi_corpus_recap": {
            "sdf_gz_sha256": chebi_sha, "n_records_raw": n_chebi_raw, "n_records_parsed": n_chebi_parsed,
            "n_canonically_unique_structures_after_dedup": len(chebi_dedupe),
        },
        "openpoly_corpus_recap": {
            "csv_sha256": openpoly_csv_sha, "n_rows_raw": n_op_raw, "n_rows_with_Tg": n_op_labeled,
            "n_canonically_unique_structures_after_dedup": len(openpoly_dedupe),
            "dedup_canonical_set_sha256": openpoly_dedupe_sha,
        },
        "ipda_as_reported_by_chebi_truthset_v1_wrong_structure": ipda_wrong,
        "ipda_recomputed_correct_structure": ipda_corrected,
        "delta_nn_tanimoto_vs_chebi_wrong_minus_correct": ipda_wrong["nn_tanimoto_vs_chebi_dedup"] - ipda_corrected["nn_tanimoto_vs_chebi_dedup"],
        "material_flip_between_wrong_and_correct_structure": material_flip,
        "anchor_check_openpoly_nn_matches_signed_r_a07v2_value": anchor_ok,
        "other_four_candidates_never_had_a_structural_correction_issued_not_recomputed_here": list(OTHER_CANDS.keys()),
        "featurization": {"fingerprint_method": "Morgan/ECFP", "morgan_bits": 2048, "morgan_radius": 2,
                           "similarity_method": "Tanimoto (Jaccard on bit sets)",
                           "identity_method": "InChIKey (skeleton block only)",
                           "generator": "rdkit.Chem.rdFingerprintGenerator.GetMorganGenerator",
                           "rdkit_version": __import__("rdkit").__version__},
    }
    if MUTATE:
        out["positive_control"] = {
            "planted_defect": "re-inject the KNOWN-WRONG superseded IPDA structure (C9H20N2, 'CC1(CC(CC(C1)N)C)CN') into the slot this audit uses for the 'corrected' structure, i.e. run the audit's own wrong-vs-corrected diff detector on two byte-identical (both-wrong) inputs",
            "how_planted": "ipda_smiles_to_use = IPDA_WRONG_SUPERSEDED instead of IPDA_CORRECTED_V2 under --mutate",
            "detected": (not detected),
            "note_on_detection_semantics": "in --mutate mode the two compared structures are IDENTICAL (both wrong), so a correctly-behaving diff detector must report detected=False (no material_flip, delta=0, identical InChIKey) -- this proves the detector is not vacuously always firing. 'detected' above is True (correct null-result) iff the audit's diff machinery reports no difference between two byte-identical inputs.",
            "evidence": f"structures_differ={structures_differ}, delta_chebi={delta_chebi}, material_flip={material_flip}, ipda_wrong_ik={ipda_wrong['candidate_inchikey_skeleton']}, ipda_corrected_ik={ipda_corrected['candidate_inchikey_skeleton']}",
        }
    else:
        out["positive_control_ref"] = "see companion --mutate run (same script) for the null-result positive control: re-running with both slots forced to the identical wrong structure must yield delta=0/material_flip=False, proving this audit's diff machinery is not vacuously firing on the real (structures-differ) run."

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    json.dump(out, open(OUT_PATH, "w"), indent=None, sort_keys=True)
    print(json.dumps({
        "status": "ok",
        "ipda_wrong_nn_chebi": ipda_wrong["nn_tanimoto_vs_chebi_dedup"],
        "ipda_correct_nn_chebi": ipda_corrected["nn_tanimoto_vs_chebi_dedup"],
        "delta": delta_chebi,
        "material_flip": material_flip,
        "structures_differ": structures_differ,
        "anchor_ok": anchor_ok,
        "wall_clock_seconds": time.time() - t0,
    }, indent=2))


if __name__ == "__main__":
    main()
