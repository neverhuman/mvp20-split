#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cure-potlife-gate conformal-interval AUDIT_ONLY
receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED/PRE_PHASE_0), does NOT modify the portfolio
manifest (66 receipts / 11 modules), any locked dataset, or the signed Arrhenius
Phase-0 KPI. Derived key_id cross-checked vs pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cure-potlife-gate/evidence/audit/potlife-conformal-interval-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = ROOT / "amphora-cure-potlife-gate/evidence/phase0/benchmark/benchmark-lock.v1.json"
KPI = ROOT / "amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
RESULT = ROOT / "amphora-cure-potlife-gate/evidence/phase0/benchmark/result.v1.json"


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
harness_sha = sha((BENCH / "run_conformal_interval.py").read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())
kpi_sha = sha(KPI.read_bytes())
result_sha = sha(RESULT.read_bytes())

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

body_obj = {
    "schema": "amphora.cure-potlife-gate.conformal-interval-receipt.v1",
    "module": "amphora-cure-potlife-gate",
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim": diag["headline"], "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "nonconformity_score": diag["nonconformity_score"],
    "n_points": diag["n_points"], "families": diag["families"],
    "results": {
        "marginal_conformal_meets_nominal": diag["gates"]["G1_marginal_conformal_meets_nominal"]["passed"],
        "marginal_coverage_alpha0.10": diag["p1_marginal_loo_jackknife_plus"]["alpha_0.10"]["empirical_coverage"],
        "marginal_coverage_alpha0.20": diag["p1_marginal_loo_jackknife_plus"]["alpha_0.20"]["empirical_coverage"],
        "median_90pct_band_multiplicative_factor": diag["p1_marginal_loo_jackknife_plus"]["alpha_0.10"]["median_band_multiplicative_factor"],
        "bootstrap_ci95_coverage_alpha0.10": [
            diag["p1_bootstrap_ci_coverage_alpha0.10"]["ci95_lo"],
            diag["p1_bootstrap_ci_coverage_alpha0.10"]["ci95_hi"]],
        "family_conditional_marginal_valid_but_not_conditional": diag["gates"]["G2_family_conditional_validity"]["marginal_valid_but_not_family_conditional"],
        "families_undercovering_alpha0.10": diag["p2_leave_one_family_out_group_conformal"]["alpha_0.10"]["families_undercovering"],
        "gaussian_directional_bias_mean_log_resid": diag["p3_parametric_gaussian_band"]["gaussian_fit"]["mean_log_resid"],
        "hottest_extrapolation_40C_marginal_coverage": diag["per_held_out_temperature_marginal_coverage"]["40.00C"]["empirical_coverage_marginal_alpha0.10"],
        "mape_ties_to_signed_kpi": diag["gates"]["G4_mape_reproduces_signed_kpi"]["passed"],
        "score_fail_closed_rate": f'{diag["gates"]["G3_score_fail_closed"]["n_fail_closed"]}/{diag["gates"]["G3_score_fail_closed"]["n_probes"]}',
    },
    "gates": diag["gates"],
    "p1_marginal_loo_jackknife_plus": diag["p1_marginal_loo_jackknife_plus"],
    "p1_bootstrap_ci_coverage_alpha0.10": diag["p1_bootstrap_ci_coverage_alpha0.10"],
    "p2_leave_one_family_out_group_conformal": diag["p2_leave_one_family_out_group_conformal"],
    "p3_parametric_gaussian_band": diag["p3_parametric_gaussian_band"],
    "per_held_out_temperature_marginal_coverage": diag["per_held_out_temperature_marginal_coverage"],
    "crosscheck_mape_vs_signed_kpi": diag["crosscheck_mape_vs_signed_kpi"],
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "claim_locks": diag["claim_locks"],
    "provenance": {
        "module_benchmark_lock_sha256": benchmark_lock_sha,
        "signed_arrhenius_kpi_sha256": kpi_sha,
        "signed_truth_table_result_sha256": result_sha,
        "harness_sha256": harness_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
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
ptype = "application/vnd.amphora.cure-potlife-conformal-interval-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "potlife-conformal-interval-receipt.v1.dsse.json"
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
print("signature_len", len(receipt["signature"]["signatures"][0]["sig"]))
print("signature_verified", True)
