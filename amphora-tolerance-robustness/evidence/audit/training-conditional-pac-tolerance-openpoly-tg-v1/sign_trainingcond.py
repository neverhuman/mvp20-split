#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-tolerance-robustness training-conditional (PAC /
Wilks-Wald tolerance-region) AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt
under evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT flip scientific_readiness (stays LOCKED_INTERNAL/UNVALIDATED),
does NOT modify the portfolio manifest (66 receipts / 11 modules), any locked
dataset, or the signed Phase-0 KPI. Derived key_id cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-tolerance-robustness/evidence/audit/training-conditional-pac-tolerance-openpoly-tg-v1"
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
harness_sha = sha((BENCH / "run_trainingcond_openpoly.py").read_bytes())

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

law = diag["training_conditional_law_shipped"]
pac = diag["pac_correction_at_shipped_n"]
body_obj = {
    "schema": "amphora.tolerance-robustness.training-conditional-pac-tolerance-receipt.v1",
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
    "training_conditional_law_shipped": law,
    "lei2018_marginal_sandwich": diag["lei2018_marginal_sandwich"],
    "empirical_replicate_study": diag["empirical_replicate_study"],
    "tie_sensitivity": diag["tie_sensitivity"],
    "nonexchangeable_control": diag["nonexchangeable_control"],
    "pac_sample_size_requirements": diag["pac_sample_size_requirements"],
    "pac_correction_at_shipped_n": pac,
    "observed_conclusions": diag["observed_conclusions"],
    "results": {
        "prob_shipped_interval_undercovers_nominal": law["prob_conditional_coverage_below_nominal"],
        "training_conditional_coverage_p05": law["coverage_p05"],
        "expected_marginal_coverage": law["expected_coverage"],
        "empirical_fraction_of_calibration_draws_below_nominal":
            diag["empirical_replicate_study"]["fraction_of_calibration_draws_below_nominal"],
        "exact_law_goodness_of_fit_p_value":
            diag["empirical_replicate_study"]["goodness_of_fit_vs_exact_law"]["p_value"],
        "tie_free_subpool_goodness_of_fit_p_value":
            diag["tie_sensitivity"]["tie_free_goodness_of_fit_vs_exact_law"]["p_value"],
        "nonexchangeable_control_goodness_of_fit_p_value":
            diag["nonexchangeable_control"]["goodness_of_fit_vs_exact_law"]["p_value"],
        "pac_corrected_rank_k_prime": pac["rank_k_prime"],
        "pac_corrected_effective_alpha": pac["effective_alpha_prime"],
        "pac_corrected_prob_undercover": pac["prob_conditional_coverage_below_nominal"],
        "pac_median_halfwidth_ratio": pac["median_halfwidth_ratio_vs_nominal"],
        "pac_median_halfwidth_cost_K": pac["median_halfwidth_cost_K"],
        "wilks_one_sided_95_95_min_n": diag["gates"]["G2_KAT_wilks_one_sided_95_95_sample_size"]["computed_n"],
        "wilks_two_sided_95_95_min_n": diag["gates"]["G3_KAT_wilks_two_sided_95_95_sample_size"]["computed_n"],
        "observed_conclusions": diag["observed_conclusions"],
        "all_known_answer_gates_passed": diag["all_known_answer_gates_passed"],
    },
    "gates": diag["gates"],
    "prior_signed_receipts": diag["prior_signed_receipts"],
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "harness_sha256": harness_sha,
        "prior_receipt": "normalized-adaptive-conformal-openpoly-tg-v1 (locally-adaptive nonconformity)",
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
ptype = "application/vnd.amphora.tolerance-robustness-training-conditional-pac-tolerance+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "training-conditional-pac-tolerance-openpoly-tg-receipt.v1.dsse.json"
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
