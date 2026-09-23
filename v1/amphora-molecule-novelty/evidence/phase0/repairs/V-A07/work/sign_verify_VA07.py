#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V-A07 independent-verify receipt for amphora-molecule-novelty.
Construction replicates the module's own R-A07 sign_repair_RA07.py / the intake
validator's sign_canon_invariance.py exactly: pae(), load_seed(), payloadType style,
envelope fields, attestation keys.

This is a VERIFY artifact, not a repair: it modifies no existing signed artifact,
appends nothing to the falsification ledger itself (the ledger append is a separate
step done by the orchestrating agent), makes no manifest change, no authority
promotion, no scientific_readiness flip.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-novelty"
ITEM = MOD / "evidence/phase0/repairs/V-A07"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

TARGET_RECEIPT = "amphora-molecule-novelty/evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json"
TARGET_RECEIPT_SHA = "72496a149815075618fd22b4e6fc60cae4953d81f7100a67b394b01b59583198"

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
harness_sha = sha((WORK / "run_verify_VA07.py").read_bytes())

# target (verified) receipt must be byte-intact right now -- we did NOT modify it
cur_target_sha = sha((ROOT / TARGET_RECEIPT).read_bytes())
assert cur_target_sha == TARGET_RECEIPT_SHA == diag["target_receipt_sha256"], \
    "target receipt changed since verification ran"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key not anchored in phase0 trust store"

body_obj = {
    "schema": diag["schema"],
    "receipt_id": "v-a07-independent-verify-of-r-a07-v1",
    "module_id": "amphora-molecule-novelty",
    "verify_item": "V-A07",
    "target_repair_item": diag["target_repair_item"],
    "target_receipt_path": diag["target_receipt_path"],
    "target_receipt_sha256": diag["target_receipt_sha256"],
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "date": diag["date"],
    "generated_on_host": "xbabe2",
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "trust_anchored_in_phase0_store": True,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "appends_to_falsification_ledger": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "verdict": diag["verdict"],
    "claim_under_attack": diag["claim_under_attack"],
    "attack_description": diag["attack_description"],
    "finding": diag["finding"],
    "reattack_five_flip_cells": diag["reattack_five_flip_cells"],
    "checks": diag["checks"],
    "statement": diag["statement"],
    "self_tests": diag["self_tests"],
    "self_tests_all_pass": diag["self_tests_all_pass"],
    "theory_reference": diag["theory_reference"],
    "rights_posture": diag["rights_posture"],
    "rdkit_version": diag["rdkit_version"],
    "reproducibility": {
        "byte_identical": canon == runB,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "harness_sha256": {"run_verify_VA07.py": harness_sha},
        "replay_method": ("run_verify_VA07.py executed twice with distinct output "
                           "filenames; canonical payload serialized with "
                           "json.dumps(sort_keys=True) each run and asserted byte-equal "
                           "before signing"),
        "two_replay_sha256_gate": "PASS",
    },
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "used_for": "AUDIT_ONLY independent-verify receipt under evidence/phase0/repairs/",
        "derives_pinned_trust_store_key_id": True,
        "signs_phase0_evaluation_or_review": False,
    },
}
body = json.dumps(body_obj, sort_keys=True).encode()
payload_b64 = base64.b64encode(body).decode()
payload_type = "application/vnd.amphora.molecule-novelty-v-a07-verify+json"
sig = eval_sk.sign(pae(payload_type, body))
sig_b64 = base64.b64encode(sig).decode()

envelope = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": {
        "payloadType": payload_type,
        "payload": payload_b64,
        "signatures": [{"keyid": eval_key_id, "sig": sig_b64}],
    },
}

# self-verify before declaring
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
pub.verify(sig, pae(payload_type, body))

DONE.mkdir(parents=True, exist_ok=True)
out_path = DONE / "v-a07-independent-verify-of-r-a07-receipt.v1.dsse.json"
out_path.write_text(json.dumps(envelope, indent=2))
print("WROTE", out_path)
print("verdict:", diag["verdict"])
print("self_verify_ok: True")
