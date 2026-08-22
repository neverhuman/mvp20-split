#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cure-potlife-gate MONDRIAN class-conditional
conformal AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under
evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT flip scientific_readiness (stays UNVALIDATED/PRE_PHASE_0),
does NOT modify the portfolio manifest (66 receipts / 11 modules), any locked
dataset, the signed Arrhenius Phase-0 KPI, or the prior signed marginal-conformal
receipt. Derived key_id cross-checked vs pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cure-potlife-gate/evidence/audit/potlife-mondrian-conformal-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = ROOT / "amphora-cure-potlife-gate/evidence/phase0/benchmark/benchmark-lock.v1.json"
KPI = ROOT / "amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
RESULT = ROOT / "amphora-cure-potlife-gate/evidence/phase0/benchmark/result.v1.json"
PRIOR = ROOT / "amphora-cure-potlife-gate/evidence/audit/potlife-conformal-interval-v1/potlife-conformal-interval-receipt.v1.dsse.json"


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
harness_sha = sha((BENCH / "run_mondrian_conformal.py").read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())
kpi_sha = sha(KPI.read_bytes())
result_sha = sha(RESULT.read_bytes())
prior_sha = sha(PRIOR.read_bytes()) if PRIOR.exists() else None

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

m10 = diag["mondrian_class_conditional"]["alpha_0.10"]
m20 = diag["mondrian_class_conditional"]["alpha_0.20"]
body_obj = {
    "schema": "amphora.cure-potlife-gate.mondrian-conformal-receipt.v1",
    "module": "amphora-cure-potlife-gate",
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_prior_signed_receipt": False,
    "claim": diag["headline"], "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "nonconformity_score": diag["nonconformity_score"],
    "n_points": diag["n_points"], "families": diag["families"],
    "families_independent_systems": diag["families_independent_systems"],
    "within_system_correlation_caveat": diag["within_system_correlation_caveat"],
    "results": {
        "marginal_meets_nominal": diag["gates"]["G1_marginal_still_meets_nominal"]["passed"],
        "mondrian_min_class_size_finite_90pct": diag["phase1_data_requirement"]["min_held_out_points_per_class_for_finite_90pct_band"],
        "mondrian_min_class_size_finite_80pct": diag["phase1_data_requirement"]["min_held_out_points_per_class_for_finite_80pct_band"],
        "current_max_class_size": diag["phase1_data_requirement"]["current_max_class_size"],
        "n_classes_finite_90pct": m10["n_classes_with_finite_band"],
        "n_classes_finite_80pct": m20["n_classes_with_finite_band"],
        "n_classes_conditionally_valid_80pct": m20["n_classes_conditionally_valid"],
        "aromatic_amine_conditional_coverage_80pct": diag["gates"]["G2_aromatic_amine_conditional_fixed_at_80pct"]["empirical_class_conditional_coverage"],
        "worst_class_conditional_coverage_80pct": m20["worst_class_conditional_coverage_among_finite"],
        "90pct_class_conditional_data_starved": diag["gates"]["G5_90pct_class_conditional_data_starved"]["confirmed"],
        "mape_ties_to_signed_kpi": diag["gates"]["G4_mape_reproduces_signed_kpi"]["passed"],
        "score_fail_closed_rate": f'{diag["gates"]["G3_score_fail_closed"]["n_fail_closed"]}/{diag["gates"]["G3_score_fail_closed"]["n_probes"]}',
    },
    "gates": diag["gates"],
    "marginal_jackknife_plus_anchor": diag["marginal_jackknife_plus_anchor"],
    "mondrian_feasibility": diag["mondrian_feasibility"],
    "mondrian_class_conditional": diag["mondrian_class_conditional"],
    "phase1_data_requirement": diag["phase1_data_requirement"],
    "crosscheck_mape_vs_signed_kpi": diag["crosscheck_mape_vs_signed_kpi"],
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "claim_locks": diag["claim_locks"],
    "provenance": {
        "module_benchmark_lock_sha256": benchmark_lock_sha,
        "signed_arrhenius_kpi_sha256": kpi_sha,
        "signed_truth_table_result_sha256": result_sha,
        "prior_marginal_conformal_receipt_sha256": prior_sha,
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
ptype = "application/vnd.amphora.cure-potlife-mondrian-conformal-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "potlife-mondrian-conformal-receipt.v1.dsse.json"
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
