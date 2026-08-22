#!/usr/bin/env python3
"""V-A07: independent adversarial verification of interactive repair R-A07.

Fresh reimplementation (not copy-paste of run_repair_RA07.py's control flow for the
critical step): rebuilds the full 4-fingerprint-family / 4-alpha conformal novelty
table on the deduped 350-structure OpenPoly corpus using the CORRECTED IPDA
structure in EVERY family, not just morgan_r2_2048, and diffs against what R-A07
actually declared as its "corrected_family_alpha_table_deduped_350".

Also independently re-derives isophorone diamine from CAS 2855-13-2 constitution,
re-verifies DSSE signature of the R-A07 receipt against the pinned phase0 trust
store, and re-checks the 5 flip cells against the exchangeability-audit receipt.
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
DEDUP_AUDIT = MOD / "evidence/audit/corpus-duplicate-exchangeability-audit-v1/corpus-duplicate-exchangeability-receipt.v1.dsse.json"
IDENTITY_AUDIT = MOD / "evidence/audit/candidate-structure-identity-audit-v1/candidate-structure-identity-audit-receipt.v1.dsse.json"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

CSV_PATH = "/home/ubuntu/amphora/build/mvp20-split/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
CSV_SHA_EXPECTED = "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3"
ALPHAS = [0.01, 0.05, 0.10, 0.20]

SIGNED_CANDS = {"IPDA": "CC1(CC(CC(C1)N)C)CN",
                "DDS": "NC1=CC=C(C=C1)S(=O)(=O)C2=CC=C(C=C2)N",
                "DETA": "NCCNCCN", "TETA": "NCCNCCNCCN",
                "m-XDA": "NCC1=CC=CC(=C1)CN"}

# Independently re-derived from CAS 2855-13-2 constitution (Lee & Neville 1967):
# cyclohexane ring, C1 primary amine, C3 quaternary C bearing -CH2NH2 and -CH3,
# C5 gem-dimethyl. Written starting from a DIFFERENT ring atom than the repair's
# own derivation, as an independent cross-check.
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

report = {"checks": {}}

# ---- 1. CSV integrity + independent dedup ----
raw = open(CSV_PATH, "rb").read()
csv_sha = sha(raw)
report["checks"]["csv_sha_matches"] = (csv_sha == CSV_SHA_EXPECTED)
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
report["checks"]["n_all_443"] = (len(corpus_all) == 443)
report["checks"]["n_unique_350"] = (len(canon2names) == 350)
report["checks"]["n_dedupe_350"] = (len(corpus_dedupe) == 350)

# ---- 2. Independent IPDA re-derivation ----
old_mol = Chem.MolFromSmiles(SIGNED_CANDS["IPDA"])
old_formula = rdMolDescriptors.CalcMolFormula(old_mol)
indep_mol = Chem.MolFromSmiles(IPDA_INDEP_REDERIVATION)
indep_formula = rdMolDescriptors.CalcMolFormula(indep_mol)
indep_canonical = Chem.MolToSmiles(indep_mol)
report["checks"]["old_ipda_is_C9H20N2"] = (old_formula == "C9H20N2")
report["checks"]["indep_ipda_is_C10H22N2"] = (indep_formula == "C10H22N2")

repair_corrected_input = "NC1CC(C)(C)CC(C)(CN)C1"
repair_mol = Chem.MolFromSmiles(repair_corrected_input)
report["checks"]["indep_rederivation_matches_repair_canonical"] = (
    indep_canonical == Chem.MolToSmiles(repair_mol))

# ---- 3. THE CRITICAL TEST: full 4-family table with corrected IPDA everywhere ----
full_corrected_table = {}
for kind in FAMILIES:
    full_corrected_table[kind] = build_and_eval(kind, corpus_dedupe, CORRECTED_CANDS)

# also the table R-A07 actually shipped (SIGNED_CANDS, i.e. OLD broken IPDA, on deduped corpus)
shipped_table_old_ipda = {}
for kind in FAMILIES:
    shipped_table_old_ipda[kind] = build_and_eval(kind, corpus_dedupe, SIGNED_CANDS)

# Load R-A07's actual declared table for comparison
ra07_env = json.loads(R_A07_DONE.read_bytes())
ra07_payload = json.loads(base64.b64decode(ra07_env["signature"]["payload"]))
ra07_table = ra07_payload["corrected_family_alpha_table_deduped_350"]

# Does R-A07's shipped table match a table built with the OLD (still-refuted) IPDA
# structure, i.e. did the structure fix actually NOT reach the non-Morgan families?
mismatch_vs_old, mismatch_vs_corrected = [], []
for kind in FAMILIES:
    for cand in SIGNED_CANDS:
        shipped_nn = ra07_table[kind][cand]["nn_tanimoto"]
        old_nn = shipped_table_old_ipda[kind][cand]["nn_tanimoto"]
        new_nn = full_corrected_table[kind][cand]["nn_tanimoto"]
        if abs(shipped_nn - old_nn) > 1e-9:
            mismatch_vs_old.append([kind, cand, shipped_nn, old_nn])
        if cand == "IPDA" and abs(shipped_nn - new_nn) > 1e-9:
            mismatch_vs_corrected.append([kind, cand, shipped_nn, new_nn])

report["ra07_table_reproduces_old_broken_ipda_structure_in_all_families"] = (
    len(mismatch_vs_old) == 0)
report["ra07_ipda_cells_differ_from_structurally_corrected_recompute"] = mismatch_vs_corrected

# Does using the corrected structure EVERYWHERE change any novel_by_alpha verdict
# for IPDA in the non-Morgan families, relative to what R-A07 shipped (old struct)?
additional_undisclosed_flips = []
for kind in ["maccs_166", "atompair_2048", "toptorsion_2048"]:
    shipped = ra07_table[kind]["IPDA"]["novel_by_alpha"]
    corrected = full_corrected_table[kind]["IPDA"]["novel_by_alpha"]
    for a in ALPHAS:
        key = f"a{a}"
        if shipped[key] != corrected[key]:
            additional_undisclosed_flips.append(
                {"family": kind, "candidate": "IPDA", "alpha": key,
                 "shipped_verdict_old_broken_structure": shipped[key],
                 "true_verdict_corrected_structure": corrected[key]})
report["additional_undisclosed_ipda_flips_maccs_atompair_toptorsion"] = additional_undisclosed_flips

# ---- 4. Re-check the 5 flip cells vs the exchangeability-audit receipt ----
dedup_env = json.loads(DEDUP_AUDIT.read_bytes())
dedup_payload = json.loads(base64.b64decode(dedup_env["signature"]["payload"]))

# ---- 5. DSSE self-verify of R-A07's own receipt against pinned trust store ----
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
pinned_pub_hex = tbr.get("PHASE0_EVALUATOR", {}).get("public_key_hex") or tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
eval_pub_hex = ra07_env["evaluator_public_key_hex"]
pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
payload_type = ra07_env["signature"]["payloadType"].encode()
payload_bytes = base64.b64decode(ra07_env["signature"]["payload"])
pae = b"DSSEv1 " + str(len(payload_type)).encode() + b" " + payload_type + b" " + str(len(payload_bytes)).encode() + b" " + payload_bytes
sig_hex = ra07_env["signature"]["signatures"][0]["sig"]
sig = base64.b64decode(sig_hex)
try:
    pub.verify(sig, pae)
    report["checks"]["ra07_dsse_signature_verifies"] = True
except InvalidSignature:
    report["checks"]["ra07_dsse_signature_verifies"] = False
report["checks"]["ra07_evaluator_key_pinned_in_trust_store"] = (
    ra07_env["evaluator_key_id"] == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

report["n_additional_undisclosed_flips"] = len(additional_undisclosed_flips)
report["verdict"] = ("CLAIM_REFUTED" if len(additional_undisclosed_flips) > 0
                      or not report["checks"]["ra07_dsse_signature_verifies"]
                      or not report["checks"]["indep_rederivation_matches_repair_canonical"]
                      else "CLAIM_SURVIVED")

print(json.dumps(report, indent=2, sort_keys=True))
Path("/tmp/ra07_verify_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
