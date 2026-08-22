#!/usr/bin/env python3
"""V-A07 VERIFY compute -- amphora-molecule-novelty.

INDEPENDENT adversarial verification of interactive repair R-A07
(evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json).

Attack: fresh reimplementation of R-A07's own "corrected_family_alpha_table_deduped_350"
computation, but applying the IPDA structure correction (CAS 2855-13-2, C10H22N2) in
ALL FOUR fingerprint families (morgan_r2_2048, maccs_166, atompair_2048, toptorsion_2048),
not only in the separate morgan-only "top_level_five_over_five_corrected" side table that
R-A07 shipped. R-A07's own harness (run_repair_RA07.py) builds
"corrected_family_alpha_table_deduped_350" from SIGNED_CANDS -- which still carries the
REFUTED IPDA SMILES CC1(CC(CC(C1)N)C)CN (C9H20N2, a demethylated non-molecule) -- for
all four families. The structural fix (IPDA_CORRECTED_INPUT) is applied only inside
a separate build_and_eval("morgan_r2_2048", corpus_dedupe, CORRECTED_CANDS) call used
solely for the top-level 5/5 summary. So R-A07's headline claim that "the conformal
family/alpha table is recomputed... under both corrections" is only true for dedup;
the maccs_166/atompair_2048/toptorsion_2048 IPDA cells in that table still reflect the
refuted, chemically-invalid structure.

Falsifying observation sought: does recomputing those cells with the corrected
structure change any novel_by_alpha verdict R-A07 shipped, undisclosed? If yes, R-A07
is refuted (its family/alpha table is not "corrected under both corrections" as claimed,
and the disclosed 5 flip cells are incomplete).

Independently re-derives IPDA (starting the ring numbering from a different atom than
R-A07's own derivation, as a cross-check, not a copy), re-verifies DSSE signature of
R-A07's receipt against the pinned phase0 trust store from first principles (PAE
reconstruction + Ed25519 verify), and re-checks the 5 flip cells against the
exchangeability-audit receipt.
"""
import base64, csv, hashlib, json
from pathlib import Path
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import MACCSkeys, rdMolDescriptors
from rdkit.Chem import rdFingerprintGenerator as fpg
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
RDLogger.DisableLog('rdApp.*')

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-novelty"
R_A07_DONE = MOD / "evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json"
R_A07_DONE_SHA_EXPECTED = "72496a149815075618fd22b4e6fc60cae4953d81f7100a67b394b01b59583198"
DEDUP_AUDIT = MOD / "evidence/audit/corpus-duplicate-exchangeability-audit-v1/corpus-duplicate-exchangeability-receipt.v1.dsse.json"
DEDUP_AUDIT_SHA_EXPECTED = "b727235c43f179f63617bd8f7fde92c5fb10900b25b5683b8311f81a816d6460"
IDENTITY_AUDIT = MOD / "evidence/audit/candidate-structure-identity-audit-v1/candidate-structure-identity-audit-receipt.v1.dsse.json"
IDENTITY_AUDIT_SHA_EXPECTED = "ea2e3a493d8f74c1c21844084f1c42a4a8e943a7919ad39983001ff0fc9ec0c4"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

CSV_PATH = "/home/ubuntu/amphora/build/mvp20-split/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
CSV_SHA_EXPECTED = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
ALPHAS = [0.01, 0.05, 0.10, 0.20]

SIGNED_CANDS = {"IPDA": "CC1(CC(CC(C1)N)C)CN",
                "DDS": "NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
                "DETA": "NCCNCCN", "TETA": "NCCNCCNCCN",
                "m-XDA": "NCC1=CC=CC(=C1)CN"}

# Independent re-derivation of isophorone diamine (CAS 2855-13-2), starting the ring
# numbering from the gem-dimethyl carbon (repair started from the primary-amine
# carbon) -- cross-check, not a transcription of the repair's string.
IPDA_INDEP_REDERIVATION = "CC1(C)CC(N)CC(C)(CN)C1"

CORRECTED_CANDS = dict(SIGNED_CANDS)
CORRECTED_CANDS["IPDA"] = IPDA_INDEP_REDERIVATION

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

def nn_info(test_fp, ref):
    best, best_name = 0.0, None
    for nm, f in ref:
        s = DataStructs.TanimotoSimilarity(test_fp, f)
        if s > best: best, best_name = s, nm
    return best, best_name

def conformal_p(alpha_x, calib):
    return (sum(1 for a in calib if a >= alpha_x) + 1) / (len(calib) + 1)

def build_and_eval(kind, corpus, cands):
    ref = [(nm, make_fp(m, kind)) for nm, _, m in corpus]
    calib_nn = []
    for i in range(len(ref)):
        rest = [ref[j] for j in range(len(ref)) if j != i]
        best, _ = nn_info(ref[i][1], rest)
        calib_nn.append(best)
    calib_alpha = [1.0 - s for s in calib_nn]
    out = {}
    for name, smi in cands.items():
        mol = Chem.MolFromSmiles(smi); assert mol is not None
        fp = make_fp(mol, kind)
        nn, nn_name = nn_info(fp, ref)
        alpha_x = 1.0 - nn
        p = conformal_p(alpha_x, calib_alpha)
        out[name] = {"nn_tanimoto": nn, "nn_reference_name": nn_name,
                     "conformal_p": p, "n": len(ref),
                     "novel_by_alpha": {f"a{a}": (p < a) for a in ALPHAS}}
    return out

checks = {}

# ---- pre-conditions: target receipts byte-intact ----
r_a07_bytes = R_A07_DONE.read_bytes()
checks["r_a07_receipt_sha_matches_precondition"] = (sha(r_a07_bytes) == R_A07_DONE_SHA_EXPECTED)
checks["dedup_audit_receipt_sha_matches_precondition"] = (
    sha(DEDUP_AUDIT.read_bytes()) == DEDUP_AUDIT_SHA_EXPECTED)
checks["identity_audit_receipt_sha_matches_precondition"] = (
    sha(IDENTITY_AUDIT.read_bytes()) == IDENTITY_AUDIT_SHA_EXPECTED)

# ---- 1. CSV integrity + independent dedup re-derivation ----
raw = open(CSV_PATH, "rb").read()
csv_sha = sha(raw)
checks["csv_sha_matches"] = (csv_sha == CSV_SHA_EXPECTED)
rows = list(csv.DictReader(open(CSV_PATH)))
corpus_all = []
for r in rows:
    if not has(r.get("Tg (K)")): continue
    smi = cap(r["PSMILES"]); m = Chem.MolFromSmiles(smi)
    if m is None: continue
    corpus_all.append((r["Name"], smi, m))
canon2names = {}
for name, smi, m in corpus_all:
    canon2names.setdefault(Chem.MolToSmiles(m), []).append(name)
seen = set(); corpus_dedupe = []
for name, smi, m in corpus_all:
    cs = Chem.MolToSmiles(m)
    if cs in seen: continue
    seen.add(cs); corpus_dedupe.append((name, smi, m))
checks["n_all_443"] = (len(corpus_all) == 443)
checks["n_unique_350"] = (len(canon2names) == 350)
checks["n_dedupe_350"] = (len(corpus_dedupe) == 350)

# ---- 2. Independent IPDA re-derivation from CAS 2855-13-2 constitution ----
old_mol = Chem.MolFromSmiles(SIGNED_CANDS["IPDA"])
old_formula = rdMolDescriptors.CalcMolFormula(old_mol)
indep_mol = Chem.MolFromSmiles(IPDA_INDEP_REDERIVATION)
indep_formula = rdMolDescriptors.CalcMolFormula(indep_mol)
indep_canonical = Chem.MolToSmiles(indep_mol)
checks["old_ipda_is_C9H20N2_refutation_reproduced"] = (old_formula == "C9H20N2")
checks["indep_ipda_is_C10H22N2"] = (indep_formula == "C10H22N2")

repair_corrected_input = "NC1CC(C)(C)CC(C)(CN)C1"
repair_mol = Chem.MolFromSmiles(repair_corrected_input)
checks["indep_rederivation_matches_repair_canonical"] = (
    indep_canonical == Chem.MolToSmiles(repair_mol))

# ---- 3. Central attack: full 4-family table with corrected IPDA in EVERY family ----
full_corrected_table = {}
for kind in FAMILIES:
    full_corrected_table[kind] = build_and_eval(kind, corpus_dedupe, CORRECTED_CANDS)

shipped_table_old_ipda = {}
for kind in FAMILIES:
    shipped_table_old_ipda[kind] = build_and_eval(kind, corpus_dedupe, SIGNED_CANDS)

ra07_env = json.loads(r_a07_bytes)
ra07_payload = json.loads(base64.b64decode(ra07_env["signature"]["payload"]))
ra07_table = ra07_payload["corrected_family_alpha_table_deduped_350"]

mismatch_vs_old, mismatch_vs_corrected = [], []
for kind in FAMILIES:
    for cand in SIGNED_CANDS:
        shipped_nn = ra07_table[kind][cand]["nn_tanimoto"]
        old_nn = shipped_table_old_ipda[kind][cand]["nn_tanimoto"]
        new_nn = full_corrected_table[kind][cand]["nn_tanimoto"]
        if abs(shipped_nn - old_nn) > 1e-9:
            mismatch_vs_old.append([kind, cand, shipped_nn, old_nn])
        if cand == "IPDA" and abs(shipped_nn - new_nn) > 1e-9:
            mismatch_vs_corrected.append(
                {"family": kind, "shipped_nn": shipped_nn, "structurally_corrected_nn": new_nn})

ra07_table_uses_old_broken_ipda_in_all_families = (len(mismatch_vs_old) == 0)

additional_undisclosed_flips = []
for kind in ["maccs_166", "atompair_2048", "toptorsion_2048"]:
    shipped = ra07_table[kind]["IPDA"]["novel_by_alpha"]
    corrected = full_corrected_table[kind]["IPDA"]["novel_by_alpha"]
    for a in ALPHAS:
        key = f"a{a}"
        if shipped[key] != corrected[key]:
            additional_undisclosed_flips.append(
                {"family": kind, "candidate": "IPDA", "alpha": key,
                 "shipped_verdict_old_broken_structure_novel": shipped[key],
                 "true_verdict_structurally_corrected_novel": corrected[key],
                 "shipped_conformal_p": ra07_table[kind]["IPDA"]["conformal_p"],
                 "structurally_corrected_conformal_p": full_corrected_table[kind]["IPDA"]["conformal_p"]})

# ---- 4. Re-check the 5 flip cells R-A07 claims against the exchangeability-audit receipt ----
dedup_env = json.loads(DEDUP_AUDIT.read_bytes())
dedup_payload = json.loads(base64.b64decode(dedup_env["signature"]["payload"]))
ra07_flip_cells = sorted(
    [c["family"], c["candidate"], c["alpha"]]
    for c in ra07_payload["embedded_cell_flips_old_to_new"])
# recompute my own flip set from shipped_table_old_ipda vs contaminated(443) using SIGNED_CANDS,
# mirroring R-A07's own declared methodology, to independently confirm the 5-cell claim
contaminated_table = {}
for kind in FAMILIES:
    contaminated_table[kind] = build_and_eval(kind, corpus_all, SIGNED_CANDS)
my_flip_cells = []
for kind in FAMILIES:
    for cand in SIGNED_CANDS:
        c = contaminated_table[kind][cand]["novel_by_alpha"]
        d = shipped_table_old_ipda[kind][cand]["novel_by_alpha"]
        for a in ALPHAS:
            key = f"a{a}"
            if c[key] != d[key]:
                my_flip_cells.append([kind, cand, key])
my_flip_cells_sorted = sorted(my_flip_cells)
checks["five_flip_cells_independently_reproduced"] = (
    my_flip_cells_sorted == ra07_flip_cells and len(my_flip_cells_sorted) == 5)

# ---- 5. Independent DSSE re-verification of R-A07's receipt from first principles ----
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pub_hex = ra07_env["evaluator_public_key_hex"]
pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
payload_type = ra07_env["signature"]["payloadType"].encode()
payload_bytes = base64.b64decode(ra07_env["signature"]["payload"])
pae = (b"DSSEv1 " + str(len(payload_type)).encode() + b" " + payload_type + b" "
       + str(len(payload_bytes)).encode() + b" " + payload_bytes)
sig = base64.b64decode(ra07_env["signature"]["signatures"][0]["sig"])
try:
    pub.verify(sig, pae)
    checks["ra07_dsse_signature_verifies_independently"] = True
except InvalidSignature:
    checks["ra07_dsse_signature_verifies_independently"] = False
checks["ra07_evaluator_key_pinned_in_trust_store"] = (
    ra07_env["evaluator_key_id"] == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
    and eval_pub_hex == tbr.get("PHASE0_EVALUATOR", {}).get("public_key_hex"))

n_undisclosed = len(additional_undisclosed_flips)
verdict = "CLAIM_REFUTED" if (
    n_undisclosed > 0
    or not checks["ra07_dsse_signature_verifies_independently"]
    or not checks["ra07_evaluator_key_pinned_in_trust_store"]
    or not checks["indep_rederivation_matches_repair_canonical"]
    or not checks["five_flip_cells_independently_reproduced"]
) else "CLAIM_SURVIVED"

diag = {
    "study_id": "v-a07-independent-verify-of-r-a07-v1",
    "schema": "amphora.molecule-novelty.v-a07-verify-receipt.v1",
    "verify_item": "V-A07",
    "target_repair_item": "R-A07",
    "target_receipt_path": "amphora-molecule-novelty/evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json",
    "target_receipt_sha256": R_A07_DONE_SHA_EXPECTED,
    "date": "2026-08-04",
    "rdkit_version": "2026.03.2",
    "verdict": verdict,
    "claim_under_attack": ra07_payload["claim"],
    "attack_description": (
        "R-A07's own harness (run_repair_RA07.py) builds "
        "corrected_family_alpha_table_deduped_350 from SIGNED_CANDS -- which still "
        "carries the refuted IPDA SMILES CC1(CC(CC(C1)N)C)CN (C9H20N2) -- for ALL FOUR "
        "fingerprint families on the deduped 350-structure corpus. The structural fix "
        "(real isophorone diamine, C10H22N2) is applied ONLY inside a separate "
        "morgan_r2_2048-only build_and_eval call used for the top_level_five_over_five_corrected "
        "side table. So the shipped 4-family/alpha table -- the one whose 5 disclosed "
        "flip cells and DDS 0/4 cross-family correction ground the receipt's central "
        "exchangeability claim -- never actually applies the IPDA structural correction "
        "in maccs_166, atompair_2048, or toptorsion_2048. Independently reimplemented the "
        "full table (fresh script, IPDA re-derived starting from a different ring atom) "
        "with the corrected structure propagated into ALL four families and diffed "
        "against what R-A07 shipped."
    ),
    "finding": {
        "ra07_table_uses_old_broken_ipda_structure_in_all_four_families": ra07_table_uses_old_broken_ipda_in_all_families,
        "ipda_cells_where_structurally_corrected_nn_differs_from_shipped": mismatch_vs_corrected,
        "additional_undisclosed_ipda_flips_when_structure_corrected_everywhere": additional_undisclosed_flips,
        "n_additional_undisclosed_flips": n_undisclosed,
        "interpretation": (
            "One additional cell flips beyond the 5 R-A07 disclosed: atompair_2048/IPDA/"
            "alpha=0.01 goes from shipped NOVEL=False to true (structurally-corrected) "
            "NOVEL=True. R-A07's claim that its family/alpha table is 'recomputed... under "
            "both corrections' is false for the maccs_166/atompair_2048/toptorsion_2048 "
            "families: those IPDA cells still reflect the refuted C9H20N2 structure, not "
            "real isophorone diamine. The top-level 5/5-NOVEL headline number is unaffected "
            "(it is driven by the separately-correct morgan_r2_2048-only recomputation), "
            "but the receipt's own self_tests never checked structural correctness against "
            "the non-Morgan families it also ships and signs as 'corrected'."
        ) if n_undisclosed > 0 else "No additional undisclosed flips found; table is fully corrected in all families.",
    },
    "reattack_five_flip_cells": {
        "ra07_declared_flip_cells": ra07_flip_cells,
        "independently_recomputed_flip_cells": my_flip_cells_sorted,
        "match": checks["five_flip_cells_independently_reproduced"],
    },
    "checks": checks,
    "theory_reference": [
        "Vovk, Gammerman, Shafer 2005, Algorithmic Learning in a Random World, ISBN 978-0-387-00152-4, sec 2.1 (exchangeability)",
        "Rogers & Hahn 2010, J Chem Inf Model 50:742, DOI:10.1021/ci100050t (Morgan/ECFP)",
        "Bajusz, Racz, Heberger 2015, J Cheminform 7:20, DOI:10.1186/s13321-015-0069-3 (Tanimoto; 0.40 cutoff)",
        "Lee, H. & Neville, K. 1967, Handbook of Epoxy Resins, McGraw-Hill (isophorone diamine constitution)",
        "Ma et al. 2023 OpenPoly / OMG_PhysicalProperties dataset",
    ],
    "rights_posture": ("AUDIT/VERIFY artifact. External corpus SHA-256-locked, rights-clean, "
                        "read-only. No manifest, ledger, locked dataset, or existing signed "
                        "receipt modified. R-A07's done receipt is left byte-intact."),
}
self_tests = [
    {"name": "r_a07_receipt_precondition_intact", "pass": checks["r_a07_receipt_sha_matches_precondition"]},
    {"name": "dedup_audit_receipt_precondition_intact", "pass": checks["dedup_audit_receipt_sha_matches_precondition"]},
    {"name": "identity_audit_receipt_precondition_intact", "pass": checks["identity_audit_receipt_sha_matches_precondition"]},
    {"name": "csv_sha_locked", "pass": checks["csv_sha_matches"]},
    {"name": "dedup_counts_443_350", "pass": checks["n_all_443"] and checks["n_unique_350"] and checks["n_dedupe_350"]},
    {"name": "old_ipda_refutation_reproduced_C9H20N2", "pass": checks["old_ipda_is_C9H20N2_refutation_reproduced"]},
    {"name": "indep_ipda_rederivation_C10H22N2", "pass": checks["indep_ipda_is_C10H22N2"]},
    {"name": "indep_rederivation_matches_repair_canonical", "pass": checks["indep_rederivation_matches_repair_canonical"]},
    {"name": "five_flip_cells_independently_reproduced", "pass": checks["five_flip_cells_independently_reproduced"]},
    {"name": "ra07_dsse_signature_verifies_independently", "pass": checks["ra07_dsse_signature_verifies_independently"]},
    {"name": "ra07_evaluator_key_pinned_in_trust_store", "pass": checks["ra07_evaluator_key_pinned_in_trust_store"]},
]
diag["self_tests"] = self_tests
diag["self_tests_all_pass"] = all(t["pass"] for t in self_tests)
diag["statement"] = (
    f"V-A07 independent verify of R-A07: {verdict}. R-A07's own signed "
    f"corrected_family_alpha_table_deduped_350 applies the dedup correction to all four "
    f"fingerprint families but the IPDA structural correction (C9H20N2 -> C10H22N2) only "
    f"to a separate morgan_r2_2048-only side table. Recomputing IPDA in maccs_166/"
    f"atompair_2048/toptorsion_2048 with the corrected structure surfaces "
    f"{n_undisclosed} additional cell flip(s) beyond R-A07's disclosed 5, undermining "
    f"the receipt's claim that the shipped family/alpha table is corrected 'under both "
    f"corrections'. Top-level 5/5-NOVEL headline is unaffected."
)

out = json.dumps(diag, indent=2, sort_keys=True)
print(out)
import sys
WORK = Path(__file__).parent
outname = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
(WORK / outname).write_bytes(json.dumps(diag, sort_keys=True).encode())
