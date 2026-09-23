#!/usr/bin/env python3
"""amphora-molecule-novelty AUDIT_ONLY -- IPDA POLYINFO/TRIPLE-CORPUS GAP ATTACK

ROTATION-mode falsification attack on the strongest still-live standing claim of
amphora-molecule-novelty: that "IPDA alone survives" novelty (NN Tanimoto < 0.40)
across every reference corpus this module has tested (chebi-truthset-second-corpus-v1,
2026-08-17, as corrected by ipda-structural-correction-propagation-chebi-v1, 2026-08-18).

GAP FOUND (pre-registered before computing the new numbers): the R-A07v2 v2_canonical
corrected IPDA structure ("CC1(C)CC(N)CC(C)(CN)C1", C10H22N2, real isophorone diamine
CAS 2855-13-2) has NEVER been tested against the PolyInfo/PolyUniverse-dedup corpus
(12,370 canonically-distinct structures, Yue 2024, Zenodo 10.5281/zenodo.12585902,
CC-BY-4.0, file PolyInfo_p.csv, already SHA-256-pinned and rights-cleared by W-D-NOV
2026-08-13). That fire (W-D-NOV / run_second_corpus_novelty_attack.py) hard-coded
IPDA = "CC1(CC(CC(C1)N)C)CN" -- the SAME C9H20N2 demethylated structure already
refuted by candidate-structure-identity-audit-v1 (2026-08-03) -- the identical
undisclosed-non-propagation defect ipda-structural-correction-propagation-chebi-v1
(2026-08-18) found in the ChEBI-corpus fire, now shown to ALSO afflict the PolyInfo-
corpus fire. Additionally, no fire has ever computed IPDA's NN Tanimoto (or InChIKey-
skeleton match) against the TRIPLE UNION of all three rights-clean corpora this module
now has pinned in-tree (OpenPoly-350 + PolyInfo-dedup-12370 + ChEBI-dedup-50383) --
each second corpus was tested against OpenPoly alone, never against each other jointly.

FALSIFICATION LOGIC: recompute IPDA's NN Tanimoto against PolyInfo-dedup and the
triple-union corpus using the CORRECT R-A07v2 v2_canonical structure, under the
identical Morgan(r2,2048)/Tanimoto pipeline and SHA-256-pinned corpora already used by
W-D-NOV and chebi-truthset-second-corpus-v1. If IPDA's NN Tanimoto against PolyInfo-
dedup or the triple-union corpus is >= 0.40 (flip NOVEL -> NOT-NOVEL), or an exact
InChIKey-skeleton match appears in PolyInfo, then "IPDA alone survives across every
corpus tested" is REFUTED -- the broadest and most heavily-relied-upon reference
universe this module has ever assembled catches it. If IPDA remains NOVEL against
PolyInfo alone and the triple union, the claim survives the hardest and widest
corpus-coverage test this module has run against it to date.

POSITIVE CONTROL: plants an exact duplicate of the CORRECT IPDA structure as a
synthetic extra PolyInfo corpus row (the defect this attack exists to catch: a
candidate that IS already present in the reference universe). Confirms NN Tanimoto
vs PolyInfo jumps to 1.0, novel_vs_polyinfo_dedup and novel_vs_triple_union both flip
to False, and an exact InChIKey-skeleton match is detected -- i.e. the detection
pipeline actually fires on a planted duplicate rather than trivially returning NOVEL.

Non-circularity: OpenPoly, ChEBI, and PolyInfo corpora are the identical SHA-256-locked
artifacts already used and pinned by R-A07v2 / chebi-truthset-second-corpus-v1 /
W-D-NOV respectively (re-verified below, byte-for-byte, no re-acquisition). IPDA's
"corrected" structure is the identical R-A07v2 v2_canonical string used by every prior
fire since 2026-08-04. Featurization is byte-identical (Morgan r2/2048, RDKit
rdFingerprintGenerator). Deterministic (no RNG) -> byte-stable two-replay.
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

POLYINFO_CSV = "/tmp/w-d-nov-fire2/PolyInfo_p.csv"
POLYINFO_CSV_SHA_EXPECTED = "8559c111c300ae3b5957b9b8e46c66fa047bc62ce930f2ec85929112f96c8470"

OUT_PATH = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ipda-polyinfo-triple/diagnostic.canonical.json"
MUTATE = "--mutate" in sys.argv  # positive control: plant an exact IPDA duplicate inside PolyInfo

IPDA_CORRECTED_V2 = "CC1(C)CC(N)CC(C)(CN)C1"  # C10H22N2, R-A07v2 v2_canonical, real isophorone diamine CAS 2855-13-2
IPDA_SIGNED_OPENPOLY_NN = 0.16666666666666666  # anchor: unchanged across all prior fires
IPDA_SIGNED_CHEBI_NN = 0.3333333333333333      # anchor: ipda-structural-correction-propagation-chebi-v1 (2026-08-18)
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
        if cs in seen:
            continue
        seen.add(cs)
        dedupe.append((name, chebi_id, cs, m))
        ik = inchikey_skeleton(m)
        if ik and ik not in ik_index:
            ik_index[ik] = (name, chebi_id, cs)
    return n_raw, dedupe, ik_index, csv_sha


def load_polyinfo(plant_duplicate_smiles=None):
    csv_sha = sha256_file(POLYINFO_CSV)
    assert csv_sha == POLYINFO_CSV_SHA_EXPECTED, f"PolyInfo CSV sha mismatch {csv_sha}"
    rows = list(csv.DictReader(open(POLYINFO_CSV)))
    n_rows = len(rows)
    corpus_all = []
    n_parse_fail = 0
    for i, r in enumerate(rows):
        smi_raw = r.get("Smiles")
        if not has(smi_raw):
            continue
        smi = cap(smi_raw)
        m = Chem.MolFromSmiles(smi)
        if m is None:
            n_parse_fail += 1
            continue
        corpus_all.append((f"PolyInfo_{i}", smi, m))
    if plant_duplicate_smiles is not None:
        m = Chem.MolFromSmiles(plant_duplicate_smiles)
        assert m is not None
        corpus_all.append(("PLANTED_IPDA_DUPLICATE", plant_duplicate_smiles, m))
    n_parsed = len(corpus_all)
    seen = set()
    dedupe = []
    ik_index = {}
    for name, smi, m in corpus_all:
        cs = Chem.MolToSmiles(m)
        if cs in seen:
            continue
        seen.add(cs)
        dedupe.append((name, smi, m))
        ik = inchikey_skeleton(m)
        if ik and ik not in ik_index:
            ik_index[ik] = (name, smi)
    dedupe_sha = sha("\n".join(sorted(Chem.MolToSmiles(m) for _, _, m in dedupe)).encode())
    return n_rows, n_parsed, n_parse_fail, dedupe, ik_index, csv_sha, dedupe_sha


def nn_similarity(test_fp, ref_fps):
    best, best_j = 0.0, -1
    for j, f in enumerate(ref_fps):
        s = DataStructs.TanimotoSimilarity(test_fp, f)
        if s > best:
            best, best_j = s, j
    return best, best_j


def main():
    t0 = time.time()
    n_op_raw, n_op_labeled, openpoly_dedupe, openpoly_csv_sha, openpoly_dedupe_sha = load_openpoly()
    print(f"[t={time.time()-t0:.1f}s] OpenPoly loaded: {len(openpoly_dedupe)} distinct", file=sys.stderr)

    n_chebi_raw, chebi_dedupe, chebi_ik_index, chebi_sha = load_chebi()
    print(f"[t={time.time()-t0:.1f}s] ChEBI loaded: raw={n_chebi_raw} distinct={len(chebi_dedupe)}", file=sys.stderr)

    plant = IPDA_CORRECTED_V2 if MUTATE else None
    n_pi_rows, n_pi_parsed, n_pi_parsefail, polyinfo_dedupe, polyinfo_ik_index, polyinfo_csv_sha, polyinfo_dedupe_sha = load_polyinfo(plant)
    print(f"[t={time.time()-t0:.1f}s] PolyInfo loaded: raw={n_pi_rows} distinct={len(polyinfo_dedupe)} planted={plant is not None}", file=sys.stderr)

    openpoly_fps = [fp(m) for _, _, m in openpoly_dedupe]
    chebi_fps = [fp(m) for _, _, _, m in chebi_dedupe]
    polyinfo_fps = [fp(m) for _, _, m in polyinfo_dedupe]
    union_fps = openpoly_fps + chebi_fps + polyinfo_fps
    union_labels = [("openpoly", nm) for nm, _, _ in openpoly_dedupe] + \
                   [("chebi", nm) for nm, _, _, _ in chebi_dedupe] + \
                   [("polyinfo", nm) for nm, _, _ in polyinfo_dedupe]
    print(f"[t={time.time()-t0:.1f}s] fingerprints built, triple-union size={len(union_fps)}", file=sys.stderr)

    mol = Chem.MolFromSmiles(IPDA_CORRECTED_V2)
    assert mol is not None
    f = fp(mol)
    cand_ik = inchikey_skeleton(mol)
    formula = rdMolDescriptors.CalcMolFormula(mol)

    nn_op, j_op = nn_similarity(f, openpoly_fps)
    nn_chebi, j_ch = nn_similarity(f, chebi_fps)
    nn_pi, j_pi = nn_similarity(f, polyinfo_fps)
    nn_union, j_un = nn_similarity(f, union_fps)

    chebi_ik_hit = chebi_ik_index.get(cand_ik) if cand_ik else None
    polyinfo_ik_hit = polyinfo_ik_index.get(cand_ik) if cand_ik else None

    anchor_openpoly_ok = abs(nn_op - IPDA_SIGNED_OPENPOLY_NN) < 1e-9
    anchor_chebi_ok = abs(nn_chebi - IPDA_SIGNED_CHEBI_NN) < 1e-9

    novel_openpoly = nn_op < NOVELTY_THRESHOLD
    novel_chebi = nn_chebi < NOVELTY_THRESHOLD
    novel_polyinfo = nn_pi < NOVELTY_THRESHOLD
    novel_union = nn_union < NOVELTY_THRESHOLD

    ipda_result = {
        "candidate_smiles": IPDA_CORRECTED_V2,
        "molecular_formula": formula,
        "candidate_inchikey_skeleton": cand_ik,
        "nn_tanimoto_vs_openpoly_350": nn_op,
        "openpoly_nn_match": openpoly_dedupe[j_op][0] if j_op >= 0 else None,
        "nn_tanimoto_vs_chebi_dedup": nn_chebi,
        "chebi_nn_match_id": chebi_dedupe[j_ch][1] if j_ch >= 0 else None,
        "chebi_nn_match_smiles": chebi_dedupe[j_ch][2] if j_ch >= 0 else None,
        "nn_tanimoto_vs_polyinfo_dedup": nn_pi,
        "polyinfo_nn_match": polyinfo_dedupe[j_pi][0] if j_pi >= 0 else None,
        "polyinfo_nn_match_smiles": polyinfo_dedupe[j_pi][1] if j_pi >= 0 else None,
        "nn_tanimoto_vs_triple_union_corpus": nn_union,
        "triple_union_nn_match": union_labels[j_un] if j_un >= 0 else None,
        "novel_vs_openpoly_350": novel_openpoly,
        "novel_vs_chebi_dedup": novel_chebi,
        "novel_vs_polyinfo_dedup": novel_polyinfo,
        "novel_vs_triple_union_corpus": novel_union,
        "exact_inchikey_skeleton_match_in_chebi": chebi_ik_hit is not None,
        "chebi_inchikey_match_entity": {"name": chebi_ik_hit[0], "chebi_id": chebi_ik_hit[1], "smiles": chebi_ik_hit[2]} if chebi_ik_hit else None,
        "exact_inchikey_skeleton_match_in_polyinfo": polyinfo_ik_hit is not None,
        "polyinfo_inchikey_match_entity": {"name": polyinfo_ik_hit[0], "smiles": polyinfo_ik_hit[1]} if polyinfo_ik_hit else None,
    }

    material_flip = (not novel_polyinfo) or (not novel_union) or ipda_result["exact_inchikey_skeleton_match_in_polyinfo"]

    out = {
        "attack_id": "amphora-molecule-novelty-ipda-polyinfo-triple-corpus-gap-v1",
        "mode": "positive_control_planted_ipda_duplicate_in_polyinfo" if MUTATE else "canonical",
        "claim_under_attack": "evidence/audit/chebi-truthset-second-corpus-v1/chebi-truthset-second-corpus-receipt.v1.dsse.json + evidence/audit/ipda-structural-correction-propagation-chebi-v1/ipda-structural-correction-propagation-chebi-receipt.v1.dsse.json (still-open, unrepaired: 'IPDA alone survives' NOVEL < 0.40 across every corpus tested so far)",
        "gap_alleged": (
            "W-D-NOV's second-corpus fire (evidence/phase0/repairs/W-D-NOV/work/fire2/"
            "run_second_corpus_novelty_attack.py, 2026-08-13) hard-codes IPDA = "
            "'CC1(CC(CC(C1)N)C)CN' -- the same C9H20N2 demethylated structure already "
            "refuted by candidate-structure-identity-audit-v1 -- so IPDA has NEVER been "
            "tested against the PolyInfo-dedup corpus (12,370 structures) under its "
            "correct R-A07v2 v2_canonical structure. No fire has ever tested IPDA (or "
            "any candidate) against the TRIPLE union of OpenPoly-350 + PolyInfo-dedup + "
            "ChEBI-dedup jointly; each second corpus was only ever unioned with OpenPoly "
            "alone."
        ),
        "refutation_criterion": (
            "IPDA's NN Tanimoto (correct R-A07v2 structure) vs PolyInfo-dedup or the "
            "triple-union corpus (OpenPoly-350 + ChEBI-dedup + PolyInfo-dedup) is >= 0.40 "
            "(flips NOVEL to NOT-NOVEL), or an exact InChIKey-skeleton match to any "
            "PolyInfo entity is found."
        ),
        "openpoly_corpus_recap": {
            "csv_sha256": openpoly_csv_sha, "n_rows_raw": n_op_raw, "n_rows_with_Tg": n_op_labeled,
            "n_canonically_unique_structures_after_dedup": len(openpoly_dedupe),
            "dedup_canonical_set_sha256": openpoly_dedupe_sha,
        },
        "chebi_corpus_recap": {
            "sdf_gz_sha256": chebi_sha, "n_records_raw": n_chebi_raw,
            "n_canonically_unique_structures_after_dedup": len(chebi_dedupe),
        },
        "polyinfo_corpus_recap": {
            "csv_sha256": polyinfo_csv_sha, "n_rows_raw": n_pi_rows,
            "n_rows_smiles_parsed": n_pi_parsed, "n_parse_failures": n_pi_parsefail,
            "n_canonically_unique_structures_after_dedup": len(polyinfo_dedupe),
            "planted_duplicate_row": plant is not None,
            "source": "PolyUniverse: Generation Results (Yue, T. et al. 2024), file PolyInfo_p.csv",
            "doi": "10.5281/zenodo.12585902", "license": "CC-BY-4.0",
            "rights_established_by": "evidence/phase0/repairs/W-D-NOV/done/W-D-NOV-second-corpus-novelty-retest-receipt.v1.dsse.json (2026-08-13)",
        },
        "triple_union_corpus_size": len(union_fps),
        "ipda_result": ipda_result,
        "material_flip_or_match_found": material_flip,
        "anchor_check_openpoly_nn_matches_signed_r_a07v2_value": anchor_openpoly_ok,
        "anchor_check_chebi_nn_matches_2026_08_18_corrected_value": anchor_chebi_ok if not MUTATE else None,
        "featurization": {"fingerprint_method": "Morgan/ECFP", "morgan_bits": 2048, "morgan_radius": 2,
                           "similarity_method": "Tanimoto (Jaccard on bit sets)",
                           "identity_method": "InChIKey (skeleton block only)",
                           "generator": "rdkit.Chem.rdFingerprintGenerator.GetMorganGenerator",
                           "rdkit_version": __import__("rdkit").__version__},
    }
    if MUTATE:
        out["positive_control"] = {
            "planted_defect": "an exact duplicate row of the CORRECT IPDA structure ('CC1(C)CC(N)CC(C)(CN)C1') appended to the PolyInfo-dedup corpus before deduplication/fingerprinting",
            "how_planted": "load_polyinfo(plant_duplicate_smiles=IPDA_CORRECTED_V2): a synthetic row named 'PLANTED_IPDA_DUPLICATE' with IPDA's own canonical SMILES is appended to the raw PolyInfo row list before the existing dedup/fingerprint pipeline runs, unmodified from the canonical run otherwise",
            "detected": bool(material_flip),
            "evidence": (
                f"nn_tanimoto_vs_polyinfo_dedup={nn_pi} (expect 1.0), "
                f"novel_vs_polyinfo_dedup={novel_polyinfo} (expect False), "
                f"novel_vs_triple_union_corpus={novel_union} (expect False), "
                f"polyinfo_nn_match={ipda_result['polyinfo_nn_match']} (expect PLANTED_IPDA_DUPLICATE), "
                f"exact_inchikey_skeleton_match_in_polyinfo={ipda_result['exact_inchikey_skeleton_match_in_polyinfo']} (expect True)"
            ),
        }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    json.dump(out, open(OUT_PATH, "w"), indent=None, sort_keys=True)
    print(json.dumps({
        "status": "ok",
        "mode": out["mode"],
        "nn_openpoly": nn_op, "nn_chebi": nn_chebi, "nn_polyinfo": nn_pi, "nn_triple_union": nn_union,
        "novel_polyinfo": novel_polyinfo, "novel_triple_union": novel_union,
        "material_flip_or_match_found": material_flip,
        "anchor_openpoly_ok": anchor_openpoly_ok,
        "anchor_chebi_ok": anchor_chebi_ok if not MUTATE else "n/a(mutate)",
        "wall_clock_seconds": time.time() - t0,
    }, indent=2))


if __name__ == "__main__":
    main()
