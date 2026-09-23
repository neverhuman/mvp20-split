#!/usr/bin/env python3
"""R-C01 fire-1 checkpoint: DSSE-Ed25519-sign the three-attempt repair
checkpoint for amphora-tolerance-robustness campaign item R-C01. AUDIT_ONLY.
Does NOT claim acceptance met (mean coverage >= 0.90 not reached by any of
the three attempts this fire); repair_status stays 'in_progress'. Does NOT
modify the portfolio manifest, any locked dataset, or any existing signed
Phase-0 KPI. Does NOT supersede anything (no attempt this fire cleared the
acceptance bar, so nothing is landed to done/ or RETRACTION-INDEX.md).

Replicates the PAE / load_seed / payloadType / two-replay-gate / self-verify
construction used across this repo's sign_*.py scripts.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-tolerance-robustness"
REPAIR = MOD / "evidence/phase0/repairs/R-C01"
WORK = REPAIR / "work"
ATTEMPTS = REPAIR / "attempts"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
DATE = "2026-08-11"
FIRE_ID = "20260811T220001-1536912-c67c777e0eec"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon_bytes = (WORK / "checkpoint.canonical.json").read_bytes()
runB_bytes = (WORK / "checkpoint.runB.json").read_bytes()
assert canon_bytes == runB_bytes, "two-replay bytes differ"
checkpoint = json.loads(canon_bytes)
checkpoint_sha = sha(canon_bytes)

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

body_obj = {
    "schema": "amphora.tolerance-robustness.r-c01-repair-checkpoint.v1",
    "study_id": "amphora-tolerance-robustness-r-c01-fire1-checkpoint",
    "authority": "AUDIT_ONLY",
    "run_type": "REPAIR checkpoint (in-progress), campaign item R-C01: attempted scaffold-aware conformal repair of the OpenPoly Tg split-conformal marginal-coverage claim against the pinned 60-seed scaffold-disjoint Monte Carlo attack",
    "module": "amphora-tolerance-robustness",
    "campaign_item_id": "R-C01",
    "fire_id": FIRE_ID,
    "date": DATE,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "acceptance_met_this_fire": checkpoint["acceptance_met_this_fire"],
    "repair_status": checkpoint["repair_status"],
    "claim_under_attack": checkpoint["claim_under_attack"],
    "pinned_attack": checkpoint["pinned_attack"],
    "acceptance_criterion": checkpoint["acceptance_criterion"],
    "attempts": checkpoint["attempts"],
    "root_cause_common_to_all_attempts": checkpoint["root_cause_common_to_all_attempts"],
    "next_fire_pre_registered_direction": checkpoint["next_fire_pre_registered_direction"],
    "provenance": {
        "checkpoint_sha256": checkpoint_sha,
        "consolidation_script": "consolidate_checkpoint.py",
        "consolidation_script_sha256": sha_file(WORK / "consolidate_checkpoint.py"),
        "attempt_scripts": {
            "attempt1": sha_file(WORK / "run_weighted_conformal_repair.py"),
            "attempt2": sha_file(WORK / "run_scaffold_cvplus_repair.py"),
            "attempt3": sha_file(WORK / "run_scaffold_cvplus_v2.py"),
        },
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_checkpoint_sha256": checkpoint_sha,
        "runB_checkpoint_sha256": sha(runB_bytes),
        "byte_identical": canon_bytes == runB_bytes,
        "numpy": "1.26.4", "scipy": "1.16.3", "sklearn": "1.7.2", "pandas": "2.1.4", "rdkit": "2026.03.2",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair checkpoint under evidence/phase0/repairs/R-C01/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.tolerance-robustness-r-c01-repair-checkpoint+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

ATTEMPTS.mkdir(parents=True, exist_ok=True)
out = ATTEMPTS / "r-c01-fire1-repair-checkpoint-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", checkpoint_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
