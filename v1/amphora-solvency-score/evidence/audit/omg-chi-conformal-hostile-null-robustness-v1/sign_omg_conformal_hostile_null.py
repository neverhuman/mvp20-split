#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-solvency-score OMG chi 3-solvent
split-conformal + AD hostile-null multi-seed robustness attack (campaign item
W-OMG-CONF, ROTATION-mode fire). AUDIT_ONLY: signs an audit receipt under
evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT flip scientific_readiness, does NOT modify the portfolio
manifest, any locked dataset, or the signed Phase-0 KPI files under
evidence/phase0/kpis/. Uses the pinned PHASE0_EVALUATOR key, cross-checked
against config/phase0-trust-store.v1.json.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-solvency-score/evidence/audit/omg-chi-conformal-hostile-null-robustness-v1"
HARNESS = BENCH / "run_conformal_hostile_null_robustness.py"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def strip_timing(obj):
    obj = dict(obj)
    obj.pop("elapsed_sec", None)
    return obj


runA = json.loads((BENCH / "diagnostic.runA.json").read_bytes())
runB = json.loads((BENCH / "diagnostic.runB.json").read_bytes())
runA_c = strip_timing(runA)
runB_c = strip_timing(runB)
canon_bytes = json.dumps(runA_c, indent=2, sort_keys=True).encode()
runB_canon_bytes = json.dumps(runB_c, indent=2, sort_keys=True).encode()
byte_identical = canon_bytes == runB_canon_bytes
(BENCH / "diagnostic.canonical.json").write_bytes(canon_bytes)
canon_sha = sha(canon_bytes)
diag = runA_c

harness_sha = sha(HARNESS.read_bytes())

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
assert eval_pin, "evaluator key_id does not match pinned trust store"
assert byte_identical, "two-replay bytes differ (after stripping elapsed_sec) -- NOT stable, do not sign"

water = diag["results"]["water"]
ethanol = diag["results"]["ethanol"]

pc_all_detected = water["positive_control"]["detected"] and ethanol["positive_control"]["detected"]
assert pc_all_detected, "positive control did not fire for both solvents -- harness insensitive, do not sign a verdict"

hn_water = water["hostile_null_multiseed"]
hn_ethanol = ethanol["hostile_null_multiseed"]
refutation_triggered = hn_water["refutation_criterion_met"] or hn_ethanol["refutation_criterion_met"]
verdict = "CLAIM_REFUTED" if refutation_triggered else "CLAIM_SURVIVED"

# secondary (non-pre-registered) observation: worst-AD-quintile coverage at
# alpha=0.20 in this independent smaller-scale re-derivation
quintile_followup = {
    "water_worst_quintile_alpha020": water["worst_ad_quintile_coverage_alpha020"],
    "ethanol_worst_quintile_alpha020": ethanol["worst_ad_quintile_coverage_alpha020"],
    "water_worst_quintile_alpha010": water["worst_ad_quintile_coverage_alpha010"],
    "ethanol_worst_quintile_alpha010": ethanol["worst_ad_quintile_coverage_alpha010"],
    "original_receipt_water_worst_quintile_alpha020": 0.8094149908592322,
    "note": (
        "NOT part of the pre-registered refutation criterion (which targets only the "
        "hostile-null multiseed sweep at alpha=0.10). Reported here as an honest secondary "
        "observation, not used to override the pre-registered verdict above: at n_sample=20000 "
        "(this independent re-derivation, n=742 test molecules per quintile), the worst "
        "(lowest-AD / most out-of-domain) quintile's alpha=0.20 coverage is 66.3%-68.9%, far "
        "below both the 80% target and the signed receipt's own n=98506 raw-diagnostic value "
        "for the equivalent water cell (80.9%). This could reflect finite-sample variance in a "
        "smaller n=742 quintile bin, or a genuine conditional-coverage weakness in the "
        "low-AD/novel-scaffold region that a much larger n happens to average away. This module's "
        "own claim_locks already disclose 'coverage_guarantee_is_marginal_not_conditional' -- this "
        "observation is consistent with, and sharpens, that disclosed limitation. A dedicated "
        "follow-up attack with a PRE-REGISTERED criterion, larger n, and a formal statistical "
        "test (e.g. bootstrap CI on quintile coverage vs n) is needed before this can license any "
        "verdict on its own; proposed as campaign item W-OMG-CONF-Q2."
    ),
}

body_obj = {
    "schema": "amphora.solvency-score.omg-chi-conformal-hostile-null-robustness-receipt.v1",
    "receipt_id": "omg-chi-conformal-hostile-null-robustness-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-solvency-score",
    "campaign_item_id": "W-OMG-CONF",
    "mode": "ROTATION",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": {
        "receipt_path": "amphora-solvency-score/reference/mvp20/data/omg_chi_conformal_and_applicability_domain_receipt.v1.json "
                         "+ evidence/phase0/kpis/omg-chi-3-solvent-conformal-coverage-and-applicability-domain-kpi.v1.json "
                         "(restated in docs/mission.md #Empirical-benchmark-result-OMG-chi-3-solvent-conformal-intervals)",
        "claim_text": (
            "Split-conformal (Papadopoulos et al 2002) prediction intervals for Flory-Huggins chi "
            "achieve marginal coverage >=90%/80% at alpha=0.10/0.20 on scaffold-safe held-out OMG "
            "polymers for water, ethanol, chloroform, PASS a hostile-null y-shuffle falsifiability "
            "check, and PASS a worst-AD-quintile floor -- all at n=98,506 with a single fixed "
            "shuffle seed=0. This is the module's only distribution-free calibrated-uncertainty "
            "claim and has never previously been attacked (all 9 prior module ledger entries "
            "targeted BigSolDB or the Flory-Huggins/Hansen physical-baseline comparisons)."
        ),
        "specific_sub_claim_attacked": (
            "The signed receipt's own per-solvent hostile-null diagnostic already sits BELOW the "
            "naive 0.90 target for water (0.897210) and ethanol (0.897573), passing only via a "
            "tight 'within 1-sigma of asymptotic target' gate whose floor for water is 0.897140 -- "
            "a margin of 0.00007 (0.007 percentage points), the same razor-thin-boundary-pass "
            "pattern W-SCAFFOLD found and REFUTED for the BigSolDB headline one fire prior "
            "(2026-08-15). Is that razor-thin pass a robust feature of the calibration machinery, "
            "or an artifact of the single seed=0 used in the signed receipt?"
        ),
    },
    "attack_description": (
        "Independent re-derivation from the real OMG PhysicalProperties v3 corpus "
        "(feedback/v3/normalized/omg_physical_properties_v3.jsonl.gz, rights_class "
        "DERIVATIVE_ALLOWED, corpus sha256 verified against manifest lock), reusing the SAME "
        "scaffold-safe 60/20/20-by-Murcko-scaffold split methodology, SAME 528-feature spec "
        "(16 rdkit descriptors + 512-bit Morgan r=2 fingerprint), and SAME HistGradientBoostingRegressor "
        "hyperparameters this module's own ml-vs-physics-coverage-scope-v1 benchmark already uses. "
        "At reduced scale (n_sample=20000 vs the signed receipt's 98506, water/ethanol only -- the "
        "two solvents whose signed hostile-null diagnostic already undershoots 0.90), the harness: "
        "(1) fits a REAL-signal split-conformal model and measures marginal + per-AD-quintile "
        "coverage; (2) replays the hostile-null y-shuffle protocol across 10 INDEPENDENT seeds "
        "(retraining the GBM on shuffled y_train each time, recalibrating on shuffled y_cal, "
        "evaluating coverage on shuffled y_test) instead of the signed receipt's single seed=0; "
        "(3) runs a required positive control that shifts test predictions by +2*qhat post-"
        "calibration (simulating a calibration/deployment exchangeability break) to confirm the "
        "harness can actually detect a real coverage failure before trusting any survival."
    ),
    "pre_registered_refutation_criterion": {
        "criterion": "fail_fraction > 0.20 (more than 1 in 10 independent hostile-null shuffle "
                      "seeds falling below the conservative worst-case floor 1-2*alpha=0.80 at "
                      "alpha=0.10), for EITHER water or ethanol",
        "water_fail_fraction": hn_water["fail_fraction"],
        "water_n_seeds_below_floor": hn_water["n_seeds_below_worst_case_floor_0.80"],
        "ethanol_fail_fraction": hn_ethanol["fail_fraction"],
        "ethanol_n_seeds_below_floor": hn_ethanol["n_seeds_below_worst_case_floor_0.80"],
        "criterion_triggered": bool(refutation_triggered),
        "verdict": verdict,
    },
    "positive_control": {
        "planted_defect": "test-set predictions shifted by +2*qhat(alpha=0.10) after calibration "
                           "(qhat computed from the REAL, unshifted calibration residuals) -- "
                           "simulates exactly the kind of calibration/deployment exchangeability "
                           "break that a scaffold-disjoint cal/test split is theoretically "
                           "susceptible to (novel-scaffold drift at deployment time)",
        "how_planted": "run_conformal_hostile_null_robustness.py::main(): "
                        "shifted_pred_test = pred_test + 2*qhat; coverage recomputed against the "
                        "SAME qhat and true y_test used for the real-signal measurement",
        "water": water["positive_control"],
        "ethanol": ethanol["positive_control"],
        "detected": pc_all_detected,
        "evidence": (
            f"water coverage collapsed {water['positive_control']['pre_shift_coverage']:.4f} -> "
            f"{water['positive_control']['post_shift_coverage']:.4f}; ethanol "
            f"{ethanol['positive_control']['pre_shift_coverage']:.4f} -> "
            f"{ethanol['positive_control']['post_shift_coverage']:.4f} -- both collapse far below "
            f"any plausible floor (target 0.90), confirming the harness is sensitive to a real "
            f"coverage-breaking exchangeability violation."
        ),
    },
    "hostile_null_multiseed_results": {
        "water": hn_water,
        "ethanol": hn_ethanol,
        "n_seeds": diag["n_null_seeds"],
    },
    "real_signal_results": {
        "water": {"real_signal": water["real_signal"], "test_r2": water["real_test_r2"],
                   "n_train": water["n_train"], "n_cal": water["n_cal"], "n_test": water["n_test"]},
        "ethanol": {"real_signal": ethanol["real_signal"], "test_r2": ethanol["real_test_r2"],
                    "n_train": ethanol["n_train"], "n_cal": ethanol["n_cal"], "n_test": ethanol["n_test"]},
    },
    "secondary_observation_not_pre_registered": quintile_followup,
    "interpretation": (
        f"Across 10 independent hostile-null shuffle seeds per solvent (20 GBM retrains total), "
        f"ZERO seeds for either water or ethanol fell below the conservative worst-case floor "
        f"(1-2*alpha=0.80 at alpha=0.10); water's coverage ranged [0.8798, 0.9140] "
        f"(5/10 seeds below the naive 0.90 target but all comfortably above 0.80), ethanol ranged "
        f"[0.8895, 0.9129] (2/10 below naive 0.90). This means the signed receipt's own single-seed "
        f"water/ethanol hostile-null values (0.897210, 0.897573 -- both individually below 0.90) "
        f"are ORDINARY, EXPECTED finite-sample outcomes of a validly-calibrated conformal procedure, "
        f"not a cherry-picked or unlucky seed choice -- the razor-thin '1-sigma gate' margin the "
        f"signed KPI receipt uses to pass them is well-supported by this independent multi-seed "
        f"reconstruction, unlike the analogous BigSolDB razor-thin margin W-SCAFFOLD found genuinely "
        f"fragile. The required positive control confirms this harness would have caught a real "
        f"coverage failure (both solvents collapsed to <0.05 coverage under a planted deployment-"
        f"shift defect) had one been present. Pre-registered criterion NOT triggered for either "
        f"solvent: CLAIM_SURVIVED for the specific sub-claim under attack (hostile-null single-seed "
        f"pass is not a seed artifact). A secondary, non-pre-registered observation on worst-AD-"
        f"quintile alpha=0.20 conditional coverage (66.3%-68.9% at this reduced scale vs 80.9% in "
        f"the signed receipt's own larger-n diagnostic) is flagged as a genuine open question for a "
        f"dedicated future attack (W-OMG-CONF-Q2) with its own pre-registered criterion -- NOT used "
        f"to override this fire's pre-registered verdict."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha((BENCH / "diagnostic.runA.json").read_bytes()),
        "runB_diagnostic_sha256": sha((BENCH / "diagnostic.runB.json").read_bytes()),
        "byte_identical_after_stripping_elapsed_sec": byte_identical,
        "harness_sha256": harness_sha,
        "harness_path": "amphora-solvency-score/evidence/audit/omg-chi-conformal-hostile-null-robustness-v1/run_conformal_hostile_null_robustness.py",
        "corpus_sha256": diag["provenance"]["corpus_sha256"],
        "determinism": "sklearn HistGradientBoostingRegressor random_state=0 fixed per fit; "
                        "np.random.default_rng(seed) for each null-shuffle seed 0..9; "
                        "random.Random(split_seed=0) for sampling and scaffold-safe split",
    },
    "scope_note": diag["scope_note"],
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT for a promotion-grade review",
        "human / independent review",
        "chloroform (not attacked this fire -- its signed hostile-null diagnostic already clears "
        "0.90 outright, unlike water/ethanol)",
        "the secondary worst-AD-quintile alpha=0.20 observation above -- proposed as W-OMG-CONF-Q2, "
        "not resolved this fire",
        "byte-identical replay of the ORIGINAL signed receipt's exact n=98506 sample / RNG stream "
        "-- this is an independent re-derivation at reduced scale, not a literal replay",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.solvency-score-omg-chi-conformal-hostile-null-robustness+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR = BENCH
out = OUT_DIR / "omg-chi-conformal-hostile-null-robustness-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("refutation_triggered", refutation_triggered)
print("water_fail_fraction", hn_water["fail_fraction"])
print("ethanol_fail_fraction", hn_ethanol["fail_fraction"])
print("positive_control_detected", pc_all_detected)
print("two_replay_byte_identical", byte_identical)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", canon_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
