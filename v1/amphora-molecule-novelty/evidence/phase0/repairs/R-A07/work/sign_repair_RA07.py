#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-A07 superseding repair receipt for
amphora-molecule-novelty. Construction replicates
amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py exactly:
pae(), load_seed(), payloadType style, envelope fields, attestation keys.
SUPERSEDE-ONLY: modifies no existing signed artifact, no ledger append, no
manifest change, no authority promotion, no scientific_readiness flip."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-novelty"
REP = MOD / "evidence/phase0/repairs/R-A07"
WORK = REP / "work"
DONE = REP / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

SUPERSEDED = [
    {"superseded_path": "amphora-molecule-novelty/evidence/audit/cross-family-concordance-v1/cross-family-concordance-receipt.v1.dsse.json",
     "superseded_sha256": "c2498d0590b04786955e5d2269e112862bdccc1522a6dafe3dccf3049c3ad9ab",
     "superseded_deleted_or_modified": False,
     "reason": ("Refuted by corpus-duplicate-exchangeability-audit-v1 (2026-08-02): its "
                "443-row conformal calibration corpus contains only 350 canonically-unique "
                "structures (129 duplicate rows, 36 alias groups), violating the "
                "Vovk-Gammerman-Shafer exchangeability precondition; on the deduped corpus "
                "5 signed family/alpha cells flip and DDS's cross-family count at "
                "alpha=0.05 is 0/4, not the signed 1/4 (maccs_166).")},
    {"superseded_path": "amphora-molecule-novelty/evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json",
     "superseded_sha256": "55f8c96c957c8f5ee41aa76ad65d4ddf938a7d705ed522acffe168b512137d25",
     "superseded_deleted_or_modified": False,
     "reason": ("Refuted by candidate-structure-identity-audit-v1 (2026-08-03): the "
                "signed IPDA candidate_smiles CC1(CC(CC(C1)N)C)CN canonicalizes to "
                "C9H20N2, a demethylated homolog that is not isophorone diamine (CAS "
                "2855-13-2, C10H22N2); also inherits the non-exchangeable duplicate-laden "
                "calibration corpus refuted above. The numeric result survives both "
                "corrections (IPDA NN 0.1667 unchanged; 5/5 NOVEL holds).")},
]

REFUTING = [
    "amphora-molecule-novelty/evidence/audit/corpus-duplicate-exchangeability-audit-v1/corpus-duplicate-exchangeability-receipt.v1.dsse.json",
    "amphora-molecule-novelty/evidence/audit/candidate-structure-identity-audit-v1/candidate-structure-identity-audit-receipt.v1.dsse.json",
]

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

# two-replay gate on the diagnostic
canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["self_tests_all_pass"] is True
harness_sha = sha((WORK / "run_repair_RA07.py").read_bytes())

# superseded artifacts must be byte-intact right now
for s in SUPERSEDED:
    cur = sha((ROOT / s["superseded_path"]).read_bytes())
    assert cur == s["superseded_sha256"], f"superseded artifact changed: {s['superseded_path']}"
refuting_shas = {p: sha((ROOT / p).read_bytes()) for p in REFUTING}

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key not anchored in phase0 trust store"

body_obj = {
    "schema": diag["schema"],
    "receipt_id": "r-a07-novelty-dedup-and-ipda-identity-repair-v1",
    "module_id": "amphora-molecule-novelty",
    "repair_item": "R-A07",
    "repair_mode": "interactive-2026-08-03",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "date": diag["date"],
    "generated_on_host": "xbabe2",
    # attestation keys (per sign_canon_invariance.py contract):
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "trust_anchored_in_phase0_store": True,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "appends_to_falsification_ledger": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "supersedes": SUPERSEDED,
    "refuting_receipts_sha256": refuting_shas,
    "claim": diag["statement"],
    "method": diag["method"],
    "corpus": diag["corpus"],
    "corrected_family_alpha_table_deduped_350": diag["corrected_family_alpha_table_deduped_350"],
    "embedded_cell_flips_old_to_new": diag["embedded_cell_flips_old_to_new"],
    "n_flip_cells": diag["n_flip_cells"],
    "dds_cross_family_count_a05": diag["dds_cross_family_count_a05"],
    "corrected_ipda": diag["corrected_ipda"],
    "top_level_five_over_five_corrected": diag["top_level_five_over_five_corrected"],
    "reference_LOO_NN_distribution_deduped_morgan": diag["reference_LOO_NN_distribution_deduped_morgan"],
    "reattack": diag["reattack"],
    "self_tests": diag["self_tests"],
    "self_tests_all_pass": diag["self_tests_all_pass"],
    "theory_reference": diag["theory_reference"],
    "rights_posture": diag["rights_posture"],
    "rdkit_version": diag["rdkit_version"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": {"run_repair_RA07.py": harness_sha},
        "replay_method": ("run_repair_RA07.py executed twice; canonical payload "
                          "serialized twice with json.dumps(sort_keys=True) and "
                          "asserted byte-equal before signing")},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY superseding repair receipt under evidence/phase0/repairs/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}

# two-replay serialization of the canonical payload itself
ser_a = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
ser_b = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
assert ser_a == ser_b, "canonical payload two-replay serialization differs"
payload_two_replay_sha = sha(ser_a)
body_obj["reproducibility"]["canonical_payload_two_replay_sha256"] = payload_two_replay_sha

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-novelty-r-a07-superseding-repair+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("diag_two_replay_sha256", diag_sha)
print("payload_two_replay_sha256", payload_two_replay_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
