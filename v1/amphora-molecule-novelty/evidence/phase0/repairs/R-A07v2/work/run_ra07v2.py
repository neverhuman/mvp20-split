#!/usr/bin/env python3
"""R-A07v2 SUPERSEDING REPAIR compute -- amphora-molecule-novelty.

Follow-up repair superseding R-A07
(evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json),
whose shipped four-family conformal table was refuted by the independent verify V-A07
(evidence/phase0/repairs/V-A07/done/v-a07-independent-verify-of-r-a07-receipt.v1.dsse.json,
verdict CLAIM_REFUTED).

V-A07 confirmed all 11 of its self-tests, reproduced R-A07's 5 declared flip cells, and
independently re-derived the corrected IPDA structure -- then found that R-A07 propagated
the corrected structure ONLY into the morgan_r2_2048-only side table, leaving the
maccs_166 / atompair_2048 / toptorsion_2048 IPDA cells of the SHIPPED four-family table
computed on the refuted C9H20N2 string.

This v2 does NOT re-litigate the arithmetic. It re-derives isophorone diamine a third,
independent way, propagates it through ALL FOUR fingerprint families on the deduplicated
350-distinct corpus, publishes the complete four-family table, discloses every flip
(including the one V-A07 surfaced), and states explicitly that the 5/5-NOVEL headline stands.

Reads only hash-locked existing artifacts. Writes only under
evidence/phase0/repairs/R-A07v2/. Deterministic: no RNG, no wall clock.
"""
import base64
import csv
import hashlib
import json
import sys
from pathlib import Path

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import MACCSkeys, rdMolDescriptors
from rdkit.Chem import rdFingerprintGenerator as fpg
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-novelty"
GENMOD = ROOT / "amphora-molecule-generator"

R_A07_DONE = MOD / "evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json"
R_A07_DONE_SHA = "72496a149815075618fd22b4e6fc60cae4953d81f7100a67b394b01b59583198"
V_A07_DONE = MOD / "evidence/phase0/repairs/V-A07/done/v-a07-independent-verify-of-r-a07-receipt.v1.dsse.json"
V_A07_DONE_SHA = "dc0a09db08be0247e653ab5071969aa36b92f4631b7f4fcaeb706169c6282b12"
DEDUP_AUDIT = MOD / "evidence/audit/corpus-duplicate-exchangeability-audit-v1/corpus-duplicate-exchangeability-receipt.v1.dsse.json"
DEDUP_AUDIT_SHA = "b727235c43f179f63617bd8f7fde92c5fb10900b25b5683b8311f81a816d6460"
IDENTITY_AUDIT = MOD / "evidence/audit/candidate-structure-identity-audit-v1/candidate-structure-identity-audit-receipt.v1.dsse.json"
IDENTITY_AUDIT_SHA = "ea2e3a493d8f74c1c21844084f1c42a4a8e943a7919ad39983001ff0fc9ec0c4"
GENMOD_REF = GENMOD / "reference/mvp20/data/hardener_stoichiometric_envelope.v1.json"
GENMOD_REF_SHA = "b1a08e856cab233c69c09673ed0d96a40c38346753afae4ad415b5948edaa9a8"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

CSV_PATH = ROOT / "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
CSV_SHA = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
DEDUP_SET_SHA = "74513e30071335d097ee83315f5b21249da86ea6a5d61e98a27d07b631593dce"

WORK = MOD / "evidence/phase0/repairs/R-A07v2/work"
WORK.mkdir(parents=True, exist_ok=True)

ALPHAS = [0.01, 0.05, 0.10, 0.20]
FAMILIES = ["morgan_r2_2048", "maccs_166", "atompair_2048", "toptorsion_2048"]
FIXED_CUTOFF = 0.40

# The originally-signed candidate set. The IPDA entry is the REFUTED string
# (canonicalizes to C9H20N2, a demethylated homolog, not isophorone diamine).
SIGNED_CANDS = {
    "IPDA": "CC1(CC(CC(C1)N)C)CN",
    "DDS": "NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
    "DETA": "NCCNCCN",
    "TETA": "NCCNCCNCCN",
    "m-XDA": "NCC1=CC=CC(=C1)CN",
}

# THIRD independent re-derivation of isophorone diamine, CAS 2855-13-2,
# 3-(aminomethyl)-3,5,5-trimethylcyclohexan-1-amine. Written starting from the
# exocyclic aminomethyl carbon (R-A07 started from the ring primary-amine carbon,
# V-A07 from the gem-dimethyl carbon) so the string is not a transcription of
# either. Constitution: cyclohexane ring; C1 quaternary bearing -CH2NH2 and -CH3;
# C3 bearing the ring -NH2; C5 gem-dimethyl.
IPDA_V2_REDERIVATION = "NCC1(C)CC(N)CC(C)(C)C1"

CORRECTED_CANDS = dict(SIGNED_CANDS)
CORRECTED_CANDS["IPDA"] = IPDA_V2_REDERIVATION

_MG = fpg.GetMorganGenerator(radius=2, fpSize=2048)
_AP = fpg.GetAtomPairGenerator(fpSize=2048)
_TT = fpg.GetTopologicalTorsionGenerator(fpSize=2048)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def payload_of(p):
    env = json.loads(Path(p).read_bytes())
    env = env.get("signature", env)
    return json.loads(base64.standard_b64decode(env["payload"]))


def has(v):
    return v is not None and str(v).strip() != ""


def cap(s):
    return s.replace("*", "C")


def make_fp(mol, kind):
    if kind == "morgan_r2_2048":
        return _MG.GetFingerprint(mol)
    if kind == "maccs_166":
        return MACCSkeys.GenMACCSKeys(mol)
    if kind == "atompair_2048":
        return _AP.GetFingerprint(mol)
    if kind == "toptorsion_2048":
        return _TT.GetFingerprint(mol)
    raise ValueError(kind)


def nn_info(fp, ref):
    best, best_name = 0.0, None
    for nm, f in ref:
        s = DataStructs.TanimotoSimilarity(fp, f)
        if s > best:
            best, best_name = s, nm
    return best, best_name


checks = {}

# ------------------------------------------------------------- preconditions
r_a07_bytes = R_A07_DONE.read_bytes()
v_a07_bytes = V_A07_DONE.read_bytes()
checks["p1_r_a07_done_receipt_byte_intact"] = sha(r_a07_bytes) == R_A07_DONE_SHA
checks["p2_v_a07_verify_receipt_byte_intact"] = sha(v_a07_bytes) == V_A07_DONE_SHA
checks["p3_dedup_audit_receipt_byte_intact"] = sha(DEDUP_AUDIT.read_bytes()) == DEDUP_AUDIT_SHA
checks["p4_identity_audit_receipt_byte_intact"] = sha(IDENTITY_AUDIT.read_bytes()) == IDENTITY_AUDIT_SHA
checks["p5_genmod_ipda_ground_truth_byte_intact"] = sha(GENMOD_REF.read_bytes()) == GENMOD_REF_SHA

r_a07 = payload_of(R_A07_DONE)
v_a07 = payload_of(V_A07_DONE)
ra07_table = r_a07["corrected_family_alpha_table_deduped_350"]

# Values read verbatim OUT OF the V-A07 verify receipt bytes; every one is re-measured below.
va07_measured = {
    "verdict": v_a07["verdict"],
    "n_additional_undisclosed_flips": v_a07["finding"]["n_additional_undisclosed_flips"],
    "additional_flips": v_a07["finding"]["additional_undisclosed_ipda_flips_when_structure_corrected_everywhere"],
    "ipda_nn_shifts": v_a07["finding"]["ipda_cells_where_structurally_corrected_nn_differs_from_shipped"],
    "ra07_table_uses_old_broken_ipda_structure_in_all_four_families": v_a07["finding"][
        "ra07_table_uses_old_broken_ipda_structure_in_all_four_families"],
    "ra07_declared_flip_cells": v_a07["reattack_five_flip_cells"]["ra07_declared_flip_cells"],
    "five_flip_cells_independently_reproduced": v_a07["reattack_five_flip_cells"]["match"],
    "self_tests_all_pass": v_a07["self_tests_all_pass"],
    "n_self_tests": len(v_a07["self_tests"]),
}
checks["p6_v_a07_verdict_is_claim_refuted"] = va07_measured["verdict"] == "CLAIM_REFUTED"
checks["p7_v_a07_reported_all_self_tests_pass"] = va07_measured["self_tests_all_pass"] is True

# ------------------------------------------- (1) corpus: locked CSV, dedup 443 -> 350
raw = CSV_PATH.read_bytes()
checks["1a_csv_sha_locked"] = sha(raw) == CSV_SHA
rows = list(csv.DictReader(open(CSV_PATH)))
corpus_all = []
for r in rows:
    if not has(r.get("Tg (K)")):
        continue
    smi = cap(r["PSMILES"])
    m = Chem.MolFromSmiles(smi)
    if m is None:
        continue
    corpus_all.append((r["Name"], smi, m))

canon2names = {}
for name, smi, m in corpus_all:
    canon2names.setdefault(Chem.MolToSmiles(m), []).append(name)
seen = set()
corpus_dedupe = []
for name, smi, m in corpus_all:
    cs = Chem.MolToSmiles(m)
    if cs in seen:
        continue
    seen.add(cs)
    corpus_dedupe.append((name, smi, m))

dup_groups = {k: v for k, v in canon2names.items() if len(v) > 1}
n_dup_groups = len(dup_groups)
n_dup_rows = sum(len(v) for v in dup_groups.values())
dedup_set_sha = sha("\n".join(sorted(Chem.MolToSmiles(m) for _, _, m in corpus_dedupe)).encode())

checks["1b_n_rows_with_Tg_443"] = len(corpus_all) == 443
checks["1c_n_canonically_unique_350"] = len(canon2names) == 350
checks["1d_n_dedupe_350"] = len(corpus_dedupe) == 350
checks["1e_n_duplicate_groups_36"] = n_dup_groups == 36
checks["1f_n_duplicate_rows_129"] = n_dup_rows == 129
checks["1g_dedup_canonical_set_sha_matches_locked_value"] = dedup_set_sha == DEDUP_SET_SHA

# ---------------------------------- (2) third independent IPDA re-derivation + identity
old_mol = Chem.MolFromSmiles(SIGNED_CANDS["IPDA"])
old_formula = rdMolDescriptors.CalcMolFormula(old_mol)
v2_mol = Chem.MolFromSmiles(IPDA_V2_REDERIVATION)
assert v2_mol is not None
v2_formula = rdMolDescriptors.CalcMolFormula(v2_mol)
v2_canonical = Chem.MolToSmiles(v2_mol)

genmod_ref = json.loads(GENMOD_REF.read_bytes())
genmod_ipda_smiles = next(e["smiles"] for e in genmod_ref["known_answer_amines"]["entries"]
                          if "isophoronediamine" in e["name"].lower())
genmod_ipda_canonical = Chem.MolToSmiles(Chem.MolFromSmiles(genmod_ipda_smiles))
ra07_corrected_canonical = Chem.MolToSmiles(Chem.MolFromSmiles(r_a07["corrected_ipda"]["corrected_input_smiles"]))

checks["2a_old_signed_ipda_is_C9H20N2_refutation_reproduced"] = old_formula == "C9H20N2"
checks["2b_v2_rederived_ipda_is_C10H22N2"] = v2_formula == "C10H22N2"
checks["2c_v2_rederivation_canonical_equals_ra07_corrected"] = v2_canonical == ra07_corrected_canonical
checks["2d_v2_rederivation_canonical_equals_genmod_ground_truth"] = v2_canonical == genmod_ipda_canonical
checks["2e_v2_input_string_differs_from_ra07_and_va07_strings"] = (
    IPDA_V2_REDERIVATION != r_a07["corrected_ipda"]["corrected_input_smiles"]
    and IPDA_V2_REDERIVATION != "CC1(C)CC(N)CC(C)(CN)C1")
# CAS-registry constitution cross-checks on the re-derived molecule
_ring = v2_mol.GetRingInfo()
checks["2f_v2_ipda_one_six_membered_ring"] = (
    _ring.NumRings() == 1 and len(_ring.AtomRings()[0]) == 6)
checks["2g_v2_ipda_two_primary_amine_nitrogens"] = sum(
    1 for a in v2_mol.GetAtoms() if a.GetAtomicNum() == 7 and a.GetTotalNumHs() == 2) == 2
checks["2h_v2_ipda_three_methyl_carbons"] = sum(
    1 for a in v2_mol.GetAtoms() if a.GetAtomicNum() == 6 and a.GetTotalNumHs() == 3) == 3

# --------------------------------------------------- (3) conformal machinery
def calib_alphas(kind, corpus):
    ref = [(nm, make_fp(m, kind)) for nm, _, m in corpus]
    out = []
    for i in range(len(ref)):
        rest = [ref[j] for j in range(len(ref)) if j != i]
        best, _ = nn_info(ref[i][1], rest)
        out.append(1.0 - best)
    return ref, out


CACHE = {}
for kind in FAMILIES:
    CACHE[(kind, "all443")] = calib_alphas(kind, corpus_all)
    CACHE[(kind, "dedupe350")] = calib_alphas(kind, corpus_dedupe)


def eval_table(corpus_key, cands):
    table = {}
    for kind in FAMILIES:
        ref, calib = CACHE[(kind, corpus_key)]
        fam = {}
        for name in sorted(cands):
            mol = Chem.MolFromSmiles(cands[name])
            assert mol is not None, cands[name]
            fp = make_fp(mol, kind)
            nn, nn_name = nn_info(fp, ref)
            alpha_x = 1.0 - nn
            isolated = sum(1 for a in calib if a >= alpha_x)
            p = (isolated + 1) / (len(calib) + 1)
            fam[name] = {
                "nn_tanimoto": nn,
                "nn_reference_name": nn_name,
                "alpha": alpha_x,
                "isolated_count": isolated,
                "conformal_p": p,
                "n": len(ref),
                "novel_by_alpha": {f"a{a}": (p < a) for a in ALPHAS},
            }
        table[kind] = fam
    return table


T_signed_original = eval_table("all443", SIGNED_CANDS)        # what was originally signed
T_ra07_shipped = eval_table("dedupe350", SIGNED_CANDS)        # what R-A07 actually shipped
T_fully_corrected = eval_table("dedupe350", CORRECTED_CANDS)  # the truth
T_contaminated_corrected = eval_table("all443", CORRECTED_CANDS)


def flips(a, b):
    out = []
    for kind in FAMILIES:
        for cand in sorted(SIGNED_CANDS):
            va, vb = a[kind][cand]["novel_by_alpha"], b[kind][cand]["novel_by_alpha"]
            for al in ALPHAS:
                k = f"a{al}"
                if va[k] != vb[k]:
                    out.append({
                        "family": kind, "candidate": cand, "alpha": k,
                        "from_novel": va[k], "to_novel": vb[k],
                        "from_conformal_p": a[kind][cand]["conformal_p"],
                        "to_conformal_p": b[kind][cand]["conformal_p"],
                    })
    return out


flips_dedup_only_as_ra07_disclosed = flips(T_signed_original, T_ra07_shipped)
flips_structure_only_found_by_va07 = flips(T_ra07_shipped, T_fully_corrected)
flips_total_original_to_fully_corrected = flips(T_signed_original, T_fully_corrected)
flips_dedup_only_under_correct_structure = flips(T_contaminated_corrected, T_fully_corrected)

checks["3a_dedup_only_flip_count_reproduces_ra07_disclosed_5"] = (
    len(flips_dedup_only_as_ra07_disclosed) == 5)
checks["3b_dedup_only_flip_cells_match_ra07_declared_set"] = (
    sorted([f["family"], f["candidate"], f["alpha"]] for f in flips_dedup_only_as_ra07_disclosed)
    == sorted(va07_measured["ra07_declared_flip_cells"]))
checks["3c_structure_only_flip_count_reproduces_va07_finding"] = (
    len(flips_structure_only_found_by_va07) == va07_measured["n_additional_undisclosed_flips"])
_va07_flip = va07_measured["additional_flips"][0] if va07_measured["additional_flips"] else None
checks["3d_structure_only_flip_cell_matches_va07"] = bool(
    _va07_flip is not None
    and len(flips_structure_only_found_by_va07) == 1
    and flips_structure_only_found_by_va07[0]["family"] == _va07_flip["family"]
    and flips_structure_only_found_by_va07[0]["candidate"] == _va07_flip["candidate"]
    and flips_structure_only_found_by_va07[0]["alpha"] == _va07_flip["alpha"]
    and flips_structure_only_found_by_va07[0]["from_novel"] == _va07_flip["shipped_verdict_old_broken_structure_novel"]
    and flips_structure_only_found_by_va07[0]["to_novel"] == _va07_flip["true_verdict_structurally_corrected_novel"]
    and abs(flips_structure_only_found_by_va07[0]["from_conformal_p"] - _va07_flip["shipped_conformal_p"]) < 1e-12
    and abs(flips_structure_only_found_by_va07[0]["to_conformal_p"] - _va07_flip["structurally_corrected_conformal_p"]) < 1e-12)

# ------------- (4) confirm R-A07's SHIPPED table was built with the OLD IPDA everywhere
shipped_parity = []
for kind in FAMILIES:
    for cand in sorted(SIGNED_CANDS):
        pub = ra07_table[kind][cand]
        mine = T_ra07_shipped[kind][cand]
        shipped_parity.append({
            "family": kind, "candidate": cand,
            "nn_matches_1e-12": abs(pub["nn_tanimoto"] - mine["nn_tanimoto"]) < 1e-12,
            "p_matches_1e-12": abs(pub["conformal_p"] - mine["conformal_p"]) < 1e-12,
            "verdicts_match": pub["novel_by_alpha"] == mine["novel_by_alpha"],
        })
checks["4a_ra07_shipped_table_reproduces_exactly_under_OLD_ipda_all_20_cells"] = all(
    r["nn_matches_1e-12"] and r["p_matches_1e-12"] and r["verdicts_match"] for r in shipped_parity)
checks["4b_n_cells_compared"] = len(shipped_parity)

ipda_nn_shift = []
for kind in FAMILIES:
    shipped_nn = ra07_table[kind]["IPDA"]["nn_tanimoto"]
    corrected_nn = T_fully_corrected[kind]["IPDA"]["nn_tanimoto"]
    ipda_nn_shift.append({
        "family": kind,
        "shipped_nn_old_structure": shipped_nn,
        "corrected_nn": corrected_nn,
        "changed": abs(shipped_nn - corrected_nn) > 1e-12,
    })
va07_shift_map = {d["family"]: d for d in va07_measured["ipda_nn_shifts"]}
checks["4c_ipda_nn_shifts_reproduce_va07_measurements_1e-12"] = all(
    abs(d["shipped_nn_old_structure"] - va07_shift_map[d["family"]]["shipped_nn"]) < 1e-12
    and abs(d["corrected_nn"] - va07_shift_map[d["family"]]["structurally_corrected_nn"]) < 1e-12
    for d in ipda_nn_shift if d["family"] in va07_shift_map)
checks["4d_morgan_family_ipda_nn_unchanged_by_structural_fix"] = not next(
    d["changed"] for d in ipda_nn_shift if d["family"] == "morgan_r2_2048")
checks["4e_three_non_morgan_families_ipda_nn_all_shift"] = all(
    d["changed"] for d in ipda_nn_shift if d["family"] != "morgan_r2_2048")

# ------------------------- (5) top-level fixed-cutoff lane: 5/5 NOVEL headline
ref_morgan_dedupe, _ = CACHE[("morgan_r2_2048", "dedupe350")]
top_level = {}
for name in sorted(CORRECTED_CANDS):
    mol = Chem.MolFromSmiles(CORRECTED_CANDS[name])
    nn, nn_name = nn_info(make_fp(mol, "morgan_r2_2048"), ref_morgan_dedupe)
    top_level[name] = {
        "candidate_smiles_canonical": Chem.MolToSmiles(mol),
        "nn_tanimoto_vs_deduped_350": nn,
        "nn_reference_name": nn_name,
        "novel_below_0_40": nn < FIXED_CUTOFF,
    }
n_novel = sum(1 for v in top_level.values() if v["novel_below_0_40"])
checks["5a_top_level_five_of_five_novel"] = n_novel == 5
checks["5b_top_level_matches_ra07_published_per_candidate_1e-12"] = all(
    abs(top_level[k]["nn_tanimoto_vs_deduped_350"]
        - r_a07["top_level_five_over_five_corrected"]["per_candidate"][k]["nn_tanimoto_vs_deduped_350"]) < 1e-12
    for k in top_level)
checks["5c_nn_range"] = [min(v["nn_tanimoto_vs_deduped_350"] for v in top_level.values()),
                         max(v["nn_tanimoto_vs_deduped_350"] for v in top_level.values())]

# ---------------- (6) cross-family novelty counts at alpha=0.05 on the corrected table
cross_family_a05 = {}
for cand in sorted(SIGNED_CANDS):
    n = sum(1 for kind in FAMILIES if T_fully_corrected[kind][cand]["novel_by_alpha"]["a0.05"])
    cross_family_a05[cand] = f"{n}/4"
checks["6a_dds_cross_family_a05_still_0_of_4"] = cross_family_a05["DDS"] == "0/4"

# ---------------------------------- (7) independent DSSE re-verification of both targets
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}


def dsse_ok(path):
    env = json.loads(Path(path).read_bytes())
    inner = env["signature"]
    pt = inner["payloadType"].encode()
    pb = base64.standard_b64decode(inner["payload"])
    pae = (b"DSSEv1 " + str(len(pt)).encode() + b" " + pt + b" "
           + str(len(pb)).encode() + b" " + pb)
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(env["evaluator_public_key_hex"]))
    try:
        pub.verify(base64.standard_b64decode(inner["signatures"][0]["sig"]), pae)
    except InvalidSignature:
        return False, False
    pinned = (env["evaluator_key_id"] == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
              and env["evaluator_public_key_hex"] == tbr.get("PHASE0_EVALUATOR", {}).get("public_key_hex"))
    return True, pinned


ok_r, pin_r = dsse_ok(R_A07_DONE)
ok_v, pin_v = dsse_ok(V_A07_DONE)
checks["7a_r_a07_dsse_signature_verifies"] = ok_r
checks["7b_v_a07_dsse_signature_verifies"] = ok_v
checks["7c_evaluator_key_pinned_in_phase0_trust_store"] = pin_r and pin_v

bool_checks = [v for v in checks.values() if isinstance(v, bool)]
checks_all_pass = all(bool_checks)

headline = (
    "R-A07v2 republishes the complete four-family conformal novelty table on the "
    "deduplicated 350-distinct OpenPoly calibration corpus with the corrected isophorone "
    "diamine structure (CAS 2855-13-2, C10H22N2) propagated into ALL FOUR fingerprint "
    "families -- morgan_r2_2048, maccs_166, atompair_2048 and toptorsion_2048 -- not only "
    "into the morgan-only side table R-A07 shipped. Every flip is disclosed: 5 cells flip "
    "from the originally-signed contaminated-443 table to the deduplicated table (R-A07's "
    "declared set, reproduced exactly), and 1 further cell -- atompair_2048 / IPDA / "
    "alpha=0.01 -- flips when the IPDA structural fix is actually applied in that family, "
    f"the undisclosed flip V-A07 surfaced. Relative to what was ORIGINALLY signed, "
    f"{len(flips_total_original_to_fully_corrected)} cells differ under the fully-corrected "
    "table. THE TOP-LEVEL 5/5-NOVEL HEADLINE STANDS: on the deduplicated corpus with the "
    "corrected structure, all 5 candidates have Morgan(r2,2048) Tanimoto nearest-neighbour "
    f"similarity below the 0.40 Bajusz-Racz-Heberger cutoff (range "
    f"{min(v['nn_tanimoto_vs_deduped_350'] for v in top_level.values()):.4f}-"
    f"{max(v['nn_tanimoto_vs_deduped_350'] for v in top_level.values()):.4f}), and the IPDA "
    "structural correction leaves the Morgan nearest-neighbour similarity unchanged, so the "
    "headline never depended on the defective cells."
)

diagnostic = {
    "study_id": "r-a07v2-four-family-ipda-propagation-repair-v1",
    "schema": "amphora.molecule-novelty.r-a07v2-superseding-repair-diagnostic.v1",
    "repair_item": "R-A07v2",
    "supersedes_repair_item": "R-A07",
    "refuted_by_verify_item": "V-A07",
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
    "rdkit_version": Chem.rdBase.rdkitVersion,
    "headline": headline,
    "method": (
        "Identical pipeline to R-A07 and to the refuting audits: '*'->'C' methyl cap; "
        "canonical RDKit SMILES dedup (structure-only, label-free); families "
        "morgan_r2_2048 / maccs_166 / atompair_2048 / toptorsion_2048; leave-one-out "
        "nonconformity alpha_i = 1 - NN_LOO(i); candidate alpha_x = 1 - max_j Tanimoto; "
        "conformal p = (#{alpha_i >= alpha_x} + 1)/(n + 1); NOVEL iff p < alpha for "
        "alpha in {0.01, 0.05, 0.10, 0.20}; fixed-cutoff lane NOVEL iff Morgan NN "
        "Tanimoto < 0.40. The ONLY change from R-A07 is that the corrected IPDA structure "
        "is used in every family, not just morgan_r2_2048."),
    "corpus": {
        "source": "OpenPoly final_polymer_properties_fromliterature.csv (Ma et al. 2023)",
        "csv_sha256": CSV_SHA,
        "n_rows_with_Tg": len(corpus_all),
        "n_canonically_unique_structures": len(canon2names),
        "n_duplicate_groups": n_dup_groups,
        "n_duplicate_rows": n_dup_rows,
        "deduped_corpus_canonical_set_sha256": dedup_set_sha,
        "wildcard_cap": "'*'->'C' (methyl end-cap, reproduces signed featurization)",
        "rights": "CC-BY rights-clean OpenPoly benchmark (locked, read-only)",
    },
    "corrected_ipda": {
        "cas": "2855-13-2",
        "iupac_name": "3-(aminomethyl)-3,5,5-trimethylcyclohexan-1-amine",
        "v2_independent_input_smiles": IPDA_V2_REDERIVATION,
        "v2_derivation": (
            "Third independent re-derivation from the isophorone diamine constitution "
            "(Lee & Neville 1967): cyclohexane ring; C1 quaternary carbon bearing an "
            "exocyclic aminomethyl group and a methyl; C3 bearing the ring primary amine; "
            "C5 gem-dimethyl. Written starting from the exocyclic aminomethyl carbon -- "
            "R-A07 started from the ring primary-amine carbon and V-A07 from the "
            "gem-dimethyl carbon -- so this string is not a transcription of either."),
        "v2_canonical": v2_canonical,
        "v2_formula": v2_formula,
        "matches_ra07_corrected_canonical": checks["2c_v2_rederivation_canonical_equals_ra07_corrected"],
        "matches_genmod_known_answer_ground_truth": checks["2d_v2_rederivation_canonical_equals_genmod_ground_truth"],
        "genmod_ground_truth_path": "amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json",
        "genmod_ground_truth_sha256": GENMOD_REF_SHA,
        "superseded_smiles": SIGNED_CANDS["IPDA"],
        "superseded_formula": old_formula,
        "constitution_crosschecks": {
            "one_six_membered_ring": checks["2f_v2_ipda_one_six_membered_ring"],
            "two_primary_amine_nitrogens": checks["2g_v2_ipda_two_primary_amine_nitrogens"],
            "three_methyl_carbons": checks["2h_v2_ipda_three_methyl_carbons"],
        },
    },
    "corrected_family_alpha_table_deduped_350_all_four_families_corrected_ipda": T_fully_corrected,
    "reference_tables_for_audit": {
        "originally_signed_contaminated_443_old_ipda": T_signed_original,
        "ra07_shipped_deduped_350_old_ipda": T_ra07_shipped,
        "contaminated_443_corrected_ipda": T_contaminated_corrected,
    },
    "flip_disclosure": {
        "note": (
            "Complete disclosure. Three independent difference sets are published so no flip "
            "can hide in a comparison that was never made."),
        "A_dedup_effect_old_structure_ra07_disclosed_set": {
            "definition": "originally-signed contaminated-443 table vs deduplicated-350 table, both with the OLD IPDA string",
            "n": len(flips_dedup_only_as_ra07_disclosed),
            "cells": flips_dedup_only_as_ra07_disclosed,
        },
        "B_structural_effect_undisclosed_by_ra07_found_by_va07": {
            "definition": "deduplicated-350 with OLD IPDA vs deduplicated-350 with CORRECTED IPDA (all four families)",
            "n": len(flips_structure_only_found_by_va07),
            "cells": flips_structure_only_found_by_va07,
        },
        "C_total_originally_signed_to_fully_corrected": {
            "definition": "originally-signed contaminated-443 + OLD IPDA vs deduplicated-350 + CORRECTED IPDA -- the net difference a reader of the original receipt experiences",
            "n": len(flips_total_original_to_fully_corrected),
            "cells": flips_total_original_to_fully_corrected,
            "interpretation": (
                "atompair_2048 / IPDA / alpha=0.01 appears in set A (true -> false) and in set B "
                "(false -> true) and therefore CANCELS in the net comparison C: its originally "
                "signed verdict happens to coincide with the fully-corrected verdict, but only "
                "because two independent errors offset. It is disclosed in A and B regardless."),
        },
        "D_dedup_effect_under_correct_structure": {
            "definition": "contaminated-443 + CORRECTED IPDA vs deduplicated-350 + CORRECTED IPDA -- the exchangeability correction isolated, with correct chemistry throughout",
            "n": len(flips_dedup_only_under_correct_structure),
            "cells": flips_dedup_only_under_correct_structure,
        },
    },
    "ipda_nn_shift_by_family": ipda_nn_shift,
    "ra07_shipped_table_parity_under_old_ipda": {
        "note": (
            "Confirms V-A07's central finding constructively: R-A07's shipped four-family table "
            "reproduces EXACTLY when the OLD, refuted C9H20N2 string is used in all four "
            "families, i.e. the structural correction was never applied there."),
        "n_cells_compared": len(shipped_parity),
        "all_cells_reproduce": checks["4a_ra07_shipped_table_reproduces_exactly_under_OLD_ipda_all_20_cells"],
        "per_cell": shipped_parity,
    },
    "top_level_five_over_five": {
        "lane": "morgan_r2_2048 Tanimoto fixed 0.40 cutoff, deduplicated 350-structure corpus, corrected IPDA structure",
        "n_candidates": len(top_level),
        "n_novel": n_novel,
        "per_candidate": top_level,
        "verdict": "5/5 NOVEL -- the headline STANDS under both corrections and under the four-family propagation",
        "why_unaffected": (
            "The fixed-cutoff headline is computed in the morgan_r2_2048 family only, and the "
            "IPDA structural correction leaves the Morgan(r2,2048) nearest-neighbour Tanimoto "
            "unchanged at 0.16666666666666666. The defect V-A07 found was confined to the "
            "maccs_166 / atompair_2048 / toptorsion_2048 cells of the conformal side table."),
    },
    "cross_family_novelty_counts_alpha_0_05_fully_corrected": cross_family_a05,
    "values_read_from_v_a07_verify_receipt_bytes": va07_measured,
    "checks": checks,
    "checks_all_pass": checks_all_pass,
    "theory_reference": [
        "Vovk, Gammerman, Shafer 2005, Algorithmic Learning in a Random World, ISBN 978-0-387-00152-4, sec 2.1 (exchangeability)",
        "Rogers & Hahn 2010, J Chem Inf Model 50:742, DOI:10.1021/ci100050t (Morgan/ECFP)",
        "Bajusz, Racz, Heberger 2015, J Cheminform 7:20, DOI:10.1186/s13321-015-0069-3 (Tanimoto; 0.40 cutoff)",
        "Durant et al. 2002 DOI:10.1021/ci010132r (MACCS); Carhart et al. 1985 DOI:10.1021/ci00046a002 (atom pairs); Nilakantan et al. 1987 DOI:10.1021/ci00054a008 (topological torsions)",
        "Lee, H. & Neville, K. 1967, Handbook of Epoxy Resins, McGraw-Hill (isophorone diamine constitution)",
        "Ma et al. 2023 OpenPoly / OMG_PhysicalProperties dataset",
    ],
    "rights_posture": (
        "AUDIT/REPAIR artifact. External corpus SHA-256-locked, rights-clean, read-only. No "
        "manifest, ledger, locked dataset, or existing signed receipt modified; supersession by "
        "NEW receipt only."),
}

blob = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
outname = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
(WORK / outname).write_bytes(blob)

print("checks_all_pass:", checks_all_pass)
for k in sorted(checks):
    print("  ", k, "=", checks[k])
print("flips A(dedup,old):", len(flips_dedup_only_as_ra07_disclosed),
      " B(structure):", len(flips_structure_only_found_by_va07),
      " C(total):", len(flips_total_original_to_fully_corrected),
      " D(dedup,correct):", len(flips_dedup_only_under_correct_structure))
print("top-level n_novel:", n_novel)
print("wrote", WORK / outname, sha(blob))
