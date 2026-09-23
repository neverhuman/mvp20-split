#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-process-qc-twin MRbar/d2-fed EWMA/CUSUM
(memory-detector) ARL0 degradation AUDIT_ONLY receipt (mr-memory-detector-
arl-degradation-v1). AUDIT_ONLY: signs an audit receipt under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness (stays LOCKED_INTERNAL/UNVALIDATED), does NOT modify
the portfolio manifest (66 receipts / 11 modules), any locked dataset, or the
signed Phase-0 process-qc KPI. Derived key_id cross-checked vs pinned trust
store. Two-replay SHA-256 byte-stability gate enforced.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-process-qc-twin/evidence/audit/mr-memory-detector-arl-degradation-v1"
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
harness_sha = sha((BENCH / "run_mr_memory_estparam_arl.py").read_bytes())
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

body_obj = {
    "schema": "amphora.process-qc-twin.mr-memory-detector-arl-degradation-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-process-qc-twin",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "attacked_claim": diag["attacked_claim"],
    "claim": diag["headline"], "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "detector_design": diag["detector_design"],
    "theory_reference": diag["theory_reference"],
    "known_parameter_reference": diag["known_parameter_reference"],
    "mr_estimator_moments_closed_form": diag["mr_estimator_moments_closed_form"],
    "results": {
        "all_known_answer_gates_passed": diag["all_known_answer_gates_passed"],
        "claim_verdict": diag["claim_verdict"],
        "gate_c4_d2_known_answer_passed": diag["gates"]["c4_d2_constants_known_answer"]["passed"],
        "gate_c4_d2_max_abs_err": diag["gates"]["c4_d2_constants_known_answer"]["c4_max_abs_err"],
        "gate_markov_chain_vs_published_passed":
            diag["gates"]["markov_chain_vs_published_anchors"]["passed"],
        "gate_markov_chain_cusum_max_rel_err":
            diag["gates"]["markov_chain_vs_published_anchors"]["cusum_max_rel_err"],
        "gate_mr_variance_closed_form_vs_mc_passed":
            diag["gates"]["mr_variance_closed_form_vs_mc"]["passed"],
        "gate_shewhart_cross_check_vs_moving_range_receipt_passed":
            diag["gates"]["shewhart_cross_check_vs_moving_range_receipt"]["passed"],
        "gate_quadrature_grid_convergence_passed":
            diag["gates"]["quadrature_grid_convergence"]["passed"],
        "gate_patnaik_proxy_vs_empirical_w_law_passed":
            diag["gates"]["patnaik_proxy_vs_empirical_w_law"]["passed"],
        "gate_known_parameter_limit_passed":
            diag["gates"]["known_parameter_limit_m_to_inf"]["passed"],
        "gate_fail_closed_passed": diag["gates"]["fail_closed"]["passed"],
        "m50_union_fa_p95_MRbar_d2": diag["baseline_size_requirement"]["m50_union_fa_p95_MRbar_d2"],
        "m50_union_fa_p95_Sc4_prior_receipt":
            diag["baseline_size_requirement"]["m50_union_fa_p95_Sc4_prior_receipt"],
        "m50_still_meets_budget_under_MRbar_d2":
            diag["baseline_size_requirement"]["m50_still_meets_budget_under_MRbar_d2"],
        "smallest_tabulated_m_meeting_criterion_MRbar_d2":
            diag["baseline_size_requirement"]["smallest_tabulated_m_meeting_criterion_MRbar_d2"],
        "smallest_tabulated_m_meeting_criterion_Sc4_prior_receipt":
            diag["baseline_size_requirement"]["smallest_tabulated_m_meeting_criterion_Sc4_prior_receipt"],
        "guaranteed_arl0_retention_at_m30_vs_known_parameter":
            diag["guaranteed_arl0_retention_at_m30_vs_known_parameter"],
    },
    "estimated_parameter_distribution_by_baseline_m":
        diag["estimated_parameter_distribution_by_baseline_m"],
    "baseline_size_requirement": diag["baseline_size_requirement"],
    "gates": diag["gates"],
    "kpi_linkage": diag["kpi_linkage"],
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "module_benchmark_lock_sha256": benchmark_lock_sha,
        "harness_sha256": harness_sha,
        "prior_receipts": "spc-arl-characterization-v1 (known-parameter ARL baseline, all "
                          "three arms); estparam-arl-degradation-v1 (Shewhart arm, S "
                          "estimator); moving-range-arl-degradation-v1 (Shewhart arm, MRbar/d2 "
                          "estimator); estparam-memory-detector-arl-degradation-v1 (EWMA/CUSUM "
                          "arms, S estimator -- the claim this receipt attacks).",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "mc_seed_base": diag["reproducibility_seed"]["mc_seed_base"],
        "n_sigma_mc": diag["reproducibility_seed"]["n_sigma_mc"],
        "quadrature_nodes": diag["reproducibility_seed"]["quadrature_nodes"],
        "quadrature_nodes_fine": diag["reproducibility_seed"]["quadrature_nodes_fine"],
        "ewma_states": diag["reproducibility_seed"]["ewma_states"],
        "cusum_states": diag["reproducibility_seed"]["cusum_states"],
        "blas_threads_pinned_to_1": True,
        "numpy": diag["reproducibility_seed"]["numpy"],
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
ptype = "application/vnd.amphora.process-qc-twin-mr-memory-detector-arl-degradation+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "mr-memory-detector-arl-degradation-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("claim_verdict", diag["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(envelope["signatures"][0]["sig"]))
print("signature_verified", True)
