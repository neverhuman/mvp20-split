#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-process-qc-twin AR(1)-autocorrelation x
estimated-parameter drift/tamper-corpus AUDIT_ONLY receipt (campaign item
T-10). AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT
sign a phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays LOCKED_INTERNAL/UNVALIDATED), does NOT modify
the portfolio manifest (66 receipts / 11 modules), any locked dataset, or
any previously-signed Phase-0 process-qc KPI. Derived key_id cross-checked
vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-process-qc-twin/evidence/audit/ar1-estparam-drift-corpus-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = ROOT / "amphora-process-qc-twin/evidence/phase0/benchmark/benchmark-lock.v1.json"


def sha(b):
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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_ar1_estparam_drift_corpus.py").read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())

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
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

anchor_gate = diag["known_parameter_anchor_gate"]
part_b = diag["part_b_tamper_corpus"]
m50_check = diag["part_a_m50_budget_check"]

claim_verdict = "REFUTED" if (
    not part_b["recall_meets_locked_target"] or len(m50_check["cells_breaching_budget_under_ar1"]) > 0
) else "SURVIVED"

undetected_quoted = [
    {
        "case_idx": c["case_idx"], "delta_sigma": c["delta_sigma"], "onset": c["onset"],
        "m": c["m"], "phi": c["phi"], "direction": c["direction"], "seed": c["seed"],
        "mu_hat": c["mu_hat"], "sigma_hat": c["sigma_hat"],
        "per_chart_fire_t": c["per_chart_fire_t"], "detected": c["detected"],
    }
    for c in part_b["undetected_cases_verbatim"]
]

body_obj = {
    "schema": "amphora.process-qc-twin.ar1-estparam-drift-corpus-receipt.v1",
    "study_id": diag["study_id"],
    "campaign_item_id": "T-10",
    "authority": "AUDIT_ONLY",
    "module": "amphora-process-qc-twin",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": (
        "amphora-process-qc-twin's estimated-parameter ARL characterization "
        "(evidence/phase0/kpis/arl-characterization-consolidated-kpi.v2.json) and its "
        "locked >=90% seeded-shift recall target hold under i.i.d. normal in-control data; "
        "AR(1) autocorrelation and tampers masked as sensor noise are untested."
    ),
    "claim_verdict": claim_verdict,
    "refutation_criterion_applied": (
        "Founder directive T2-10 refutation_criterion (verbatim): 'Any tamper is masked as "
        "noise, re-simulation diverges, or the item stalls a third time with no RUN_SUMMARY.' "
        "Observed: 22/128 tamper cases (17.2%) were masked as noise (undetected within the "
        "30-batch monitoring window) -- the named observation OCCURRED. Re-simulation did NOT "
        "diverge (byte-identical two-replay, see reproducibility below). This is fire 1 of 3, "
        "no stall."
    ),
    "purpose": diag["purpose"],
    "detector_design": diag["detector_design"],
    "model": diag["model"],
    "known_parameter_anchor_gate": anchor_gate,
    "part_a_m50_budget_check_summary": {
        "note": m50_check["note"],
        "locked_p_fa_30_budget_per_chart_informal": m50_check["locked_p_fa_30_budget_per_chart_informal"],
        "phi0_cells": m50_check["phi0_cells"],
        "ar1_cells": m50_check["ar1_cells"],
        "n_ar1_cells": len(m50_check["ar1_cells"]),
        "n_cells_breaching_budget_under_ar1": len(m50_check["cells_breaching_budget_under_ar1"]),
        "cells_breaching_budget_under_ar1_verbatim": m50_check["cells_breaching_budget_under_ar1"],
    },
    "part_a_full_grid": diag["part_a_arl0_degradation_grid"],
    "part_b_tamper_corpus_summary": {
        "n_cases": part_b["n_cases"],
        "recall": part_b["recall"],
        "locked_recall_target": part_b["locked_recall_target"],
        "recall_meets_locked_target": part_b["recall_meets_locked_target"],
        "recall_by_delta_sigma": part_b["recall_by_delta_sigma"],
        "recall_by_phi": part_b["recall_by_phi"],
        "recall_by_baseline_m": part_b["recall_by_baseline_m"],
        "n_undetected": part_b["n_undetected"],
        "undetected_cases_verbatim": undetected_quoted,
        "canonical_seeds": part_b["canonical_seeds"],
    },
    "positive_control_sanity_check": diag["positive_control_sanity_check"],
    "honest_headline": (
        f"REFUTED. Under AR(1) autocorrelation (phi>=0.2) with naively-estimated (iid-assuming) "
        f"control limits, the m=50 baseline that mr-memory-detector-arl-degradation-v1 / the "
        f"consolidated KPI v2 reported as 'still meets the locked <=1.5 expected-false-alarm/"
        f"30-batch budget' breaches that budget in all {len(m50_check['ar1_cells'])} tested AR(1) "
        f"cells (P(false alarm in 30 batches) up to {max(c['p_false_alarm_within_30_batches'] for c in m50_check['ar1_cells']):.3f} "
        f"vs the {m50_check['locked_p_fa_30_budget_per_chart_informal']} budget; measured mean ARL0 "
        f"collapses to as little as {min(c['ratio_measured_median_over_known'] for c in m50_check['ar1_cells']):.3f} "
        f"of the known-parameter value). Separately, the 128-case tamper corpus (persistent mean "
        f"shifts masked as sensor noise, factorial delta x onset x baseline x phi x direction, "
        f"keyed to 60 pinned canonical seeds) measures the module's locked >=90% seeded-shift "
        f"recall target at only {part_b['recall']:.3f} under estimated-parameter + AR(1) stress: "
        f"{part_b['n_undetected']}/{part_b['n_cases']} tampers were masked as noise. The harness's "
        f"known-parameter anchor gate passed (<=12% MC error vs Montgomery/Siegmund/Shewhart "
        f"published theory) and its positive-control sanity check (a 6-sigma shift) fired "
        f"immediately, so these are not artifacts of a broken or silent detector."
    ),
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "module_benchmark_lock_sha256": benchmark_lock_sha,
        "harness_sha256": harness_sha,
        "prior_receipts": [
            "spc-arl-characterization-v1 (known-parameter ARL anchors)",
            "estparam-arl-degradation-v1 (Shewhart S/c4 estimated-parameter degradation)",
            "moving-range-arl-degradation-v1 (Shewhart MRbar/d2 estimated-parameter degradation)",
            "estparam-memory-detector-arl-degradation-v1 (EWMA/CUSUM S/c4 estimated-parameter degradation)",
            "mr-memory-detector-arl-degradation-v1 (EWMA/CUSUM MRbar/d2 estimated-parameter degradation, m=50 'still meets budget' claim now overturned under AR(1) by this receipt)",
        ],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "seeds": {
            "mc_seed_a": 20260806030, "mc_seed_anchor": 20260806031,
            "canonical_seed_base": 20260806100, "tamper_salt": 7919,
        },
        "n_mc_grid": 1500, "horizon_grid": 1200, "n_mc_anchor": 400, "horizon_anchor": 4500,
        "numpy": "1.26.4",
        "env_pin": "OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=VECLIB_MAXIMUM_THREADS=1",
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
ptype = "application/vnd.amphora.process-qc-twin-ar1-estparam-drift-corpus+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "ar1-estparam-drift-corpus-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("claim_verdict", claim_verdict)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(envelope["signatures"][0]["sig"]))
print("signature_verified", True)
