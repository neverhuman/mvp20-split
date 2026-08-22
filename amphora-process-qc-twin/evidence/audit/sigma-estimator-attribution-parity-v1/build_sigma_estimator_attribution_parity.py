#!/usr/bin/env python3
"""Build the deterministic diagnostic body for the sigma-estimator-attribution
parity audit (amphora-process-qc-twin, ROTATION-mode attack, no campaign item).

Attacks the sigma-estimator ATTRIBUTION claim embedded in the signed
mr-memory-detector-arl-degradation-v1 receipt (folded into the consolidated
ARL-characterization KPI v2 and restated in mission.md): that
"MRbar/d2(2)" -- not "S/c4(m)" -- is "the estimator the Individuals chart
actually defaults to (operating estimator)". This script performs an
independent, deterministic source-vs-runtime parity check: it does NOT invoke
any RNG, wall clock, or network. All runtime figures it cites were captured
in a prior `cargo test --test qc_sigma_estimator_attribution_probe` run and
are hard-coded here verbatim (bit-exact f64 values), so this build is
reproducible byte-for-byte across replays.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-process-qc-twin/evidence/audit/sigma-estimator-attribution-parity-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def c4(n):
    return math.sqrt(2.0 / (n - 1)) * math.exp(math.lgamma(n / 2.0) - math.lgamma((n - 1) / 2.0))


def raw_s(vals):
    n = len(vals)
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / (n - 1)
    return mean, math.sqrt(var)


def mr_d2(vals):
    diffs = [abs(vals[i] - vals[i - 1]) for i in range(1, len(vals))]
    mrbar = sum(diffs) / len(diffs)
    return mrbar / 1.128, mrbar


# --- identical arrays to the Rust probe (qc_sigma_estimator_attribution_probe.rs) ---
scenario_a = [100.0 + (((i % 5)) - 2) * 0.1 for i in range(20)]
scenario_b = [99.0 + i * (2.0 / 19.0) + (((i % 5)) - 2) * 0.1 for i in range(20)]

meanA, sA = raw_s(scenario_a)
c4_20 = c4(20)
sc4A = sA / c4_20
mrA, mrbarA = mr_d2(scenario_a)

meanB, sB = raw_s(scenario_b)
sc4B = sB / c4_20
mrB, mrbarB = mr_d2(scenario_b)

designed_shift = 100.777981
uclA_mr = meanA + 3.0 * mrA
uclB_mr = meanB + 3.0 * mrB
uclB_raw = meanB + 3.0 * sB

# --- real runtime output, captured from `cargo test --test
# qc_sigma_estimator_attribution_probe -- --nocapture` on this checkout
# (amphora-formulation-capabilities/src/lib.rs sha256 below). Hard-coded here
# (not re-invoked) so this build script is deterministic/replay-safe; the
# capture command and raw stdout line are recorded verbatim in
# runtime_probe.stdout_line for independent re-execution.
runtime_probe = {
    "command": "cargo test --workspace --locked --test qc_sigma_estimator_attribution_probe -- --nocapture",
    "stdout_line": (
        'PROBE_JSON:{"scenario_a_sawtooth":{"baseline_mean":100.0,'
        '"baseline_sigma":0.14509525002200233,"baseline_sigma_bits":4594395627601993973},'
        '"scenario_b_drift_warmup":{"baseline_mean":99.99999999999999,'
        '"baseline_sigma":0.6731906086450297,"baseline_sigma_bits":4604238781493762562,'
        '"cusum_alerts":[],"designed_shift_value":100.777981,"ewma_alerts":[],'
        '"shewhart_alerts":[]}}'
    ),
    "test_result_line": "test probe_sigma_estimator_attribution ... ok",
    "scenario_a_baseline_sigma_runtime": 0.14509525002200233,
    "scenario_b_baseline_sigma_runtime": 0.6731906086450297,
    "scenario_b_alerts_on_designed_shift": {"shewhart": [], "ewma": [], "cusum": []},
}

assert runtime_probe["scenario_a_baseline_sigma_runtime"] == sA, "scenario A runtime/offline raw-S mismatch"
assert runtime_probe["scenario_b_baseline_sigma_runtime"] == sB, "scenario B runtime/offline raw-S mismatch"

body = {
    "schema": "amphora.process-qc-twin.sigma-estimator-attribution-parity-receipt.v1",
    "study_id": "sigma-estimator-attribution-parity-v1",
    "campaign_item_id": "",
    "authority": "AUDIT_ONLY",
    "module": "amphora-process-qc-twin",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": (
        "amphora-process-qc-twin/evidence/audit/mr-memory-detector-arl-degradation-v1/"
        "mr-memory-detector-arl-degradation-receipt.v1.dsse.json (folded into "
        "evidence/phase0/kpis/arl-characterization-consolidated-kpi.v2.json and restated in "
        "docs/mission.md's 'ARL characterization KPI' section), field "
        "estimated_parameter_memory_detectors_MR_d2.sigma_estimator, asserts VERBATIM: "
        "'MRbar/d2(2) -- the estimator the Individuals chart actually defaults to (operating "
        "estimator, not the S/c4 upper bound)'; the twin field "
        "estimated_parameter_memory_detectors_S_c4.sigma_estimator asserts VERBATIM: 'S/c4(m) "
        "(flagged by the source receipt as an UPPER BOUND, not the operating estimator -- see "
        "MRbar/d2 cross below, now CLOSED)'. The receipt's own 'purpose' field states this "
        "attribution is exactly what it exists to test: 'Recomputes the module's guaranteed "
        "30-batch union false-alarm table under the sigma estimator the Individuals chart "
        "actually defaults to.' This attribution -- not merely the false-alarm numbers -- is "
        "the claim under attack here."
    ),
    "claim_verdict": "REFUTED",
    "refutation_criterion_applied": (
        "The attacked field is a factual claim about which sigma estimator the live, checked "
        "amphora-process-qc-twin implementation uses: 'the estimator the Individuals chart "
        "actually defaults to'. This is refuted if direct inspection of the live, checked "
        "source (amphora-formulation-capabilities/src/lib.rs::audit_process_qc, the exact "
        "function mission.md cites as 'the live checked implementation') shows the runtime "
        "computes a different estimator, AND real (not simulated) execution of that function "
        "confirms the mismatch has operational consequence (a genuine out-of-control shift, "
        "flaggable under the claimed estimator's control limits, is missed under the runtime's "
        "actual limits). Both occurred."
    ),
    "source_ground_truth": {
        "live_implementation_function": "amphora-formulation-capabilities/src/lib.rs::audit_process_qc",
        "lib_rs_sha256_as_read_this_audit": sha(ROOT / "amphora-formulation-capabilities/src/lib.rs"),
        "mission_md_cited_lib_rs_sha256": "8b7612325bff9830da1eebd1dc6ba4af411205581ce388c45fdc6be5356edde0",
        "hash_note": (
            "The two hashes above differ. This audit does not adjudicate why (concurrent "
            "unrelated edits by other agents are permitted under this fire's concurrency "
            "model); it is flagged here for transparency and provenance only, and is NOT part "
            "of this receipt's claim_verdict. The sigma formula quoted below was read from the "
            "file at the sha256 this audit actually captured, and cross-confirmed live via "
            "`cargo test` against the same checkout, so this finding is grounded in the exact "
            "bytes that were executed."
        ),
        "sigma_formula_extracted_lines_113_121": (
            "let mean = series.baseline.iter().map(|o| o.value).sum::<f64>() / "
            "series.baseline.len() as f64;\n"
            "let var = series.baseline.iter().map(|o| (o.value - mean).powi(2)).sum::<f64>() "
            "/ (series.baseline.len() - 1) as f64;\n"
            "let sigma = var.sqrt();"
        ),
        "formula_classification": (
            "Bessel-corrected (n-1) sample variance of the full baseline window, square-rooted. "
            "This is the plain (uncorrected-by-c4) sample standard deviation S. It is computed "
            "directly from squared deviations about the baseline mean; the function contains no "
            "consecutive-difference (moving-range) computation anywhere, and no division by a "
            "c4(n) or d2(2) unbiasing constant."
        ),
        "independent_confirmation_the_module_already_blessed": {
            "location": "amphora-formulation-capabilities/tests/process_qc_twin_phase0_kpi.rs",
            "function": "independent_mean_sigma",
            "doc_comment_verbatim": (
                "Independent Rust recompute of baseline mean and sample stdev using the same"
            ),
            "cross_check": (
                "This is the module's own Phase-0 KPI gate's independent recompute, asserted "
                "bit-exact (`.to_bits()` equality) against the runtime's `baseline_mean` / "
                "`baseline_sigma` (shewhart_arith_ok gate). Its own doc comment already labels "
                "the quantity 'sample stdev', not MRbar/d2 -- the module's own blessed ground "
                "truth for 'what the runtime does' independently corroborates this audit's "
                "source reading, using a mechanism (bit-exact to_bits() equality) the module's "
                "own governance already treats as authoritative."
            ),
            "file_sha256": sha(ROOT / "amphora-formulation-capabilities/tests/process_qc_twin_phase0_kpi.rs"),
        },
    },
    "live_runtime_probe": {
        "harness": "amphora-formulation-capabilities/tests/qc_sigma_estimator_attribution_probe.rs",
        "harness_sha256": sha(ROOT / "amphora-formulation-capabilities/tests/qc_sigma_estimator_attribution_probe.rs"),
        "note": (
            "New probe-only test file (no assertions; data capture only). Not a KPI gate; does "
            "not alter or supersede process_qc_twin_phase0_kpi.rs or any signed KPI."
        ),
        **runtime_probe,
    },
    "independent_python_rederivation": {
        "formulas": {
            "raw_S": "sqrt(sum((x_i - mean)^2) / (n-1))  -- identical to lib.rs::audit_process_qc",
            "S_over_c4": "raw_S / c4(n), c4(n)=sqrt(2/(n-1))*Gamma(n/2)/Gamma((n-1)/2)  -- unbiased-for-normal estimator",
            "MRbar_over_d2": "mean(|x_i - x_{i-1}|) / 1.128  -- the estimator the attacked receipt names as operating",
        },
        "c4_20": c4_20,
        "scenario_a_sawtooth_module_own_fixture_pattern": {
            "values": scenario_a,
            "mean": meanA,
            "raw_S": sA,
            "S_over_c4": sc4A,
            "MRbar_over_d2": mrA,
            "MRbar": mrbarA,
            "raw_S_vs_MRbar_d2_relative_diff_pct": (sA - mrA) / mrA * 100.0,
            "runtime_baseline_sigma_matches_raw_S": True,
        },
        "scenario_b_drift_warmup_physically_realistic": {
            "description": (
                "Linear ramp of total range 2.0 across the 20 baseline observations (e.g. a "
                "cure-oven or dispense-head warm-up during pilot onboarding) with the same "
                "local wiggle superimposed as scenario A. Finite, uniquely and strictly "
                "sequenced, non-empty batch ids: passes every existing fail-closed gate in "
                "audit_process_qc (time-ordering, contamination, missingness)."
            ),
            "values": [round(v, 6) for v in scenario_b],
            "mean": meanB,
            "raw_S": sB,
            "S_over_c4": sc4B,
            "MRbar_over_d2": mrB,
            "MRbar": mrbarB,
            "raw_S_vs_MRbar_d2_relative_diff_pct": (sB - mrB) / mrB * 100.0,
            "raw_S_vs_S_over_c4_relative_diff_pct": (sB - sc4B) / sc4B * 100.0,
            "runtime_baseline_sigma_matches_raw_S": True,
        },
        "interpretation": (
            "On the module's own benign closed-form sawtooth fixture, raw S, S/c4, and MRbar/d2 "
            "happen to sit within ~11% of one another -- close enough that the misattribution was "
            "easy to miss and never previously exercised. Under a physically realistic drifting "
            "baseline (a plausible pilot-onboarding warm-up transient, not a contrived edge "
            "case), raw S diverges from MRbar/d2 by 246%, while diverging from S/c4 by only "
            "-1.3% -- i.e. the runtime's ACTUAL estimator tracks the S/c4 family (as expected, "
            "since raw S and S/c4 are both full-sample-variance-based, differing only by a "
            "deterministic bias correction) and does NOT track MRbar/d2 at all. This is the "
            "opposite of the attacked receipt's classification, which treats S/c4 as the "
            "sidelined 'upper bound' and MRbar/d2 as the real operating estimator."
        ),
    },
    "operational_consequence_demonstrated_live": {
        "setup": (
            "Scenario B baseline (drift-warmup) plus one monitoring observation at "
            f"{designed_shift}, designed offline as mean_B + 4*MRbar/d2(2)_B -- a genuine "
            "out-of-control condition that a correctly MRbar/d2-based 3-sigma Shewhart limit "
            "WOULD flag (4 sigma_mr > 3 sigma_mr limit)."
        ),
        "mrbar_d2_based_ucl_scenario_b": uclB_mr,
        "would_flag_under_claimed_operating_estimator": bool(designed_shift > uclB_mr),
        "raw_s_based_ucl_scenario_b_actual_runtime": uclB_raw,
        "runtime_shewhart_alerts_on_designed_shift": runtime_probe["scenario_b_alerts_on_designed_shift"]["shewhart"],
        "runtime_ewma_alerts_on_designed_shift": runtime_probe["scenario_b_alerts_on_designed_shift"]["ewma"],
        "runtime_cusum_alerts_on_designed_shift": runtime_probe["scenario_b_alerts_on_designed_shift"]["cusum"],
        "detected_by_actual_runtime": bool(
            len(runtime_probe["scenario_b_alerts_on_designed_shift"]["shewhart"]) > 0
            or len(runtime_probe["scenario_b_alerts_on_designed_shift"]["ewma"]) > 0
            or len(runtime_probe["scenario_b_alerts_on_designed_shift"]["cusum"]) > 0
        ),
        "conclusion": (
            "A shift that a correctly-attributed MRbar/d2-based limit would catch is missed by "
            "all three detectors (Shewhart, EWMA, CUSUM) in the live, checked runtime under a "
            "physically plausible drifting baseline, because the runtime's real estimator (raw "
            "sample S) inflates under baseline drift in a way MRbar/d2 does not. This is a "
            "directly demonstrated, real (cargo-executed, not simulated) consequence of the "
            "misattribution, not merely a labeling nitpick."
        ),
    },
    "honest_headline": (
        "REFUTED. The signed mr-memory-detector-arl-degradation-v1 receipt (folded into the "
        "consolidated ARL-characterization KPI v2 and restated in mission.md) asserts MRbar/d2(2) "
        "is 'the estimator the Individuals chart actually defaults to (operating estimator)' and "
        "S/c4(m) is merely an 'upper bound, not the operating estimator'. Direct inspection of the "
        "live, checked amphora-formulation-capabilities/src/lib.rs::audit_process_qc function -- "
        "cross-confirmed by the module's own bit-exact independent-recompute Phase-0 gate (which "
        "already labels the quantity 'sample stdev') and by a fresh cargo-executed probe on this "
        "exact checkout -- shows the runtime computes plain (uncorrected) sample standard "
        "deviation over the full baseline window: no moving range is ever computed. This tracks "
        "the S/c4 family (raw_S vs S/c4 diverges only -1.3% on a drifting baseline) and diverges "
        "sharply from MRbar/d2 (+246% on the same input) -- the exact opposite of the attacked "
        "receipt's classification. The consequence is real, not cosmetic: on a physically "
        "plausible drifting baseline, a genuine out-of-control shift that a correctly "
        "MRbar/d2-attributed 3-sigma limit would flag is missed by all three live detectors "
        "(Shewhart, EWMA, CUSUM) because the runtime's actual raw-S estimate inflates under "
        "baseline drift. No receipt on file has ever characterized ARL/false-alarm/recall "
        "degradation under the estimator the runtime actually uses (raw, uncorrected sample S); "
        "the entire consolidated ARL-characterization KPI v2 has, since its first fire, "
        "characterized an estimator (MRbar/d2) the deployed code does not implement."
    ),
    "closes": [
        "Closes whether 'the estimator the Individuals chart actually defaults to' in "
        "mr-memory-detector-arl-degradation-v1 / KPI v2 is factually MRbar/d2, as asserted.",
    ],
    "does_not_close": [
        "Does not re-run the ARL/false-alarm Monte Carlo grid under the TRUE operating estimator "
        "(raw, uncorrected sample S over the baseline window) -- that characterization remains "
        "an open gap and is the natural next repair (would need its own MC study analogous to "
        "estparam-arl-degradation-v1/moving-range-arl-degradation-v1 but keyed to raw S, not "
        "S/c4 or MRbar/d2).",
        "Does not assert which estimator SHOULD be used (that is a module design decision, not "
        "an audit finding); only that the deployed one differs from what was characterized and "
        "labeled 'operating'.",
        "Does not modify, delete, or re-sign mr-memory-detector-arl-degradation-v1, "
        "arl-characterization-consolidated-kpi.v2.json, or any other prior signed receipt "
        "(supersede-never-rewrite; all remain byte-intact on disk).",
    ],
    "provenance": {
        "lib_rs_sha256_as_read": sha(ROOT / "amphora-formulation-capabilities/src/lib.rs"),
        "phase0_kpi_test_sha256": sha(ROOT / "amphora-formulation-capabilities/tests/process_qc_twin_phase0_kpi.rs"),
        "probe_test_sha256": sha(ROOT / "amphora-formulation-capabilities/tests/qc_sigma_estimator_attribution_probe.rs"),
        "attacked_kpi_v2_sha256": sha(ROOT / "amphora-process-qc-twin/evidence/phase0/kpis/arl-characterization-consolidated-kpi.v2.json"),
        "attacked_receipt_sha256": sha(ROOT / "amphora-process-qc-twin/evidence/audit/mr-memory-detector-arl-degradation-v1/mr-memory-detector-arl-degradation-receipt.v1.dsse.json"),
        "benchmark_lock_sha256": sha(ROOT / "amphora-process-qc-twin/evidence/phase0/benchmark/benchmark-lock.v1.json"),
    },
}

OUT.mkdir(parents=True, exist_ok=True)
canon_bytes = json.dumps(body, indent=2, sort_keys=True).encode()
(OUT / "diagnostic.canonical.json").write_bytes(canon_bytes)
print("WROTE diagnostic.canonical.json", hashlib.sha256(canon_bytes).hexdigest())
