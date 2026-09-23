#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-process-qc-twin estimated-parameter EWMA/CUSUM
(memory-detector) ARL0 degradation AUDIT_ONLY receipt. AUDIT_ONLY: signs an
audit receipt under evidence/audit/; does NOT sign a phase0 evaluation/review,
does NOT promote authority, does NOT flip scientific_readiness (stays
LOCKED_INTERNAL/UNVALIDATED), does NOT modify the portfolio manifest
(66 receipts / 11 modules), any locked dataset, or the signed Phase-0 process-qc
KPI. Derived key_id cross-checked vs pinned trust store. Two-replay SHA-256
byte-stability gate enforced.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-process-qc-twin/evidence/audit/estparam-memory-detector-arl-degradation-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = ROOT / "amphora-process-qc-twin/evidence/phase0/benchmark/benchmark-lock.v1.json"


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
assert diag["all_known_answer_gates_passed"] is True, "not all gates passed"
harness_sha = sha((BENCH / "run_memory_estparam_arl.py").read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())

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

tbl = {r["m"]: r for r in diag["estimated_parameter_distribution_by_baseline_m"]}
g = diag["gates"]

body_obj = {
    "schema": "amphora.process-qc-twin.estparam-memory-detector-arl-degradation-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-process-qc-twin",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim": diag["headline"], "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "detector_design": diag["detector_design"],
    "exact_conditional_reduction": diag["exact_conditional_reduction"],
    "theory_reference": diag["theory_reference"],
    "known_parameter_reference": diag["known_parameter_reference"],
    "results": {
        "all_known_answer_gates_passed": diag["all_known_answer_gates_passed"],
        "c4_max_abs_err": g["c4_constant_known_answer"]["max_abs_err"],
        "c4_passed": g["c4_constant_known_answer"]["passed"],
        "shewhart_anchor_passed": g["shewhart_known_parameter_anchor"]["passed"],
        "cusum_markov_vs_montgomery_t9p4_max_rel_err":
            g["cusum_markov_chain_vs_published"]["max_rel_err_vs_published"],
        "cusum_markov_vs_published_passed": g["cusum_markov_chain_vs_published"]["passed"],
        "ewma_lambda1_generalized_shewhart_max_rel_err":
            g["ewma_lambda_to_1_recovers_generalized_shewhart"]["max_rel_err"],
        "ewma_lambda1_passed": g["ewma_lambda_to_1_recovers_generalized_shewhart"]["passed"],
        "known_parameter_limit_max_rel_err":
            g["known_parameter_limit_m_to_inf"]["max_rel_err"],
        "known_parameter_limit_passed": g["known_parameter_limit_m_to_inf"]["passed"],
        "direct_mc_max_rel_err": g["direct_run_length_mc_method_agreement"]["max_rel_err"],
        "direct_mc_passed": g["direct_run_length_mc_method_agreement"]["passed"],
        "cusum_richardson_eliminant_max_rel_shift":
            g["cusum_richardson_eliminant_stability"]["max_eliminant_rel_shift"],
        "cusum_richardson_passed": g["cusum_richardson_eliminant_stability"]["passed"],
        "quadrature_convergence_max_rel_err": g["quadrature_grid_convergence"]["max_rel_err"],
        "quadrature_convergence_passed": g["quadrature_grid_convergence"]["passed"],
        "fail_closed_passed": g["fail_closed"]["passed"],
        "EWMA_m20_guaranteed_arl0_p05": tbl[20]["ewma"]["arl0_p05_guaranteed"],
        "EWMA_m30_guaranteed_arl0_p05": tbl[30]["ewma"]["arl0_p05_guaranteed"],
        "EWMA_m30_median_arl0": tbl[30]["ewma"]["arl0_median"],
        "EWMA_m300_guaranteed_arl0_p05": tbl[300]["ewma"]["arl0_p05_guaranteed"],
        "CUSUM_m20_guaranteed_arl0_p05": tbl[20]["cusum"]["arl0_p05_guaranteed"],
        "CUSUM_m30_guaranteed_arl0_p05": tbl[30]["cusum"]["arl0_p05_guaranteed"],
        "CUSUM_m30_median_arl0": tbl[30]["cusum"]["arl0_median"],
        "CUSUM_m300_guaranteed_arl0_p05": tbl[300]["cusum"]["arl0_p05_guaranteed"],
        "SHEWHART_m30_guaranteed_arl0_p05": tbl[30]["shewhart"]["arl0_p05_guaranteed"],
        "guaranteed_arl0_retention_at_m30_vs_known_parameter":
            diag["guaranteed_arl0_retention_at_m30_vs_known_parameter"],
        "worst_degrading_arm_at_m30": diag["worst_degrading_arm_at_m30"],
        "union_fa_p95_per_30_batch_m20": tbl[20]["union_false_alarms_per_30_batch"]["p95_guaranteed"],
        "union_fa_p95_per_30_batch_m30": tbl[30]["union_false_alarms_per_30_batch"]["p95_guaranteed"],
        "union_fa_p95_per_30_batch_m50": tbl[50]["union_false_alarms_per_30_batch"]["p95_guaranteed"],
        "union_fa_p95_per_30_batch_m100": tbl[100]["union_false_alarms_per_30_batch"]["p95_guaranteed"],
        "union_fa_median_per_30_batch_m30": tbl[30]["union_false_alarms_per_30_batch"]["median"],
        "known_parameter_union_fa_per_30_batch":
            diag["known_parameter_reference"]["union_false_alarms_per_30_batch"],
        "smallest_tabulated_m_meeting_fa_budget":
            diag["baseline_size_requirement"]["smallest_tabulated_m_meeting_criterion"],
        "m30_meets_locked_false_alarm_budget": bool(
            tbl[30]["union_false_alarms_per_30_batch"]["p95_guaranteed"] <= 1.5),
    },
    "estimated_parameter_distribution_by_baseline_m":
        diag["estimated_parameter_distribution_by_baseline_m"],
    "guaranteed_arl0_retention_at_m30_vs_known_parameter":
        diag["guaranteed_arl0_retention_at_m30_vs_known_parameter"],
    "baseline_size_requirement": diag["baseline_size_requirement"],
    "gates": diag["gates"],
    "kpi_linkage": diag["kpi_linkage"],
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "module_benchmark_lock_sha256": benchmark_lock_sha,
        "harness_sha256": harness_sha,
        "prior_receipts": "spc-arl-characterization-v1 (known-parameter ARL baseline, "
                          "all three arms); estparam-arl-degradation-v1 (Shewhart arm, "
                          "S estimator); moving-range-arl-degradation-v1 (Shewhart arm, "
                          "MRbar/d2 estimator)",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "mc_seed_base": diag["reproducibility_seed"]["mc_seed_base"],
        "mc_runs": diag["reproducibility_seed"]["mc_runs"],
        "quadrature_nodes": diag["reproducibility_seed"]["quadrature_nodes"],
        "ewma_states": diag["reproducibility_seed"]["ewma_states"],
        "cusum_states": diag["reproducibility_seed"]["cusum_states"],
        "blas_threads_pinned_to_1": True,
        "numpy": "1.26.4", "scipy": "1.16.3",
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
ptype = "application/vnd.amphora.process-qc-twin-estparam-memory-detector-arl-degradation+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "estparam-memory-detector-arl-degradation-receipt.v1.dsse.json"
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
