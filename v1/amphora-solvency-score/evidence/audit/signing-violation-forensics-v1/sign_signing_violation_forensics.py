#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-solvency-score signing-violation forensic
close-out AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under
evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT flip scientific_readiness, does NOT modify the portfolio
manifest (66 receipts / 11 modules), any locked dataset, or the signed Phase-0
KPI files under evidence/phase0/kpis/. Derived key_id cross-checked vs the
pinned phase0 trust store.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-solvency-score/evidence/audit/signing-violation-forensics-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runb = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runb, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_signing_violation_forensics.py").read_bytes())

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
assert eval_pin, "evaluator key_id does not match pinned trust store"

body_obj = {
    "schema": "amphora.solvency-score.signing-violation-forensics-receipt.v1",
    "receipt_id": "signing-violation-forensics-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FORENSIC_AUDIT_CLOSEOUT",
    "module": "amphora-solvency-score",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": {
        "receipt_path": "amphora-solvency-score/evidence/phase0/kpis/hansen-temperature-envelope-v1-kpi.v1.json",
        "claim_text": (
            "The 4 SIGNING_VIOLATION alerts (2026-07-27T13:11, 2026-07-28T18:10, "
            "2026-07-29T23:06, 2026-07-31T04:09) indicate unsigned evidence was "
            "committed by the loop."
        ),
    },
    "alerts_investigated": diag["alerts_investigated"],
    "root_cause": diag["root_cause"],
    "per_file_verification": diag["per_file_verification"],
    "aggregate": diag["aggregate"],
    "conclusion": diag["conclusion"],
    "verdict": "CLAIM_REFUTED",
    "recommendation": diag["recommendation"],
    "closes": [
        "SIGNING_VIOLATION alert 2026-07-27T13:11 (false positive, field-name mismatch)",
        "SIGNING_VIOLATION alert 2026-07-28T18:10 (false positive, field-name mismatch)",
        "SIGNING_VIOLATION alert 2026-07-29T23:06 (false positive, field-name mismatch)",
        "SIGNING_VIOLATION alert 2026-07-31T04:09 (false positive, field-name mismatch)",
    ],
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "harness_sha256": harness_sha,
        "kpi_pointer_verification_pubkey": diag["pinned_verification_pubkey"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runb),
        "byte_identical": canon == runb,
        "harness_sha256": harness_sha,
        "determinism": "pure-stdlib + cryptography Ed25519-verify-only, no wall-clock, no RNG",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.solvency-score-signing-violation-forensics+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "signing-violation-forensics-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
