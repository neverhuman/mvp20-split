#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-formulation-arithmetic X-MASS-IDENTITY
AUDIT_ONLY done receipt. Refutes the framing of mass_balance_identity_rate
(one metric within the signed Phase-0 mass-balance KPI) as an independent,
falsifiable check of mass conservation. Does NOT modify the live Rust engine,
the locked dataset, the signed Phase-0 KPI, or the 66/11 manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-formulation-arithmetic/evidence/phase0/repairs/X-MASS-IDENTITY"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
KPI = ROOT / "amphora-formulation-arithmetic/evidence/phase0/kpis/formulation-arithmetic-mass-balance-kpi.v1.json"
LIB_RS = ROOT / "amphora-formulation-capabilities/src/lib.rs"
KPI_HARNESS = ROOT / "amphora-formulation-capabilities/tests/formulation_arithmetic_phase0_kpi.rs"


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
assert diag["verdict"] == "MASS_BALANCE_IDENTITY_RATE_TAUTOLOGICAL__ZERO_DETECTION_POWER"
assert diag["reimplementation_cross_check"]["reimplementation_matches_signed_benchmark"] is True
assert diag["defect_injection_demonstration"]["identity_rate_unchanged_by_defect"] is True
assert diag["defect_injection_demonstration"]["agreement_rate_detects_defect"] is True
harness_sha = sha(WORK / "run_mass_identity_tautology.py")
kpi_sha = sha(KPI)

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
    "schema": "amphora.formulation-arithmetic.mass-balance-identity-tautology-repair.v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-formulation-arithmetic",
    "campaign_item_id": "X-MASS-IDENTITY",
    "repair_status": "n/a_refutation_not_repair",
    "resolution": "refuted",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_live_rust_engine": False,
    "claim_tested": "amphora-formulation-arithmetic/evidence/phase0/kpis/formulation-arithmetic-mass-balance-kpi.v1.json :: mass_balance_identity_rate",
    "verdict": "CLAIM_REFUTED",
    "diagnostic": diag,
    "provenance": {
        "lib_rs_sha256": sha(LIB_RS),
        "kpi_harness_sha256": sha(KPI_HARNESS),
        "signed_phase0_kpi_sha256": kpi_sha,
        "kat_fixture": "amphora-formulation-arithmetic/reference/phase0-formulation-arithmetic-known-answer.v1.json",
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
        "used_for": "AUDIT_ONLY refutation receipt under evidence/phase0/repairs/X-MASS-IDENTITY/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.formulation-arithmetic-mass-balance-identity-tautology+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "X-MASS-IDENTITY.done-receipt.v1.dsse.json"
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
