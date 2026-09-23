#!/usr/bin/env python3
"""
Supersedes arl-characterization-consolidated-kpi.v1.json (campaign item
V1-KPI-QC). v1 indexed 4 signed AUDIT_ONLY ARL-degradation receipts and
explicitly listed a 5th (mr-memory-detector-arl-degradation-v1, the MRbar/d2 x
EWMA/CUSUM cross) under `awaiting`, not yet signed. That 5th receipt is now
signed (campaign item W-QC, fire 1). This v2 supersedes v1 to fold it in.
v1 is NOT deleted or modified (supersede-never-rewrite); its path and sha256
are recorded in this receipt's `supersedes` block, and this receipt performs
no new statistical test -- it restates already-measured values from 5
already-signed receipts.
"""
import base64, hashlib, json, os, sys

MODULE_ROOT = "/home/ubuntu/amphora/build/mvp20-split/amphora-process-qc-twin"
SEED_PATH = "/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed"
V1_PATH = "evidence/phase0/kpis/arl-characterization-consolidated-kpi.v1.json"

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dsse_payload(path):
    d = json.load(open(path))
    sig = d.get("signature", d)
    payload = json.loads(base64.b64decode(sig["payload"]))
    return d, sig, payload


def build():
    os.chdir(MODULE_ROOT)

    audits = [
        ("evidence/audit/spc-arl-characterization-v1/"
         "spc-arl-characterization-receipt.v1.dsse.json"),
        ("evidence/audit/estparam-arl-degradation-v1/"
         "estparam-arl-degradation-receipt.v1.dsse.json"),
        ("evidence/audit/moving-range-arl-degradation-v1/"
         "moving-range-arl-degradation-receipt.v1.dsse.json"),
        ("evidence/audit/estparam-memory-detector-arl-degradation-v1/"
         "estparam-memory-detector-arl-degradation-receipt.v1.dsse.json"),
        ("evidence/audit/mr-memory-detector-arl-degradation-v1/"
         "mr-memory-detector-arl-degradation-receipt.v1.dsse.json"),
    ]

    audit_index = []
    for rel in audits:
        raw, sig, payload = load_dsse_payload(rel)
        audit_index.append({
            "study_id": payload.get("study_id"),
            "receipt_path": rel,
            "receipt_sha256": sha256_file(rel),
            "evaluator_key_id": raw.get("evaluator_key_id"),
            "authority": payload.get("authority"),
            "claim": payload.get("claim"),
            "all_known_answer_gates_passed": payload.get("results", {}).get(
                "all_known_answer_gates_passed"),
            "does_not_close": payload.get("does_not_close", []),
        })

    r_spc = load_dsse_payload(audits[0])[2]["results"]
    r_est_s = load_dsse_payload(audits[1])[2]["results"]
    r_mr = load_dsse_payload(audits[2])[2]["results"]
    r_mem = load_dsse_payload(audits[3])[2]["results"]
    r_mrmem = load_dsse_payload(audits[4])[2]["results"]

    known_parameter_reference = {
        "shewhart_arl0_3sigma": 370.4,
        "shewhart_geometric_max_rel_err_vs_published": r_spc["shewhart_geometric_max_rel_err"],
        "ewma_arl0_lambda0p2_L3": r_spc["ewma_module_arl0_lam0.2_L3"],
        "cusum_siegmund_max_rel_err_vs_montgomery_t9p4": r_spc["cusum_siegmund_max_rel_err"],
        "kpi_arl1_at_1sigma": r_spc["kpi_arl1_at_1sigma"],
        "kpi_union_false_alarms_per_30_batch_known_parameter": r_spc["kpi_union_false_alarms_per_30_batch"],
        "source": "spc-arl-characterization-v1",
    }

    estimated_parameter_shewhart_S_c4 = {
        "sigma_estimator": "S/c4(m)",
        "m20_guaranteed_arl0_p05": r_est_s["m20_guaranteed_arl0_p05"],
        "m20_median_arl0": r_est_s["m20_median_arl0"],
        "m30_guaranteed_arl0_p05": r_est_s["m30_guaranteed_arl0_p05"],
        "m30_median_arl0": r_est_s["m30_median_arl0"],
        "m300_guaranteed_arl0_p05": r_est_s["m300_guaranteed_arl0_p05"],
        "smallest_tabulated_m_meeting_p05_ge_200": r_est_s["smallest_tabulated_m_meeting_p05_ge_200"],
        "source": "estparam-arl-degradation-v1",
    }

    estimated_parameter_shewhart_MR_d2 = {
        "sigma_estimator": "MRbar/d2(2)",
        "asymptotic_relative_efficiency_vs_Sc4": r_mr["asymptotic_relative_efficiency_MR_vs_Sc4"],
        "m20_guaranteed_arl0_p05": r_mr["MR_m20_guaranteed_arl0_p05"],
        "m30_guaranteed_arl0_p05": r_mr["MR_m30_guaranteed_arl0_p05"],
        "m300_guaranteed_arl0_p05": r_mr["MR_m300_guaranteed_arl0_p05"],
        "smallest_tabulated_m_meeting_p05_ge_200": r_mr["smallest_tabulated_m_meeting_p05_ge_200_MR"],
        "source": "moving-range-arl-degradation-v1",
    }

    estimated_parameter_memory_detectors_S_c4 = {
        "sigma_estimator": "S/c4(m) (flagged by the source receipt as an UPPER BOUND, "
                            "not the operating estimator -- see MRbar/d2 cross below, now CLOSED)",
        "EWMA_m20_guaranteed_arl0_p05": r_mem["EWMA_m20_guaranteed_arl0_p05"],
        "EWMA_m30_guaranteed_arl0_p05": r_mem["EWMA_m30_guaranteed_arl0_p05"],
        "EWMA_m300_guaranteed_arl0_p05": r_mem["EWMA_m300_guaranteed_arl0_p05"],
        "CUSUM_m20_guaranteed_arl0_p05": r_mem["CUSUM_m20_guaranteed_arl0_p05"],
        "CUSUM_m30_guaranteed_arl0_p05": r_mem["CUSUM_m30_guaranteed_arl0_p05"],
        "CUSUM_m300_guaranteed_arl0_p05": r_mem["CUSUM_m300_guaranteed_arl0_p05"],
        "guaranteed_arl0_retention_at_m30_vs_known_parameter": r_mem[
            "guaranteed_arl0_retention_at_m30_vs_known_parameter"],
        "worst_degrading_arm_at_m30": r_mem["worst_degrading_arm_at_m30"],
        "union_false_alarms_per_30_batch_p95_by_m": {
            "m20": r_mem["union_fa_p95_per_30_batch_m20"],
            "m30": r_mem["union_fa_p95_per_30_batch_m30"],
            "m50": r_mem["union_fa_p95_per_30_batch_m50"],
            "m100": r_mem["union_fa_p95_per_30_batch_m100"],
        },
        "false_alarm_budget_per_30_batch": 1.5,
        "smallest_tabulated_m_meeting_fa_budget": r_mem["smallest_tabulated_m_meeting_fa_budget"],
        "m30_meets_locked_false_alarm_budget": r_mem["m30_meets_locked_false_alarm_budget"],
        "source": "estparam-memory-detector-arl-degradation-v1",
    }

    estimated_parameter_memory_detectors_MR_d2 = {
        "sigma_estimator": "MRbar/d2(2) -- the estimator the Individuals chart actually "
                            "defaults to (operating estimator, not the S/c4 upper bound)",
        "claim_verdict": r_mrmem["claim_verdict"],
        "guaranteed_arl0_retention_at_m30_vs_known_parameter": r_mrmem[
            "guaranteed_arl0_retention_at_m30_vs_known_parameter"],
        "m50_union_fa_p95_MRbar_d2": r_mrmem["m50_union_fa_p95_MRbar_d2"],
        "m50_union_fa_p95_Sc4_prior_receipt": r_mrmem["m50_union_fa_p95_Sc4_prior_receipt"],
        "false_alarm_budget_per_30_batch": 1.5,
        "m50_still_meets_budget_under_MRbar_d2": r_mrmem["m50_still_meets_budget_under_MRbar_d2"],
        "smallest_tabulated_m_meeting_criterion_MRbar_d2": r_mrmem[
            "smallest_tabulated_m_meeting_criterion_MRbar_d2"],
        "smallest_tabulated_m_meeting_criterion_Sc4_prior_receipt": r_mrmem[
            "smallest_tabulated_m_meeting_criterion_Sc4_prior_receipt"],
        "source": "mr-memory-detector-arl-degradation-v1",
    }

    honest_headline = (
        "Known-parameter (infinite-baseline) reference: Shewhart ARL0=370.4, EWMA(0.2,3) "
        f"ARL0={known_parameter_reference['ewma_arl0_lambda0p2_L3']}, union false-alarm rate "
        f"{known_parameter_reference['kpi_union_false_alarms_per_30_batch_known_parameter']} per "
        "30 batches -- all Markov-chain/geometric solvers reproduce published anchors "
        "(Montgomery 2020 Table 9.4; Siegmund 1985; Shewhart 1931) to <=3.1% relative error. "
        "The MRbar/d2 x EWMA/CUSUM cross that v1 of this KPI left open under `awaiting` is now "
        "CLOSED (mr-memory-detector-arl-degradation-v1, SURVIVED): under sigma_hat=MRbar/d2 -- "
        "the estimator the Individuals chart actually defaults to, not the S/c4 upper bound the "
        "module previously reported under -- the guaranteed (5th-percentile) in-control run "
        "length at m=30 retains only "
        f"{estimated_parameter_memory_detectors_MR_d2['guaranteed_arl0_retention_at_m30_vs_known_parameter']} "
        "of the known-parameter value across the three detector arms (worse than the S/c4 figures "
        f"{estimated_parameter_memory_detectors_S_c4['guaranteed_arl0_retention_at_m30_vs_known_parameter']}, "
        "as expected since MRbar/d2 has fewer effective degrees of freedom). The locked "
        "<=1.5-expected-false-alarm/30-batch union budget at the smallest previously-reported "
        f"sufficient baseline m=50 is "
        f"{estimated_parameter_memory_detectors_MR_d2['m50_union_fa_p95_MRbar_d2']} under MRbar/d2 "
        f"(vs {estimated_parameter_memory_detectors_MR_d2['m50_union_fa_p95_Sc4_prior_receipt']} "
        "under S/c4) -- STILL inside the 1.5 budget, and the smallest tabulated baseline meeting "
        "the budget under MRbar/d2 is m=50, UNCHANGED from the S/c4-based figure. The module's "
        "m=20-25 pilot baseline remains roughly half the m=50 baseline this characterization "
        "shows is needed to meet the locked false-alarm budget, under either sigma estimator -- "
        "this is a decision-relevant gap for any prospective 30-batch pilot design, not a "
        "pass/fail on module correctness."
    )

    payload = {
        "$schema": "amphora.module-phase0-kpi.v1",
        "schema": "amphora.process-qc-twin.arl-characterization-consolidated-kpi.v2",
        "kpi_id": "amphora-process-qc-twin-phase0-arl-characterization-consolidated-v2",
        "module_id": "amphora-process-qc-twin",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "REAL_ARITHMETIC",
        "phase": "PRE_PHASE_0",
        "promotes_authority": False,
        "modifies_manifest": False,
        "modifies_signed_phase0_kpi": False,
        "scientific_success_asserted": False,
        "campaign_item_id": "W-QC",
        "supersedes": {
            "superseded_path": V1_PATH,
            "superseded_sha256": sha256_file(V1_PATH),
            "superseded_deleted_or_modified": False,
            "reason": ("v1 indexed 4 signed receipts and explicitly listed a 5th "
                       "(mr-memory-detector-arl-degradation-v1, the MRbar/d2 x EWMA/CUSUM "
                       "cross) under `awaiting`, not yet signed. That receipt is now signed "
                       "(campaign item W-QC). This is not a refutation of v1's content -- "
                       "v1's four restated receipts remain independently valid and unchanged "
                       "-- it is a completion supersession folding in the previously-awaited "
                       "5th result, per supersede-never-rewrite discipline."),
        },
        "capability": (
            "Consolidated index of this module's ARL (average run length) degradation "
            "characterization: known-parameter Shewhart/EWMA/CUSUM anchors validated against "
            "published tables, and estimated-parameter (finite-baseline) degradation of the "
            "guaranteed in-control run length and the three-detector union false-alarm rate, "
            "under both the sample-S/c4 and moving-range MRbar/d2 sigma estimators, now for "
            "BOTH the Shewhart-only and the full EWMA/CUSUM memory-detector stacks. This "
            "receipt fits no new model and runs no new statistical test: it indexes five "
            "already-signed AUDIT_ONLY receipts and restates their measured values."
        ),
        "honest_headline": honest_headline,
        "known_parameter_reference": known_parameter_reference,
        "estimated_parameter_shewhart_S_c4": estimated_parameter_shewhart_S_c4,
        "estimated_parameter_shewhart_MR_d2": estimated_parameter_shewhart_MR_d2,
        "estimated_parameter_memory_detectors_S_c4": estimated_parameter_memory_detectors_S_c4,
        "estimated_parameter_memory_detectors_MR_d2": estimated_parameter_memory_detectors_MR_d2,
        "audit_verdicts_index": audit_index,
        "n_audits_indexed": len(audit_index),
        "n_audits_all_gates_passed": sum(
            1 for a in audit_index if a["all_known_answer_gates_passed"]),
        "claim_locks": {
            "no_batch_release_authority": True,
            "no_manufacturing_qualification_authority": True,
            "no_product_performance_authority": True,
            "no_regulatory_authority": True,
            "no_release_authority": True,
            "no_phase_1_or_phase_2_claim": True,
            "pre_phase_0_research_only": True,
            "declarative_public_baseline_only": True,
            "consolidation_only_no_new_data_fit": True,
        },
        "awaiting": [
            "PHASE0_EVALUATOR signed evaluation.v1.dsse.json / PHASE0_INTERNAL_REVIEWER signed "
            "phase0-review-receipt.v1.json for full Phase-0 promotion (human dual-identity "
            "ceremony; out of this cron's authority).",
            "Prospective time-ordered 30-batch pilot with seeded controls measuring realized "
            "recall/false-alarm/false-release rates -- all figures here are theory "
            "characterizations (i.i.d. normal in-control assumption), not measurements on real "
            "batches.",
            "Out-of-control (ARL1) performance under estimated parameters, and the recall >=90% "
            "half of the module's locked KPI, remain uncharacterized by these five receipts.",
            "Only the span-2 moving range d2(2) is characterized; larger MR spans remain open.",
        ],
        "does_not_close": [
            "No coating-efficacy, product-performance, batch-release, or corrosion-rank "
            "authority.",
            "This receipt indexes and restates already-signed audit verdicts; it performs no new "
            "statistical test and fits no new model.",
            "Does not modify, supersede-in-place, or re-sign any of the five indexed audit "
            "receipts, nor the superseded v1 KPI; all remain independently valid on disk and are "
            "referenced by path + sha256.",
            "i.i.d. normal in-control data is assumed throughout the indexed receipts; "
            "autocorrelation and non-normality are not modeled.",
        ],
    }
    return payload


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()


def pae(payload_type, payload_bytes):
    pt = payload_type.encode()
    return (b"DSSEv1 " + str(len(pt)).encode() + b" " + pt + b" "
            + str(len(payload_bytes)).encode() + b" " + payload_bytes)


def dsse_sign(payload_bytes, payload_type, seed):
    sk = Ed25519PrivateKey.from_private_bytes(seed)
    pub = sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    keyid = "phase0-evaluator-" + hashlib.sha256(pub).hexdigest()
    sig = sk.sign(pae(payload_type, payload_bytes))
    env = {"payload": base64.b64encode(payload_bytes).decode(),
           "payloadType": payload_type,
           "signatures": [{"keyid": keyid, "sig": base64.b64encode(sig).decode()}]}
    return env, keyid, pub, sig


if __name__ == "__main__":
    d1 = build(); b1 = canon(d1); h1 = hashlib.sha256(b1).hexdigest()
    d2 = build(); b2 = canon(d2); h2 = hashlib.sha256(b2).hexdigest()
    assert b1 == b2, "two-replay byte MISMATCH"
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
    print("n_audits_indexed:", d1["n_audits_indexed"],
          "| n_all_gates_passed:", d1["n_audits_all_gates_passed"])

    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        outdir = os.path.join(MODULE_ROOT, "evidence/phase0/kpis")
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "arl-characterization-consolidated-kpi.v2.diagnostic.canonical.json"), "wb") as f:
            f.write(b1)
        with open(os.path.join(outdir, "arl-characterization-consolidated-kpi.v2.diagnostic.runB.json"), "wb") as f:
            f.write(b2)
        seed = open(SEED_PATH, "rb").read().strip()
        if len(seed) != 32:
            try:
                seed = bytes.fromhex(seed.decode())
            except Exception:
                seed = seed[:32]
        pt = "application/vnd.amphora.process-qc-twin-arl-characterization-consolidated-kpi.v2+json"
        env, keyid, pub, sig = dsse_sign(b1, pt, seed)
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(pub).verify(sig, pae(pt, b1))
        receipt = {"signature": env, "evaluator_key_id": keyid,
                   "evaluator_public_key_hex": pub.hex()}
        outpath = os.path.join(outdir, "arl-characterization-consolidated-kpi.v2.json")
        with open(outpath, "w") as f:
            f.write(json.dumps(receipt, indent=2, sort_keys=True))
        print("emitted diagnostic + signed receipt:", outpath)
        print("self_verify_signature", True)
        print("envelope_sha256", hashlib.sha256(open(outpath, "rb").read()).hexdigest())
