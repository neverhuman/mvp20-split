#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score : three-series-barrier-ranking-v1

Executes the mission.md-locked primary KPI test (blinded Kendall tau at
metrics.barrier_index >= 0.50, superior to solids-only and PVC-only hostile
nulls) against the 3 strict, in-class, open-table-read, CC-BY literature
series that campaign item C4 (2026-08-01) hash-locked to bring
strict_literature_count from 2 to 3: asperti2024, zhu2022,
alam2022_pa450_pa3282 (E-series). This is the FIRST execution of this test
against any real data -- it was never run before this fire.

*** ADAPTATION / DEVIATION DISCLOSURE (Nosek et al. 2018 PNAS 115(11):2600-2606
norm, as required by PREREGISTRATION.md "Frozen script hash-lock commitment") ***
This script REUSES, byte-for-byte unchanged in their numerical logic, the core
primitives and pre-committed constants of the frozen
benchmarks/st19168-preregistered-v1/analyze_st19168_preregistered.py
(frozen_script_sha256 recorded below): batch_tau_b, tau_b_point,
all_perm_index_array, exact_or_mc_permutation_pvalue, ALPHA=0.05,
LOCKED_TAU_TARGET=0.50, FEASIBILITY_FLOOR=6, EXACT_ENUM_MAX_N=10.
It DEVIATES structurally from that script in two disclosed ways, both
required by the campaign item's own instructions and neither chosen after
seeing whether they would help or hurt the result:
  1. It evaluates 3 INDEPENDENT within-study series separately (no pooling,
     honoring each source's declared use_limit) instead of one 10-system
     ST-19168 draw -- ST-19168 remains rights-quarantined and untouched.
  2. It does not assume a computable `locked_barrier_index` predictor exists.
     load_systems() in the frozen script required it as a precondition; this
     script instead checks, mechanically, whether it CAN be computed for
     these series (see LOCKED_PREDICTOR_AVAILABILITY below) and reports the
     answer honestly rather than failing to parse.
These are structural/scope adaptations, not statistical-threshold tuning:
alpha, the tau target, the feasibility floor, and the permutation/bootstrap
machinery are all unchanged from the frozen script.

LOCKED_PREDICTOR_AVAILABILITY (mechanical finding, not a per-series data gap):
`metrics.barrier_index` (EisPredictionV1.barrier_index in
amphora-barrier-corrosion-score/src/lib.rs, SHA-256 recorded below) has NO
code path that ever assigns it `Some(..)` -- every constructor site
(EisPredictionV1::abstain, and the two literal struct constructions in
`predict()`) sets it to `None`, and this is exercised and asserted by the
module's own live unit test `test_fit_keeps_endpoints_separate_and_summary_
never_claims_circuit` (`assert!(prediction.barrier_index.is_none())`), which
this fire re-ran live via `cargo test -p amphora-barrier-corrosion-score`
(5/5 passed) immediately before writing this script. Separately and
independently, `predict()` requires an `EisObservationV1` carrying a real
multi-frequency `spectrum: Vec<EisPointV1>`, a `rights_receipt_sha256`, and
`rights_eligible=true` -- none of which exist for asperti2024/zhu2022/
alam2022, whose CC-BY table-reads captured only a single summary metric
(Rc or RP2) per formulation level, not per-frequency spectra or an
instrument-level rights receipt. Both facts independently make
`locked_barrier_index` unavailable for this analysis; this script does not
fabricate a synthetic spectrum to force a number out of the live model, since
that would not be real evidence.

Truth-score sign convention: unlike ST-19168 (rust_creep_mm, lower=better,
negated), all three literature series report resistance-domain metrics
(Rc or RP2 in ohm.cm2 / MOhm.cm2-equivalent) where HIGHER = better barrier,
already matching the "higher truth score = better barrier" convention -- no
negation applied here (this is a metric-domain fact stated in each source's
own extraction, not a choice).

Hostile-null definition (within a single-resin ladder varying one filler/
hardener-ratio variable, matching the already-locked convention from
benchmarks/barrier-null-char-v1, SHA-256 of its signed receipt recorded
below): solids-only and PVC-only both collapse to a single monotone-in-level
predictor, because adding filler (asperti2024, zhu2022) or increasing
hardener stoichiometric ratio (alam2022 E-series) is the ONLY compositional
variable that changes within each ladder. EXCEPTION: alam2022's E-series is
an explicitly unpigmented/clear-coat hardener-ratio study
(`pigment_package: "unpigmented / clear coat hardener-ratio study"`), so its
true PVC = 0 for every system -- a constant, not a monotone ladder. The
PVC-only null is therefore reported as UNDEFINED_DEGENERATE (zero-variance
predictor, tau_b mathematically undefined) for alam2022, not silently
conflated with the solids-only null.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

ALPHA = 0.05
LOCKED_TAU_TARGET = 0.50
FEASIBILITY_FLOOR = 6            # inherited unchanged from the frozen st19168 script
EXACT_ENUM_MAX_N = 10            # inherited unchanged
Z_ALPHA_ONE_SIDED = float(norm.ppf(1 - ALPHA))

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-barrier-corrosion-score"
CORROSION_SERIES = MODULE / "reference/mvp20/data/corrosion_series.json"
ALAM_EXTRACTION = MODULE / "reference/mvp20/data/literature_extractions/alam2022_pa450_pa3282.json"
LIB_RS = MODULE / "src/lib.rs"
FROZEN_SCRIPT = MODULE / "benchmarks/st19168-preregistered-v1/analyze_st19168_preregistered.py"
NULL_CHAR_RECEIPT = MODULE / "benchmarks/barrier-null-char-v1/null_char_receipt.v1.dsse.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# Frozen-script primitives, reused unchanged (see module docstring above for
# the disclosed adaptation). Copied rather than imported so this package is
# self-contained and independently re-runnable/re-hashable.
# ---------------------------------------------------------------------------
def batch_tau_b(X, Y):
    X = np.atleast_2d(X)
    Y = np.atleast_2d(Y)
    n = X.shape[1]
    pi, pj = np.triu_indices(n, k=1)
    xs = np.sign(X[:, pi] - X[:, pj])
    ys = np.sign(Y[:, pi] - Y[:, pj])
    num = (xs * ys).sum(axis=1)
    n0 = n * (n - 1) / 2.0
    n1 = (xs == 0).sum(axis=1)
    n2 = (ys == 0).sum(axis=1)
    denom = np.sqrt((n0 - n1) * (n0 - n2))
    with np.errstate(invalid="ignore", divide="ignore"):
        tau = np.where(denom > 0, num / denom, 0.0)
    return tau, denom > 0


def tau_b_point(x, y):
    tau, valid = batch_tau_b(np.asarray(x)[None, :], np.asarray(y)[None, :])
    return float(tau[0]), bool(valid[0])


def all_perm_index_array(n):
    return np.array(list(itertools.permutations(range(n))), dtype=np.int16)


def exact_permutation_pvalue(x, truth):
    """Exact full-enumeration one-sided permutation p-value for tau_b(x,truth)>0.
    n<=EXACT_ENUM_MAX_N always holds for these series (n=3,4,5), so no Monte
    Carlo fallback branch is needed (the frozen script's MC branch is unused
    here by construction, not by omission)."""
    n = len(truth)
    x = np.asarray(x, dtype=float)
    truth = np.asarray(truth, dtype=float)
    obs_tau, valid = tau_b_point(x, truth)
    if not valid:
        return {
            "observed_tau": None,
            "status": "UNDEFINED_DEGENERATE_PREDICTOR",
            "reason": "predictor has zero variance (all values tied); tau_b denominator is zero",
        }
    idx_perms = all_perm_index_array(n)
    truth_perm = truth[idx_perms]
    x_batch = np.repeat(x[None, :], idx_perms.shape[0], axis=0)
    perm_taus, _ = batch_tau_b(x_batch, truth_perm)
    n_eval = int(idx_perms.shape[0])
    ge = int(np.sum(perm_taus >= obs_tau - 1e-12))
    p = (ge + 1) / (n_eval + 1)
    return {
        "observed_tau": round(obs_tau, 6),
        "status": "OK",
        "method": "exact_full_enumeration",
        "n_reference_permutations": n_eval,
        "p_value_one_sided": round(float(p), 8),
        "min_achievable_p_value_one_sided_at_this_n": round(1.0 / n_eval, 8),
    }


# ---------------------------------------------------------------------------
# Honest power statement (Bonett & Wright 2000, Psychometrika 65(1):23-28,
# DOI:10.1007/BF02294183) -- same closed form already cited in
# PREREGISTRATION.md and in amphora-public-corrosion-benchmark's
# eis-reproducibility-discrimination-power-v1.
# ---------------------------------------------------------------------------
def bonett_wright_n_required(r, power=0.80, alpha=ALPHA):
    z_power = float(norm.ppf(power))
    return 3 + 1.06 * ((Z_ALPHA_ONE_SIDED + z_power) / math.atanh(r)) ** 2


def bonett_wright_achieved_power(r, n):
    if n <= 3:
        return None  # formula degenerate: (n-3) term is zero, no finite power
    z_power = math.atanh(r) * math.sqrt((n - 3) / 1.06) - Z_ALPHA_ONE_SIDED
    return float(norm.cdf(z_power))


def bonett_wright_min_detectable_tau(n, power=0.80, alpha=ALPHA):
    if n <= 3:
        return None  # degenerate: only the r->1 asymptote, not achievable in a finite test
    z_power = float(norm.ppf(power))
    atanh_r = (Z_ALPHA_ONE_SIDED + z_power) * math.sqrt(1.06 / (n - 3))
    r = math.tanh(atanh_r)
    return min(r, 1.0)


# ---------------------------------------------------------------------------
# Series construction (within-study only; no cross-study pooling)
# ---------------------------------------------------------------------------
def build_series_from_corrosion_series(entry):
    levels = entry["levels"]
    values = [float(v) for v in entry["values"]]
    system_ids = [f"{entry['id']}::{lvl}" for lvl in levels]
    numeric_levels = []
    for lvl in levels:
        if isinstance(lvl, (int, float)):
            numeric_levels.append(float(lvl))
        else:
            # ordinal string levels (e.g. "E-0","E-1","E-2"): the trailing
            # integer IS the declared ordinal (more hardener -> higher digit),
            # not an inferred choice -- it is the paper's own label.
            numeric_levels.append(float(str(lvl).rsplit("-", 1)[-1]))
    return {
        "series_id": entry["id"],
        "cite": entry["cite"],
        "doi": entry.get("doi"),
        "variable": entry["variable"],
        "metric": entry["metric"],
        "use_limit": entry["use_limit"],
        "system_ids": system_ids,
        "n_systems": len(values),
        "truth_higher_is_better": values,
        "hostile_null_solids_and_loading_level": numeric_levels,
        "pvc_degenerate": entry["id"].startswith("alam2022"),
    }


def build_alam_f_series_bonus():
    """Companion F-series (PA-3282) from the SAME alam2022 paper -- same
    strict rights, same within-study rule. NOT one of the 3 counted series in
    corrosion_series.json.strict_literature_series; reported as a bonus
    within-study corroboration only, clearly separated from the primary 3."""
    d = json.loads(ALAM_EXTRACTION.read_bytes())
    rows = d["pa3282_series"]["rows"]
    rp2_30d = {r[0]: r[8] for r in rows if r[1] == "30d"}
    order = ["F-0", "F-1", "F-2"]
    values = [float(rp2_30d[k]) for k in order]
    return {
        "series_id": "alam2022_pa450_pa3282__F_series_BONUS_NOT_ONE_OF_THE_3",
        "cite": d["cite"],
        "doi": d["doi"],
        "variable": d["pa3282_series"]["variable"],
        "metric": "RP2 (MOhm-equivalent) @30d saline immersion, PA-3282 series",
        "use_limit": d["use_limit"],
        "system_ids": [f"alam2022_F::{k}" for k in order],
        "n_systems": len(values),
        "truth_higher_is_better": values,
        "hostile_null_solids_and_loading_level": [0.0, 1.0, 2.0],
        "pvc_degenerate": True,
    }


def analyze_series(s):
    n = s["n_systems"]
    truth = s["truth_higher_is_better"]
    solids_null = s["hostile_null_solids_and_loading_level"]

    result = {
        "series_id": s["series_id"],
        "cite": s["cite"],
        "doi": s["doi"],
        "variable": s["variable"],
        "metric": s["metric"],
        "use_limit_honored": s["use_limit"],
        "n_systems": n,
        "system_ids": s["system_ids"],
    }

    result["feasibility"] = "OK" if n >= FEASIBILITY_FLOOR else "FAIL_CLOSED_INSUFFICIENT_N"
    result["feasibility_floor"] = FEASIBILITY_FLOOR

    result["locked_predictor_availability"] = {
        "available": False,
        "reason": (
            "metrics.barrier_index has no code path in the live "
            "amphora-barrier-corrosion-score/src/lib.rs that ever sets it to Some(..); "
            "it is unconditionally None on every EisPredictionV1 construction site "
            "(abstain() and both literal constructions inside predict()), independently "
            "confirmed by re-running the module's own live unit test suite this fire "
            "(cargo test -p amphora-barrier-corrosion-score: 5/5 passed, including "
            "test_fit_keeps_endpoints_separate_and_summary_never_claims_circuit's "
            "assert!(prediction.barrier_index.is_none())). Separately, predict() requires "
            "a full multi-frequency EisObservationV1.spectrum plus a rights_receipt_sha256 "
            "and rights_eligible=true; this literature table-read captured only a single "
            "summary resistance metric per level, not a per-frequency spectrum or an "
            "instrument-level rights receipt, so even a hypothetical working model could "
            "not be fed a real observation for this series."
        ),
    }

    # H1a (primary): tau(locked, truth) > 0 AND >= 0.50 -- structurally NOT_EVALUABLE:
    # the locked predictor does not exist as a computable quantity for this series,
    # independent of and prior to the n<FEASIBILITY_FLOOR gate below.
    result["h1a_primary_locked_vs_truth"] = {
        "hypothesis": "tau_b(locked_barrier_index, truth) > 0, one-sided, AND >= 0.50",
        "verdict": "NOT_EVALUABLE",
        "reason": "locked_barrier_index unavailable (see locked_predictor_availability)",
    }

    # Informational-only (NOT gated -- n below the pre-committed feasibility floor
    # for every one of these 3 series) headroom characterization of the hostile
    # nulls, reusing the exact same tau_b + exact-permutation primitives as the
    # frozen script, extending benchmarks/barrier-null-char-v1's Spearman-based
    # finding to tau-b for protocol consistency.
    solids_info = exact_permutation_pvalue(solids_null, truth)
    result["informational_only_not_gated"] = {
        "note": (
            "n < FEASIBILITY_FLOOR for this series; the frozen protocol's own "
            "pre-committed floor means NO inferential gate is evaluated below. These "
            "numbers are reported for transparency only, exactly as barrier-null-char-v1 "
            "reported Spearman headroom at these same small n -- they are not, and cannot "
            "be treated as, a pass/fail statistical test."
        ),
        "solids_only_null_vs_truth": solids_info,
    }
    if s["pvc_degenerate"]:
        result["informational_only_not_gated"]["pvc_only_null_vs_truth"] = {
            "status": "UNDEFINED_DEGENERATE_PREDICTOR",
            "reason": "PVC=0 (constant) for every system in this series (unpigmented/clear-coat study); tau_b denominator is zero",
        }
    else:
        result["informational_only_not_gated"]["pvc_only_null_vs_truth"] = (
            "identical to solids_only_null_vs_truth: within this single-resin filler "
            "ladder both hostile nulls collapse to the same monotone-in-loading "
            "predictor, matching the already-locked convention in "
            "benchmarks/barrier-null-char-v1 (SHA-256 of its signed receipt recorded in "
            "this receipt's provenance block)."
        )

    result["gate_summary"] = {
        "step1_primary_locked_target": False,
        "step2_superiority_vs_solids": None,
        "step3_superiority_vs_pvc": None,
    }
    result["verdict"] = "NOT_EVALUABLE" if result["feasibility"] == "FAIL_CLOSED_INSUFFICIENT_N" else "LOCKED_KPI_NOT_SUPPORTED"
    result["does_not_close"] = [
        "This is a within-study (no-pooling) analysis of 3 small literature ladders, "
        "not the locked mission.md primary KPI itself (a blinded four-track "
        "independent-panel comparison). It cannot promote authority, phase, or "
        "manifest state on its own.",
    ]
    return result


def honest_power_section(series_results):
    per_series = []
    for r in series_results:
        n = r["n_systems"]
        min_p = round(1.0 / math.factorial(n), 8)
        achieved_power_at_locked_target = bonett_wright_achieved_power(LOCKED_TAU_TARGET, n)
        min_detectable_tau_80pct = bonett_wright_min_detectable_tau(n, power=0.80)
        per_series.append({
            "series_id": r["series_id"],
            "n_systems": n,
            "min_achievable_exact_one_sided_p_value_at_this_n": min_p,
            "can_ever_reach_alpha_0p05_one_sided_at_this_n": bool(min_p < ALPHA),
            "bonett_wright_asymptotic_achieved_power_at_locked_target_tau_0p50": (
                round(achieved_power_at_locked_target, 4) if achieved_power_at_locked_target is not None else None
            ),
            "bonett_wright_asymptotic_min_detectable_tau_at_80pct_power": (
                round(min_detectable_tau_80pct, 4) if min_detectable_tau_80pct is not None else "DEGENERATE_AT_N_LE_3_ONLY_R_TO_1_ASYMPTOTE"
            ),
        })

    n_series_total = len(series_results)
    # meta-level: treat each series' point-estimate direction as one Bernoulli
    # trial in an exact binomial sign test across the "n=3 series" -- the
    # weakest possible aggregation, offered because it is the only test whose
    # minimum achievable p-value can be stated in closed form at n=3 studies.
    min_sign_test_p_at_3_series = round(1.0 / (2 ** n_series_total), 6)

    return {
        "reference": "Bonett & Wright 2000, Psychometrika 65(1):23-28, DOI:10.1007/BF02294183 (same formula cited in PREREGISTRATION.md and reused unchanged)",
        "closed_form_n_required_for_80pct_power_at_locked_target_tau_0p50_alpha_0p05_one_sided": round(
            bonett_wright_n_required(LOCKED_TAU_TARGET), 2
        ),
        "per_series_power_at_actual_n": per_series,
        "per_series_headline": (
            "At the locked target tau=0.50, one-sided alpha=0.05: asperti2024 (n=4) has "
            "~13% asymptotic achieved power and would require an observed tau of ~0.99 to "
            "reach 80% power; zhu2022 (n=5) has ~19% achieved power and would require "
            "tau~0.95; alam2022 E-series (n=3) is combinatorially INCAPABLE of reaching "
            "alpha=0.05 one-sided significance at ANY observed tau (including a perfect "
            "tau=1.0), because with n=3 there are only 3!=6 possible permutations and the "
            "best achievable exact one-sided p-value is 1/6~0.167 > 0.05 -- this is an "
            "exact combinatorial fact, not an asymptotic approximation."
        ),
        "meta_level_n_equals_3_series_statement": {
            "question": "Is tau>=0.5 resolvable using the 3 series as 3 independent units of evidence?",
            "weakest_possible_aggregation": "exact binomial sign test on 3 series-level directional point estimates",
            "min_achievable_one_sided_p_value_at_n_3_series": min_sign_test_p_at_3_series,
            "can_ever_reach_alpha_0p05_at_n_3_series": bool(min_sign_test_p_at_3_series < ALPHA),
            "interpretation": (
                "Even in the best possible case -- all 3 series agreeing in direction -- a "
                "3-unit sign test cannot reach one-sided alpha=0.05 (min p=1/8=0.125). "
                "The honest conclusion is unconditional: tau>=0.5 is NOT resolvable, "
                "in principle, from 3 series of this size, regardless of what the data show. "
                "This mirrors and extends the pre-registered n=10 ST-19168 finding "
                "(~41% achieved power for a SINGLE series at n=10) to the present n=3,4,5 "
                "per-series, n=3-series-of-evidence reality: small-n underpowering is a "
                "structural, recurring, honestly-disclosed property of this module's "
                "literature corroboration, not something this fire's data happened to "
                "produce."
            ),
        },
    }


def run():
    corrosion_bytes = CORROSION_SERIES.read_bytes()
    d = json.loads(corrosion_bytes)
    by_id = {s["id"]: s for s in d["series"]}
    primary_ids = ["asperti2024", "zhu2022", "alam2022_pa450_pa3282"]
    assert set(primary_ids) == set(d["strict_literature_series"]), (
        "primary_ids must exactly match corrosion_series.json's own strict_literature_series"
    )

    primary_series = [build_series_from_corrosion_series(by_id[i]) for i in primary_ids]
    bonus_series = build_alam_f_series_bonus()

    primary_results = [analyze_series(s) for s in primary_series]
    bonus_result = analyze_series(bonus_series)

    evaluable_count = sum(1 for r in primary_results if r["feasibility"] == "OK")
    all_pass = evaluable_count > 0 and all(
        r["gate_summary"]["step1_primary_locked_target"] for r in primary_results if r["feasibility"] == "OK"
    )

    frozen_script_bytes = FROZEN_SCRIPT.read_bytes()
    lib_rs_bytes = LIB_RS.read_bytes()
    null_char_receipt_bytes = NULL_CHAR_RECEIPT.read_bytes()

    result = {
        "schema": "amphora.barrier-corrosion-score.three-series-barrier-ranking-analysis-result.v1",
        "module": "amphora-barrier-corrosion-score",
        "benchmark": "three-series-barrier-ranking-v1",
        "campaign_item_id": "W1",
        "alpha": ALPHA,
        "locked_tau_target": LOCKED_TAU_TARGET,
        "feasibility_floor": FEASIBILITY_FLOOR,
        "provenance": {
            "corrosion_series_json_sha256": sha(corrosion_bytes),
            "frozen_st19168_preregistered_script_sha256": sha(frozen_script_bytes),
            "lib_rs_sha256": sha(lib_rs_bytes),
            "barrier_null_char_v1_receipt_sha256": sha(null_char_receipt_bytes),
            "adaptation_disclosure": (
                "Adapts the frozen st19168-preregistered-v1 script's numerical primitives "
                "and pre-committed constants (unchanged) to 3 independent within-study "
                "literature series instead of one ST-19168 draw; see module docstring for "
                "the full disclosed deviation, per Nosek et al. 2018 PNAS 115(11):2600-2606."
            ),
        },
        "primary_3_series_no_pooling": primary_results,
        "bonus_within_study_corroboration_not_one_of_the_3": bonus_result,
        "aggregate": {
            "n_series_evaluated": len(primary_results),
            "n_series_feasibility_ok": evaluable_count,
            "n_series_locked_predictor_available": 0,
            "locked_kpi_verdict": "LOCKED_KPI_NOT_SUPPORTED_STRUCTURALLY_NOT_EVALUABLE",
            "all_gates_pass": bool(all_pass),
        },
        "honest_power_statement": honest_power_section(primary_results),
        "does_not_close": [
            "This is a within-study (no cross-study pooling), literature-corroboration "
            "analysis of 3 small CC-BY ladders. It is not the mission.md-locked primary "
            "KPI itself (a blinded four-track independent-panel comparison) and cannot "
            "promote authority, phase, or manifest state.",
            "It does not establish, and explicitly refutes as currently evaluable, any "
            "claim that a locked barrier ranking (metrics.barrier_index) outperforms the "
            "solids-only/PVC-only hostile nulls -- the locked predictor is structurally "
            "unavailable in the live implementation, independent of these 3 series' n.",
        ],
    }
    return result


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True)


if __name__ == "__main__":
    import sys
    res = run()
    text = canon(res)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text)
        print("wrote", sys.argv[1])
    else:
        print(text)
    print("RESULT_SHA256", hashlib.sha256(text.encode()).hexdigest(), file=sys.stderr)
