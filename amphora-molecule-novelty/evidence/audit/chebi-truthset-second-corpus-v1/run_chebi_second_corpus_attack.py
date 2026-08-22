#!/usr/bin/env python3
"""amphora-molecule-novelty AUDIT_ONLY -- CHEBI SMALL-MOLECULE SECOND-CORPUS ATTACK.

ROTATION-mode falsification attack on the strongest still-live standing claim of
amphora-molecule-novelty: the signed KPI
evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json
("REAL FINDING: 5/5 candidates classified NOVEL", NN Tanimoto 0.1579-0.3929 vs the
442-row/350-distinct OpenPoly *polymer* corpus).

PRIOR ATTACK (W-D-NOV, 2026-08-13) already added one second corpus -- PolyInfo, itself
another POLYMER-repeat-unit corpus -- and the claim SURVIVED (all 5 stayed below 0.40
against the union). This fire uses a categorically different, harder reference corpus:
ChEBI release-252, 3-star curated entries -- a database of real, discrete SMALL-MOLECULE
chemical entities (not polymer repeat-unit fragments), already rights-cleared and in-tree
for amphora-molecule-property (rights_class DERIVATIVE_ALLOWED, CC-BY-4.0, see
amphora-molecule-property/reference/mvp20/data/feedback_v3/rights/rights_chebi_release_252_3star_v3.json).
It has never been used by amphora-molecule-novelty. A small-molecule database is the
correct-shaped corpus to catch "this candidate is already a cataloged known compound" --
which a polymer-repeat-unit corpus structurally cannot, since even an exact commodity
diamine curative gets compared only to capped monomer *fragments* of unrelated polymers.

FALSIFICATION LOGIC (mirrors W-D-NOV's own pre-registered criterion, corpus substituted):
if any of the 5 candidates classified NOVEL (NN Tanimoto < 0.40) against OpenPoly-350
alone has NN Tanimoto >= 0.40 against ChEBI-dedup (equivalently: flips to NOT-NOVEL under
the union of OpenPoly-350 and ChEBI-dedup), the "5/5 NOVEL" claim is REFUTED as stated.
We additionally check literal identity via InChIKey (skeleton block, ignoring
protonation/stereo layers) as a second, threshold-independent line of evidence: an exact
InChIKey-skeleton match means the candidate is not just "close to" but IS an already-
cataloged ChEBI entity, which no Tanimoto-threshold argument can talk around.

Non-circularity: OpenPoly corpus is the identical SHA-256-locked CSV + dedup set used by
every prior novelty receipt (R-A07 dedup-350, sha pinned below). ChEBI SDF is SHA-256-
locked to its own acquisition receipt. Featurization is byte-identical to the signed KPI
(Morgan r2/2048, RDKit rdFingerprintGenerator). Deterministic (no RNG) -> byte-stable
across replays. AUDIT_ONLY: touches no manifest, no locked dataset, no signed Phase-0 KPI,
writes only inside amphora-molecule-novelty/evidence/audit/.
"""
import csv, gzip, hashlib, json, sys, time
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator as fpg
RDLogger.DisableLog('rdApp.*')

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
OPENPOLY_CSV = f"{ROOT}/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
OPENPOLY_CSV_SHA_EXPECTED = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
OPENPOLY_DEDUP_SHA_EXPECTED = "74513e30071335d097ee83315f5b21249da86ea6a5d61e98a27d07b631593dce"

CHEBI_SDF = f"{ROOT}/amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.sdf.gz"
CHEBI_SDF_SHA_EXPECTED = "8f17627476c66e899dabe3cd7ae1cbb94f7ee6c67f2ee91f077a77a19c940ad7"

OUT_PATH = sys.argv[1] if len(sys.argv) > 1 else "/tmp/chebi-second-corpus/diagnostic.canonical.json"
MUTATE = "--mutate" in sys.argv  # positive-control mode: corrupt a candidate to a KNOWN ChEBI entity

CANDS = {"IPDA": "CC1(CC(CC(C1)N)C)CN", "DDS": "NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
         "DETA": "NCCNCCN", "TETA": "NCCNCCNCCN", "m-XDA": "NCC1=CC=CC(=C1)CN"}
SIGNED_BASELINE_NN = {"IPDA": 0.16666666666666666, "DDS": 0.39285714285714285,
                       "DETA": 0.16666666666666666, "TETA": 0.15789473684210525,
                       "m-XDA": 0.23809523809523808}
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
    ik_index = {}  # inchikey_skeleton -> (name, smi, mol) first occurrence
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


def nn_similarity(test_fp, ref_fps, skip_idx=None):
    best, best_j = 0.0, -1
    for j, f in enumerate(ref_fps):
        if j == skip_idx:
            continue
        s = DataStructs.TanimotoSimilarity(test_fp, f)
        if s > best:
            best, best_j = s, j
    return best, best_j


def main():
    t0 = time.time()
    cands = dict(CANDS)
    positive_control = None
    if MUTATE:
        # Positive control: replace DETA's SMILES with a byte-identical restatement of a
        # near-certain ChEBI-cataloged commodity chemical (acetone) to prove the detector
        # fires on a planted exact-catalog match, then restore for the report.
        planted_name, planted_smi = "DETA", "CC(C)=O"  # acetone, CHEBI:15347
        positive_control = {"planted_defect": f"{planted_name} candidate_smiles replaced with acetone SMILES ({planted_smi}), a certain-to-be-cataloged ChEBI entity",
                             "how_planted": f"CANDS['{planted_name}'] = '{planted_smi}' (was '{CANDS[planted_name]}')"}
        cands[planted_name] = planted_smi

    n_op_raw, n_op_labeled, openpoly_dedupe, openpoly_csv_sha, openpoly_dedupe_sha = load_openpoly()
    print(f"[t={time.time()-t0:.1f}s] OpenPoly loaded: {len(openpoly_dedupe)} distinct", file=sys.stderr)

    n_chebi_raw, n_chebi_parsed, chebi_dedupe, chebi_ik_index, chebi_sha = load_chebi()
    print(f"[t={time.time()-t0:.1f}s] ChEBI loaded: raw={n_chebi_raw} parsed={n_chebi_parsed} distinct={len(chebi_dedupe)}", file=sys.stderr)

    openpoly_fps = [fp(m) for _, _, m in openpoly_dedupe]
    chebi_fps = [fp(m) for _, _, _, m in chebi_dedupe]
    print(f"[t={time.time()-t0:.1f}s] fingerprints built", file=sys.stderr)

    union_fps = openpoly_fps + chebi_fps
    union_labels = [("openpoly", nm) for nm, _, _ in openpoly_dedupe] + \
                   [("chebi", nm) for nm, _, _, _ in chebi_dedupe]

    cand_results = {}
    for name, smi in cands.items():
        mol = Chem.MolFromSmiles(smi)
        assert mol is not None, f"candidate {name} SMILES failed to parse: {smi}"
        f = fp(mol)
        nn_openpoly, j_op = nn_similarity(f, openpoly_fps)
        nn_chebi, j_ch = nn_similarity(f, chebi_fps)
        nn_union, j_un = nn_similarity(f, union_fps)
        cand_ik = inchikey_skeleton(mol)
        ik_hit = chebi_ik_index.get(cand_ik) if cand_ik else None

        signed_nn = SIGNED_BASELINE_NN.get(name)
        anchor_exact = (signed_nn is not None and abs(nn_openpoly - signed_nn) < 1e-12)
        novel_openpoly = nn_openpoly < NOVELTY_THRESHOLD
        novel_chebi = nn_chebi < NOVELTY_THRESHOLD
        novel_union = nn_union < NOVELTY_THRESHOLD

        cand_results[name] = {
            "candidate_smiles": smi,
            "nn_tanimoto_vs_openpoly_350": nn_openpoly,
            "openpoly_nn_match": openpoly_dedupe[j_op][0] if j_op >= 0 else None,
            "anchor_exact_match_to_signed_kpi": anchor_exact,
            "nn_tanimoto_vs_chebi_dedup": nn_chebi,
            "chebi_nn_match_name": chebi_dedupe[j_ch][0] if j_ch >= 0 else None,
            "chebi_nn_match_id": chebi_dedupe[j_ch][1] if j_ch >= 0 else None,
            "chebi_nn_match_smiles": chebi_dedupe[j_ch][2] if j_ch >= 0 else None,
            "nn_tanimoto_vs_union_corpus": nn_union,
            "union_nn_match": union_labels[j_un] if j_un >= 0 else None,
            "novel_vs_openpoly_350": novel_openpoly,
            "novel_vs_chebi_dedup": novel_chebi,
            "novel_vs_union_corpus": novel_union,
            "flipped_novel_to_not_novel_under_union": (novel_openpoly and not novel_union),
            "candidate_inchikey_skeleton": cand_ik,
            "exact_inchikey_skeleton_match_in_chebi": ik_hit is not None,
            "inchikey_match_chebi_entity": {"name": ik_hit[0], "chebi_id": ik_hit[1], "smiles": ik_hit[2]} if ik_hit else None,
        }
        print(f"[t={time.time()-t0:.1f}s] {name}: nn_openpoly={nn_openpoly:.4f} nn_chebi={nn_chebi:.4f} ik_hit={ik_hit is not None}", file=sys.stderr)

    n_flips = sum(1 for v in cand_results.values() if v["flipped_novel_to_not_novel_under_union"])
    n_ik_hits = sum(1 for v in cand_results.values() if v["exact_inchikey_skeleton_match_in_chebi"])
    all_survive_union = all(v["novel_vs_union_corpus"] for v in cand_results.values())
    anchor_ok = all(v["anchor_exact_match_to_signed_kpi"] for k, v in cand_results.items() if k in SIGNED_BASELINE_NN and not (MUTATE and k == "DETA"))

    out = {
        "attack_id": "amphora-molecule-novelty-chebi-truthset-second-corpus-attack-v1",
        "mode": "mutated_positive_control" if MUTATE else "canonical",
        "claim_under_attack": "evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json#all_candidates_classified_novel_below_0_40_threshold (5/5 canonical epoxy-amine candidates NOVEL, NN Tanimoto < 0.40, vs OpenPoly-350 corpus alone)",
        "refutation_criterion": "Any of the 5 canonical candidates classified NOVEL (NN Tanimoto < 0.40) against OpenPoly-350 alone flips to NOT-NOVEL (NN Tanimoto >= 0.40) when the reference corpus is the union of OpenPoly-350 and ChEBI release-252 3-star-dedup; equivalently, an exact InChIKey-skeleton match to a cataloged ChEBI entity.",
        "chebi_corpus": {
            "source": "ChEBI release 252, 3-star curated subset (EBI FTP archive)",
            "url": "https://ftp.ebi.ac.uk/pub/databases/chebi/archive/rel252/SDF/chebi_3_stars.sdf.gz",
            "license": "CC-BY-4.0",
            "rights_class": "DERIVATIVE_ALLOWED",
            "rights_decision_file": "amphora-molecule-property/reference/mvp20/data/feedback_v3/rights/rights_chebi_release_252_3star_v3.json",
            "already_in_tree_for_module": "amphora-molecule-property (never previously used by amphora-molecule-novelty)",
            "sdf_gz_sha256": chebi_sha,
            "n_records_raw": n_chebi_raw,
            "n_records_parsed": n_chebi_parsed,
            "n_canonically_unique_structures_after_dedup": len(chebi_dedupe),
        },
        "openpoly_corpus_recap": {
            "csv_sha256": openpoly_csv_sha,
            "n_rows_raw": n_op_raw,
            "n_rows_with_Tg": n_op_labeled,
            "n_canonically_unique_structures_after_dedup": len(openpoly_dedupe),
            "dedup_canonical_set_sha256": openpoly_dedupe_sha,
        },
        "candidate_chebi_retest": cand_results,
        "anchor_check_openpoly_nn_matches_signed_kpi_exactly": anchor_ok,
        "n_candidates_flipped_novel_to_not_novel_under_chebi_union": n_flips,
        "n_candidates_with_exact_inchikey_skeleton_match_in_chebi": n_ik_hits,
        "all_5_survive_chebi_union_corpus_novelty_below_0_40": all_survive_union,
        "featurization": {"fingerprint_method": "Morgan/ECFP", "morgan_bits": 2048, "morgan_radius": 2,
                           "similarity_method": "Tanimoto (Jaccard on bit sets)",
                           "identity_method": "InChIKey (skeleton block only, ignoring protonation/stereo/isotope layers)",
                           "generator": "rdkit.Chem.rdFingerprintGenerator.GetMorganGenerator",
                           "rdkit_version": __import__("rdkit").__version__},
        "positive_control": positive_control,
    }
    if positive_control is not None:
        pc = cand_results["DETA"]
        positive_control["detected"] = bool(pc["exact_inchikey_skeleton_match_in_chebi"] or not pc["novel_vs_chebi_dedup"])
        positive_control["evidence"] = (
            f"planted candidate DETA=acetone: nn_tanimoto_vs_chebi_dedup={pc['nn_tanimoto_vs_chebi_dedup']:.6f}, "
            f"novel_vs_chebi_dedup={pc['novel_vs_chebi_dedup']}, "
            f"exact_inchikey_skeleton_match_in_chebi={pc['exact_inchikey_skeleton_match_in_chebi']} "
            f"(matched entity: {pc['inchikey_match_chebi_entity']})"
        )
        out["positive_control"] = positive_control

    Path_dir = "/".join(OUT_PATH.split("/")[:-1])
    import os
    os.makedirs(Path_dir, exist_ok=True)
    json.dump(out, open(OUT_PATH, "w"), indent=None, sort_keys=True)
    print(json.dumps({
        "status": "ok", "n_flips": n_flips, "n_ik_hits": n_ik_hits,
        "all_5_survive": all_survive_union, "anchor_ok": anchor_ok,
        "positive_control": out.get("positive_control"),
        "wall_clock_seconds": time.time() - t0,
    }, indent=2))


if __name__ == "__main__":
    main()
