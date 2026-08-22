#!/usr/bin/env python3
"""
Promotes the module's ARL-degradation characterization work into a Phase-0 KPI
surface. Campaign item V1-KPI-QC: this module has 4 signed AUDIT_ONLY
ARL-degradation audit receipts (known-parameter anchors; estimated-parameter
Shewhart under S/c4; estimated-parameter Shewhart under MRbar/d2; estimated-
parameter EWMA/CUSUM memory-detector union under S/c4) but had NO
evidence/phase0/kpis/ surface indexing them. This receipt consolidates and
RESTATES already-measured values from those four signed receipts -- it fits no
new model and runs no new statistical test. A 5th audit
(mr-memory-detector-arl-degradation-v1, closing the MRbar/d2 x EWMA/CUSUM
cross) was launched this same fire and is executing in the background; it is
listed under `awaiting` and, if it lands, a later fire should supersede this
KPI to fold it in (never rewrite in place).
"""
import base64, hashlib, json, os, sys

MODULE_ROOT = "/home/ubuntu/amphora/build/mvp20-split/amphora-process-qc-twin"
SEED_PATH = "/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed"

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

    # -------- restated measured values (verbatim from the four signed receipts.results) --------
    spc = audit_index[0]
    est_s = audit_index[1]
    mr = audit_index[2]
    mem = audit_index[3]
    r_spc = load_dsse_payload(audits[0])[2]["results"]
    r_est_s = load_dsse_payload(audits[1])[2]["results"]
    r_mr = load_dsse_payload(audits[2])[2]["results"]
    r_mem = load_dsse_payload(audits[3])[2]["results"]

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
                            "not the operating estimator -- see MRbar/d2 cross below)",
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

    honest_headline = (
        "Known-parameter (infinite-baseline) reference: Shewhart ARL0=370.4, EWMA(0.2,3) "
        f"ARL0={known_parameter_reference['ewma_arl0_lambda0p2_L3']}, union false-alarm rate "
        f"{known_parameter_reference['kpi_union_false_alarms_per_30_batch_known_parameter']} per "
        "30 batches -- all four Markov-chain/geometric solvers reproduce published anchors "
        "(Montgomery 2020 Table 9.4; Siegmund 1985; Shewhart 1931) to <=3.1% relative error. "
        "At the module's actual m=20-25 pilot baseline size (per docs/mission.md), guaranteed "
        "(5th-percentile) in-control run length collapses to roughly 9.5-13.3% of the "
        "known-parameter value at m=30 across all three detector arms "
        f"(retention {estimated_parameter_memory_detectors_S_c4['guaranteed_arl0_retention_at_m30_vs_known_parameter']}), "
        "and the locked <=1.5-expected-false-alarm/30-batch union budget is NOT met at m=30 "
        f"(observed {estimated_parameter_memory_detectors_S_c4['union_false_alarms_per_30_batch_p95_by_m']['m30']} "
        "at p95, under the S/c4 estimator). The smallest tabulated baseline meeting that budget is "
        f"m={estimated_parameter_memory_detectors_S_c4['smallest_tabulated_m_meeting_fa_budget']}, "
        "roughly double the module's current pilot baseline size -- this is a decision-relevant "
        "gap for any prospective 30-batch pilot design, not a pass/fail on module correctness. "
        "That m=50 finding was computed under sigma_hat=S/c4, which the source receipt itself "
        "flags as an upper bound (the MRbar/d2 estimator the Individuals chart actually defaults "
        "to is strictly worse, ARE=0.605); the MRbar/d2 x EWMA/CUSUM cross that would close this "
        "gap is listed under `awaiting` below."
    )

    payload = {
        "$schema": "amphora.module-phase0-kpi.v1",
        "schema": "amphora.process-qc-twin.arl-characterization-consolidated-kpi.v1",
        "kpi_id": "amphora-process-qc-twin-phase0-arl-characterization-consolidated-v1",
        "module_id": "amphora-process-qc-twin",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "REAL_ARITHMETIC",
        "phase": "PRE_PHASE_0",
        "promotes_authority": False,
        "modifies_manifest": False,
        "modifies_signed_phase0_kpi": False,
        "scientific_success_asserted": False,
        "campaign_item_id": "V1-KPI-QC",
        "capability": (
            "Consolidated index of this module's ARL (average run length) degradation "
            "characterization: known-parameter Shewhart/EWMA/CUSUM anchors validated against "
            "published tables, and estimated-parameter (finite-baseline) degradation of the "
            "guaranteed in-control run length and the three-detector union false-alarm rate, "
            "under both the sample-S/c4 and moving-range MRbar/d2 sigma estimators. This "
            "receipt does not fit a new model or run a new statistical test: it indexes four "
            "already-signed AUDIT_ONLY receipts and restates their measured values so the "
            "module's strongest evidence on detector reliability is discoverable from "
            "evidence/phase0/kpis/ instead of only from evidence/audit/."
        ),
        "honest_headline": honest_headline,
        "known_parameter_reference": known_parameter_reference,
        "estimated_parameter_shewhart_S_c4": estimated_parameter_shewhart_S_c4,
        "estimated_parameter_shewhart_MR_d2": estimated_parameter_shewhart_MR_d2,
        "estimated_parameter_memory_detectors_S_c4": estimated_parameter_memory_detectors_S_c4,
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
            "mr-memory-detector-arl-degradation-v1: closes the MRbar/d2 x EWMA/CUSUM cross "
            "(whether the memory-detector arms still meet the m=50 false-alarm budget once fed "
            "the sigma estimator the Individuals chart actually defaults to). Run script is "
            "checked in at evidence/audit/mr-memory-detector-arl-degradation-v1/"
            "run_mr_memory_estparam_arl.py and was launched this same fire; not yet signed. A "
            "later fire should supersede this KPI (never rewrite in place) to fold in the result.",
            "PHASE0_EVALUATOR signed evaluation.v1.dsse.json / PHASE0_INTERNAL_REVIEWER signed "
            "phase0-review-receipt.v1.json for full Phase-0 promotion (human dual-identity "
            "ceremony; out of this cron's authority).",
            "Prospective time-ordered 30-batch pilot with seeded controls measuring realized "
            "recall/false-alarm/false-release rates -- all figures here are theory "
            "characterizations (i.i.d. normal in-control assumption), not measurements on real "
            "batches.",
            "Out-of-control (ARL1) performance under estimated parameters, and the recall >=90% "
            "half of the module's locked KPI, remain uncharacterized by these four receipts.",
        ],
        "does_not_close": [
            "No coating-efficacy, product-performance, batch-release, or corrosion-rank "
            "authority.",
            "This receipt indexes and restates already-signed audit verdicts; it performs no new "
            "statistical test and fits no new model.",
            "Does not modify, supersede, or re-sign the four indexed audit receipts; all remain "
            "independently valid and are referenced by path + sha256.",
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
        with open(os.path.join(outdir, "arl-characterization-consolidated-kpi.diagnostic.canonical.json"), "wb") as f:
            f.write(b1)
        with open(os.path.join(outdir, "arl-characterization-consolidated-kpi.diagnostic.runB.json"), "wb") as f:
            f.write(b2)
        seed = open(SEED_PATH, "rb").read().strip()
        if len(seed) != 32:
            try:
                seed = bytes.fromhex(seed.decode())
            except Exception:
                seed = seed[:32]
        pt = "application/vnd.amphora.process-qc-twin-arl-characterization-consolidated-kpi.v1+json"
        env, keyid, pub, sig = dsse_sign(b1, pt, seed)
        # self-verify before declaring
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(pub).verify(sig, pae(pt, b1))
        receipt = {"signature": env, "evaluator_key_id": keyid,
                   "evaluator_public_key_hex": pub.hex()}
        outpath = os.path.join(outdir, "arl-characterization-consolidated-kpi.v1.json")
        with open(outpath, "w") as f:
            f.write(json.dumps(receipt, indent=2, sort_keys=True))
        print("emitted diagnostic + signed receipt:", outpath)
        print("self_verify_signature", True)
        print("envelope_sha256", hashlib.sha256(open(outpath, "rb").read()).hexdigest())
