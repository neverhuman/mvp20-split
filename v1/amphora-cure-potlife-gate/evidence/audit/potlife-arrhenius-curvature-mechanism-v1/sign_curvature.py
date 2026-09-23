#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cure-potlife-gate CURVATURE-MECHANISM AUDIT_ONLY
receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED/PRE_PHASE_0), does NOT modify the
portfolio manifest (66 receipts / 11 modules), the locked known-answer dataset,
the signed Arrhenius Phase-0 KPI, or any prior signed receipt. Derived key_id
cross-checked vs the pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
BENCH = MOD / "evidence/audit/potlife-arrhenius-curvature-mechanism-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
KPI = MOD / "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
RESULT = MOD / "evidence/phase0/benchmark/result.v1.json"
KA = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"
PRIOR = [
    MOD / "evidence/audit/potlife-conformal-interval-v1/potlife-conformal-interval-receipt.v1.dsse.json",
    MOD / "evidence/audit/potlife-mondrian-conformal-v1/potlife-mondrian-conformal-receipt.v1.dsse.json",
    MOD / "evidence/audit/amine-class-parsimony-v1/amine-class-parsimony-receipt.v1.dsse.json",
]


def sha(b): return hashlib.sha256(b).hexdigest()


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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_curvature_mechanism.py").read_bytes())

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

g3 = diag["G3_kamal_sourour_refuted"]
g8 = diag["G8_leave_one_temperature_out"]
g6 = diag["G6_legwise_bias_and_ceiling_breach"]

body_obj = {
    "schema": "amphora.cure-potlife-gate.curvature-mechanism-receipt.v1",
    "module": "amphora-cure-potlife-gate",
    "authority": "AUDIT_ONLY",
    "axis": "THEORY",
    "run_type": diag["run_type"],
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_prior_signed_receipt": False,
    "claim": diag["headline"],
    "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "constants": diag["constants"],
    "dataset": diag["dataset"],
    "results": {
        "reproduces_signed_kpi_mape": diag["G1_reproduces_signed_kpi"]["passed"],
        "n_systems_with_convex_curvature":
            diag["G2_curvature_is_real"]["n_systems_positive_curvature"],
        "observed_mean_curvature_c2": diag["G2_curvature_is_real"]["observed_mean_c2"],
        "rounding_null_p_mean_c2_ge_observed":
            diag["G2_curvature_is_real"]["null_p_mean_c2_ge_observed"],
        "rounding_null_effect_size_sigma":
            diag["G2_curvature_is_real"]["effect_size_sigma_over_null"],
        "kamal_sourour_verdict": g3["verdict"],
        "kamal_sourour_cells_evaluated": g3["cells_evaluated"],
        "kamal_sourour_cells_matching_deficit": g3["cells_reproducing_rho_in_band"],
        "kamal_sourour_cells_matching_deficit_and_curvature":
            g3["cells_reproducing_both_rho_and_curvature_magnitude"],
        "kamal_sourour_curvature_shortfall_factor":
            g3["observed_over_model_max_curvature_ratio"],
        "vft_global_T0_K": diag["G5_vft_alternative"]["global_T0_K"],
        "vft_model_rho": diag["G5_vft_alternative"]["model_mean_rho"],
        "observed_rho": diag["G5_vft_alternative"]["observed_mean_rho"],
        "loto_overall_mape": g8["overall_mape"],
        "loto_winner": g8["winner"],
        "vft_beats_incumbent_out_of_sample": g8["M2_beats_M0"],
        "legs_breaching_kpi_ceiling": g6["legs_breaching_ceiling"],
        "applicability_domain_fail_closed_rate":
            diag["G9_applicability_domain_fail_closed"]["fail_closed_rate"],
    },
    "gates": {
        "G1_reproduces_signed_kpi": diag["G1_reproduces_signed_kpi"],
        "G2_curvature_is_real": {k: v for k, v in diag["G2_curvature_is_real"].items()
                                 if k != "reported_quanta"},
        "G3_kamal_sourour_refuted": {k: v for k, v in g3.items()
                                     if k != "example_rho_matching_cells"},
        "G4_flory_stockmayer_alpha_star_invariance":
            diag["G4_flory_stockmayer_alpha_star_invariance"],
        "G5_vft_alternative": diag["G5_vft_alternative"],
        "G6_legwise_bias_and_ceiling_breach": g6,
        "G7_effective_independence": diag["G7_effective_independence"],
        "G8_leave_one_temperature_out": g8,
        "G9_applicability_domain_fail_closed":
            {k: v for k, v in diag["G9_applicability_domain_fail_closed"].items()
             if k != "probes"},
    },
    "gates_summary": diag["gates_summary"],
    "per_system": diag["per_system"],
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase1_requirement": diag["phase1_requirement"],
    "claim_locks": diag["claim_locks"],
    "provenance": {
        "locked_known_answer_dataset_sha256": sha(KA.read_bytes()),
        "module_benchmark_lock_sha256": sha(BLOCK.read_bytes()),
        "signed_arrhenius_kpi_sha256": sha(KPI.read_bytes()),
        "signed_truth_table_result_sha256": sha(RESULT.read_bytes()),
        "prior_signed_receipts_sha256": {p.parent.name: sha(p.read_bytes())
                                         for p in PRIOR if p.exists()},
        "harness_sha256": harness_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "monte_carlo_seed": 20260730,
        "monte_carlo_draws": 20000,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": ("Reviewer key referenced for provenance only; no independent human "
                 "review performed.")},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cure-potlife-curvature-mechanism-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "potlife-arrhenius-curvature-mechanism-receipt.v1.dsse.json"
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
