#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-design-rule-score
applicability-domain-leverage-extrapolation-v1 AUDIT_ONLY receipt. AUDIT_ONLY:
signs an audit receipt under benchmarks/; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest (66 receipts /
11 modules), module-manifest.json, any locked dataset, or a signed Phase-0
KPI. Two-replay byte gate enforced. Derived key_id cross-checked vs pinned
trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-design-rule-score/benchmarks/applicability-domain-leverage-extrapolation-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

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

canon = (BENCH / "applicability_domain_leverage_extrapolation.canonical.json").read_bytes()
runA = (BENCH / "applicability_domain_leverage_extrapolation.runA.json").read_bytes()
runB = (BENCH / "applicability_domain_leverage_extrapolation.runB.json").read_bytes()
assert canon == runA == runB, "two-replay bytes differ"
body_sha = sha(canon)
script_sha = sha((BENCH / "run_ad_leverage.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw(); rev_pub_hex = rev_pub.hex()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body = canon
ptype = "application/vnd.amphora.design-rule-score-applicability-domain-leverage-extrapolation-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {
    "schema": "amphora.design-rule-score.applicability-domain-leverage-extrapolation-receipt.v1",
    "module": "amphora-design-rule-score",
    "signing_authority": "AUDIT_ONLY",
    "authority_ceiling": "REAL_ARITHMETIC",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_module_manifest": False,
    "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "modifies_existing_receipts": False,
    "canonical_body_sha256": body_sha,
    "run_a_canonical_sha256": sha(runA),
    "run_b_canonical_sha256": sha(runB),
    "two_replay_sha256_gate": "PASS" if canon == runA == runB else "FAIL",
    "byte_identical": canon == runA == runB,
    "generator_script_sha256": script_sha,
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "eval_derives_pinned_trust_store_key_id": bool(eval_pin),
    "reviewer_key_id": rev_key_id,
    "reviewer_public_key_hex": rev_pub_hex,
    "reviewer_derives_pinned_trust_store_key_id": bool(rev_pin),
    "reviewer_signature_present": False,
    "trust_anchored_in_phase0_store": bool(eval_pin),
    "signature": envelope,
}
out = BENCH / "applicability-domain-leverage-extrapolation-receipt.v1.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_gate", receipt["two_replay_sha256_gate"])
print("body_sha256", body_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(envelope["signatures"]))
print("signature_verified", True)
