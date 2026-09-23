#!/usr/bin/env python3
"""R-C01 fire-1 checkpoint consolidation: deterministically summarizes the
three repair attempts already run this fire against the identical pinned
60-seed scaffold-disjoint Monte Carlo protocol. Pure function of already-
computed, checked-in diagnostic files -- no randomness, run twice to prove
byte-stability (two-replay gate) for the signed checkpoint receipt.
"""
import json
import hashlib


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


WORK = "amphora-tolerance-robustness/evidence/phase0/repairs/R-C01/work"

d1 = json.load(open(f"{WORK}/diagnostic.canonical.json"))
d2 = json.load(open(f"{WORK}/cvplus_diagnostic.canonical.json"))
d3 = json.load(open(f"{WORK}/cvplus_v2_diagnostic.canonical.json"))

out = {
    "campaign_item_id": "R-C01",
    "claim_under_attack": {
        "claim_text": "A scaffold-aware conformal calibrator achieves mean coverage >= 0.90 under the SAME 60-seed scaffold-safe MC that refuted the 0.9683 claim (observed mean 0.8746).",
        "receipt_path": "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/",
    },
    "pinned_attack": {
        "script_path": "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/run_repeated_scaffold_conformal.py",
        "script_sha256": "96be585e27428a1f9bec0a7e2c078f9488711df5515790bc24ac35ac97cf0e09",
        "modified": False,
        "diagnostic_path": "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/diagnostic.canonical.json",
        "diagnostic_sha256": "4d4582e74ca2fc8b2566fd9336bcff6594ecc8837a40195b417c66a9d37756f9",
        "n_seeds": 60,
        "seeds": "0..59, identical to the refuting receipt",
        "original_mean_coverage_refuted": 0.8745741048157474,
        "original_ci_95": [0.8496965095063559, 0.8973702091130503],
    },
    "acceptance_criterion": "mean coverage_scaffold_safe over the identical 60-seed protocol >= 0.90",
    "attempts": [
        {
            "id": "attempt1_weighted_conformal_tibshirani2019",
            "method": "Classifier-based (LogisticRegression) covariate-shift weighted split-conformal, Tibshirani, Barber, Candes, Ramdas (2019) NeurIPS 'Conformal Prediction Under Covariate Shift'. Weight = odds(p_hat(test|x)) from a train_pool-vs-test discriminator on the same Morgan512+log10MW features, clipped to [1e-3,1-1e-3] only for numerical stability (not tuned).",
            "script": "run_weighted_conformal_repair.py",
            "script_sha256": sha(f"{WORK}/run_weighted_conformal_repair.py"),
            "splits_identical_to_pinned_attack": d1["parity_check_vs_refuting_receipt"]["splits_identical"],
            "result": {
                "coverage_mean": d1["summary_stats"]["coverage_weighted_mean"],
                "mean_frac_unbounded_intervals": d1["summary_stats"]["mean_frac_unbounded_intervals"],
            },
            "verdict": "DEGENERATE_NOT_A_REPAIR",
            "diagnosis": "Scaffold-safe splits have ZERO scaffold overlap between train_pool and test by construction, and Morgan fingerprints substantially encode scaffold identity, so the discriminator separates the two populations almost perfectly (p_test~=1 for essentially every test point after clipping). Every test point's own normalized weight then dominates its calibration set's total weight, driving every weighted quantile to +inf. Result: mean 'coverage' = 1.0 but frac_unbounded_intervals = 1.0 -- every interval is the entire real line. This is vacuous/undeployable, not a genuine repair, and is reported honestly rather than claimed as a survival.",
        },
        {
            "id": "attempt2_scaffold_cvplus_simplified",
            "method": "Scaffold-grouped leave-one-scaffold-out residual pool (CV+ style, Barber, Candes, Ramdas, Tibshirani 2021 Ann. Statist. 49(1)), SIMPLIFIED: pooled out-of-fold |residual| quantile applied around a single final full-train_pool-fit prediction (understates true CV+ width by collapsing fold-to-fold model variability).",
            "script": "run_scaffold_cvplus_repair.py",
            "script_sha256": sha(f"{WORK}/run_scaffold_cvplus_repair.py"),
            "splits_identical_to_pinned_attack": d2["parity_check_vs_refuting_receipt"]["splits_identical"],
            "result": d2["summary_stats"],
            "verdict": "INFORMATIVE_INSUFFICIENT",
            "diagnosis": "Mean coverage improved from 0.8746 (unrepaired) to 0.8825 (modest +0.008, mean width inflation 1.09x) by removing in-distribution leakage between the attacked protocol's random point-level calib/proper_train split (which does not respect scaffold boundaries). Still short of the 0.90 floor: 28/60 seeds remain below 0.90.",
        },
        {
            "id": "attempt3_scaffold_cvplus_correct",
            "method": "CORRECT scaffold-grouped CV+ construction per Barber et al. 2021: per-test-point asymmetric bounds from order statistics of {mu_{-g(i)}(x_test) +/- R_i^CV} across all n_pool training points, alpha=0.05 (same nominal target as the attacked KPI, not tuned against any 60-seed outcome).",
            "script": "run_scaffold_cvplus_v2.py",
            "script_sha256": sha(f"{WORK}/run_scaffold_cvplus_v2.py"),
            "splits_identical_to_pinned_attack": d3["parity_check_vs_refuting_receipt"]["splits_identical"],
            "result": d3["summary_stats"],
            "verdict": "WORSE_THAN_ATTEMPT2",
            "diagnosis": "Mean coverage 0.8619, WORSE than both the unrepaired baseline (0.8746) and the simplified attempt #2 (0.8825). Root cause: 7/60 seeds have train_pool < 30 points (range 13-266, driven by heavy Bemis-Murcko scaffold-size skew in OpenPoly -- a few giant scaffolds can absorb most of the 40% test-fraction target, starving train_pool for that draw). With very few scaffold folds, individual fold-excluded Ridge models (512+1 features on as few as ~13 points) are extremely high-variance extrapolators, and the CV+ order-statistic construction is itself only asymptotically well-behaved with many folds -- amplifying rather than damping noise for these seeds. This is a genuine, informative negative result: naive CV+ generalization is not a free win under this dataset's severe per-seed scaffold-size skew.",
        },
    ],
    "root_cause_common_to_all_attempts": "OpenPoly Tg's Bemis-Murcko scaffold-size distribution is highly skewed. The pinned 60-seed protocol assigns whole scaffolds to test until reaching ~40% of n_total; for several seeds this consumes nearly all of the dataset (train_pool as small as 13 points, n_test up to 424/443), leaving too little calibration-side data for ANY calibration method (weighted, Mondrian, or CV+) to produce a stable, informative correction. Any repair strategy pursued in a future fire on this item should explicitly address (or explicitly bound the impact of) these degenerate small-train_pool seeds rather than treating all 60 seeds as uniformly tractable.",
    "acceptance_met_this_fire": False,
    "repair_status": "in_progress",
    "next_fire_pre_registered_direction": "Two candidate directions for fire 2, NEITHER tuned against this fire's 60-seed outcomes (both derivable from calibration-side data / theory alone before re-running the pinned protocol): (a) Mondrian conformal stratified by a FIXED, data-only (non-seed-dependent) scaffold clustering (e.g. Butina clustering on scaffold Morgan fingerprints at a pre-chosen similarity threshold, computed once from the full scaffold set, independent of any MC seed) with an explicit small-cluster fallback-to-global rule, analogous to this module's own existing Mondrian audit chain; (b) explicitly bound and separately report coverage on the degenerate small-train_pool seeds (e.g. train_pool < 30) versus the well-powered seeds, since a single pooled mean coverage number conflates a data-scarcity failure mode with a calibration-method failure mode -- an honest re-scope receipt may be the correct outcome if the degenerate seeds turn out to be structurally unrepairable from calibration-side choices alone.",
}

body = json.dumps(out, indent=2, sort_keys=True)
print(body)
