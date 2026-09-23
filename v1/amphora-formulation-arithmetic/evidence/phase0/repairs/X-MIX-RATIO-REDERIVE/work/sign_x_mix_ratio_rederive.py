#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-formulation-arithmetic X-MIX-RATIO-REDERIVE
AUDIT_ONLY receipt. Independent re-derivation + independent-seed Monte Carlo
cross-check + positive-control defect-injection attack on mix-ratio-conversion-v1
(PHR-by-weight <-> by-volume mix-ratio <-> amine:epoxide equivalents index
conversion engine, GUM LPU + MC uncertainty). Does NOT modify the live Rust
engine, the locked dataset, the signed Phase-0 KPI, or the 66/11 manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-formulation-arithmetic/evidence/phase0/repairs/X-MIX-RATIO-REDERIVE"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
TARGET_RECEIPT = ROOT / "amphora-formulation-arithmetic/evidence/audit/mix-ratio-conversion-v1/mix-ratio-conversion-receipt.v1.dsse.json"
FACTS = ROOT / "amphora-ingredient-library/reference/mvp20/data/facts.json"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


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


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha_bytes(canon)
diag = json.loads(canon)
assert diag["verdict"] == "CLAIM_SURVIVED__MIX_RATIO_LPU_REDERIVATION_MATCHES"
assert diag["real_all_pass"] is True
assert diag["mc_all_pass"] is True
assert diag["defect_all_fire"] is True
harness_sha = sha(WORK / "rederive_mix_ratio.py")

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = "phase0-evaluator-" + hashlib.sha256(eval_pub).hexdigest()
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = "phase0-internal-reviewer-" + hashlib.sha256(bytes.fromhex(rev_pub_hex)).hexdigest()
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.formulation-arithmetic.mix-ratio-independent-rederivation-repair.v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-formulation-arithmetic",
    "campaign_item_id": "X-MIX-RATIO-REDERIVE",
    "repair_status": "n/a_survival_not_repair",
    "resolution": "survived",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_live_rust_engine": False,
    "claim_tested": "amphora-formulation-arithmetic/evidence/audit/mix-ratio-conversion-v1/mix-ratio-conversion-receipt.v1.dsse.json :: MIX_RATIO_CONVERSION_ENGINE_READY__KNOWN_ANSWER_BATTERY_PASS__PRIMER_REPRODUCED",
    "verdict": "CLAIM_SURVIVED",
    "refutation_criterion": diag["refutation_criterion"],
    "observed_result": diag["observed_result"],
    "positive_control": diag["positive_control"],
    "diagnostic": diag,
    "provenance": {
        "target_receipt_sha256": sha(TARGET_RECEIPT),
        "facts_json_sha256": sha(FACTS),
        "harness_sha256": harness_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha_bytes(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY survival receipt under evidence/phase0/repairs/X-MIX-RATIO-REDERIVE/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.formulation-arithmetic-mix-ratio-independent-rederivation+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "X-MIX-RATIO-REDERIVE.done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out))
print("signature_verified", True)
