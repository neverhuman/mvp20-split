#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-tolerance-robustness normalized/adaptive conformal
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness (stays LOCKED_INTERNAL/UNVALIDATED), does NOT modify
the portfolio manifest (66 receipts / 11 modules), any locked dataset, or the
signed Phase-0 KPI. Derived key_id cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-tolerance-robustness/evidence/audit/normalized-adaptive-conformal-openpoly-tg-v1"
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
harness_sha = sha((BENCH / "run_normalized_openpoly.py").read_bytes())

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
    "schema": "amphora.tolerance-robustness.normalized-adaptive-conformal-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-tolerance-robustness",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim": diag["headline"], "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "dataset": diag["dataset"],
    "protocol": diag["protocol"],
    "base_learner_point_metrics": diag["base_learner_point_metrics"],
    "ordinary_constant_width_conformal": diag["ordinary_constant_width_conformal"],
    "normalized_adaptive_conformal": diag["normalized_adaptive_conformal"],
    "efficiency_comparison": diag["efficiency_comparison"],
    "adaptivity": diag["adaptivity"],
    "difficulty_conditional_coverage": diag["difficulty_conditional_coverage"],
    "observed_conclusions": diag["observed_conclusions"],
    "results": {
        "ordinary_marginal_coverage": diag["ordinary_constant_width_conformal"]["marginal_coverage"],
        "normalized_marginal_coverage": diag["normalized_adaptive_conformal"]["marginal_coverage"],
        "normalized_more_efficient_median": diag["efficiency_comparison"]["normalized_more_efficient_median"],
        "normalized_width_error_spearman_rho": diag["adaptivity"]["normalized_halfwidth_vs_abs_error_spearman_rho"],
        "normalized_width_error_spearman_p": diag["adaptivity"]["normalized_halfwidth_vs_abs_error_spearman_p"],
        "normalized_improves_worst_difficulty_stratum": diag["difficulty_conditional_coverage"]["normalized_improves_worst_stratum"],
        "observed_conclusions": diag["observed_conclusions"],
        "all_known_answer_gates_passed": diag["all_known_answer_gates_passed"],
    },
    "gates": diag["gates"],
    "prior_signed_receipts": diag["prior_signed_receipts"],
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "harness_sha256": harness_sha,
        "prior_receipt": "mondrian-conformal-openpoly-tg-v1 (fixed-bin category-conditional coverage)",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "numpy": "1.26.4", "scipy": "1.16.3", "sklearn": "1.7.2", "rdkit": "2026.03.2",
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
ptype = "application/vnd.amphora.tolerance-robustness-normalized-adaptive-conformal+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "normalized-adaptive-conformal-openpoly-tg-receipt.v1.dsse.json"
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
