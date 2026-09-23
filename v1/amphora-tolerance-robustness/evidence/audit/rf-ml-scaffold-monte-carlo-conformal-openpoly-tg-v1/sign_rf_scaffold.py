#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-tolerance-robustness RF-ML scaffold Monte
Carlo conformal-coverage falsification AUDIT_ONLY receipt. AUDIT_ONLY: signs
an audit receipt under evidence/audit/; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip scientific
readiness (stays LOCKED_INTERNAL/UNVALIDATED), does NOT modify the portfolio
manifest, any locked dataset, or the signed Phase-0 KPI. Derived key_id
cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-tolerance-robustness/evidence/audit/rf-ml-scaffold-monte-carlo-conformal-openpoly-tg-v1"
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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_rf_scaffold_conformal.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
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
    "schema": "amphora.tolerance-robustness.rf-ml-scaffold-monte-carlo-conformal-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-tolerance-robustness",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": diag["claim_under_attack"],
    "dataset": diag["dataset"],
    "n_seeds": diag["n_seeds"],
    "target_test_n_fixed_across_draws": diag["target_test_n_fixed_across_draws"],
    "rf_kwargs": diag["rf_kwargs"],
    "featurization": diag["featurization"],
    "summary_stats": diag["summary_stats"],
    "falsification_tests": diag["falsification_tests"],
    "verdict": diag["verdict"],
    "positive_control": diag.get("positive_control"),
    "theory_references": diag["theory_references"],
    "prior_analogous_attack_receipt": "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/repeated-scaffold-monte-carlo-conformal-openpoly-tg-receipt.v1.dsse.json",
    "escalation_note": "The RF-ML split-conformal sibling KPI (split-conformal-on-rf-ml-openpoly-tg-kpi.v1.json) reused "
        "the same 442/443-molecule openpoly Tg corpus as the already-refuted Ridge-base split-conformal claim "
        "but had only ever been evaluated on a single random seed=0 60/20/20 split -- never scaffold-tested. "
        "This receipt closes that gap: identical pinned N=60 scaffold-disjoint Monte Carlo protocol "
        "(same scaffold-assignment / test-fraction logic, same F1/F2/F3 pre-registered criteria, same "
        "0.90 floor and 0.25 breach threshold) applied to the RF base predictor with its exact published "
        "featurization (Morgan512 + log10 MolWt) and hyperparameters (n_estimators=300, max_depth=10, "
        "random_state=0). Result: mean scaffold-safe coverage collapses to 0.8621 (worse than the Ridge "
        "case's 0.8746), min single-draw coverage as low as 0.4693, 55% of the 60 draws (33/60) breach the "
        "0.90 floor, and the 95% bootstrap CI [0.8330, 0.8888] on the mean excludes the nominal 0.95 target. "
        "All three pre-registered falsification criteria (F1 Wilcoxon p=1.03e-9, F2 fraction-below-floor "
        "0.55 > 0.25, F3 bootstrap CI excludes 0.95) fire. The ML-base-predictor conformal wrapper's "
        "coverage guarantee, like its physics-Ridge sibling, does not survive scaffold-disjoint deployment "
        "shift on this corpus.",
    "provenance": {
        "harness_sha256": harness_sha,
        "prior_receipt": "repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1 (Ridge-base analogue, REFUTED)",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "numpy": "1.26.4", "scipy": "1.16.3", "sklearn": "1.7.2", "pandas": "2.1.4", "rdkit": "2026.03.2",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.tolerance-robustness-rf-ml-scaffold-monte-carlo-conformal+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "rf-ml-scaffold-monte-carlo-conformal-openpoly-tg-receipt.v1.dsse.json"
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
print("signature_len", len(envelope["signatures"][0]["sig"]))
print("signature_verified", True)
